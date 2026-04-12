# FusionTrade AI — Claude Code Agent Guide

This file is the authoritative context document for all Claude Code agents working on this project.
Read it fully before touching any file.

---

## Project Identity

**FusionTrade AI** is a trading intelligence platform that fuses LSTM + PatchTST machine learning signals, FinBERT news sentiment, and Claude LLM two-phase analysis into a single conviction score (0–100) with BUY/SELL/HOLD/DIVERGENT verdicts. It serves forex pairs, Gold, and crypto.

- **Backend:** FastAPI, port `2001`, Python 3.12
- **Database:** SQLite at `data/fusion_trade.db`
- **Venv:** `/home/naynek/Desktop/Backup/FX/FX/venv` (shared venv — storage constraint, always use this)
- **Frontend:** Not yet built. See `FRONTEND_VISION.md` for the full roadmap.

---

## Critical Rules (Read Before Every Task)

### 1. Always Use the Shared Venv
```bash
source /home/naynek/Desktop/Backup/FX/FX/venv/bin/activate
```
Never create a new venv. Install all packages into this one:
```bash
pip install <package>
```

### 2. The FX Older Folder Is Off-Limits
`/home/naynek/Desktop/Backup/FX/FX/` is the OLD project. **fusion_trade is fully independent.**
- No `sys.path` manipulation pointing to `/FX/FX/`
- No `os.chdir()` calls to that directory
- No imports from `model_service`, `FX/services/`, or `FX/transformers/`
- No `FX_PROJECT_PATH` in config or `.env`
- If you see any of these patterns, remove them immediately

### 3. Run the Server From the Project Root
```bash
cd /home/naynek/Desktop/Backup/FX/fusion_trade
source ../FX/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 2001
```

### 4. Token Storage — Never localStorage
The `access_token` lives in memory only (React state). The refresh token lives in an httpOnly cookie set by the server. Never write tokens to `localStorage` or `sessionStorage`.

