# FusionTrade AI — Frontend Vision & Product Roadmap

> **Status:** Planning complete. Backend fully operational. Frontend is greenfield.  
> **Stack:** React 18 + Vite + Tailwind CSS + TanStack Query + lightweight-charts  
> **Backend:** FastAPI at `http://localhost:2001`  

---

## Design Philosophy

Three principles that run through every screen:

1. **Conviction over noise** — a trader doesn't want 40 numbers, they want: *how sure is the system, and why?* The Fusion Score (0–100) + verdict is always the hero element.
2. **Agreement is signal** — when LSTM and PatchTST agree, that's more valuable than either alone. Agreement/conflict must be immediately scannable, not buried in a table.
3. **AI as co-analyst, not oracle** — Claude explicitly challenges the models. The UI shows Claude's independent bias *first*, then whether it validates or contradicts the fusion verdict. This is the product's unique edge — no other trading tool shows an AI actively pushing back on its own signals.

---

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | React 18 + Vite | Fast HMR, standard ecosystem |
| Styling | Tailwind CSS v3 | Terminal aesthetic with custom palette |
| Routing | React Router v6 | File-based, nested routes |
| API / cache | TanStack Query v5 | Stale-while-revalidate, mutation handling |
| HTTP | Axios | Interceptor for JWT refresh |
| Charts | lightweight-charts (TradingView) | Free, performant, candlestick + overlays |
| Markdown | react-markdown | Render Claude's raw_response |
| Toasts | react-hot-toast | Non-intrusive notifications |
| Icons | lucide-react | Consistent, tree-shakeable |

**Vite proxy:** `/api → http://localhost:2001` — no port hardcoded anywhere in client code.

---

## Phase 1 — MVP (~6 days to working product)

### Routes

```
PUBLIC:
  /login
  /register
  /verify-email
  /forgot-password
  /reset-password

PROTECTED:
  /                    → redirects to /analysis/GC=F
  /analysis/:symbol    → THE core product (GOLD is default)
  /journal             → trade history + performance stats
  /models              → ML registry + admin triggers
  /newsletter          → preview + send
  /settings            → profile + password + subscription tier
```

### Project File Structure

```
fusion-frontend/
└── src/
    ├── api/
    │   ├── client.ts          # axios instance + JWT refresh interceptor
    │   ├── auth.ts            # all /api/v1/auth/* calls
    │   ├── fusion.ts          # all /api/v1/fusion/* calls
    │   ├── journal.ts         # all /api/v1/journal/* calls
    │   ├── ml.ts              # all /api/v1/ml/* calls
    │   └── newsletter.ts      # all /api/v1/newsletter/* calls
    ├── types/
    │   ├── fusion.ts          # TypeScript interfaces mirroring Pydantic schemas
    │   ├── journal.ts
    │   └── auth.ts
    ├── context/
    │   └── AuthContext.tsx    # access_token in memory ONLY (never localStorage)
    ├── hooks/
    │   ├── useFusion.ts       # useQuery, staleTime 5min
    │   ├── useSentiment.ts    # useQuery, staleTime 3min
    │   ├── useLLMAnalysis.ts  # useMutation (user-triggered, not auto-fetched)
    │   └── useJournal.ts
    ├── pages/
    │   ├── auth/              # Login, Register, VerifyEmail, ForgotPw, ResetPw
    │   ├── AnalysisPage.tsx   # /analysis/:symbol — core product
    │   ├── JournalPage.tsx
    │   ├── ModelsPage.tsx
    │   ├── NewsletterPage.tsx
    │   └── SettingsPage.tsx
    ├── components/
    │   ├── layout/            # AppShell, Sidebar, TopBar, ProtectedRoute
    │   ├── fusion/            # FusionScoreWidget, VerdictBadge, TimeframeGrid,
    │   │                      # TimeframeCard, ModelAgreementBar, ProbabilityTriangle,
    │   │                      # TargetsPanel, ReasoningBlock
    │   ├── sentiment/         # SentimentPanel, SentimentMeter, SentimentCounts,
    │   │                      # HeadlineList
    │   ├── llm/               # LLMAnalysisPanel, LLMActionBadge, LLMRawMarkdown
    │   ├── journal/           # StatsBar, JournalTable, JournalRow, OutcomeBadge
    │   └── ui/                # ConfidenceBar, SignalChip, Skeleton, ErrorBanner, Button
    └── utils/
        ├── symbolMeta.ts      # display names, pip sizes, emoji flags per symbol
        └── formatPrice.ts
```

