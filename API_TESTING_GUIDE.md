# 🧪 FusionTrade AI: API Testing & Verification Guide

This guide provides step-by-step instructions for testing all currently implemented features of the FusionTrade backend using `curl` or the Swagger UI.

---

## 🚦 1. Base Setup
- **Base URL:** `http://127.0.0.1:1999`
- **Swagger Documentation:** `http://127.0.0.1:1999/docs`
- **Authenticated User:** `rogendopeter@gmail.com`
- **Testing Password:** `Testing123!`

---

## 🔑 2. Authentication Flow (JWT)

### A. Login & Obtain Token
Before testing any protected routes, you must obtain an access token.
```bash
curl -X POST http://127.0.0.1:1999/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "rogendopeter@gmail.com", "password": "Testing123!"}'
```
**Swagger UI:** Use the `/api/v1/auth/login` endpoint, then copy the `access_token` and click the **"Authorize"** button at the top of the page to paste it.

### B. Verify "Me" Endpoint
Confirms the token is valid and returns your user profile.
```bash
curl -X GET http://127.0.0.1:1999/api/v1/auth/me \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

---

## 🧠 3. Fusion Intelligence (The Core)

### A. Run Symbol Analysis
This runs the "Gatekeeper" logic: it fetches LSTM (Primary) and PatchTST (Secondary) signals across timeframes.
```bash
curl -X GET "http://127.0.0.1:1999/api/v1/fusion/GC=F?include_sentiment=true" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```
**What to look for:**
- `master_fusion_score`: Should be > 70 for High Conviction.
- `logic.confluence`: `true` if both models agree on direction.
- `reasoning`: A human-readable explanation of the signal.

---

## 📓 4. Trading Journal & Verification

### A. View History
Lists all past predictions and their current statuses (Pending, Win, Loss).
```bash
curl -X GET http://127.0.0.1:1999/api/v1/journal/ \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### B. Verification Logic (Automated)
The system has a background task in `workers/tasks/verification.py` that checks prices every 10 minutes. To test this, you can look at the `app_logs.out` to see "Price check triggered" messages.

---

## 📡 5. Market Communications

### A. Newsletter Preview
Generates an institutional-grade HTML report for a specific watchlist.
```bash
curl -X POST "http://127.0.0.1:1999/api/v1/newsletter/preview" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["EURUSD=X", "GC=F"], "period": "daily"}'
```

---

## 🛠️ 6. ML Management & Registry

### A. List Active Models
Shows which models are currently available on Hugging Face and being used by the API.
```bash
curl -X GET http://127.0.0.1:1999/api/v1/ml/registry \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### B. Trigger Retraining (Advanced)
Queues a background job to retrain a model on fresh data.
```bash
curl -X POST "http://127.0.0.1:1999/api/v1/ml/predict/trigger" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

---

## 📊 7. Troubleshooting
If an endpoint returns an error, check the live logs on your server:
```bash
tail -f /home/naynek/Desktop/Backup/FX/fusion_trade/app_logs.out
```
Look for **"ModuleNotFoundError"** or **"Database Connection"** issues.
