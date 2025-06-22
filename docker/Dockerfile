FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install required Python packages
RUN pip install --no-cache-dir \
    requests \
    flask \
    python-dateutil

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Copy the monitoring script
COPY ../src/bitaxe_monitor.py /app/src/
COPY ../requirements.txt /app/

# Create config directory
RUN mkdir -p /app/config

# Expose the web interface port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/metrics || exit 1

# Run the monitor
CMD ["python", "/app/src/bitaxe_monitor.py"]
