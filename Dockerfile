# Use an official Python 3.12 slim image
FROM python:3.12-slim

# Install system dependencies required for building packages and for Playwright/crawl4ai
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libsqlite3-dev \
    sqlite3 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    ffmpeg \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create a non-root user
RUN useradd -m -s /bin/bash appuser

# Copy the requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt  

# GROQ API key
ARG GROQ_API_KEY
ENV GROQ_API_KEY=${GROQ_API_KEY}  

# Install Playwright and its dependencies
RUN playwright install chromium

# Set Playwright cache path and permissions
ENV PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright
RUN mkdir -p /home/appuser/.cache/ms-playwright && \
    chown -R appuser:appuser /home/appuser/.cache/ms-playwright && \
    chmod -R 775 /home/appuser/.cache/ms-playwright

# Run crawl4ai-setup before starting the app
RUN crawl4ai-setup

# Copy the rest of the project files into the container
COPY . /app/

# Set ownership and permissions for the whole project
RUN chown -R appuser:appuser /app && \
    chmod -R 775 /app

# Set Hugging Face cache directory
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p /app/.cache/huggingface && \
    chown -R appuser:appuser /app/.cache/huggingface && \
    chmod -R 775 /app/.cache/huggingface

# Fix Streamlit port binding issue
RUN mkdir -p /home/appuser/.streamlit && \
    echo "[server]" > /home/appuser/.streamlit/config.toml && \
    echo "port = 8080" >> /home/appuser/.streamlit/config.toml && \
    echo "enableCORS = false" >> /home/appuser/.streamlit/config.toml

# Set environment variables
ENV CRAWL4AI_CACHE_DIR="/app/.crawl4ai"  
ENV PYTHONPATH=/app

# Expose the Streamlit port
EXPOSE 8080  

# Switch to non-root user
USER appuser  

# Set the default command to run your Streamlit application
ENTRYPOINT ["python", "-m", "streamlit", "run", "src/UI/app.py", "--server.port=8080", "--server.address=0.0.0.0"]