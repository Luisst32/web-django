from django.core.management.base import BaseCommand
from users.models import Usuarios  

class Command(BaseCommand):
    help = 'Actualiza los perfiles de usuario sin foto de perfil y les asigna una foto predeterminada'

    def handle(self, *args, **kwargs):
        usuarios_sin_foto = Usuarios.objects.filter(foto_perfil__isnull=True) | Usuarios.objects.filter(foto_perfil='')

        for usuario in usuarios_sin_foto:
            usuario.foto_perfil = 'default/default-profil.jpg'  
            usuario.save()
            self.stdout.write(self.style.SUCCESS(f'Perfil actualizado para {usuario.username}'))

        self.stdout.write(self.style.SUCCESS('Actualización de perfiles completada.'))
