from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    """
    Attache request.entreprise = l'entreprise du user connecté.
    Toutes les vues pourront ensuite filtrer avec request.entreprise
    sans jamais faire confiance à une donnée envoyée par le client.
    """
    def process_request(self, request):
        request.entreprise = None
        if request.user.is_authenticated:
            profil = getattr(request.user, 'profil', None)
            if profil:
                request.entreprise = profil.entreprise