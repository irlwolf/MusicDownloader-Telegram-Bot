# Use a Python base image
FROM python:3.10-slim

# Install system dependencies (FFmpeg is required for this bot)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Start the bot
CMD ["python3", "main.py"]
