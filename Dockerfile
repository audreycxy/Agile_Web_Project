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

# Expose port 5000 as the local-Docker default. On hosts like Render that
# inject a $PORT environment variable, the CMD below uses that value instead.
EXPOSE 5000

# Seed the demo admin and player accounts (idempotent — only manages the two
# seeded accounts, leaves other users alone), then start the Waitress server
# on the port the host assigns. Falls back to 5000 for local `docker run`.
CMD sh -c "python scripts/seed_users.py && waitress-serve --listen=0.0.0.0:${PORT:-5000} wsgi:app"
