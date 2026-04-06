# 🏆 Global Fusion Hackathon: FusionTrade AI Roadmap

**Project Vision:** An institutional-grade market intelligence terminal that fusions technical AI (PatchTST), battle-tested LSTMs, and fundamental sentiment (FinBERT) to empower retail traders.

---

## 🛠️ Phase 1: The Intelligent Backend (Days 1–3)
*Goal: Transition from scripts to a production-ready Secure API.*

### 1.1 Infrastructure & Database
- [ ] **Directory Restructuring:** Separate logic into `/backend` and `/frontend`.
- [ ] **Database Setup (SQLModel + SQLite):** 
    - `User` table (Auth, HF Tokens).
    - `PredictionJournal` table (Symbol, Direction, TP1/2/3, SL, Status).
    - `ModelRegistry` table (Track versions and backtest ROIs).
- [ ] **Background Worker:** Implement a task that runs every 15m to check if "Pending" journal entries hit their TP or SL.

### 1.2 Authentication Layer
- [ ] **JWT Implementation:** Secure all prediction routes.
- [ ] **Endpoints:** 
    - `POST /api/auth/register`
    - `POST /api/auth/login`
    - `GET /api/user/profile`

### 1.3 The "Fusion" Intelligence API
- [ ] **Unified Signal Endpoint:** `GET /api/v1/fusion/{symbol}`
    - Aggregates 15m, 30m, 1h, 4h signals.
    - Calculates the **Master Fusion Score** (Weighted agreement).
    - Returns "Reasoning" strings (e.g., "LSTM confirms PatchTST trend").
- [ ] **User-Led Training:** 
    - `POST /api/ml/retrain`: Trigger a background training job.
    - `POST /api/ml/push`: Push local improvements to the user's Hugging Face account.

---

## 🎨 Phase 2: The "Exquisite" React UI (Days 4–6)
*Goal: A high-fidelity, "glassmorphism" terminal dashboard.*

### 2.1 UI Foundation
- [ ] **Tech Stack:** Vite + React + Tailwind CSS + Lucide Icons.
- [ ] **Theme:** Dark Terminal (#0A0A0A) with Neon Green/Crimson accents.
- [ ] **Landing Page:** 
    - Hero section: "Institutional Intelligence for All."
    - "Live Alpha Ticker": Real-time signal feed.

### 2.2 The Trading Terminal (Main Dashboard)
- [ ] **Market Watch Sidebar:** Real-time price list with sparklines.
- [ ] **Fusion Chart (TradingView):** 
    - Candlestick chart.
    - Overlay: LSTM & PatchTST prediction lines.
    - Visual TP/SL zones.
- [ ] **Confluence Matrix:** A grid showing "Agreement" across all 5 timeframes.
- [ ] **Sentiment Pulse:** A gauge showing news-driven "Fear vs Greed."

### 2.3 The AI Trading Journal
- [ ] **Performance View:** A timeline of past predictions.
- [ ] **Verification Badges:** "TP1 HIT", "SL HIT", "EXPIRED".
- [ ] **Stats Dashboard:** Visualizing total ROI, Win Rate, and Profit Factor.

---

## 🚀 Phase 3: The "Winning" Polish (Days 7–9)
*Goal: Documentation, Demo, and Impact Analysis.*

### 3.1 Explainable AI (XAI)
- [ ] **Insight Tooltips:** Hovering over a signal explains *why* (e.g., "RSI Overbought + PatchTST Downward Cross").
- [ ] **Daily Fusion Report:** A "Generate PDF" button for the comprehensive newsletter.

### 3.2 Documentation & Video
- [ ] **README.md:** World-class documentation with architectural diagrams.
- [ ] **Demo Video:** A 2-minute walkthrough showing a prediction being generated, verified, and logged in the journal.
- [ ] **Pitch Deck:** Focus on the "Global Fusion" of technical and fundamental AI.

---

## 💡 Critical "Hackathon" Differentiators
1. **The Fusion Score:** Don't just provide a signal; provide a **Confidence Metric** based on model agreement.
2. **Accountability:** The **Trading Journal** proves the AI's transparency (we show the losses too).
3. **Distribution:** Models hosted on **Hugging Face Hub** proves the system is scalable and cloud-native.
