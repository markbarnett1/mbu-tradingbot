# Render-ready Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Render sets PORT env var
ENV PORT=8080
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8080", "app:app"]
