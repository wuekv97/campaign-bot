# Dockerfile for Telegram Bot + Web Admin Panel
# Run both processes in one container (dev/demo). For production, consider separate services.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data logs

# Default: run both bot and web panel
CMD ["python", "run.py", "all"]
