FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # PROJECT_NAME=rumbia \
    # DJANGO_SETTINGS_MODULE=${PROJECT_NAME}.settings \
    PORT=8000
ENV PROJECT_NAME=rumbia
ENV DJANGO_SETTINGS_MODULE=${PROJECT_NAME}.settings    

# Instalar dependencias del sistema
# Incluimos: gcc, pkg-config, libmariadb-dev (para mysqlclient) y libpq-dev (para PostgreSQL opcional)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    pkg-config \
    libmariadb-dev \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

#  Copiar e instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

#  Copiar todo el proyecto
COPY . /app

#  Crear usuario no-root
RUN addgroup --system app && adduser --system --ingroup app app \
 && chown -R app:app /app
USER app

EXPOSE ${PORT}

#  Migrar, collectstatic y arrancar con gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn ${PROJECT_NAME}.wsgi:application --bind 0.0.0.0:${PORT} --workers 3"]
# CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn ${PROJECT_NAME}.wsgi:application --bind 0.0.0.0:${PORT} --workers 3"]