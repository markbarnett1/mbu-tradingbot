FROM python:3.11-slim

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app

EXPOSE 8080
CMD ["bash", "-lc", "exec gunicorn -w 3 -b 0.0.0.0:${PORT:-8080} app:app"]