### Analysis Page Layout — The Hero Screen

**Desktop (60/40 split):**
```
┌──────────────────────────────────────────────────────────┐
│ TopBar:  [EUR/USD] [GBP/USD] [GOLD ●] [BTC]   ↺ 3m ago │
├──────────────────────────────┬───────────────────────────┤
│                              │                           │
│   FusionScoreWidget          │   SentimentPanel          │
│   (arc gauge + verdict)      │   (meter + headlines)     │
│                              │                           │
│   TimeframeGrid  (2×2)       ├───────────────────────────┤
│                              │                           │
│   TargetsPanel (TP1/SL/ATR)  │   LLMAnalysisPanel        │
│                              │   [Get AI Analysis ▶]     │
│   ReasoningBlock             │                           │
│                              │                           │
└──────────────────────────────┴───────────────────────────┘
```

**Mobile:** same components, single-column stack, same order.

---

### Key Component Designs

#### FusionScoreWidget
SVG arc gauge (270° sweep). Color zones:
- `0–30` → `rose-500` (conflict / low conviction)
- `30–60` → `amber-400` (moderate)
- `60–80` → `emerald-400` (strong)
- `80–100` → `emerald-300` + pulse animation (HIGH CONVICTION)

Inside the arc: large score number. Verdict text below, color-matched.  
Right side: LSTM PRIMARY + PATCHTST SECONDARY chips — green "Confluence ✓" or red "Conflict ✗".

#### TimeframeCard (×4, arranged in 2×2 grid)
```
┌──────────────────────────────────┐
│ 1H                ══════░░  62%  │  ← ModelAgreementBar
│ LSTM  [SELL]   ──────────  26%  │  ← SignalChip + ConfidenceBar
│ PST   [HOLD]   ──── N/A          │
│ ▲UP 33%  ▬FLAT 31%  ▼DOWN 34%   │  ← ProbabilityTriangle
│ $4703.70  →  $4687.46  ▼ -0.3%  │  ← price prediction row
└──────────────────────────────────┘
```

**ModelAgreementBar:** horizontal bar, left half = LSTM color, right half = PatchTST color. Both same direction → solid color + glow. Conflict → split red/green.

**ProbabilityTriangle:** three proportional horizontal segments — `UP=emerald`, `FLAT=slate`, `DOWN=rose`. Percentages inside each segment (tooltip on mobile). Winning segment has a small chevron indicator above it. If `patchtst` unavailable → "Model not available" in slate text. This is the most important visual for making ML output readable to non-technical traders.

