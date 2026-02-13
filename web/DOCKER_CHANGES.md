# RESUMEN DE CAMBIOS - DOCKER Y WEBSOCKETS

## ✅ Problemas Solucionados

### 1. **Gunicorn → Daphne**
- **Problema**: Gunicorn es WSGI, no soporta WebSockets
- **Solución**: Cambiado a Daphne (servidor ASGI)
- **Archivo**: `Dockerfile`

### 2. **Falta de Redis en docker-compose**
- **Problema**: Sin Redis, los Channel Layers no funcionan
- **Solución**: Agregado servicio Redis con configuración correcta
- **Archivo**: `docker-compose.yml`

### 3. **Archivos estáticos no se servían (CSS/JS)**
- **Problema**: Faltaba `STATIC_ROOT` y WhiteNoise
- **Solución**: 
  - Agregado `STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')`
  - Instalado `whitenoise>=6.6.0`
  - Agregado WhiteNoise middleware
  - Ejecutado `collectstatic`
- **Archivo**: `web/settings.py`, `requirements.txt`

### 4. **Chat colapsa al abrir**
- **Problema**: Código JavaScript sin manejo de errores en WebSocket
- **Solución**: Agregado validación y logging detallado
- **Archivos**: 
  - `chat/templates/chat/floating_chat.html`
  - `chat/templates/chat/partials/chat_window.html`

### 5. **Configuración incompleta para Cloudflare**
- **Problema**: Faltaban headers y configuración de seguridad
- **Solución**: Agregados ajustes específicos para proxy reverso
- **Archivo**: `web/settings.py`

---

## 📋 CAMBIOS REALIZADOS

### Dockerfile
```dockerfile
# Agregado: redis-tools para verificación de conexiones
# CMD: Daphne en lugar de Gunicorn
```

### docker-compose.yml
```yaml
# Agregado servicio Redis
# depends_on para asegurar orden de inicio
# CHANNELS_REDIS_HOST apuntando a nombre del servicio
```

### requirements.txt
```
+ whitenoise>=6.6.0
+ daphne (ya estaba)
+ channels-redis (ya estaba)
```

### web/settings.py
```python
# AGREGADO:
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
SECURE_HSTS_SECONDS = 31536000
SECURE_PROXY_TRUSTED_IPS = '*'
CHANNEL_LAYERS['capacity'] = 1500
CHANNEL_LAYERS['expiry'] = 10

# MIDDLEWARE:
'whitenoise.middleware.WhiteNoiseMiddleware'  # Agregado después de SecurityMiddleware
```

### chat/templates (WebSocket fixes)
- Mejor manejo de errores
- Console.log para debugging
- Validación de chatId antes de conectar
- Try/catch en renderización de mensajes

---

## 🔧 CONFIGURACIÓN CLOUDFLARE

Para que los WebSockets funcionen correctamente con Cloudflare:

### 1. **En Cloudflare Dashboard:**
   - Ir a: **Network** → **WebSockets** → **Enabled** ✅
   - Ir a: **Network** → **Gzip Compression** → **On**
   - Ir a: **Rules** → **Page Rules** → Crear regla para `/ws/*`

### 2. **Page Rules (si aplica):**
   ```
   URL: milanesa.shop/ws/*
   - Cache Level: Bypass
   - Performance: Off
   - Security: Low (durante testing)
   ```

### 3. **Headers desde Cloudflare:**
   - Cloudflare envía: `X-Forwarded-Proto: https`
   - Django confía en este header gracias a: `SECURE_PROXY_SSL_HEADER`

### 4. **Certificado SSL:**
   - Debe ser **Full (strict)** o **Full** (no Flexible)
   - Actualizar en: **SSL/TLS** → **Overview**

### 5. **DNS:**
   - Asegurar que tu dominio apunta correctamente a tu servidor
   - Status debe ser: **DNS only** o **Proxied**

---

## 🚀 CÓMO INICIAR DESPUÉS DE CAMBIOS

```bash
cd /home/luis/web-django/web

# Opción 1: Usar el script
./run-docker.sh

# Opción 2: Comandos manuales
docker compose down -v
docker compose build
docker compose up -d
docker compose exec -T web python manage.py collectstatic --noinput
```

---

## 🔍 VERIFICACIÓN

### 1. **Docker está corriendo:**
```bash
docker compose ps
# Debe mostrar: django_web (Up) y django_redis (Up)
```

### 2. **Redis está disponible:**
```bash
docker exec django_redis redis-cli ping
# Respuesta: PONG
```

### 3. **Acceder a la app:**
- **Local**: http://localhost:8000
- **Producción**: https://www.milanesa.shop

### 4. **Verificar WebSockets (F12 → Network):**
- Buscar conexiones `ws://` o `wss://`
- Status debe ser `101` (Switching Protocols)
- NO debe ser `404` o `403`

### 5. **Revisar logs:**
```bash
docker compose logs -f web
# Buscar líneas con "WSCONNECT" sin "WSDISCONNECT"
```

---

## ⚠️ POSIBLES PROBLEMAS FUTUROS

Si el chat sigue colapsando:

1. **Verificar console del navegador (F12):**
   - Buscar errores de JavaScript
   - Buscar errores de WebSocket

2. **Verificar logs de Docker:**
   ```bash
   docker compose logs web --tail=100
   ```

3. **Verificar Redis:**
   ```bash
   docker compose logs redis --tail=50
   ```

4. **Reiniciar servicios:**
   ```bash
   docker compose restart web
   docker compose restart redis
   ```

5. **Cloudflare puede estar bloqueando:**
   - Ir a **Security** → **Firewall Rules**
   - Agregar excepción para `/ws/*`

---

## 📞 SOPORTE

Si necesitas ayuda:
1. Revisa los logs: `docker compose logs web`
2. Verifica la consola del navegador: F12
3. Comprueba que Redis está corriendo: `docker compose ps`
4. Verifica la configuración de Cloudflare en el dashboard

¡Los WebSockets y el chat deberían funcionar ahora! 🎉
