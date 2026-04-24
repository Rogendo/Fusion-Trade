# FusionTrade AI — Technical Reference

**Stack:** FastAPI · SQLite · Celery + Redis · JWT Auth · LSTM · PatchTST · FinBERT · Claude Sonnet

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Architectural Decisions](#3-architectural-decisions)
4. [Intelligence Pipeline](#4-intelligence-pipeline)
5. [Database Schema](#5-database-schema)
6. [Environment Configuration](#6-environment-configuration)
7. [Running the Server](#7-running-the-server)
8. [Celery Workers](#8-celery-workers)
9. [Complete Endpoint Reference](#9-complete-endpoint-reference)
10. [curl Test Suite](#10-curl-test-suite)
11. [Known Constraints & Bugs Fixed](#11-known-constraints--bugs-fixed)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FusionTrade AI API                        │
│                 FastAPI on port 2001                         │
├────────────┬──────────────┬──────────────┬──────────────────┤
│  Auth      │  Fusion      │  Journal     │  Newsletter      │
│  /auth/*   │  /fusion/*   │  /journal/*  │  /newsletter/*   │
├────────────┴──────────────┴──────────────┴──────────────────┤
│              Intelligence Layer                              │
│  lstm_service → FX/model_service.py (HuggingFace LSTM)     │
│  patchtst_service → FX/transformers/ (PatchTST)            │
│  news_service → FX/services/news_service.py (RSS feeds)    │
│  sentiment_service → FX/services/sentiment_analyzer.py     │
│  llm_service → Anthropic Claude API (two-phase prompt)     │
├─────────────────────────────────────────────────────────────┤
│              Data Layer                                      │
│  SQLite (fusion_trade.db) · Redis (Celery broker)          │
├─────────────────────────────────────────────────────────────┤
│              Background Workers (Celery)                     │
│  verify journals (15min) · predictions (06:00 UTC)         │
│  newsletter (07:00 UTC, if NEWSLETTER_ENABLED=true)        │
└─────────────────────────────────────────────────────────────┘
```

### FX Project Dependency

FusionTrade reuses the trained LSTM models, FinBERT sentiment analyzer, and news
scraping service from the parent `FX/` project. The `intelligence/` layer wraps
these via `sys.path` injection rather than duplicating 100k+ lines of ML code.

**`FX_PROJECT_PATH`** in `.env` controls where these are loaded from.

> Future goal: migrate all ML services into `fusion_trade/` to make it standalone.

---

## 2. Project Structure

```
fusion_trade/
├── app/
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Pydantic BaseSettings (.env)
│   ├── api/v1/
│   │   ├── auth.py               # 11 auth endpoints
│   │   ├── fusion.py             # Fusion intelligence endpoints
│   │   ├── journal.py            # Trading journal CRUD
│   │   ├── ml.py                 # ML management
│   │   └── newsletter.py         # Newsletter endpoints
│   ├── core/
│   │   ├── database.py           # SQLite engine, get_session()
│   │   ├── deps.py               # JWT auth dependencies
│   │   └── security.py           # bcrypt, JWT creation/decode
│   ├── models/                   # SQLModel table definitions
│   │   ├── user.py
│   │   ├── journal.py            # PredictionJournal
│   │   ├── model_registry.py
│   │   ├── email_verification.py
│   │   ├── password_reset.py
│   │   └── news_cache.py
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── auth.py
│   │   ├── fusion.py             # FusionResponse, SentimentBlock, LLMAnalysisBlock
│   │   └── journal.py
│   └── services/
│       ├── auth_service.py       # Registration, login, reset flow
│       ├── email_service.py      # SMTP Gmail sender
│       ├── fusion_service.py     # Agreement algorithm + scoring
│       ├── journal_service.py    # Trade tracking + verification
│       ├── newsletter_service.py # HTML email generation
│       └── sentiment_cache_service.py
├── intelligence/
│   ├── lstm_service.py           # LSTM inference wrapper
│   ├── patchtst_service.py       # PatchTST inference wrapper
│   ├── news_service.py           # RSS news wrapper (FX project)
│   ├── sentiment_service.py      # FinBERT wrapper (FX project)
│   └── llm_service.py            # Claude two-phase prompt
├── workers/
│   ├── celery_app.py             # Celery + beat schedule
│   └── tasks/
│       ├── verification.py       # Journal outcome verification
│       ├── predictions.py        # Daily LSTM predictions
│       └── newsletter.py         # Scheduled newsletter dispatch
├── data/
│   └── fusion_trade.db           # SQLite database
├── migrations/
│   └── migrate_csv.py            # Import predictions_log.csv
└── .env                          # Configuration
```

---

## 3. Architectural Decisions

### JWT Authentication (python-jose + passlib/bcrypt)

Access tokens expire in 30 minutes, refresh tokens in 7 days. Refresh tokens are delivered as `httpOnly` cookies for XSS protection. Email verification uses single-use 64-char tokens (24h expiry). Password reset tokens expire in 15 minutes.

### Agreement Algorithm

```
BUY   → only if LSTM == BUY  AND PatchTST == BUY  (both must agree)
SELL  → only if LSTM == SELL AND PatchTST == SELL
Otherwise → DIVERGENT (HOLD)
```

### Fusion Score (0–100)

```
Base: 55 (directional) or 30 (HOLD/DIVERGENT)
Weighted by timeframe: 4h=0.35, 1h=0.30, 30m=0.20, 15m=0.15
Model weights:         LSTM=0.60, PatchTST=0.40
Boost:                 confidence × agreement × weight × 50
```

### Dual LSTM Confidence

- `confidence` = magnitude-based: `abs_change × 80–100`, capped 0–1
- `direction_confidence` = LSTM direction head probability (binary classifier)
- These are two separate model outputs and mean different things

### Two-Phase Claude Prompt (No Bias)

Claude receives data in this order to prevent confirmation bias:

**Phase 1 — Independent analysis (price + news + sentiment only)**
> Claude must form its own directional view BEFORE seeing ML predictions

**Phase 2 — Model challenge (ML predictions revealed)**
> Claude explicitly states whether it validates or challenges the fusion verdict
> `validates_fusion: bool` and `divergence_reason: str | None` capture this

### `transformers` Library Shadow Fix

`FX/transformers/__init__.py` is an empty file that shadows HuggingFace's
`transformers` pip package when `FX/` is in `sys.path`. Fix: `app/main.py`
pre-imports `transformers` at startup — before any FX paths are added — so
`sys.modules['transformers']` always points to the real package.

### NEWSLETTER_ENABLED Flag

Daily newsletter is opt-in via env var. The Celery beat schedule is always
registered but the task checks `NEWSLETTER_ENABLED` and returns early if false.
Manual trigger via `POST /api/v1/newsletter/trigger` always sends regardless.

---

## 4. Intelligence Pipeline

### Signal Flow

```
Request: GET /api/v1/fusion/EURUSD=X?include_sentiment=true&include_llm=true

1. fusion_service.get_fusion()
   ├── For each timeframe [15m, 30m, 1h, 4h]:
   │   ├── lstm_service.get_lstm_signal()     → SignalResult (confidence, direction_confidence, OHLCV)
   │   └── patchtst_service.get_patchtst_signal() → SignalResult (prob_up, prob_flat, prob_down)
   │
   ├── Agreement Algorithm → dominant direction
   ├── Fusion Score calculation
   │
   ├── [if include_sentiment=True]
   │   ├── news_service.get_news_for_symbol() → RSS headlines
   │   └── sentiment_service.get_sentiment()  → FinBERT analysis
   │
   └── [if include_llm=True]
       └── llm_service.get_llm_analysis()
           ├── Phase 1: Claude independent analysis
           └── Phase 2: Claude validates/challenges ML signals

2. FusionResponse returned with:
   - symbol, master_fusion_score, verdict, logic{}
   - timeframes{} with per-TF confidence breakdown
   - targets{tp1, sl, atr}
   - sentiment{} (optional)
   - llm_analysis{} (optional)
```

### Performance Characteristics

| Operation | Cold Start | Warm (cached) |
|-----------|-----------|---------------|
| LSTM inference (1 TF) | ~30–60s (HF model download) | ~5–15s per call |
| FinBERT models | ~60–90s (first call ever) | ~15s (news fetch) |
| Claude LLM | — | ~5–15s per API call |
| News RSS fetch | ~10–15s | 15-min cache |

---

## 5. Database Schema

**5 tables in SQLite (`data/fusion_trade.db`):**

```sql
users                  -- id, email, hashed_password, full_name, is_verified, subscription_tier
prediction_journal     -- symbol, interval, signal, lstm_signal, patchtst_signal, fusion_score,
                       -- entry_price, tp1/tp2/tp3, stop_loss, status (PENDING/WIN/LOSS/EXPIRED)
model_registry         -- symbol, interval, model_type, repo_id, win_rate, profit_factor
email_verifications    -- user_id, code, used, expires_at
password_resets        -- user_id, code, used, expires_at
news_cache             -- symbol, sentiment data, cached_at (15-min TTL)
```

---

## 6. Environment Configuration

Edit `fusion_trade/.env`:

```env
# App
APP_NAME=FusionTrade AI
API_PORT=1999            # Server port (use 2001 if 1999 is occupied)
DEBUG=true

# Auth
SECRET_KEY=<change-in-production>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./data/fusion_trade.db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email (Gmail SMTP)
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=your-app-password    # Gmail App Password (not your Gmail password)
SMTP_FROM_ADDRESS=your@gmail.com

# HuggingFace
HF_TOKEN=hf_...
HF_LSTM_REPO=rogendo/forex-lstm-models
HF_TST_REPO=rogendo/forex-patchtst-models

# Claude AI
CLAUDE_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-20250514

# FX Project Path
FX_PROJECT_PATH=/home/naynek/Desktop/Backup/FX/FX

# Newsletter
NEWSLETTER_ENABLED=false          # Set to true for automatic daily emails at 07:00 UTC
```

---

## 7. Running the Server

**Activate the venv first:**
```bash
source /home/naynek/Desktop/Backup/FX/FX/venv/bin/activate
cd /home/naynek/Desktop/Backup/FX/fusion_trade
```

**Start the API server:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 2001 --reload
```

**Swagger UI:** http://127.0.0.1:2001/docs  
**ReDoc:** http://127.0.0.1:2001/redoc  
**OpenAPI JSON:** http://127.0.0.1:2001/openapi.json

---

## 8. Celery Workers

Requires Redis running:
```bash
redis-server &
```

**Start Celery worker:**
```bash
cd /home/naynek/Desktop/Backup/FX/fusion_trade
celery -A workers.celery_app worker --loglevel=info
```

**Start Celery Beat (scheduler):**
```bash
celery -A workers.celery_app beat --loglevel=info
```

**Beat schedule:**
| Task | Schedule | Purpose |
|------|---------|---------|
| `verify-pending-journals` | Every 15 minutes | Check PENDING journal entries against live prices; mark WIN/LOSS/EXPIRED |
| `daily-predictions` | 06:00 UTC | Run LSTM inference for all symbols, save to journal |
| `daily-newsletter` | 07:00 UTC | Send newsletter if `NEWSLETTER_ENABLED=true`; manual trigger always works |

---

## 9. Complete Endpoint Reference

### Auth (`/api/v1/auth`)
| Method | Endpoint | Auth | Description |
|--------|---------|------|-------------|
| POST | `/register` | No | Register new user; sends verification email |
| POST | `/login` | No | Login; returns access_token + sets refresh cookie |
| POST | `/refresh` | Cookie | Get new access token using refresh cookie |
| POST | `/logout` | Bearer | Clears refresh cookie |
| GET | `/me` | Bearer | Get current user profile |
| PUT | `/me` | Bearer | Update full_name or hf_token |
| POST | `/verify-email` | No | Verify email with code from link |
| POST | `/resend-verification` | No | Resend verification email |
| POST | `/forgot-password` | No | Send password reset email |
| POST | `/reset-password` | No | Reset password with code from link |
| POST | `/change-password` | Bearer | Change password (requires current password) |

### Fusion Intelligence (`/api/v1/fusion`)
| Method | Endpoint | Query Params | Description |
|--------|---------|-------------|-------------|
| GET | `/{symbol}` | `include_sentiment=true`, `include_llm=false` | Full fusion: LSTM + PatchTST + optional FinBERT + optional Claude |
| GET | `/{symbol}/sentiment` | — | Standalone FinBERT news sentiment (no ML inference) |
| POST | `/{symbol}/llm-analysis` | — | Standalone Claude two-phase analysis |
| POST | `/analyze` | — | POST version of GET for frontend |
| POST | `/finetune` | — | Queue transfer-learning job via Celery |

**Symbols:** `EURUSD=X`, `GBPUSD=X`, `GC=F` (Gold), `BTC-USD`, `USDJPY=X`, etc.

### Trading Journal (`/api/v1/journal`)
| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/` | List journal entries (paginated, filterable by status/symbol) |
| GET | `/stats` | Win rate, profit factor, total pips, max drawdown |
| GET | `/{entry_id}` | Single journal entry |
| POST | `/verify-now` | Manually trigger outcome verification (normally done by Celery) |

### ML Management (`/api/v1/ml`)
| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/registry` | List registered model versions |
| POST | `/predict/trigger` | Queue LSTM prediction job via Celery |
| POST | `/backtest/trigger` | Queue backtest via Celery |

> Note: `/predict/trigger` and `/backtest/trigger` require Redis + Celery worker running.

### Newsletter (`/api/v1/newsletter`)
| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/status` | SMTP config + NEWSLETTER_ENABLED flag |
| POST | `/preview` | Generate HTML without sending (preview only) |
| POST | `/send` | Generate and send immediately |
| POST | `/trigger` | Queue send via Celery worker (async) |

### Newsletter Email Quality

The HTML email includes per symbol:
- **Header:** FusionTrade AI logo, date, pair count with bullish/bearish/divergent summary
- **Per symbol block:**
  - Fusion verdict badge (color-coded: green=BUY, red=SELL, orange=HOLD)
  - Fusion score bar (0–100 with color gradient)
  - Timeframe confluence grid (LSTM signal + confidence + direction_confidence vs PatchTST probabilities)
  - TP1/SL/ATR targets
  - FinBERT sentiment bar (overall sentiment, score, bias, headline counts)
  - Claude LLM synopsis (if `include_llm=true`: independent bias, validates/challenges fusion, entry strategy)
  - Reasoning paragraph
- **Footer:** Disclaimer

---

## 10. curl Test Suite

### Setup

```bash
# Start server first
cd /home/naynek/Desktop/Backup/FX/fusion_trade
source /home/naynek/Desktop/Backup/FX/FX/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 2001

# In another terminal, get a token
TOKEN=$(curl -s -X POST http://127.0.0.1:2001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"devtest@fusiontrade.ai","password":"DevTest123!"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))")
echo "Token: ${TOKEN:0:40}..."
```

### Health

```bash
curl http://127.0.0.1:2001/api/health
# Expected: {"status":"healthy","version":"1.0.0","service":"FusionTrade AI"}
```

### Auth Endpoints

```bash
# Register
curl -s -X POST http://127.0.0.1:2001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"SecurePass123!","full_name":"Your Name"}'

# Login
curl -s -X POST http://127.0.0.1:2001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"SecurePass123!"}'

# Profile
curl -s http://127.0.0.1:2001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Update profile
curl -s -X PUT http://127.0.0.1:2001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"New Name"}'

# Change password
curl -s -X POST http://127.0.0.1:2001/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"OldPass123!","new_password":"NewPass123!"}'

# Forgot password (sends reset email)
curl -s -X POST http://127.0.0.1:2001/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'

# Reset password (use code from email)
curl -s -X POST http://127.0.0.1:2001/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"code":"<code-from-email>","new_password":"NewPass123!"}'

# Verify email (use code from registration email)
curl -s -X POST http://127.0.0.1:2001/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"code":"<code-from-email>"}'

# Logout
curl -s -X POST http://127.0.0.1:2001/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

### Fusion Endpoints

```bash
# Full fusion — LSTM + PatchTST + FinBERT sentiment (default)
# Note: First call takes ~60s (LSTM loads from HuggingFace). Subsequent calls are faster.
curl -s "http://127.0.0.1:2001/api/v1/fusion/EURUSD=X?include_sentiment=true&include_llm=false" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Full fusion with Claude LLM (costs API credits, ~15s additional)
curl -s "http://127.0.0.1:2001/api/v1/fusion/EURUSD=X?include_sentiment=true&include_llm=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# No sentiment (faster — LSTM only)
curl -s "http://127.0.0.1:2001/api/v1/fusion/GBPUSD=X?include_sentiment=false&include_llm=false" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# FinBERT standalone sentiment
# Note: First call loads FinBERT models (~90s). Subsequent calls ~15s (news fetch only).
curl -s "http://127.0.0.1:2001/api/v1/fusion/GC=F/sentiment" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Claude LLM standalone analysis
curl -s -X POST "http://127.0.0.1:2001/api/v1/fusion/EURUSD=X/llm-analysis" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD=X","timeframes":["1h","4h"]}' | python3 -m json.tool

# POST version (for frontend)
curl -s -X POST http://127.0.0.1:2001/api/v1/fusion/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC-USD","include_sentiment":true,"include_llm":false}' \
  | python3 -m json.tool
```

### Expected Fusion Response Structure

```json
{
  "symbol": "EURUSD=X",
  "master_fusion_score": 60.2,
  "verdict": "MODERATE BUY",
  "logic": {
    "primary_lstm": "BUY",
    "secondary_patchtst": "BUY",
    "confluence": true
  },
  "timeframes": {
    "15m": {
      "lstm": "HOLD",
      "patchtst": "N/A",
      "agreement": 0.5,
      "lstm_confidence": 0.0,
      "lstm_direction_confidence": 0.45,
      "lstm_direction_accuracy": 46.3,
      "patchtst_confidence": null,
      "patchtst_prob_up": null,
      "patchtst_prob_flat": null,
      "patchtst_prob_down": null,
      "current_price": 1.15301,
      "predicted_price": 1.15290
    },
    "4h": { "..." : "..." }
  },
  "targets": {
    "tp1": 1.1581,
    "tp2": null,
    "tp3": null,
    "sl": 1.14916,
    "atr": 0.00238
  },
  "reasoning": "LSTM and PatchTST confirm BUY across key timeframes.",
  "sentiment": {
    "overall_sentiment": "bullish",
    "overall_score": 0.175,
    "trading_bias": "BUY",
    "bias_strength": "moderate",
    "positive_count": 6,
    "negative_count": 3,
    "neutral_count": 4,
    "news_count": 15,
    "top_headlines": [
      {"title": "EUR/USD gains on ECB comments", "source": "ForexLive"}
    ]
  },
  "llm_analysis": {
    "action": "BUY",
    "confidence_level": "medium",
    "independent_bias": "Bullish",
    "validates_fusion": true,
    "divergence_reason": null,
    "market_structure": "Strong uptrend with EUR/USD breaking key resistance...",
    "news_impact": "ECB hawkish commentary supports EUR...",
    "entry_strategy": "Enter on pullback to 1.1520 support...",
    "key_levels": {"entry": 1.152, "sl": 1.149, "tp1": 1.158},
    "warnings": ["USD strength could reverse on NFP data", "..."],
    "raw_response": "## A) Market Structure..."
  }
}
```

### Journal Endpoints

```bash
# List entries
curl -s "http://127.0.0.1:2001/api/v1/journal/?limit=10&status=PENDING" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Stats
curl -s http://127.0.0.1:2001/api/v1/journal/stats \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Trigger verification manually (normally Celery does this every 15min)
curl -s -X POST http://127.0.0.1:2001/api/v1/journal/verify-now \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### ML Endpoints

```bash
# Registry
curl -s http://127.0.0.1:2001/api/v1/ml/registry \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Trigger prediction (requires Redis + Celery)
curl -s -X POST http://127.0.0.1:2001/api/v1/ml/predict/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD=X","interval":"4h"}' | python3 -m json.tool
```

### Newsletter Endpoints

```bash
# Status (shows NEWSLETTER_ENABLED flag)
curl -s http://127.0.0.1:2001/api/v1/newsletter/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Preview HTML (no email sent)
curl -s -X POST http://127.0.0.1:2001/api/v1/newsletter/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols":["EURUSD=X","GBPUSD=X"],"include_llm":false,"period":"daily"}' \
  | python3 -m json.tool

# Send immediately
curl -s -X POST http://127.0.0.1:2001/api/v1/newsletter/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols":["EURUSD=X","GBPUSD=X","GC=F","BTC-USD"],"include_llm":false,"period":"daily","recipients":["you@gmail.com"]}' \
  | python3 -m json.tool

# Queue via Celery (requires Redis)
curl -s -X POST http://127.0.0.1:2001/api/v1/newsletter/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols":["EURUSD=X"],"include_llm":false,"period":"daily"}' \
  | python3 -m json.tool
```

### Swagger UI Testing

Visit: **http://127.0.0.1:2001/docs**

1. Click `POST /api/v1/auth/login` → Try it out → `{"email":"devtest@fusiontrade.ai","password":"DevTest123!"}`
2. Copy the `access_token` from the response
3. Click **Authorize** (lock icon, top right) → enter `Bearer <token>`
4. All endpoints are now unlocked for testing

---

## 11. Known Constraints & Bugs Fixed

### Fixed Bugs

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `Extra inputs not permitted` from FX config | FX's config.py reads `.env` relative to CWD; fusion_trade's `.env` has extra keys | `os.chdir(FX_PATH)` before importing model_service |
| `cannot import name 'BertTokenizer' from 'transformers'` | `FX/transformers/__init__.py` (empty file) shadowed HuggingFace package | Pre-import `transformers` in `app/main.py` before FX paths added to sys.path |
| `cannot import name 'sanitize_symbol' from 'config'` | After LSTM adds `FX/` to sys.path, PatchTST's `from config import sanitize_symbol` finds FX/config.py instead of FX/transformers/config.py | Move `FX/transformers/` to position 0 before PatchTST imports |
| `profit_factor=inf` crashing JSON | Division by zero when no losses | Cap to 999.0 when gross_loss=0 |
| Newsletter `get_fusion()` missing `db` arg | Newsletter service calls fusion outside request context | Create `Session(engine)` inline in newsletter_service.py |
| LLM endpoint `get_fusion()` missing `db` arg | Endpoint missing `db: Session = Depends(get_session)` | Added db parameter to llm_analysis endpoint |

### Current Constraints

| Constraint | Notes |
|-----------|-------|
| **Market hours** | LSTM fails on weekends/bank holidays (Easter Monday, Christmas) — Yahoo Finance returns no data. Cached data from previous sessions may still work. |
| **FX folder dependency** | `FX_PROJECT_PATH` must point to the parent FX project. Future work: migrate ML services into fusion_trade. |
| **PatchTST models** | Not yet available on HuggingFace for all pairs. `N/A` shown in timeframe grid when model missing. |
| **LSTM cold start** | First inference per session downloads model from HuggingFace (~60s). Cached in `~/.cache/huggingface/`. |
| **FinBERT cold start** | First sentiment call downloads FinBERT models (~90s). Cached in `~/.cache/huggingface/`. Subsequent calls ~15s (news fetch). |
| **Redis required** | Celery endpoints (`/ml/predict/trigger`, `/ml/backtest/trigger`, `/journal/verify-now`, `/newsletter/trigger`) return 500 if Redis not running. |

### Test Credentials

```
Email:    devtest@fusiontrade.ai
Password: DevTest123!
Tier:     pro (all features unlocked)
```

---

*FusionTrade AI — Not financial advice. Always manage your risk.*
