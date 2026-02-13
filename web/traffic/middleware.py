import logging
from django.utils.deprecation import MiddlewareMixin
from datetime import datetime

logger = logging.getLogger(__name__)

class TrafficMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
class ActiveUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # Aquí puedes loguear información de los usuarios conectados
            logger.info(f"Usuario conectado: {request.user.username}, Fecha y Hora: {datetime.now()}")