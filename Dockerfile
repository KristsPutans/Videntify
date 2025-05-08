# Use official Python image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p logs/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "src/main.py"]
