# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Frontend (pre-built dist, no npm required in Docker)
# Build locally first:  cd fusion-fronted && npm run build
# ─────────────────────────────────────────────────────────────────────────────
FROM alpine:3.19 AS frontend-builder

WORKDIR /app/frontend
COPY fusion-fronted/dist ./dist
# Output: /app/frontend/dist


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Python backend
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS backend

# System deps needed by TA-Lib, TensorFlow, torch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    libgomp1 \
    libhdf5-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library (required before pip install TA-Lib)
RUN wget -q http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib && ./configure --prefix=/usr && make && make install \
    && cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz \
    && ldconfig

WORKDIR /app

# Install Python dependencies (heavy layer — cache separately)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY app/        ./app/
COPY intelligence/ ./intelligence/
COPY workers/    ./workers/
COPY migrations/ ./migrations/
COPY data/       ./data/

# Copy frontend build from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/static

# Persistent data volume mount point
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 2001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "2001", "--workers", "2"]
