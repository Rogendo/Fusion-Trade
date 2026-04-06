# 📋 FX-Predict: Current System Audit (As of April 2026)

This document represents the absolute current state of the running backend. It serves as the baseline before any "FusionTrade" modifications.

---

## 🏗️ 1. Core Architecture
- **Framework:** FastAPI (Python 3.12)
- **Primary Intelligence:** LSTM Models (Hugging Face Hub Edition)
- **Data Source:** Yahoo Finance (`yfinance`) with custom volume calculation for FX pairs.
- **Verification:** Scheduled validation via `apscheduler`.
- **Integrations:** MetaTrader 5 (MT5), Google Sheets, Gmail (SMTP).

---

## 📡 2. Endpoint Registry

### A. System & Metadata
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Serves the static HTML dashboard. |
| `/api/health` | `GET` | Returns status of Hub connectivity and model loading. |
| `/api/available-pairs` | `GET` | Fetches available symbols/intervals from the HF Hub. |
| `/api/economic-events` | `GET` | Reads local `economic_events.json`. |

### B. Prediction & Intelligence (The "Brain")
| Endpoint | Method | Input Params | Current Logic |
| :--- | :--- | :--- | :--- |
| `/api/predict` | `POST` | `symbol`, `period`, `interval` | Runs **LSTM** inference from Hub. Returns price + signal. |
| `/api/analyze-confluence` | `POST` | `symbol` | Iterates 15m, 30m, 1h, 4h using **LSTM** models. |
| `/api/performance-stats` | `GET` | `symbol`, `interval` | Returns Win Rate/Profit factor from model metadata. |
| `/api/sentiment` | `POST` | `symbol` | Runs **FinBERT** analysis on recent news headlines. |
| `/api/llm-analysis` | `POST` | `symbol`, `interval`, `include_news` | Combines LSTM + News into a prompt for **LLM (Claude/GPT)**. |

### C. History & Verification
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/prediction-history` | `GET` | Paginated view of `predictions_log.csv`. Includes real-time ROI calculation. |
| `/api/validate-history` | `POST` | Manually triggers price-check for `Pending` trades in CSV. |

### D. Newsletter & Reports
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/newsletter/preview` | `POST` | Generates HTML preview of the daily newsletter. |
| `/api/newsletter/send` | `POST` | Emails the newsletter to configured recipients. |
| `/api/comprehensive-report`| `POST` | Combines Technical + Sentiment + LLM into a single JSON/HTML report. |
| `/api/market-overview` | `GET` | High-level summary of all configured symbols. |

### E. MT5 Integration (Automation)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/mt5/status` | `GET` | Account balance, equity, and connection health. |
| `/api/mt5/execute` | `POST` | Manual trigger to open a trade in MetaTrader 5. |
| `/api/mt5/positions` | `GET` | List of currently open trades. |
| `/api/mt5/toggle` | `POST` | Enable/Disable automated execution. |

---

## 🔍 3. Identified Gaps (Pre-Fusion)
1. **Model Conflict:** PatchTST is currently "external" to the main `app.py`. It is run via scripts but not served via the API.
2. **Persistence:** The system relies heavily on `.csv` files (`predictions_log.csv`). This will cause performance issues as history grows.
3. **Security:** No User Authentication. The entire API is exposed to anyone who can reach the port.
4. **Logic:** The "Confluence" logic currently only uses LSTMs. It does not check if PatchTST agrees.

---

## 🎯 4. State of the Models
- **LSTM (Active):** Battle-tested, integrated into all API routes.
- **PatchTST (Trained):** Verified on server, pushed to Hub, but **NOT** yet connected to the `app.py` endpoints.
