# Multi-stage build for smaller final image
FROM python:3.9-slim AS builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgtk-3-0 \
    libavcodec59 \
    libavformat59 \
    libswscale6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Set working directory
WORKDIR /app

# Copy only necessary application files (dataset and output are mounted as volumes)
COPY api/ ./api/
COPY core/ ./core/
COPY services/ ./services/
COPY detection/ ./detection/
COPY dashboard/ ./dashboard/
COPY get_video.py .

# Create necessary directories (these will be mounted as volumes)
RUN mkdir -p dataset/frames output/frames_with_bbox

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command
CMD ["python", "-m", "api.main"]
