# Minimal, reproducible image
FROM python:3.11-slim

# System updates & build deps for cryptography
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy dependency list first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of your app
COPY . /app

# Render provides $PORT. Expose for local clarity.
EXPOSE 8080

# Start gunicorn (3 workers is fine on Render Free)
# IMPORTANT: bind to 0.0.0.0:$PORT and point to app:app
CMD ["bash", "-lc", "exec gunicorn -w 3 -b 0.0.0.0:${PORT:-8080} app:app"]
