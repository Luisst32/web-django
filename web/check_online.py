import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import Usuarios
from django.utils import timezone

print("=== USERS LAST SEEN ===")
for u in Usuarios.objects.exclude(last_seen=None).order_by('-last_seen')[:10]:
    diff = (timezone.now() - u.last_seen).total_seconds()
    print(f"{u.username}: last_seen {diff:.0f}s ago, is_online={u.is_online}")