### 5. Do Not Mock the Database
All tests and verification must hit the real SQLite database. The dev test user is:
- Email: `devtest@fusiontrade.ai`
- Password: `DevTest123!`
- Tier: `pro`, verified

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  FastAPI — port 2001                                 │
│  app/api/v1/: auth, fusion, journal, ml, newsletter │
├─────────────────────────────────────────────────────┤
│  Services (app/services/)                            │
│  fusion_service.py  — orchestrates full pipeline    │
│  auth_service.py    — JWT + bcrypt                  │
│  journal_service.py — prediction tracking           │
│  newsletter_service.py — HTML generation + SMTP     │
│  sentiment_cache_service.py — SQLite cache layer    │
├─────────────────────────────────────────────────────┤
│  Intelligence Layer (intelligence/)                  │
│  lstm_service.py      → vendors/lstm_engine.py      │
│  patchtst_service.py  → patchtst/ local package     │
│  news_service.py      → vendors/news_service.py     │
│  sentiment_service.py → vendors/sentiment_analyzer  │
│  llm_service.py       → Anthropic Claude API        │
├─────────────────────────────────────────────────────┤
│  Vendors (intelligence/vendors/) — self-contained   │
│  lstm_engine.py        — standalone LSTM inference  │
│  news_service.py       — RSS feed aggregator        │
│  sentiment_analyzer.py — FinBERT multi-model        │
├─────────────────────────────────────────────────────┤
│  PatchTST Package (intelligence/patchtst/)          │
│  config.py, models/, data/ — full local package     │
│  Models downloaded from HuggingFace on first run    │
├─────────────────────────────────────────────────────┤
│  Data Layer                                          │
│  SQLite: data/fusion_trade.db (5 tables)            │
│  Redis: localhost:6379 (Celery broker)              │
│  HuggingFace cache: ~/.cache/huggingface/           │
└─────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
fusion_trade/
├── app/
│   ├── main.py                  # FastAPI app, router registration, lifespan
│   ├── config.py                # Pydantic BaseSettings — all env vars
│   ├── api/v1/
│   │   ├── auth.py              # 11 auth endpoints
│   │   ├── fusion.py            # GET /{symbol}, POST /analyze, /llm-analysis, /sentiment
│   │   ├── journal.py           # GET /, /stats, /{id}, POST /verify-now
│   │   ├── ml.py                # GET /registry, POST /predict/trigger, /backtest/trigger
│   │   └── newsletter.py        # GET /status, POST /preview, /send, /trigger
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── journal.py           # PredictionJournal — all trade tracking fields
│   │   ├── model_registry.py    # LSTM/PatchTST registry with performance stats
│   │   ├── news_cache.py        # 1hr sentiment cache per symbol
│   │   ├── email_verification.py
│   │   └── password_reset.py
│   ├── schemas/
│   │   ├── fusion.py            # FusionResponse, TimeframeSignal, SentimentBlock,
│   │   │                        # LLMAnalysisBlock, FusionTargets — SOURCE OF TRUTH
│   │   ├── journal.py           # JournalEntryResponse, JournalStatsResponse
│   │   └── auth.py              # UserResponse, TokenResponse, request bodies
│   ├── services/
│   │   ├── fusion_service.py    # get_fusion() — main orchestration function
│   │   ├── auth_service.py
│   │   ├── journal_service.py
│   │   ├── newsletter_service.py
│   │   ├── email_service.py     # Gmail SMTP
│   │   └── sentiment_cache_service.py
│   └── core/
│       ├── database.py          # SQLAlchemy engine + session
│       ├── deps.py              # get_current_verified_user, limiter
│       └── security.py          # JWT encode/decode, bcrypt
│
├── intelligence/
│   ├── lstm_service.py          # Thin wrapper → vendors/lstm_engine
│   │                            # Contains SignalResult dataclass (used everywhere)
│   ├── patchtst_service.py      # Uses intelligence.patchtst.* (local package)
│   │                            # Models stored in intelligence/patchtst/exports/
│   ├── news_service.py          # Thin wrapper → vendors/news_service
│   ├── sentiment_service.py     # Thin wrapper → vendors/sentiment_analyzer
│   ├── llm_service.py           # Two-phase Claude prompt, FusionLLMInput, LLMAnalysis
│   ├── vendors/
│   │   ├── lstm_engine.py       # Self-contained 440-line LSTM engine
│   │   │                        # Downloads from Rogendo/forex-lstm-models (HuggingFace)
│   │   │                        # Returns: {latest, metrics, ohlc_data}
│   │   ├── news_service.py      # RSS feeds: ForexLive, FXStreet, DailyFX, Investing.com
│   │   │                        # 15-min cache, currency keyword filtering
│   │   └── sentiment_analyzer.py # FinBERT: yiyanghkust/finbert-tone
│   │                              # Lazy-loads ~30s on first call, cached singleton
│   └── patchtst/
│       ├── config.py            # MODEL_CONFIG: d_model=256, num_layers=4, d_ff=512
│       │                        # INTERVAL_CONFIG per timeframe (patch_len, stride, lookback)
│       │                        # ROOT_DIR = intelligence/patchtst/ (all paths relative)
│       ├── models/
│       │   ├── patchtst.py      # PatchTST architecture (channel-independent transformer)
│       │   └── heads.py         # RegressionHead, ClassificationHead
│       └── data/
│           ├── fetcher.py       # yfinance OHLCV + tick volume calculation
│           ├── features.py      # 17 features: RSI, MACD, ATR, BB, SMA, ROC, MOM, etc.
│           └── preprocessor.py  # RobustScaler load/save/fit/transform
│
├── workers/                     # Celery tasks
│   ├── celery_app.py
│   ├── prediction_worker.py     # Daily 06:00 UTC — runs fusion for all symbols
│   └── journal_worker.py        # Every 15min — verifies open prediction outcomes
│
├── data/
│   └── fusion_trade.db          # SQLite database
│
├── .env                         # Secrets (see Environment section below)
├── requirements.txt
├── FRONTEND_VISION.md           # Full frontend roadmap (MVP through institutional)
├── API_TESTING_GUIDE.md         # curl test suite for all endpoints
└── CLAUDE.md                    # This file
```

---

## Intelligence Pipeline — How Data Flows

```
GET /api/v1/fusion/GC=F?include_sentiment=true&include_llm=false
          │
          ▼
  fusion_service.get_fusion(symbol, timeframes, include_sentiment, include_llm)
          │
          ├─► For each timeframe (15m, 30m, 1h, 4h):
          │     ├─ lstm_service.get_lstm_signal(symbol, interval)
          │     │     └─ vendors/lstm_engine.LSTMInferenceEngine.make_predictions()
          │     │           ├─ _load_model()     → HuggingFace: Rogendo/forex-lstm-models
          │     │           ├─ _fetch_data()     → yfinance download
          │     │           ├─ _build_features() → 20 technical indicators
          │     │           └─ returns {latest, metrics, ohlc_data}
          │     │
          │     └─ patchtst_service.get_patchtst_signal(symbol, interval)
          │           ├─ _ensure_model_files()   → HuggingFace: Rogendo/forex-patchtst-models
          │           ├─ intelligence.patchtst.data.fetcher.fetch_ohlcv()
          │           ├─ intelligence.patchtst.data.features.build_features()
          │           └─ returns SignalResult with prob_up/prob_flat/prob_down
          │
          ├─► Fusion scoring algorithm:
          │     - Per-TF agreement score: 1.0 both agree, 0.5 partial, 0.0 conflict
          │     - Master score: weighted average across timeframes
          │     - Verdict: HIGH CONVICTION (>70) | MODERATE (50-70) | DIVERGENT (<50)
          │
          ├─► If include_sentiment=True:
          │     ├─ news_service.get_news_for_symbol()  → RSS feeds, 15-min cache
          │     └─ sentiment_service.get_sentiment()    → FinBERT analysis
          │
          └─► If include_llm=True:
                ├─ Builds FusionLLMInput (ohlcv + indicators + news + ML signals)
                └─ llm_service.get_llm_analysis() → Two-phase Claude prompt
                      Phase 1: Independent price/news analysis (Claude forms own view)
                      Phase 2: Claude compares its view against ML predictions
                      Returns: LLMAnalysis with validates_fusion + divergence_reason
