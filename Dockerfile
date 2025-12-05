FROM python:3.11-slim

LABEL maintainer="Abner Fonseca"
LABEL description="Brazilian Fraud Data Generator - Synthetic financial transaction data"
LABEL version="3.1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-streaming.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-streaming.txt

# Copy source code
COPY src/ ./src/
COPY generate.py .
COPY stream.py .

# Create output directory
RUN mkdir -p /output

# Default environment variables
ENV OUTPUT_DIR=/output
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV KAFKA_TOPIC=transactions

# Expose for potential metrics endpoint (future)
EXPOSE 9400

# Default command shows help
ENTRYPOINT ["python"]
CMD ["generate.py", "--help"]
