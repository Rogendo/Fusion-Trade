# 🧪 Scientific Protocol: The "Battle of the Hubs" & Universal Fine-Tuning

This document defines the rigorous evaluation and expansion plan for the FusionTrade AI intelligence core.

---

## 🔬 Experiment 1: The "Blind" Simulation (Head-to-Head)
**Objective:** Empirically prove profitability by simulating real-world trading on data never seen by the models.

### 1.1 Experimental Setup
- **Hidden Window:** March 15, 2026, to March 29, 2026 (14 Days of "Out-of-Sample" data).
- **Starting Capital:** $1,000.00 USD per account.
- **Trading Assets:** Gold (`GC=F`) across all 5 timeframes (5m, 15m, 30m, 1h, 4h).

### 1.2 The Three Portfolios
| Account | Logic | Role |
| :--- | :--- | :--- |
| **A: The Veteran** | Executes signals from **LSTM Hub** only. | Baseline Stability |
| **B: The Challenger**| Executes signals from **PatchTST Hub** only. | Aggressive Growth |
| **C: The Fusion** | Executes ONLY when **LSTM and PatchTST Agree.** | Professional Risk Management |

### 1.3 Execution Rules (The "Fixed Hand")
- **Risk per Trade:** 2% of current balance ($20 initial).
- **Reward-to-Risk (RR):** Fixed 1.5 : 1 (Stop Loss set at 1x ATR, Take Profit at 1.5x ATR).
- **Friction:** $0.50 per trade simulated spread/commission.
- **Trade Limit:** First 100 valid signals detected in the 14-day window.

---

## 🧠 Experiment 2: Universal Pattern Fine-Tuning (Transfer Learning)
**Objective:** Determine if the patterns learned from Gold can be successfully "Transferred" to Currency pairs.

### 2.1 The "Foundational" Base
- **Base Model:** `GC_F_30m_patchtst.pt` (The +70% ROI model).
- **Rationale:** This model has demonstrated the highest "Market Intuition."

### 2.2 The Fine-Tuning Protocol
1. **Architecture Freezing:** Lock the Transformer Encoder weights (the "Eyes" of the model).
2. **Head Re-Training:** Unfreeze only the `price_head` and `dir_head`.
3. **Data Injection:** Train for 10 epochs on:
    - `EURUSD=X`
    - `GBPUSD=X`
    - `USDJPY=X`
4. **Validation:** Compare the "Fine-Tuned Gold Model" against a "From-Scratch EURUSD Model."
    - *Success Metric:* If the Fine-Tuned model achieves > 45% accuracy in < 5 epochs.

---

## 📊 Reporting Metrics
For every simulation run, the `simulation_engine.py` must output:
1. **Net ROI:** Total percentage gain/loss.
2. **Profit Factor:** Gross Profit / Gross Loss.
3. **Max Drawdown:** The largest "peak-to-valley" drop in equity.
4. **Agreement Alpha:** The percentage increase in Win Rate when using Account C (Fusion).
