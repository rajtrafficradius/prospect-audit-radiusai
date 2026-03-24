FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Playwright and Matplotlib
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install chromium --with-deps

# Copy the rest of the application
COPY . .

# Expose the port Railway expects
EXPOSE $PORT

# Run the FastAPI server
CMD uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}