```

### SignalResult Dataclass (defined in `intelligence/lstm_service.py`)
Used by both LSTM and PatchTST wrappers — the shared currency between intelligence and fusion layers:
```python
@dataclass
class SignalResult:
    signal: str                    # BUY | SELL | HOLD
    confidence: float              # magnitude-based (0–1)
    direction_confidence: float    # direction head probability (0–1)
    current_price: float
    predicted_price: float
    prob_up: Optional[float]       # PatchTST only
    prob_flat: Optional[float]     # PatchTST only
    prob_down: Optional[float]     # PatchTST only
    direction_accuracy: Optional[float]  # historical model accuracy %
    rsi, macd, atr, support, resistance, trend  # from LSTM indicators
    stop_loss, take_profit         # ATR-based risk levels
    ohlcv: list                    # last 30 candles for LLM prompt
```

---

## Supported Symbols & Models

| Symbol | Description | LSTM Models | PatchTST Models |
|--------|-------------|-------------|-----------------|
| `EURUSD=X` | Euro/US Dollar | 15m, 30m, 1h, 4h | 15m, 1h |
| `GBPUSD=X` | GBP/US Dollar | 15m, 30m, 1h, 4h | 15m, 1h |
| `GC=F` | Gold/USD | 15m, 30m, 1h, 4h | 15m, 30m, 1h, 4h |
| `BTC-USD` | Bitcoin/USD | 15m, 30m, 1h, 4h | varies |

**Model storage:**
- LSTM: `~/.cache/huggingface/` (auto-downloaded from `Rogendo/forex-lstm-models`)
- PatchTST: `intelligence/patchtst/exports/` (auto-downloaded from `Rogendo/forex-patchtst-models`)

**PatchTST architecture (matches HuggingFace saved models):**
- `d_model=256`, `num_layers=4`, `d_ff=512`, `head_dim=64`, `num_heads=4`
- Do NOT change these — they must match the saved checkpoints exactly

---

## API Endpoints Reference

### Fusion Intelligence
```
GET  /api/v1/fusion/{symbol}
     ?include_sentiment=true   (FinBERT, ~2s warm / instant if cached)
     ?include_llm=false        (Claude API, ~30s, opt-in — costs credits)
     Rate: 20/min
     Returns: FusionResponse (full schema in app/schemas/fusion.py)

GET  /api/v1/fusion/{symbol}/sentiment
     Standalone FinBERT. No ML inference.
     Rate: 30/min
     Returns: SentimentBlock

POST /api/v1/fusion/{symbol}/llm-analysis
     Body: FusionRequest
     Two-phase Claude analysis.
     Rate: 5/min
     Returns: LLMAnalysisBlock

POST /api/v1/fusion/analyze
     Body: FusionRequest (symbol, timeframes, include_sentiment, include_llm)
     Rate: 10/min
     Returns: FusionResponse
