FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY wsgi.py .

# Expose port
EXPOSE 5000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Run the application
CMD ["python", "wsgi.py"]
