import uuid
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import Permission, RolePersonnalise, ProfilUtilisateur, Entreprise, Site
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import InvitationUtilisateur
from rest_framework.permissions import BasePermission


def verifier_admin_groupe(request):
    """Lève une PermissionDenied si l'utilisateur n'est pas Administrateur Groupe."""
    profil = getattr(request.user, 'profil', None)
    if not profil or not profil.est_admin_groupe:
        raise PermissionDenied("Cette action est réservée à un administrateur groupe.")


# ── Serializers ──────────────────────────────────────────────────────────────

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permission
        fields = ['id', 'code', 'libelle', 'module', 'description']

class RolePersonnaliseSerializer(serializers.ModelSerializer):
    permissions      = PermissionSerializer(many=True, read_only=True)
    permissions_ids  = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(),
        write_only=True, source='permissions'
    )
    nb_utilisateurs  = serializers.SerializerMethodField()
    site_nom         = serializers.SerializerMethodField()

    class Meta:
        model  = RolePersonnalise
        fields = ['id', 'nom', 'description', 'est_admin', 'acces_tous_sites', 'site', 'site_nom',
                  'permissions', 'permissions_ids', 'nb_utilisateurs', 'created_at']

    def get_nb_utilisateurs(self, obj):
        return obj.utilisateurs.count()

    def get_site_nom(self, obj):
        return obj.site.nom if obj.site else None


class SiteSerializer(serializers.ModelSerializer):
    nb_utilisateurs = serializers.SerializerMethodField()

    class Meta:
        model  = Site
        fields = ['id', 'nom', 'code', 'adresse', 'actif', 'est_principal', 'nb_utilisateurs',
                  'compteur_fnc_actuel', 'created_at']
        read_only_fields = ['id', 'est_principal', 'compteur_fnc_actuel', 'created_at']

    def get_nb_utilisateurs(self, obj):
        return obj.utilisateurs_autorises.count()


class SiteLightSerializer(serializers.ModelSerializer):
    """Version allégée de Site, utilisée en imbriqué dans ProfilUtilisateurSerializer."""
    class Meta:
        model  = Site
        fields = ['id', 'nom', 'code', 'est_principal']


class ProfilUtilisateurSerializer(serializers.ModelSerializer):
    username         = serializers.CharField(source='user.username', read_only=True)
    email            = serializers.CharField(source='user.email', read_only=True)
    full_name        = serializers.SerializerMethodField()
    role_nom         = serializers.SerializerMethodField()
    sites_autorises  = SiteLightSerializer(many=True, read_only=True)
    est_admin_groupe = serializers.BooleanField(read_only=True)
    est_admin_site   = serializers.BooleanField(read_only=True)

    class Meta:
        model  = ProfilUtilisateur
        fields = ['id', 'username', 'email', 'full_name', 'role', 'role_personnalise', 'role_nom',
                  'sites_autorises', 'est_admin_groupe', 'est_admin_site', 'actif', 'created_at']

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_role_nom(self, obj):
        if obj.role_personnalise:
            return obj.role_personnalise.nom
        return obj.get_role_display()