```

### Auth
```
POST /api/v1/auth/register       body: {email, password, full_name}
POST /api/v1/auth/login          body: {email, password} → sets httpOnly refresh cookie
POST /api/v1/auth/refresh        → uses httpOnly cookie → new access_token
POST /api/v1/auth/logout
GET  /api/v1/auth/me
PUT  /api/v1/auth/me             body: {full_name?, email?}
POST /api/v1/auth/verify-email   body: {code}
POST /api/v1/auth/change-password body: {current_password, new_password}
POST /api/v1/auth/forgot-password body: {email}
POST /api/v1/auth/reset-password  body: {code, new_password}
POST /api/v1/auth/resend-verification body: {email}
```

### Journal
```
GET  /api/v1/journal/            ?symbol&status&page&page_size(max 200)
GET  /api/v1/journal/stats       → {total_trades, wins, losses, win_rate, profit_factor, total_pips}
GET  /api/v1/journal/{entry_id}
POST /api/v1/journal/verify-now  → triggers Celery verification task
```

### ML
```
GET  /api/v1/ml/registry         ?model_type=(lstm|patchtst)
POST /api/v1/ml/predict/trigger  → runs predictions for all symbols
POST /api/v1/ml/backtest/trigger ?symbol&interval → triggers backtest
```

### Newsletter
```
GET  /api/v1/newsletter/status
POST /api/v1/newsletter/preview   body: NewsletterRequest → {status, preview_html, stats}
POST /api/v1/newsletter/send      body: NewsletterRequest → sends email
POST /api/v1/newsletter/trigger   body: NewsletterRequest → Celery async
```

### Health
```
GET  /api/health   → {status, version, service}  (public, no auth)
```

---

## Database Schema

### users
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | primary key |
| email | str | unique |
| hashed_password | str | bcrypt |
| full_name | str | |
| is_active | bool | |
| is_verified | bool | must be true to use protected endpoints |
| is_superuser | bool | |
| subscription_tier | str | `free` or `pro` |
| hf_token | str | optional HuggingFace token |
| created_at, updated_at | datetime | |

### prediction_journal
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| user_id | UUID FK | nullable (system predictions) |
| symbol | str | e.g. GC=F |
| interval | str | e.g. 1h |
| signal | str | BUY/SELL/HOLD/DIVERGENT |
| lstm_signal, patchtst_signal | str | per-model signals |
| fusion_score | float | 0–100 |
| entry_price, predicted_price | float | |
| take_profit_1/2/3, stop_loss | float | |
| confidence | float | |
| status | str | PENDING/TP1_HIT/TP2_HIT/TP3_HIT/SL_HIT/EXPIRED/IGNORED |
| outcome | str | WIN/LOSS/NEUTRAL |
| exit_price, pips | float | filled by journal_worker |
| created_at, verified_at | datetime | |

### model_registry
| Field | Type | Notes |
|-------|------|-------|
| id | int | |
| symbol, interval | str | |
| model_type | str | lstm/patchtst |
| repo_id, filename | str | HuggingFace references |
| win_rate, profit_factor, max_drawdown | float | |
| total_trades, direction_accuracy | float | |
| is_active | bool | |
| notes | str | |

### news_cache
Caches FinBERT sentiment per symbol. TTL: 1 hour. Auto-expired by `cache_expires_at` field.

---

## Environment Variables (`.env`)

```env
# App
APP_NAME=FusionTrade AI
APP_VERSION=1.0.0
DEBUG=true
API_PORT=1999           # note: server is run on 2001 via uvicorn flag

# Auth
SECRET_KEY=<jwt-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./data/fusion_trade.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=rogendopeter@gmail.com
SMTP_PASSWORD=<gmail-app-password>
SMTP_FROM_ADDRESS=rogendopeter@gmail.com
SMTP_USE_SSL=true
FRONTEND_URL=http://localhost:5173

# HuggingFace
HF_TOKEN=<hf-token>
HF_LSTM_REPO=rogendo/forex-lstm-models
HF_TST_REPO=rogendo/forex-patchtst-models

# LLM
LLM_PROVIDER=claude
CLAUDE_API_KEY=<anthropic-api-key>
CLAUDE_MODEL=claude-sonnet-4-20250514

# Newsletter (manual trigger always works regardless of this flag)
NEWSLETTER_ENABLED=false

