# ==============================================================================
# Brazilian Fraud Data Generator
# ==============================================================================
# Multi-platform Docker image for generating synthetic Brazilian financial data
# Supports: transactions, customers, rides, devices with fraud patterns
# ==============================================================================
FROM python:3.11-slim AS base

# OCI Image Labels (standardized)
LABEL org.opencontainers.image.title="Brazilian Fraud Data Generator"
LABEL org.opencontainers.image.description="Generate synthetic Brazilian financial transaction and rideshare data with configurable fraud patterns"
LABEL org.opencontainers.image.authors="Abner Fonseca <afborda@gmail.com>"
LABEL org.opencontainers.image.url="https://github.com/afborda/brazilian-fraud-data-generator"
LABEL org.opencontainers.image.source="https://github.com/afborda/brazilian-fraud-data-generator"
LABEL org.opencontainers.image.documentation="https://github.com/afborda/brazilian-fraud-data-generator#readme"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="Abner Fonseca"

# Dynamic labels (set during build via --build-arg)
ARG VERSION=4.0.0
ARG BUILD_DATE
ARG VCS_REF

LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FRAUD_GENERATOR_VERSION=${VERSION}

WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-streaming.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-streaming.txt

# Copy source code
COPY src/ ./src/
COPY generate.py .
COPY stream.py .

# Create output directory with proper permissions
RUN mkdir -p /output && chmod 777 /output

# Default environment variables
ENV OUTPUT_DIR=/output
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV KAFKA_TOPIC=transactions

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.fraud_generator; print('OK')" || exit 1

# Expose for potential metrics endpoint (future)
EXPOSE 9400

# Default command shows help
ENTRYPOINT ["python"]
CMD ["generate.py", "--help"]
