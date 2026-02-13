from django.apps import AppConfig
import sys
import threading
import json

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        import notifications.signals
        if 'runserver' in sys.argv:
            # Esperamos 2 segundos para que la DB arranque bien
            timer = threading.Timer(2.0, self.enviar_notificaciones_inicio)
            timer.start()

    def enviar_notificaciones_inicio(self):
        try:
            from django.contrib.sessions.models import Session
            from django.utils import timezone
            from users.models import DispositivoSesion
            from webpush.models import PushInformation
            
            # ELIMINAMOS LA IMPORTACIÓN QUE CAUSABA EL ERROR
            # from webpush import WebPushException (Borrado)

            try:
                from webpush.utils import _send_notification
            except ImportError:
                from webpush.utils import send_notification as _send_notification

            print("\n" + "="*60)
            print("[INFO] BUSCANDO DISPOSITIVOS VINCULADOS...")

            sesiones_activas = Session.objects.filter(expire_date__gte=timezone.now())
            claves_activas = [s.session_key for s in sesiones_activas]
            dispositivos = DispositivoSesion.objects.filter(session_key__in=claves_activas)
            
            enviados = 0

            for disp in dispositivos:
                try:
                    target = PushInformation.objects.filter(
                        subscription__endpoint=disp.endpoint
                    ).first()

                    if target:
                        payload_dict = {
                            "head": "Servidor Online",
                            "body": f"Hola {target.user.username}, Milanesa activa.",
                            "icon": "/static/logo/logo.png",
                            "url": "http://127.0.0.1:8000"
                        }
                        
                        payload_json = json.dumps(payload_dict)
                        
                        try:
                            # INTENTO DE ENVÍO
                            _send_notification(target.subscription, payload_json, ttl=1000)
                            print(f"   [OK] Enviado a: {target.user.username}")
                            enviados += 1

                        except Exception as e:
                            # === AUTO-LIMPIEZA GENÉRICA ===
                            # Convertimos el error a texto y buscamos los códigos HTTP
                            error_str = str(e)
                            
                            # 410 = Gone (Ya no existe), 404 = Not Found (No encontrado)
                            if "410" in error_str or "404" in error_str:
                                print(f"   [LIMPIEZA] Usuario {target.user.username} se desuscribió. Borrando...")
                                target.delete() 
                                disp.delete()
                            else:
                                print(f"   [FALLO] Error enviando a {target.user.username}: {e}")

                    else:
                        pass

                except Exception as e:
                    print(f"   [ERROR LOOP]: {e}")

            if enviados > 0:
                print(f"[RESUMEN] Notificaciones enviadas: {enviados}")
            else:
                print("[INFO] Ningun dispositivo activo para notificar.")
                
            print("="*60 + "\n")

        except Exception as e:
            print(f"[ERROR STARTUP]: {e}")    