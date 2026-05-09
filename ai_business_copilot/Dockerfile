# ─────────────────────────────────────────────────────────
#  AI Business Decision Copilot — Dockerfile
# ─────────────────────────────────────────────────────────

FROM python:3.11-slim

# System dependencies needed by Prophet / pystan
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Generate sample data if not present
RUN python data/generate_sample_data.py || true

EXPOSE 8501 8000

# Default: run dashboard (override in docker-compose)
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
