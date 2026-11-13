from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PermissionViewSet, RolePersonnaliseViewSet, ProfilUtilisateurViewSet, SiteViewSet
from .views import InvitationViewSet, AccepterInvitationViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

router = DefaultRouter()
router.register(r'permissions',   PermissionViewSet,        basename='permissions')
router.register(r'roles',         RolePersonnaliseViewSet,  basename='roles')
router.register(r'sites',         SiteViewSet,               basename='sites')
router.register(r'utilisateurs',  ProfilUtilisateurViewSet, basename='utilisateurs-tenant')
router.register(r'invitations',         InvitationViewSet,        basename='invitations')
router.register(r'invitation-publique', AccepterInvitationViewSet, basename='invitation-publique')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_permissions(request):
    """Retourne la liste des permissions de l'utilisateur connecté, son niveau
    d'administration (Groupe = tous les sites, Site = ses sites), et ses sites."""
    if request.user.is_superuser:
        from .models import Permission
        codes = list(Permission.objects.values_list('code', flat=True))
        return Response({
            'permissions': codes, 'est_admin': True,
            'est_admin_groupe': True, 'est_admin_site': False, 'mes_sites': [],
        })
    try:
        profil            = request.user.profil
        est_admin_groupe  = profil.est_admin_groupe
        est_admin_site    = profil.est_admin_site
        mes_sites         = list(profil.sites_autorises.values('id', 'nom'))

        if profil.role_personnalise:
            if profil.role_personnalise.est_admin:
                from .models import Permission
                codes = list(Permission.objects.values_list('code', flat=True))
                return Response({
                    'permissions': codes, 'est_admin': True,
                    'est_admin_groupe': est_admin_groupe, 'est_admin_site': est_admin_site,
                    'mes_sites': mes_sites,
                })
            codes = list(profil.role_personnalise.permissions.values_list('code', flat=True))
            return Response({
                'permissions': codes, 'est_admin': False,
                'est_admin_groupe': est_admin_groupe, 'est_admin_site': est_admin_site,
                'mes_sites': mes_sites,
            })
        return Response({
            'permissions': [], 'est_admin': est_admin_groupe,
            'est_admin_groupe': est_admin_groupe, 'est_admin_site': est_admin_site,
            'mes_sites': mes_sites,
        })
    except Exception:
        pass
    return Response({'permissions': [], 'est_admin': False, 'est_admin_groupe': False, 'est_admin_site': False, 'mes_sites': []})

urlpatterns = [
    path('', include(router.urls)),
    path('mes-permissions/', mes_permissions, name='mes-permissions'),
]