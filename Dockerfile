FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m nonroot
USER nonroot

COPY . .

EXPOSE 8000

CMD newrelic-admin run-program gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --access-logfile - \
    logistic-api.wsgi:application