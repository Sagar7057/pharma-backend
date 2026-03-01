FROM python:3.9-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# chmod AFTER copying files
RUN chmod +x start.sh

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-3000}/health || exit 1

CMD ["sh", "-c", "./start.sh"]
