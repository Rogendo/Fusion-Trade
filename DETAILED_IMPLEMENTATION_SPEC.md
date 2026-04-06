# 🏗️ FusionTrade AI: Professional Multi-Agent System Specification

**Project Vision:** An institutional-grade market intelligence terminal fusing technical AI (PatchTST), battle-tested LSTMs, and fundamental sentiment (FinBERT).
**Core Mandate:** Everything must work. Architecture must be modular, secure, and high-performance.

---

## 📂 1. Unified Project Structure
Every agent must adhere to this directory layout to prevent import conflicts and config shadowing.

```text
fusion-trade/
├── backend/                 # FastAPI Service (Port 1999)
│   ├── app/
│   │   ├── api/             # V1 Routes (auth, fusion, journal, reporting)
│   │   ├── core/            # Unified config.py, security.py (JWT)
│   │   ├── db/              # database.py, models/ (SQLModel schemas)
│   │   ├── services/        # Business logic (news_service, newsletter, report_gen)
│   │   └── main.py          # Entry point
│   ├── intelligence/        # THE BRAIN (Consolidated AI logic)
│   │   ├── models/          # model_service.py (LSTM), patchtst_service.py
│   │   ├── hubs/            # Logic for HF Hub (rogendo/forex-*)
│   │   └── training/        # finetune_pipeline.py, train_single.py
│   └── requirements.txt
├── frontend/                # React (Vite + TS + Tailwind)
│   ├── src/
│   │   ├── components/      # FusionChart, ConfluenceMatrix, SignalCard
│   │   ├── store/           # Zustand state management
│   │   └── pages/           # Dashboard, Journal, Settings
│   └── package.json
└── data/                    # Unified Persistence
    ├── cache/               # Parquet/OHLCV files
    └── fusion_trade.db      # SQLite Database (Primary state)
```

---

## 🛰️ 2. Module Specifications

### 🧠 Module A: The Intelligence Lead (ML Agent)
*Focus: Hub Integration, Stability-First Logic, and Cross-Asset Patterns.*
- **Gatekeeper Logic:** LSTM is **Primary**. PatchTST is **Secondary Confirmation**.
- **The Agreement Algorithm:** 
    - BUY only if `LSTM == BUY` AND `PatchTST == BUY`.
    - If they disagree, return `DIVERGENT (HOLD)`.
- **Transfer Learning:** Implement the `finetune_pipeline.py` to freeze Gold encoders and train heads on FX (EURUSD, etc.).
- **Blind Simulation:** Run `backtest_sim.py` every 24h to update "Live Win Rate" stats in the Registry.

### 🛰️ Module B: The Core Architect (Backend Agent)
*Focus: API Security, Database Persistence, and Task Automation.*
- **Database Schema:** 
    - `User`: (id, email, password_hash, hf_token, preferences).
    - `Journal`: (symbol, timeframe, signals from both models, entry_price, status).
- **Authentication:** JWT-based protection for all prediction and report routes.
- **Verification Worker:** Background task to check if `PENDING` journal entries hit TP/SL.
- **Legacy Migration:** Script to import `predictions_log.csv` into the new SQLite DB.

### 🎨 Module C: The UX/UI Engineer (Frontend Agent)
*Focus: High-Fidelity Terminal Experience.*
- **The "Bloomberg" Dashboard:** Dark theme, glassmorphism cards.
- **FusionChart:** TradingView charts with prediction overlays (Dashed lines for LSTM vs PatchTST).
- **Confluence Matrix:** Real-time 5x2 grid (5 intervals x 2 models) showing signal alignment.
- **Intelligence Overlay:** Tooltips explaining "The Why" behind every signal.

---

## 📂 3. The "Everything Works" API Contracts

### **Main Intelligence Endpoint**
`GET /api/v1/fusion/{symbol}`
```json
{
  "symbol": "GC=F",
  "master_fusion_score": 85.0, // 0-100 based on agreement
  "verdict": "HIGH CONVICTION BUY",
  "logic": {
    "primary_lstm": "BUY",
    "secondary_patchtst": "BUY",
    "confluence": true
  },
  "timeframes": {
    "15m": {"lstm": "BUY", "ptst": "BUY", "agreement": 1.0},
    "1h": {"lstm": "BUY", "ptst": "HOLD", "agreement": 0.5}
  },
  "targets": {"tp1": 2160.5, "sl": 2145.0}
}
```

### **Retraining Endpoint**
`POST /api/v1/ml/finetune`
- Input: `target_symbol`, `source_model_id` (e.g., Gold_30m).
- Action: Runs the background transfer learning task.

---

## 🚀 Phase 1 Execution (The Move)
1. **Initialize Backend Folder:** Create the structure and move `model_service.py` and `patchtst.py`.
2. **Unified Config:** Create `backend/app/core/config.py` that merges root settings and model settings.
3. **Database Spin-up:** Initialize `fusion_trade.db` using SQLModel.
4. **Validation:** Run the `backtest_sim.py` using the NEW structure to confirm no import breaks.