# MT5 (Windows-only, disabled)
MT5_ENABLED=false
MT5_AUTO_EXECUTE=false
```

---

## Key Patterns & Conventions

### Singleton Services
All intelligence services use a singleton pattern with a `get_*()` factory:
```python
_instance: Optional[LSTMInferenceEngine] = None

def get_lstm_engine() -> LSTMInferenceEngine:
    global _instance
    if _instance is None:
        _instance = LSTMInferenceEngine()
    return _instance
```
Do not instantiate these classes directly. Always call `get_*()`.

### Import Pattern for Intelligence Wrappers
The 4 intelligence wrappers use absolute imports from the local vendors/patchtst packages:
```python
# CORRECT
from intelligence.vendors.lstm_engine import get_lstm_engine
from intelligence.patchtst.config import sanitize_symbol, INTERVAL_CONFIG

# WRONG — do not do this
import sys; sys.path.insert(0, '/home/naynek/Desktop/Backup/FX/FX')
from model_service import get_model_service
```

### Error Handling in Intelligence Layer
All inference functions return `None` on failure — never raise. The fusion service skips `None` results gracefully:
```python
def get_lstm_signal(symbol, interval) -> Optional[SignalResult]:
    try:
        ...
    except Exception as e:
        logger.warning("LSTM inference failed for %s %s: %s", symbol, interval, e)
        return None
```

### Rate Limiting
Applied via `slowapi` + `@limiter.limit("N/period")` decorators. Rate limit state is in-memory. Limits listed in the API reference above.

### Authentication Middleware
All protected endpoints use `Depends(get_current_verified_user)`. This:
1. Extracts `Authorization: Bearer <token>` header
2. Decodes and validates JWT
3. Checks `user.is_verified == True`
4. Returns the `User` ORM object

---

## Known Issues & Hard-Won Fixes

### Market Holidays
yfinance returns empty data on market holidays (Easter, Christmas, weekends). LSTM inference will fail gracefully and return `None`. PatchTST may still work (uses cached OHLCV if available). This is **expected behavior** — do not attempt to fix it.

### PatchTST Architecture Must Match Checkpoints
The `intelligence/patchtst/config.py` `ModelConfig` must be:
```python
d_model=256, num_layers=4, d_ff=512, head_dim=64, num_heads=4
```
These match the HuggingFace saved models. Any change will cause `state_dict` load errors.

### feedparser Required for News
The vendors/news_service.py requires `feedparser`. If missing:
```bash
pip install feedparser
```

### FinBERT First-Call Latency
`sentiment_analyzer.py` lazy-loads FinBERT models on first call (~30s). The singleton caches them. All subsequent calls are fast. Do not timeout on the first sentiment request.

### EURUSD PatchTST — Only 15m and 1h Models Exist
`EURUSD=X` and `GBPUSD=X` PatchTST models only exist for 15m and 1h intervals on HuggingFace. 30m and 4h will return `None` — this is expected, not a bug. GC=F (Gold) has all 4 timeframes.

### Newsletter HTML Key
The preview endpoint returns `preview_html`, not `html`:
```json
{ "status": "success", "preview_html": "<!DOCTYPE html>...", "stats": {...} }
```

---

## Development Commands

### Start the Server
```bash
cd /home/naynek/Desktop/Backup/FX/fusion_trade
source ../FX/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 2001
# Background:
nohup uvicorn app.main:app --host 0.0.0.0 --port 2001 > /tmp/fserver.log 2>&1 &
```

### Check Server is Running
```bash
curl -s http://127.0.0.1:2001/api/health
```

### Get JWT Token (Dev)
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:2001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"devtest@fusiontrade.ai","password":"DevTest123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Test Full GC=F Pipeline
```bash
curl -s "http://127.0.0.1:2001/api/v1/fusion/GC%3DF?include_sentiment=true&include_llm=false" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### View Live Logs
```bash
tail -f /tmp/fserver.log | grep -v sqlalchemy
```

### Interactive API Explorer (browser)
```
http://127.0.0.1:2001/docs
```

### Install a New Dependency
```bash
source /home/naynek/Desktop/Backup/FX/FX/venv/bin/activate
pip install <package>
# Add to requirements.txt manually after
```

---

## Frontend — What's Next

The frontend does not exist yet. Full vision is in `FRONTEND_VISION.md`.

**Stack:** React 18 + Vite + Tailwind CSS + TanStack Query v5 + Axios  
**Port:** `5173` (already in CORS origins)  
**Proxy:** Vite dev server proxies `/api → http://localhost:2001`