# ── ViewSets ─────────────────────────────────────────────────────────────────

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste fixe des permissions — lecture seule."""
    permission_classes = [IsAuthenticated]
    serializer_class   = PermissionSerializer
    pagination_class   = None

    def get_queryset(self):
        return Permission.objects.all().order_by('module', 'code')

    @action(detail=False, methods=['get'], url_path='par-module')
    def par_module(self, request):
        """Retourne les permissions groupées par module."""
        from itertools import groupby
        perms = Permission.objects.all().order_by('module', 'code')
        resultat = {}
        for perm in perms:
            if perm.module not in resultat:
                resultat[perm.module] = []
            resultat[perm.module].append(PermissionSerializer(perm).data)
        return Response(resultat)


class RolePersonnaliseViewSet(viewsets.ModelViewSet):
    """
    CRUD des rôles, scopés par site :
    - site=None -> rôle global, visible et assignable sur tous les sites.
      Seul un Administrateur Groupe peut créer/modifier un rôle global.
    - site=<Site> -> rôle propre à ce site. Un Administrateur Site ne peut
      créer/gérer que des rôles rattachés à l'un de SES sites — jamais un
      rôle global, jamais un rôle admin, jamais le rôle d'un autre site.

    Un Administrateur Site voit dans sa liste : les rôles globaux (pour
    pouvoir les assigner) + les rôles propres à ses sites. Il ne voit pas
    les rôles propres à un site auquel il n'a pas accès.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = RolePersonnaliseSerializer
    pagination_class   = None

    def get_queryset(self):
        profil = self.request.user.profil
        qs = RolePersonnalise.objects.filter(
            entreprise=profil.entreprise
        ).prefetch_related('permissions')

        if not profil.est_admin_groupe:
            # Un Admin Site ne voit QUE les rôles rattachés à ses propres
            # sites — pas les rôles globaux, réservés au Groupe Admin.
            qs = qs.filter(site_id__in=profil.sites_ids_autorises)

        return qs

    def _verifier_peut_gerer_role(self, data=None, role_existant=None, creation=False):
        profil = getattr(self.request.user, 'profil', None)
        if not profil or not (profil.est_admin_groupe or profil.est_admin_site):
            raise PermissionDenied("Seul un administrateur peut gérer les rôles.")

        if profil.est_admin_groupe:
            return

        # Administrateur Site : jamais un rôle admin
        if role_existant is not None and role_existant.est_admin:
            raise PermissionDenied("Seul un administrateur groupe peut modifier un rôle administrateur.")
        if data and data.get('est_admin'):
            raise PermissionDenied("Seul un administrateur groupe peut créer un rôle administrateur.")

        # Administrateur Site : jamais un rôle global, ni le rôle d'un autre site
        if role_existant is not None:
            if role_existant.site_id is None:
                raise PermissionDenied("Seul un administrateur groupe peut modifier un rôle global.")
            if role_existant.site_id not in profil.sites_ids_autorises:
                raise PermissionDenied("Vous ne pouvez gérer que les rôles de vos propres sites.")

        if creation or (data is not None and 'site' in data):
            site_cible = data.get('site') if data else None
            if site_cible is None:
                raise PermissionDenied("Un rôle créé par un administrateur site doit être rattaché à l'un de ses sites.")
            if site_cible.id not in profil.sites_ids_autorises:
                raise PermissionDenied("Vous ne pouvez rattacher ce rôle qu'à l'un de vos propres sites.")

    def perform_create(self, serializer):
        self._verifier_peut_gerer_role(data=serializer.validated_data, creation=True)
        serializer.save(entreprise=self.request.user.profil.entreprise)

    def perform_update(self, serializer):
        self._verifier_peut_gerer_role(data=serializer.validated_data, role_existant=serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._verifier_peut_gerer_role(role_existant=instance)
        instance.delete()


class SiteViewSet(viewsets.ModelViewSet):
    """
    CRUD des sites d'une entreprise. Création/modification/suppression
    réservées à l'Administrateur Groupe — la structure des sites d'une
    entreprise est une décision organisationnelle globale, pas locale.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = SiteSerializer
    pagination_class   = None

    def get_queryset(self):
        profil = self.request.user.profil
        qs = Site.objects.filter(entreprise=profil.entreprise).order_by('nom')
        if not profil.est_admin_groupe:
            qs = qs.filter(pk__in=profil.sites_ids_autorises)
        return qs

    def perform_create(self, serializer):
        verifier_admin_groupe(self.request)
        entreprise = self.request.user.profil.entreprise
        est_premier_site = not Site.objects.filter(entreprise=entreprise).exists()
        serializer.save(entreprise=entreprise, est_principal=est_premier_site)

    def perform_update(self, serializer):
        verifier_admin_groupe(self.request)
        serializer.save()

    @action(detail=True, methods=['post'], url_path='definir-principal')
    def definir_principal(self, request, pk=None):
        verifier_admin_groupe(request)
        site = self.get_object()
        Site.objects.filter(
            entreprise=site.entreprise, est_principal=True
        ).exclude(pk=site.pk).update(est_principal=False)
        site.est_principal = True
        site.save()
        return Response({'message': f'"{site.nom}" défini comme site principal'})

    @action(detail=True, methods=['post'], url_path='toggle-actif')
    def toggle_actif(self, request, pk=None):
        verifier_admin_groupe(request)
        site = self.get_object()
        site.actif = not site.actif
        site.save()
        return Response({'actif': site.actif})

    def destroy(self, request, *args, **kwargs):
        verifier_admin_groupe(request)
        site       = self.get_object()
        entreprise = site.entreprise

        if Site.objects.filter(entreprise=entreprise).count() <= 1:
            return Response(
                {'erreur': "Impossible de supprimer le dernier site de l'entreprise."},
                status=400
            )
        if site.est_principal:
            return Response(
                {'erreur': "Ce site est le site principal. Définissez un autre site comme "
                            "principal avant de le supprimer."},
                status=400
            )
        return super().destroy(request, *args, **kwargs)


class ProfilUtilisateurViewSet(viewsets.ModelViewSet):
    """
    Un Administrateur Groupe voit et gère tous les utilisateurs de l'entreprise.
    Un Administrateur Site (ou tout autre utilisateur avec un rôle ayant la
    permission d'accès à cette vue) ne voit que les utilisateurs partageant
    au moins un de ses propres sites.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = ProfilUtilisateurSerializer
    pagination_class   = None

    def get_queryset(self):
        profil = self.request.user.profil
        qs = ProfilUtilisateur.objects.filter(
            entreprise=profil.entreprise
        ).select_related('user', 'role_personnalise').prefetch_related('sites_autorises')

        if not profil.est_admin_groupe:
            qs = qs.filter(sites_autorises__id__in=profil.sites_ids_autorises).distinct()

        return qs

    @action(detail=True, methods=['post'], url_path='assigner-role')
    def assigner_role(self, request, pk=None):
        profil    = self.get_object()
        role_id   = request.data.get('role_id')
        demandeur = request.user.profil

        if not (demandeur.est_admin_groupe or demandeur.est_admin_site):
            return Response({'erreur': "Seul un administrateur peut assigner un rôle."}, status=403)

        role = None
        if role_id:
            try:
                role = RolePersonnalise.objects.get(id=role_id, entreprise=demandeur.entreprise)
            except RolePersonnalise.DoesNotExist:
                return Response({'erreur': 'Rôle introuvable'}, status=400)

            if role.est_admin and not demandeur.est_admin_groupe:
                return Response(
                    {'erreur': "Seul un administrateur groupe peut assigner un rôle administrateur."}, status=403
                )
            if role.site_id is None and not demandeur.est_admin_groupe:
                return Response(
                    {'erreur': "Seul un administrateur groupe peut assigner un rôle global."}, status=403
                )
            if (role.site_id is not None and not demandeur.est_admin_groupe
                    and not demandeur.sites_autorises.filter(pk=role.site_id).exists()):
                return Response(
                    {'erreur': "Vous ne pouvez assigner que des rôles globaux ou propres à vos sites."}, status=403
                )

        profil.assigner_role(role)  # invariant rôle/site géré par le modèle
        return Response(ProfilUtilisateurSerializer(profil).data)


    @action(detail=True, methods=['post'], url_path='assigner-sites')
    def assigner_sites(self, request, pk=None):
        profil     = self.get_object()
        sites_ids  = request.data.get('sites_ids', [])
        demandeur  = request.user.profil
        entreprise = demandeur.entreprise

        if not (demandeur.est_admin_groupe or demandeur.est_admin_site):
            return Response({'erreur': "Seul un administrateur peut gérer les sites d'un utilisateur."}, status=403)

        sites = list(Site.objects.filter(id__in=sites_ids, entreprise=entreprise))
        if len(sites) != len(set(sites_ids)):
            return Response(
                {'erreur': "Un ou plusieurs sites sont introuvables dans cette entreprise."}, status=400
            )

        if not demandeur.est_admin_groupe:
            if not set(sites_ids).issubset(set(demandeur.sites_ids_autorises)):
                return Response(
                    {'erreur': "Vous ne pouvez assigner que des sites auxquels vous avez vous-même accès."}, status=403
                )

        profil.synchroniser_sites(sites)  # invariant rôle/site géré par le modèle
        return Response(ProfilUtilisateurSerializer(profil).data)

    @action(detail=True, methods=['post'], url_path='toggle-actif')
    def toggle_actif(self, request, pk=None):
        demandeur = request.user.profil
        if not (demandeur.est_admin_groupe or demandeur.est_admin_site):
            return Response({'erreur': "Seul un administrateur peut activer/désactiver un utilisateur."}, status=403)
        profil = self.get_object()
        profil.actif = not profil.actif
        profil.save()
        return Response({'actif': profil.actif})
    

class InvitationSerializer(serializers.ModelSerializer):
    invite_par_nom = serializers.SerializerMethodField()
    role_nom       = serializers.SerializerMethodField()
    site_nom       = serializers.SerializerMethodField()
    est_expiree    = serializers.BooleanField(read_only=True)

    class Meta:
        model  = InvitationUtilisateur
        fields = ['id', 'email', 'prenom', 'nom', 'role', 'role_nom', 'site', 'site_nom',
                  'acceptee', 'est_expiree', 'invite_par_nom', 'created_at', 'expire_le']
        read_only_fields = ['id', 'acceptee', 'invite_par_nom', 'created_at', 'est_expiree', 'expire_le']

    def get_invite_par_nom(self, obj):
        if obj.invite_par:
            return obj.invite_par.get_full_name() or obj.invite_par.username
        return ''

    def get_role_nom(self, obj):
        return obj.role.nom if obj.role else ''

    def get_site_nom(self, obj):
        return obj.site.nom if obj.site else ''


class InvitationViewSet(viewsets.ModelViewSet):
    """
    Un Administrateur Groupe peut inviter sur n'importe quel site de
    l'entreprise (ou laisser vide -> site principal à l'acceptation).
    Un Administrateur Site ne peut inviter que sur un de ses propres sites,
    et ne peut jamais assigner un rôle administrateur ou global à l'invité.
    Un utilisateur non-admin ne peut ni voir ni créer d'invitation.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = InvitationSerializer
    pagination_class   = None

    def get_queryset(self):
        profil = self.request.user.profil
        if not (profil.est_admin_groupe or profil.est_admin_site):
            return InvitationUtilisateur.objects.none()
        return InvitationUtilisateur.objects.filter(
            entreprise=profil.entreprise
        ).select_related('role', 'invite_par', 'site')

    def perform_create(self, serializer):
        demandeur  = self.request.user.profil
        entreprise = demandeur.entreprise

        if not (demandeur.est_admin_groupe or demandeur.est_admin_site):
            raise PermissionDenied("Seul un administrateur peut inviter un utilisateur.")

        role = serializer.validated_data.get('role')
        if role and role.est_admin and not demandeur.est_admin_groupe:
            raise PermissionDenied("Seul un administrateur groupe peut inviter avec un rôle administrateur.")
        if role and role.site_id is None and not demandeur.est_admin_groupe:
            raise PermissionDenied("Seul un administrateur groupe peut inviter avec un rôle global.")

        site = serializer.validated_data.get('site')
        if not demandeur.est_admin_groupe:
            sites_autorises = demandeur.sites_autorises.all()
            if site and site not in sites_autorises:
                raise PermissionDenied("Vous ne pouvez inviter que sur un site auquel vous avez accès.")
            if not site:
                site = sites_autorises.filter(est_principal=True).first() or sites_autorises.first()

        if role and role.site_id is not None and site and role.site_id != site.id:
            raise PermissionDenied(f"Le rôle \"{role.nom}\" est réservé au site \"{role.site.nom}\".")

        invitation = serializer.save(
            entreprise  = entreprise,
            site        = site,
            invite_par  = self.request.user,
            expire_le   = timezone.now() + timedelta(days=7),
        )
        self._envoyer_email_invitation(invitation)

    def _envoyer_email_invitation(self, invitation):
        try:
            app_url = getattr(settings, 'APP_BASE_URL', 'http://localhost:3000')
            lien    = f"{app_url}/invitation/{invitation.token}"
            context = {
                'invitation': invitation,
                'lien':       lien,
                'app_url':    app_url,
            }
            html = render_to_string('emails/invitation.html', context)
            msg  = EmailMultiAlternatives(
                subject    = f'[Defex QMS] Vous avez été invité à rejoindre {invitation.entreprise.nom}',
                body       = f'Bonjour {invitation.prenom}, cliquez ici pour créer votre compte : {lien}',
                from_email = settings.DEFAULT_FROM_EMAIL,
                to         = [invitation.email],
            )
            msg.attach_alternative(html, 'text/html')
            msg.send()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Erreur envoi invitation : {e}')

    @action(detail=True, methods=['post'], url_path='renvoyer')
    def renvoyer(self, request, pk=None):
        invitation = self.get_object()
        if invitation.acceptee:
            return Response({'erreur': 'Cette invitation a déjà été acceptée'}, status=400)
        invitation.token     = uuid.uuid4()
        invitation.expire_le = timezone.now() + timedelta(days=7)
        invitation.save()
        self._envoyer_email_invitation(invitation)
        return Response({'message': 'Invitation renvoyée'})


class AccepterInvitationViewSet(viewsets.ViewSet):
    """Endpoints publics pour accepter une invitation — pas d'auth requise."""
    permission_classes = []

    @action(detail=False, methods=['get'], url_path='(?P<token>[^/.]+)/verifier')
    def verifier(self, request, token=None):
        try:
            invitation = InvitationUtilisateur.objects.get(token=token, acceptee=False)
            if invitation.est_expiree:
                return Response({'erreur': 'Cette invitation a expiré'}, status=400)
            return Response({
                'prenom':     invitation.prenom,
                'nom':        invitation.nom,
                'email':      invitation.email,
                'entreprise': invitation.entreprise.nom,
                'site':       invitation.site.nom if invitation.site else None,
            })
        except InvitationUtilisateur.DoesNotExist:
            return Response({'erreur': 'Invitation invalide ou déjà utilisée'}, status=404)

    @action(detail=False, methods=['post'], url_path='(?P<token>[^/.]+)/accepter')
    def accepter(self, request, token=None):
        try:
            invitation = InvitationUtilisateur.objects.get(token=token, acceptee=False)
            if invitation.est_expiree:
                return Response({'erreur': 'Cette invitation a expiré'}, status=400)

            mot_de_passe = request.data.get('mot_de_passe')
            if not mot_de_passe or len(mot_de_passe) < 8:
                return Response({'erreur': 'Le mot de passe doit contenir au moins 8 caractères'}, status=400)

            # Créer le compte utilisateur
            username = invitation.email.split('@')[0]
            if User.objects.filter(username=username).exists():
                username = f"{username}_{str(invitation.token)[:4]}"

            user = User.objects.create_user(
                username   = username,
                email      = invitation.email,
                password   = mot_de_passe,
                first_name = invitation.prenom,
                last_name  = invitation.nom,
            )

            from .models import ProfilUtilisateur
            profil = ProfilUtilisateur.objects.create(
                user              = user,
                entreprise        = invitation.entreprise,
                role              = 'production',
                role_personnalise = invitation.role,
                actif             = True,
            )
            # Rattache l'utilisateur au site de l'invitation, ou au site
            # principal de l'entreprise si aucun site n'a été précisé
            # (invitations créées avant l'ajout de ce champ, ou invitation
            # d'un admin groupe sans site choisi).
            site_a_assigner = invitation.site or Site.objects.filter(
                entreprise=invitation.entreprise, est_principal=True
            ).first()
            if site_a_assigner:
                profil.sites_autorises.add(site_a_assigner)

            invitation.acceptee = True
            invitation.save()

            return Response({'message': 'Compte créé avec succès. Vous pouvez maintenant vous connecter.'})

        except InvitationUtilisateur.DoesNotExist:
            return Response({'erreur': 'Invitation invalide ou déjà utilisée'}, status=404)
        
class HasQMSPermission(BasePermission):
    """
    Permission DRF générique.
    Usage : permission_classes = [IsAuthenticated, HasQMSPermission('qms.creer_fnc')]
    """
    def __init__(self, code_permission):
        self.code_permission = code_permission

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        try:
            profil = request.user.profil
            return profil.a_permission(self.code_permission)
        except Exception:
            return False


def require_permission(code):
    """Factory qui retourne une classe de permission DRF."""
    class DynamicPermission(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            if request.user.is_superuser:
                return True
            try:
                return request.user.profil.a_permission(code)
            except Exception:
                return False
    DynamicPermission.__name__ = f'Permission_{code}'
    return DynamicPermission