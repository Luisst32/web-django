from users.models import Usuarios, Seguidores
from django.db.models import Q, Count

class RecommendationService:
    @staticmethod
    def get_suggestions(user, limit=5):
        """
        Retorna usuarios que el usuario actual NO sigue,
        priorizando aquellos seguidos por personas que el usuario ya sigue (Amigos en común).
        """
        if not user.is_authenticated:
            return []

        # IDs de usuarios que YA sigue (incluyéndose a sí mismo)
        following_ids = list(Seguidores.objects.filter(usuario=user).values_list('seguido_id', flat=True))
        following_ids.append(user.id)

        # Excluir esos IDs, anotar coincidencias y ordenar
        # FIX POSTGRES: Usar values('id') para evitar error de GROUP BY con todos los campos
        suggested_ids = Usuarios.objects.exclude(
            id__in=following_ids
        ).annotate(
            mutual_count=Count('seguidores', filter=Q(seguidores__usuario_id__in=following_ids))
        ).order_by('-mutual_count', '-id').values_list('id', flat=True)[:limit]
        
        # Recuperar objetos reales (en el orden correcto)
        suggestions = list(Usuarios.objects.filter(id__in=suggested_ids))
        # Reordenar en Python para mantener el orden de importancia (mutual_count)
        suggestions.sort(key=lambda x: list(suggested_ids).index(x.id))
        
        return suggestions
