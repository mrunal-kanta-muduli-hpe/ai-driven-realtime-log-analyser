# Smart Log Analyzer - Docker Configuration
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV SLA_CONFIG_PATH=/app/configs/config.yaml

# Create non-root user
RUN groupadd -r sla && useradd -r -g sla sla

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/sla/.local

# Copy application code
COPY src/ src/
COPY configs/ configs/
COPY requirements.txt .
COPY setup.py .
COPY README.md .

# Create necessary directories
RUN mkdir -p data/models data/processed logs && \
    chown -R sla:sla /app

# Switch to non-root user
USER sla

# Add local Python packages to PATH
ENV PATH=/home/sla/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.main; print('OK')" || exit 1

# Default command
CMD ["python", "src/main.py", "--help"]

# Labels for metadata
LABEL maintainer="dev-team@company.com"
LABEL version="1.0.0"
LABEL description="Smart Log Analyzer - Intelligent Error Pattern Detection & Automated Defect Management"
LABEL org.opencontainers.image.source="https://github.com/company/smart-log-analyzer"
LABEL org.opencontainers.image.documentation="https://github.com/company/smart-log-analyzer/docs"
LABEL org.opencontainers.image.licenses="MIT"
