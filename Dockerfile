FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=landuse_project.settings

WORKDIR /app

# System deps for scientific stack
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source
COPY . /app

# Install Python dependencies (kept minimal per project docs)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "if [ \"${RUN_MIGRATIONS_ON_START:-false}\" = \"true\" ]; then python manage.py migrate --noinput; fi; gunicorn landuse_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-600} --access-logfile - --error-logfile -"]
