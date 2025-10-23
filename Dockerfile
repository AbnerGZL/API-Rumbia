FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PROJECT_NAME=rumbia \
    DJANGO_SETTINGS_MODULE=${PROJECT_NAME}.settings \
    PORT=8000

# dependencias del sistema (ajusta si usas otro motor de BD)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copiar requirements y instalarlos primero para aprovechar cache de docker
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# copiar el resto del proyecto
COPY . /app

# crear usuario no-root y ajustar permisos
RUN addgroup --system app && adduser --system --ingroup app app \
 && chown -R app:app /app

USER app

EXPOSE ${PORT}

# Al iniciar: migraciones, collectstatic y arranque con gunicorn.
# Reemplaza PROJECT_NAME en tiempo de build o run si es necesario:
# docker build --build-arg PROJECT_NAME=mi_proyecto -t miimagen .
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn ${PROJECT_NAME}.wsgi:application --bind 0.0.0.0:${PORT} --workers 3"]