### Key Frontend Rules
1. Token in **memory only** — `AuthContext` React state, never `localStorage`
2. On page reload → call `POST /api/v1/auth/refresh` immediately using the httpOnly cookie
3. On 401 → refresh once → retry → logout if still 401
4. LLM Analysis is a `useMutation`, not a `useQuery` — user-triggered, not auto-fetched
5. Free vs Pro gating: `subscription_tier === 'pro'` unlocks LLM Analysis button

### TypeScript Types Source of Truth
All TypeScript interfaces in `src/types/fusion.ts` must mirror `app/schemas/fusion.py` exactly.  
All journal types must mirror `app/schemas/journal.py` exactly.  
Never invent field names — check the Pydantic schema first.

### Build Order (Day-by-Day)
```
Day 1  → Auth shell: Vite scaffold, Tailwind, Router, AuthContext, Login/Register
Day 2-3 → Analysis core: FusionScoreWidget, TimeframeGrid, ProbabilityTriangle
Day 4  → Enrichments: SentimentMeter, HeadlineList, LLMAnalysisPanel (30s loading UX)
Day 5  → Journal: StatsBar, JournalTable, OutcomeBadge
Day 6  → Polish: ModelsPage, NewsletterPage, SettingsPage, mobile pass
```

### The Four Unique UI Properties (never compromise these)
1. **Transparent conflict** — when LSTM ≠ PatchTST, show it prominently
2. **AI vs AI** — `validates_fusion` + `divergence_reason` always visible when LLM runs
3. **Probability bars** — `prob_up/prob_flat/prob_down` as proportional visual segments
4. **Honest accuracy** — `lstm_direction_accuracy` shown next to every signal

---

## Product Vision Summary

| Phase | Timeline | Key Features |
|-------|----------|-------------|
| MVP | ~6 days | Analysis page, Journal, Auth, Newsletter preview |
| Phase 2 | 1–2 months | Live OHLCV chart, real-time ticker, signal alerts, backtest viz |
| Phase 3 | 3–6 months | Strategy builder, model fine-tuning UI, risk calculator, AI chat |
| Phase 4 | 6–12 months | PWA, subscription gating (Stripe), API keys, community feed |
| Phase 5 | 12+ months | Multi-user teams, React Native mobile app, deep backtesting engine |

**Business context:** FusionTrade targets retail forex traders who want institutional-quality AI analysis. The product's edge is transparency — it shows *why* it's recommending a trade, *how confident* each model is, and *when the AI disagrees with itself*. No other retail tool does this.

---

## Verification Checklist (Run After Any Significant Change)

```bash
# 1. Server starts clean
curl -s http://127.0.0.1:2001/api/health

# 2. No FX folder contamination
python3 -c "
import sys; sys.path.insert(0,'/home/naynek/Desktop/Backup/FX/fusion_trade')
from intelligence.lstm_service import get_lstm_signal
from intelligence.patchtst_service import get_patchtst_signal
from intelligence.news_service import get_news_for_symbol
from intelligence.sentiment_service import get_sentiment
fx='/home/naynek/Desktop/Backup/FX/FX'
print('FX in path:', fx in sys.path)
mods=[k for k,v in __import__('sys').modules.items() if hasattr(v,'__file__') and v.__file__ and '/FX/FX/' in str(v.__file__)]
print('FX modules:', mods or 'NONE')
"

# 3. Full GC=F pipeline (LSTM + PatchTST + Sentiment)
TOKEN=$(curl -s -X POST http://127.0.0.1:2001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"devtest@fusiontrade.ai","password":"DevTest123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s "http://127.0.0.1:2001/api/v1/fusion/GC%3DF?include_sentiment=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('Score:', d.get('master_fusion_score'))
print('Verdict:', d.get('verdict'))
print('TFs:', list(d.get('timeframes',{}).keys()))
sent=d.get('sentiment',{})
print('Sentiment:', sent.get('trading_bias'), sent.get('overall_score'))
print('Headlines:', len(sent.get('top_headlines',[])))
"
```

Expected output:
- Score: a number (e.g. 33.1)
- Verdict: DIVERGENT (HOLD) or HIGH CONVICTION BUY/SELL
- TFs: ['15m', '30m', '1h', '4h']
- Sentiment: BUY/SELL/NEUTRAL + score
- Headlines: 10
