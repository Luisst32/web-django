FROM python:3.12-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente
COPY . /app/

# Puerto interno
EXPOSE 8000

# PRODUCCIÓN: Daphne (soporta WebSockets con Django Channels)
CMD ["daphne", \
     "-b", "0.0.0.0", \
     "-p", "8000", \
     "-t", "300", \
     "--application-close-timeout", "300", \
     "--ping-interval", "20", \
     "--ping-timeout", "20", \
     "web.asgi:application"]
