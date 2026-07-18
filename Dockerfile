# Simple dev container for Django Playground.
# Runs the Django dev server against settings_dev; the SQLite DB lives on a
# mounted volume (see docker-compose.yml) so data persists across sessions.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django project
COPY DjangoPlayground/ ./DjangoPlayground/
COPY docker/entrypoint.sh /entrypoint.sh
# Normalize line endings (in case of CRLF from a Windows checkout) and make executable
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Mount point for the persistent SQLite database (see DB_NAME in compose)
RUN mkdir -p /data

# manage.py lives here
WORKDIR /app/DjangoPlayground

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
