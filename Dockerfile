# 1. Use Python 3.11-slim as the base
FROM python:3.11-slim

# 2. Install system dependencies
# We added nodejs here to solve YouTube signature challenges
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /app

# 4. Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Start the bot (This MUST be the very last line)
CMD ["python3", "main.py"]
