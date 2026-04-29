# Running project inside Docker container
# Use Python 3.11 slim image as the base
FROM python:3.11-slim

# Set working folder to /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project
COPY . .

# Create /app/instance
RUN mkdir -p /app/instance

# Expose port 5000 for the Flask app 
EXPOSE 5000

# Run the Flask app using Waitress
CMD ["waitress-serve", "--listen=0.0.0.0:5000", "wsgi:app"]
