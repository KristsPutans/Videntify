FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

# Install compatible Python dependencies in the correct order
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy==1.23.5 && \
    pip install --no-cache-dir werkzeug==2.0.3 flask==2.0.1 requests==2.28.1 && \
    pip install --no-cache-dir pymilvus==2.0.0

# Clean up build dependencies to reduce image size
RUN apt-get purge -y --auto-remove gcc libc6-dev

# Expose the port
EXPOSE 5050

# Run the server with debug flag
CMD ["python", "/app/connector.py", "--debug"]
