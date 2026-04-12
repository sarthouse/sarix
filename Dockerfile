FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*
    
RUN addgroup --system django && adduser --system --ingroup django django

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chown -R django:django /app

RUN mkdir -p /home/django && chown django:django /home/django

ENV HOME=/home/django \
    XDG_CACHE_HOME=/home/django/.cache

USER django


EXPOSE 8000