from django.apps import AppConfig


class PublicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'publications'
    default = True
    
    def ready(self):
        import publications.signals