**ConfidenceBar:** thin `h-2` filled bar. LSTM shows two values:
- *Signal Strength* (`lstm_confidence`) — how large the predicted price move is
- *Direction Certainty* (`lstm_direction_confidence`) — the direction head probability
- *Historical Accuracy* (`lstm_direction_accuracy`) — shown as a static stat, not a bar (it's a model property, not a per-signal value)

#### SentimentMeter
Half-arc SVG gauge (-1 to +1), animated needle on load. Score mapped to human label:

| Range | Label |
|-------|-------|
| -1.0 → -0.5 | Strongly Bearish |
| -0.5 → -0.1 | Moderately Bearish |
| -0.1 → +0.1 | Neutral |
| +0.1 → +0.5 | Moderately Bullish |
| +0.5 → +1.0 | Strongly Bullish |

Three pill counts: `"2 📈 Bullish"` `"5 📉 Bearish"` `"3 — Neutral"`.  
Headlines: scrollable list (10 items). Title + source + relative time. Summary in hover tooltip — not inline (keeps mobile clean). Clicking opens `link` in new tab.

#### LLMAnalysisPanel
**Collapsed (default):** purple "Get AI Analysis" button. Hint: "(~30s · Claude API · Pro)". Only enabled for pro-tier users.

**Loading:** animated progress bar 0→85% over 25s (pauses at 85% until response arrives). Message: *"Claude is independently analyzing the market..."*

**Loaded:**
```
┌─────────────────────────────────────────────────────┐
│  Claude's Verdict:  [WAIT]  medium confidence        │
│                                                      │
│  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │ Independent     │  │ Fusion Validation         │  │
│  │ Bias: Bearish ▼ │  │ ⚠ Challenges ML Signal   │  │
│  └─────────────────┘  │ "Models diverge at 4h..." │  │
│                        └──────────────────────────┘  │
│                                                      │
│  Market Structure   │  News Impact  │  Entry Strategy│
│  (full text — no truncation on any panel)            │
│                                                      │
│  Key Levels:  TP1 $4941.80  │  SL $4543.63          │
│                                                      │
│  ⚠ Oil surge indicates risk-on sentiment             │
│  ⚠ Geopolitical premium diminishing                  │
│  ⚠ 4h LSTM contradicts all shorter-term signals     │
│                                                      │
│  [▼ View full Claude response]  ← collapsible MD    │
└─────────────────────────────────────────────────────┘
```

The validation box is the product's most unique element:
- `validates_fusion=true` → **emerald** "Confirms ML Signal ✓"
- `validates_fusion=false` → **amber** "Challenges ML Signal ⚠" + `divergence_reason` in a callout

#### Color System
```js
// tailwind.config.js
extend.colors = {
  terminal: {
    bg:      '#080d18',   // deep space navy
    surface: '#0d1526',   // card background
    border:  '#1a2840',   // card border
    muted:   '#243454',   // secondary borders
  }
}
```
All cards: `bg-terminal-surface border border-terminal-border rounded-xl p-4`  
Body: `bg-terminal-bg text-slate-100`

#### Auth — Session Management
- Access token stored **in memory only** (React state in `AuthContext`) — never `localStorage`
- On page reload: call `POST /api/v1/auth/refresh` immediately in `AuthContext.useEffect` using the httpOnly refresh cookie → silently restore session
- On any 401: axios interceptor retries once → on second 401, calls `logout()` → navigate to `/login`

#### Symbol Meta (`utils/symbolMeta.ts`)
```typescript
const SYMBOL_META = {
  'EURUSD=X': { label: 'EUR/USD', type: 'forex',     pipSize: 0.0001, flag: '🇪🇺' },
  'GBPUSD=X': { label: 'GBP/USD', type: 'forex',     pipSize: 0.0001, flag: '🇬🇧' },
  'GC=F':     { label: 'Gold',    type: 'commodity',  pipSize: 0.10,   flag: '🏅' },
  'BTC-USD':  { label: 'Bitcoin', type: 'crypto',     pipSize: 1.00,   flag: '₿'  },
}
```

### Build Order (fastest path to working product)

| Day | Work |
|-----|------|
| 1 | Vite scaffold, Tailwind, Router, QueryClient, AuthContext, axios client, Login/Register/VerifyEmail pages, AppShell skeleton |
| 2–3 | `types/fusion.ts` + `api/fusion.ts` + `useFusion` hook, FusionScoreWidget, SignalChip/ConfidenceBar/VerdictBadge (reusables), TimeframeCard + TimeframeGrid, ProbabilityTriangle, ModelAgreementBar, TargetsPanel + ReasoningBlock |
| 4 | `useSentiment` hook, SentimentMeter + SentimentCounts + HeadlineList, `useLLMAnalysis` mutation, LLMAnalysisPanel with all loading states + react-markdown |
| 5 | `api/journal.ts` + `useJournal` hooks, StatsBar, JournalTable + OutcomeBadge, filter dropdowns + pagination |
| 6 | ModelsPage (registry table + trigger buttons), NewsletterPage (preview in sandboxed iframe), SettingsPage, skeleton states on all panels, mobile responsive pass, ErrorBoundary around each major panel |

---

## Phase 2 — Product Deepening (1–2 months post-MVP)

### Live OHLCV Chart
The LSTM engine already returns `ohlc_data` (last 30 candles). Feed directly into **lightweight-charts** `addCandlestickSeries`. Overlays:
- Support/resistance horizontal lines (from `support`/`resistance` in LSTM output)
- Predicted price diamond marker at next candle
- TP1 and SL as colored horizontal bands
- Signal arrow at the last candle (▲ BUY, ▼ SELL)

Transforms the page from a signals dashboard into a proper trading terminal feel.

### Real-Time Price Ticker
New backend: `GET /api/v1/stream/{symbol}` — SSE endpoint polling yfinance every 30s. Frontend subscribes on symbol open. `current_price` updates live without re-running full ML inference. The fusion score "goes live."

### Multi-Symbol Dashboard (`/dashboard`)
Grid of compact `FusionScoreMiniCard` components — one per symbol. Score arc (60px) + verdict chip + agreement indicator. One-click to full analysis. All 4 symbols scannable in under 5 seconds. This is the natural landing page once the user has seen the full analysis once.

### Signal Alerts
New backend tables: `alert_rules`, `notifications`. Rule types: `score_above_threshold`, `verdict_buy`, `verdict_sell`, `confluence_agree`. Channels: browser push (Web Push API + service worker) + email via existing SMTP. Frontend: alert configuration panel in Settings. **Most valuable feature for traders not watching the screen.**

### Backtest Visualisation
Equity curve chart (cumulative pips over time) built from existing journal data. Per-model performance breakdown: LSTM-only vs PatchTST-only vs Fusion-agreement-only trades. Sharpe ratio, max drawdown, win streak. **No new backend needed** — all from `GET /api/v1/journal/?page_size=200`.

### Timeframe Selection Controls
Multi-select chip group in the TopBar. Calls `POST /api/v1/fusion/analyze` with selected subset. User can focus on just 4h, or expand to include 5m and 1d.

---

## Phase 3 — Platform Expansion (3–6 months)

### Strategy Builder
Visual drag-and-drop rules composer. Example rule: *"BUY only when: LSTM 4h = BUY AND PatchTST 1h = BUY AND Sentiment = Bullish AND Score > 70."* Each condition is a configurable block. Strategy instantly backtested against journal history. **The biggest product differentiator** — no retail tool lets traders compose their own ML fusion strategy.

### Model Fine-Tuning UI
Frontend wizard for the existing `POST /api/v1/fusion/finetune` endpoint:
1. Select base model (e.g. EURUSD 1h LSTM)
2. Select fine-tune target symbol (e.g. GBPJPY 1h)
3. Set epochs (Quick: 5, Thorough: 20)
4. "Start" → live progress polling until model appears in registry
5. New model auto-appears with performance stats

Pro-tier only. Extends coverage beyond 4 default symbols without developer involvement.

### Risk Calculator Panel
Overlay on Analysis page. User inputs: account size ($) + risk per trade (% or $). System calculates: position size (lots), dollar value of TP/SL, risk:reward ratio, pip value in account currency. Uses `atr`, `tp1`, `sl` from current fusion response. **Pure frontend calculation** — no backend changes needed.

### AI Chat Interface (Market Q&A)
Chat panel anchored bottom-right. Natural language questions:
- *"Why is the 4h LSTM disagreeing with PatchTST?"*
- *"What would change this to a BUY signal?"*
- *"Summarise my last 5 Gold journal entries"*

New backend endpoint: `POST /api/v1/fusion/{symbol}/chat` — accepts `{question, context: FusionResponse}`, passes to Claude, returns conversational answer. Makes the product accessible to non-technical traders who don't understand "softmax probabilities."

### Portfolio View (`/portfolio`)
Aggregates active journal entries across all symbols. Total open exposure (long vs short bias), net pip P&L, correlation warnings (*"You're long EUR/USD AND GBP/USD — high correlation risk"*).

---

## Phase 4 — Scale & Monetisation (6–12 months)

### Progressive Web App (PWA)
`manifest.json` + service worker added to Vite build:
- Install to home screen (iOS + Android)
- Offline cache of last-loaded analysis
- Background sync for journal verification
- Push notifications for alert rules
- Zero backend changes needed

### Subscription Gating UI
| Tier | Features |
|------|---------|
| Free | Fusion signals + sentiment |
| Pro | LLM analysis, alerts, strategy builder, fine-tuning UI |

Upgrade prompt on locked features. `/pricing` comparison page. Stripe checkout: `POST /api/v1/billing/checkout-session` + webhook to update `subscription_tier`.

### API Key Access (Developer Tier)
Key management in Settings (generate/revoke). Backend: `api_keys` table + key-based auth middleware. Interactive API explorer styled as trading terminal. Usage metrics panel (calls this month vs limit). Algo traders can integrate FusionTrade signals into their own systems.

### Community Signal Feed (`/feed`)
Pro users publish their current analysis view (anonymised or named). Aggregated community bias per symbol (% bullish/bearish). Follow specific users. Compare journal performance to community average. Backend: `signal_publications` + `follows` tables.

---

## Phase 5 — Institutional & White-Label (12+ months)

### Multi-User Teams
Role-based access: admin / analyst / trader / read-only. Shared journal and team P&L rollup. Team-wide alert rules. White-label domain support (`analysis.yourfirm.com`).

### Native Mobile App
React Native using the same API. All SVG components (FusionScoreWidget, SentimentMeter, ProbabilityTriangle) translate directly via `react-native-svg`. Shared type definitions and API client code.

### Deep Backtesting Engine
3+ years historical OHLCV → simulate LSTM/PatchTST signal generation → apply trading rules (enter on signal, exit at TP1 or SL) → walk-forward validation → Monte Carlo simulation (1000 randomised trade sequences) → PDF report export. Institutional-grade feature no free tool offers for transformer-based models.

---

## What Makes This Product Unique

| Property | What the UI shows |
|----------|-------------------|
| **Transparent conflict** | When LSTM ≠ PatchTST — the UI shows it, not hides it. Exact timeframes in conflict, explained. |
| **AI that argues with itself** | `validates_fusion` flag + `divergence_reason` shown prominently — Claude's independent view vs the models. |
| **Probability distributions** | `prob_up / prob_flat / prob_down` as a proportional visual bar — not a single number. Shows *how uncertain* the model is. |
| **Honest accuracy** | `lstm_direction_accuracy` (~50%) displayed next to every signal. The system tells you how well the model has historically performed. Honesty builds trust. |

These four properties are the product's core identity. Every UI decision should reinforce them.

---

## API Rate Limits (important for frontend design)

| Endpoint | Limit |
|----------|-------|
| `GET /api/v1/fusion/{symbol}` | 20/min |
| `GET /api/v1/fusion/{symbol}/sentiment` | 30/min |
| `POST /api/v1/fusion/{symbol}/llm-analysis` | 5/min |
| `POST /api/v1/fusion/analyze` | 10/min |
| `POST /api/v1/newsletter/preview` | 5/min |
| `POST /api/v1/newsletter/send` | 3/hour |

React Query's built-in deduplication prevents redundant calls. Add a 12s cooldown timer on the LLM Analysis button after each click. Minimum refetch interval: 3s.

---

## Critical Backend Files (source of truth for TypeScript types)

| File | Purpose |
|------|---------|
| `app/schemas/fusion.py` | All FusionResponse, TimeframeSignal, SentimentBlock, LLMAnalysisBlock fields |
| `app/schemas/journal.py` | JournalEntryResponse, JournalStatsResponse, JournalListResponse |
| `app/api/v1/auth.py` | Refresh cookie name, full auth flow |
| `app/api/v1/fusion.py` | Rate limits, endpoint signatures |
| `app/config.py` | CORS origins (`http://localhost:5173`), subscription_tier |
| `app/models/journal.py` | All DB fields, status enum values |
| `intelligence/llm_service.py` | LLMAnalysis dataclass — all fields Claude returns |

---

## End-to-End Verification Checklist

```
Auth
  ✓ Register → receive verification email → click link → verified
  ✓ Login → redirect to /analysis/GC=F
  ✓ Page reload → session restores silently via refresh cookie
  ✓ 401 response → interceptor retries → redirects to /login on second 401

Analysis Page (GC=F)
  ✓ FusionScoreWidget: arc fills to correct score, color matches zone, verdict displayed
  ✓ TimeframeGrid: all 4 TFs, LSTM + PatchTST signals, ProbabilityTriangle proportions correct
  ✓ ModelAgreementBar: solid when both agree, split when conflict
  ✓ TargetsPanel: TP1/SL/ATR with pip distance from current price
  ✓ SentimentPanel: needle at correct position, 10 headlines, summary in tooltip
  ✓ LLM button: disabled for free users, purple for pro
  ✓ LLM loading: progress bar animates, pauses at 85%, then content fades in
  ✓ LLM loaded: action + bias + validation box + three warnings + collapsible raw response
  ✓ Validation box: emerald when validates_fusion=true, amber when false

Journal
  ✓ StatsBar: win rate color-coded, all 6 stats visible
  ✓ Table: symbol/signal/score/entry/TP1/SL/status/outcome columns
  ✓ OutcomeBadge: WIN=green, LOSS=red, PENDING=slate outline

Newsletter
  ✓ Preview: HTML rendered in sandboxed iframe, not raw on page

Mobile
  ✓ Single column, no horizontal scroll, all panels tap-accessible
```
