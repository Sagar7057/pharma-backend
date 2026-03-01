FROM python:3.9-slim
WORKDIR /app/backend

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the backend folder contents into WORKDIR
COPY backend/ .

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
