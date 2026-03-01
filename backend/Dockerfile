FROM python:3.9-slim
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements FIRST (important for caching)
COPY backend/requirements.txt .
# Upgrade pip
RUN pip install --upgrade pip
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy application code
COPY . .
# Expose port
EXPOSE 3000
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1
# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]

