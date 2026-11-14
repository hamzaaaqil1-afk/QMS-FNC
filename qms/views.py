from rest_framework import viewsets, filters, status, parsers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db.models import Count, Q , Prefetch
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from datetime import date
from django.utils import timezone

from .models import (
    NonConformite, ServiceProcessus, ClassificationFNC,
    OrigineEcart, StatutFNC, ActionCorrective, Analyse5M,
    SectionFNC, OptionListe, TemplateFormulaireFNC,
    PieceJointeFNC, PieceJointeAnalyse5M, PieceJointeAction,
    CAPA, CommentaireFNC, Audit, LigneChecklist,
    EcartAudit, PlanAction, ParametresEntreprise,
    ChampPersonnalise, ValeurChampFNC, TemplateExportFNC,Constat
)
from .serializers import (
    NonConformiteListSerializer, NonConformiteDetailSerializer,
    SectionFNCSerializer, SectionStructureSerializer,
    ServiceProcessusSerializer, ClassificationFNCSerializer,
    OrigineEcartSerializer, StatutFNCSerializer,
    ActionCorrectivelListSerializer, ActionCorrectivelDetailSerializer,
    Analyse5MSerializer, CommentaireFNCSerializer,
    PieceJointeFNCSerializer, PieceJointeAnalyse5MSerializer,
    PieceJointeActionSerializer, UserSerializer,
    CAPAListSerializer, CAPADetailSerializer,
    AuditListSerializer, AuditDetailSerializer,
    LigneChecklistSerializer, EcartAuditSerializer,
    PlanActionSerializer, ParametresEntrepriseSerializer,
    ChampPersonnaliseSerializer, ValeurChampFNCSerializer,
    TemplateExportFNCSerializer, TemplateFormulaireFNCSerializer,
    OptionListeSerializer, ConstatListSerializer
)
from tenants.views import require_permission




def envoyer_notification_action(action):
    if not action.responsable.email:
        return
    try:
        context = {
            'action': action,
            'responsable_nom': action.responsable.get_full_name() or action.responsable.username,
            'app_url': getattr(settings, 'APP_BASE_URL', 'http://localhost:3000'),
        }
        html = render_to_string('emails/action_notification.html', context)
        msg  = EmailMultiAlternatives(
            subject    = f'[Defex QMS] Nouvelle action assignée : {action.reference}',
            body       = f'Nouvelle action {action.reference} assignée à vous. Échéance : {action.date_echeance}',
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [action.responsable.email],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Erreur envoi email action : {e}')


class TenantSiteFilterMixin:
    """
    Isolation multi-tenant + multi-site pour les ViewSet QMS.

    Applique deux filtres à chaque queryset :
    1. Entreprise (tenant) — filtre obligatoire, sécurité critique.
    2. Site — restreint aux sites_autorises de l'utilisateur, sauf s'il
       a un accès admin (tous les sites de son entreprise).

    Utilisation dans une sous-classe :
        class MonViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
            CHAMP_ENTREPRISE = 'entreprise'  # ou 'entreprise_tenant' selon le modèle
            def get_queryset(self):
                qs = MonModele.objects.select_related(...)
                return self.filtrer_tenant_site(qs)
            def perform_create(self, serializer):
                serializer.save(**self.get_creation_kwargs())

    Un header optionnel `X-Site-Actif` (envoyé par le frontend une fois le
    sélecteur de site en place) permet à un utilisateur multi-sites de
    restreindre la vue à un site précis. Sans ce header : un admin voit
    tous ses sites, un utilisateur non-admin voit tous SES sites autorisés,
    et une création est rattachée au site principal par défaut.
    """
    CHAMP_ENTREPRISE = 'entreprise'
    CHAMP_SITE        = 'site'

    def _profil(self):
        return getattr(self.request.user, 'profil', None)

    def _a_acces_tous_sites(self, profil):
        if profil.role_personnalise and profil.role_personnalise.est_admin:
            return True
        if profil.role == 'admin' and not profil.role_personnalise:
            return True
        return False

    def _site_actif_id(self):
        return self.request.headers.get('X-Site-Actif')

    def filtrer_tenant_site(self, queryset):
        profil = self._profil()
        if not profil:
            return queryset.none()

        queryset = queryset.filter(**{self.CHAMP_ENTREPRISE: profil.entreprise})
        site_actif_id = self._site_actif_id()

        if self._a_acces_tous_sites(profil):
            if site_actif_id:
                queryset = queryset.filter(**{f'{self.CHAMP_SITE}_id': site_actif_id})
            return queryset

        sites_ids = profil.sites_ids_autorises
        queryset = queryset.filter(**{f'{self.CHAMP_SITE}_id__in': sites_ids})
        if site_actif_id:
            queryset = queryset.filter(**{f'{self.CHAMP_SITE}_id': site_actif_id})
        return queryset

    def get_site_pour_creation(self):
        """Détermine le site à assigner à un nouvel enregistrement créé par l'utilisateur courant."""
        profil = self._profil()
        if not profil:
            return None

        site_actif_id = self._site_actif_id()
        if site_actif_id:
            site = profil.sites_autorises.filter(pk=site_actif_id).first()
            if site:
                return site
            if self._a_acces_tous_sites(profil):
                from tenants.models import Site
                site = Site.objects.filter(pk=site_actif_id, entreprise=profil.entreprise).first()
                if site:
                    return site

        return (profil.sites_autorises.filter(est_principal=True).first()
                or profil.sites_autorises.first())

    def get_creation_kwargs(self):
        """kwargs à fusionner dans serializer.save() pour injecter entreprise + site à la création."""
        profil = self._profil()
        if not profil:
            return {}
        kwargs = {self.CHAMP_ENTREPRISE: profil.entreprise}
        site = self.get_site_pour_creation()
        if site:
            kwargs[self.CHAMP_SITE] = site
        return kwargs


class CAPAViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'type_capa', 'fnc']
    search_fields      = ['reference', 'titre', 'description']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = CAPA.objects.select_related('fnc', 'responsable', 'detecte_par', 'verificateur', 'validateur')
        return self.filtrer_tenant_site(qs)

    def get_serializer_class(self):
        if self.action == 'list':
            return CAPAListSerializer
        return CAPADetailSerializer

    def perform_create(self, serializer):
        serializer.save(detecte_par=self.request.user, **self.get_creation_kwargs())

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        capa           = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['ouvert', 'en_cours', 'verification', 'clos', 'annule']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': f'Statut invalide'}, status=400)
        capa.statut = nouveau_statut
        capa.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})

    @action(detail=True, methods=['post'], url_path='cloturer')
    def cloturer(self, request, pk=None):
        from datetime import date
        capa = self.get_object()
        capa.statut              = 'clos'
        capa.date_cloture        = date.today()
        capa.validateur          = request.user
        capa.commentaire_cloture = request.data.get('commentaire', '')
        capa.save()
        return Response({'message': 'CAPA clôturée avec succès'})

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = User.objects.filter(is_active=True).order_by('first_name')
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]


class NonConformiteViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut_ref','type_fnc', 'gravite', 'origine_ecart_ref', 'processus_ref', 'classification_ref', 'redacteur', 'responsable_user']
    search_fields      = ['numero', 'libelle', 'description', 'produit_concerne', 'client', 'fournisseur']
    ordering           = ['-created_at']
    CHAMP_ENTREPRISE   = 'entreprise_tenant'
    
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'structure_remplie', 'dashboard_qms']:
            return [IsAuthenticated(), require_permission('qms.voir_fnc')()]
        elif self.action == 'create':
            return [IsAuthenticated(), require_permission('qms.creer_fnc')()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), require_permission('qms.modifier_fnc')()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), require_permission('qms.supprimer_fnc')()]
        elif self.action == 'changer_statut':
            return [IsAuthenticated(), require_permission('qms.changer_statut')()]
        elif self.action in ['export_pdf', 'export_word']:
            return [IsAuthenticated(), require_permission('qms.exporter_fnc')()]
        return [IsAuthenticated()]
    
    
    def get_queryset(self):
        qs = NonConformite.objects.select_related(
            'redacteur', 'responsable_user', 'verificateur'
        ).prefetch_related('commentaires', 'pieces_jointes')
        return self.filtrer_tenant_site(qs)

    def get_serializer_class(self):
        if self.action == 'list':
            return NonConformiteListSerializer
        return NonConformiteDetailSerializer

    def perform_create(self, serializer):
        template_id = self.request.data.get('template_id')
        type_fnc = 'nc_produit'
        
        if template_id:
            try:
                template = TemplateFormulaireFNC.objects.get(id=template_id)
                type_fnc = template.type_objet
            except TemplateFormulaireFNC.DoesNotExist:
                pass

        premier_statut = StatutFNC.objects.filter(actif=True).order_by('ordre').first()
        
        serializer.save(
            redacteur  = self.request.user,
            type_fnc   = type_fnc,
            statut_ref = premier_statut,
            **self.get_creation_kwargs()
        )

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        import datetime
        today  = datetime.date.today()
        fncs   = self.filtrer_tenant_site(NonConformite.objects.all())
        ouvertes = fncs.exclude(statut_ref__est_final=True)

        # Retards
        en_retard = sum(1 for f in ouvertes if f.est_en_retard)

        # Coût non-qualité
        from django.db.models import Sum
        cout_total = fncs.aggregate(s=Sum('cout_non_qualite'))['s'] or 0

        # Par gravité
        par_gravite = {
            'critique':    fncs.filter(gravite='critique').count(),
            'majeur':      fncs.filter(gravite='majeur').count(),
            'mineur':      fncs.filter(gravite='mineur').count(),
            'observation': fncs.filter(gravite='observation').count(),
        }

        # Par type
        par_type = {}
        for t, _ in NonConformite.TYPE_NC_CHOICES:
            par_type[t] = fncs.filter(type_nc=t).count()

        # Tendance mensuelle (6 derniers mois)
        tendance = []
        for i in range(5, -1, -1):
            mois = today.replace(day=1) - datetime.timedelta(days=i * 30)
            nb   = fncs.filter(date_detection__year=mois.year, date_detection__month=mois.month).count()
            tendance.append({'mois': mois.strftime('%b %Y'), 'nb': nb})

        return Response({
            'total':             fncs.count(),
            'ouvertes':          ouvertes.count(),
            'en_retard':         en_retard,
            'cloturees_mois':    fncs.filter(statut_ref__est_final=True, date_cloture__month=today.month).count(),
            'cout_non_qualite':  float(cout_total),
            'par_gravite':       par_gravite,
            'par_type':          par_type,
            'tendance':          tendance,
            'taux_cloture':      round(fncs.filter(statut_ref__est_final=True).count() / fncs.count() * 100, 1) if fncs.count() > 0 else 0,
        })

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        fnc          = self.get_object()
        nouveau_code = request.data.get('statut')
        if not nouveau_code:
            return Response({'erreur': 'statut obligatoire'}, status=400)

        try:
            nouveau_statut = StatutFNC.objects.get(code=nouveau_code)
        except StatutFNC.DoesNotExist:
            return Response({'erreur': f'Statut "{nouveau_code}" introuvable'}, status=400)

        fnc.statut_ref = nouveau_statut

        if nouveau_statut.est_final and not fnc.date_cloture:
            import datetime
            fnc.date_cloture = datetime.date.today()

        fnc.save()
        serializer = NonConformiteDetailSerializer(fnc, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='ajouter-commentaire')
    def ajouter_commentaire(self, request, pk=None):
        fnc     = self.get_object()
        contenu = request.data.get('contenu', '')
        type_c  = request.data.get('type_comment', 'commentaire')
        if not contenu:
            return Response({'erreur': 'Contenu obligatoire'}, status=400)
        comment = CommentaireFNC.objects.create(
            fnc          = fnc,
            auteur       = request.user,
            contenu      = contenu,
            type_comment = type_c,
        )
        return Response({'message': 'Commentaire ajouté', 'id': str(comment.id)})

    @action(detail=True, methods=['post'], url_path='generer-capa')
    def generer_capa(self, request, pk=None):
        fnc = self.get_object()
        if fnc.capa_generee:
            return Response({'erreur': 'Une CAPA a déjà été générée pour cette FNC'}, status=400)
        capa = CAPA.objects.create(
            titre           = f"CAPA suite FNC {fnc.numero} — {fnc.libelle[:100]}",
            description     = f"CAPA générée automatiquement depuis la FNC {fnc.numero}.\n\nDescription : {fnc.description}",
            fnc             = fnc,
            entreprise      = fnc.entreprise_tenant,
            site            = fnc.site,
            type_capa     = 'corrective',
            statut          = 'ouvert',
            responsable     = fnc.responsable_user or request.user,
            date_echeance   = fnc.date_echeance,
            date_detection  = date.today(),
        )
        fnc.capa_generee = True
        fnc.save()
        return Response({'message': f'CAPA {capa.numero} générée', 'capa_id': str(capa.id)})

    @action(detail=True, methods=['post'], url_path='upload-piece-jointe')
    def upload_piece_jointe(self, request, pk=None):
        fnc     = self.get_object()
        fichier = request.FILES.get('fichier')
        if not fichier:
            return Response({'erreur': 'Fichier obligatoire'}, status=400)
        pj = PieceJointeFNC.objects.create(
            fnc          = fnc,
            nom_fichier  = fichier.name,
            type_fichier = request.data.get('type_fichier', 'photo'),
            fichier      = fichier,
            taille       = fichier.size,
            uploaded_by  = request.user,
        )
        return Response({'message': 'Fichier uploadé', 'id': str(pj.id), 'nom': pj.nom_fichier})
    
    @action(detail=True, methods=['get'], url_path='structure-remplie')
    def structure_remplie(self, request, pk=None):
        """Renvoie la structure dynamique (sections + champs) avec les valeurs résolues pour cette FNC."""
        fnc = self.get_object()
        sections = SectionFNC.objects.filter(actif=True).order_by('ordre', 'nom').prefetch_related('champs')

        resultat = []
        for section in sections:
            champs_data = []
            champs = [c for c in section.champs.all() if c.actif]
            champs = sorted(champs, key=lambda c: (c.ordre, c.nom))

            for champ in champs:
                if champ.type_rendu in ('tableau_actions', 'bloc_signature'):
                    continue  # blocs structurels, non pertinents pour cet affichage
                valeur = champ.get_valeur_pour_fnc(fnc)
                champs_data.append({
                    'id': str(champ.id),
                    'nom': champ.nom,
                    'cle': champ.cle,
                    'type_rendu': champ.type_rendu,
                    'largeur_rendu': champ.largeur_rendu,
                    'valeur': valeur,
                })

            if champs_data:
                resultat.append({
                    'id': str(section.id),
                    'nom': section.nom,
                    'code': section.code,
                    'champs': champs_data,
                })

        return Response(resultat)
    
    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        from django.http import HttpResponse
        from .pdf_generator import generer_pdf_fnc
        from .models import ParametresEntreprise, ValeurChampFNC
        fnc    = self.get_object()
        params = ParametresEntreprise.get_pour_entreprise(fnc.entreprise_tenant)
        
        # Récupérer les valeurs custom
        valeurs_custom = ValeurChampFNC.objects.filter(fnc=fnc).select_related('champ')

        sections = {
            'identification':     request.query_params.get('identification', 'true') == 'true',
            'classification':     request.query_params.get('classification', 'true') == 'true',
            'description':        request.query_params.get('description', 'true') == 'true',
            'actions_immediates': request.query_params.get('actions_immediates', 'true') == 'true',
            'analyse':            request.query_params.get('analyse', 'true') == 'true',
            'plan_action':        request.query_params.get('plan_action', 'true') == 'true',
            'cloture':            request.query_params.get('cloture', 'true') == 'true',
            'signatures':         request.query_params.get('signatures', 'true') == 'true',
        }
        
        import json
        config_str = request.query_params.get('config', '{}')
        try:
            config_champs = json.loads(config_str)
        except Exception:
            config_champs = {}
        
        buffer = generer_pdf_fnc(fnc, parametres={
            'nom_entreprise': params.nom_entreprise,
            'reference_doc':  params.reference_doc,
            'version_doc':    params.version_doc,
            'pied_de_page':   params.pied_de_page,
            'adresse':        params.adresse,
            'logo_path':      params.logo.path if params.logo else None,
            'valeurs_custom': valeurs_custom,
            'sections':       sections,
            'config_champs': config_champs,
            'afficher_nom_pied':       params.afficher_nom_pied,
            'afficher_adresse_pied':   params.afficher_adresse_pied,
            'afficher_reference_pied': params.afficher_reference_pied,
            'afficher_date_pied':      params.afficher_date_pied,
            'afficher_confidentiel':   params.afficher_confidentiel,
        })
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="FNC-{fnc.numero}.pdf"'
        return response
    
    @action(detail=True, methods=['get'], url_path='export-word')
    def export_word(self, request, pk=None):
        from django.http import HttpResponse
        from .word_generator import generer_word_fnc
        from .models import ParametresEntreprise, ValeurChampFNC
        fnc    = self.get_object()
        params = ParametresEntreprise.get_pour_entreprise(fnc.entreprise_tenant)
        
        # Récupérer les valeurs custom
        valeurs_custom = ValeurChampFNC.objects.filter(fnc=fnc).select_related('champ')
        sections = {
            'identification':     request.query_params.get('identification', 'true') == 'true',
            'classification':     request.query_params.get('classification', 'true') == 'true',
            'description':        request.query_params.get('description', 'true') == 'true',
            'actions_immediates': request.query_params.get('actions_immediates', 'true') == 'true',
            'analyse':            request.query_params.get('analyse', 'true') == 'true',
            'plan_action':        request.query_params.get('plan_action', 'true') == 'true',
            'cloture':            request.query_params.get('cloture', 'true') == 'true',
            'signatures':         request.query_params.get('signatures', 'true') == 'true',
        }
        
        import json
        config_str = request.query_params.get('config', '{}')
        try:
            config_champs = json.loads(config_str)
        except Exception:
            config_champs = {}
            
        buffer = generer_word_fnc(fnc, parametres={
            'nom_entreprise': params.nom_entreprise,
            'reference_doc':  params.reference_doc,
            'version_doc':    params.version_doc,
            'pied_de_page':   params.pied_de_page,
            'adresse':        params.adresse,
            'logo_path':      params.logo.path if params.logo else None,
            'valeurs_custom': valeurs_custom,
            'sections':       sections,
            'config_champs': config_champs,
            'afficher_nom_pied':       params.afficher_nom_pied,
            'afficher_adresse_pied':   params.afficher_adresse_pied,
            'afficher_reference_pied': params.afficher_reference_pied,
            'afficher_date_pied':      params.afficher_date_pied,
            'afficher_confidentiel':   params.afficher_confidentiel,
        })
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="FNC-{fnc.numero}.docx"'
        return response




class ActionCorrectivelViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'type_action', 'processus_ref', 'fnc']
    search_fields      = ['reference', 'description', 'resultat']
    ordering           = ['date_echeance']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'mes_actions']:
            return [IsAuthenticated(), require_permission('qms.voir_action')()]
        elif self.action == 'create':
            return [IsAuthenticated(), require_permission('qms.creer_action')()]
        elif self.action == 'cloturer':
            return [IsAuthenticated(), require_permission('qms.cloturer_action')()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), require_permission('qms.modifier_action')()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), require_permission('qms.supprimer_action')()]
        return [IsAuthenticated()]

    def _verifier_non_verrouillee(self, obj):
        """
        Invariant métier : une action clôturée (statut='realisee') ne peut plus
        être modifiée ni supprimée, sauf par un administrateur (groupe ou site).
        """
        from rest_framework.exceptions import ValidationError
        profil = self.request.user.profil
        if obj.est_verrouillee and not (profil.est_admin_groupe or profil.est_admin_site):
            raise ValidationError({
                'erreur': "Cette action est clôturée et ne peut plus être modifiée ou "
                          "supprimée. Seul un administrateur peut le faire."
            })

    def perform_update(self, serializer):
        self._verifier_non_verrouillee(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._verifier_non_verrouillee(instance)
        instance.delete()

    def get_queryset(self):
        qs = ActionCorrective.objects.select_related('fnc', 'responsable', 'ref_cause')
        return self.filtrer_tenant_site(qs)

    def get_serializer_class(self):
        if self.action == 'list':
            return ActionCorrectivelListSerializer
        return ActionCorrectivelDetailSerializer
    
    def perform_create(self, serializer):
        action = serializer.save(**self.get_creation_kwargs())
        envoyer_notification = self.request.data.get('envoyer_notification', False)
        if envoyer_notification in (True, 'true', 'True', '1'):
            envoyer_notification_action(action)

    @action(detail=False, methods=['get'], url_path='mes-actions')
    def mes_actions(self, request):
        actions = self.get_queryset().filter(responsable=request.user)
        serializer = ActionCorrectivelListSerializer(actions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cloturer')
    def cloturer(self, request, pk=None):
        from datetime import date
        obj               = self.get_object()
        obj.statut        = 'realisee'
        obj.date_cloture  = date.today()
        obj.resultat      = request.data.get('resultat', '')
        obj.save()
        return Response({'message': 'Action clôturée avec succès'})


class Analyse5MViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = Analyse5MSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['fnc', 'categorie', 'statut', 'processus_responsable']
    search_fields      = ['cause_analysee', 'cause_racine']

    def get_queryset(self):
        qs = Analyse5M.objects.select_related('fnc').prefetch_related('actions')
        return self.filtrer_tenant_site(qs)
    
    def perform_create(self, serializer):
        serializer.save(**self.get_creation_kwargs())
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), require_permission('qms.voir_analyse5m')()]
        elif self.action == 'create':
            return [IsAuthenticated(), require_permission('qms.creer_analyse5m')()]
        return [IsAuthenticated()]

        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_qms(request):
    today = date.today()

    profil = getattr(request.user, 'profil', None)
    fnc_qs = NonConformite.objects.all()
    action_qs = ActionCorrective.objects.all()
    if profil:
        fnc_qs = fnc_qs.filter(entreprise_tenant=profil.entreprise)
        action_qs = action_qs.filter(entreprise=profil.entreprise)
        est_admin = (profil.role_personnalise and profil.role_personnalise.est_admin) or \
                    (profil.role == 'admin' and not profil.role_personnalise)
        if not est_admin:
            sites_ids = profil.sites_ids_autorises
            fnc_qs = fnc_qs.filter(site_id__in=sites_ids)
            action_qs = action_qs.filter(site_id__in=sites_ids)

    # Stats FNC
    fnc_total    = fnc_qs.count()
    fnc_ouvertes  = fnc_qs.exclude(statut_ref__est_final=True).count()
    fnc_cloturees = fnc_qs.filter(statut_ref__est_final=True).count()
    statuts       = fnc_qs.values('statut_ref__code').annotate(count=Count('id')).order_by('statut_ref__code')

    # Répartition par gravité
    gravites = fnc_qs.values('gravite').annotate(
        count=Count('id')
    ).order_by('gravite')

    # Répartition par processus
    processus     = fnc_qs.exclude(processus_ref=None).values('processus_ref__nom').annotate(count=Count('id')).order_by('-count')[:6]

    # Stats actions
    actions_total   = action_qs.count()
    actions_cours   = action_qs.filter(statut='en_cours').count()
    actions_retard  = action_qs.filter(
        statut='en_cours',
        date_echeance__lt=today
    ).count()
    actions_realisees = action_qs.filter(statut='realisee').count()

    # Mes actions (utilisateur connecté)
    mes_actions = action_qs.filter(
        responsable=request.user,
        statut='en_cours'
    ).select_related('fnc').order_by('date_echeance')[:5]

    mes_actions_data = [{
        'id':           str(a.id),
        'reference':    a.reference,
        'description':  a.description[:60],
        'fnc_numero':   a.fnc.numero if a.fnc else '',
        'fnc_id':       str(a.fnc.id) if a.fnc else '',
        'date_echeance':a.date_echeance.isoformat(),
        'est_en_retard':a.date_echeance < today,
    } for a in mes_actions]

    # Dernières FNC
    dernieres_fnc = fnc_qs.exclude(statut_ref__est_final=True).order_by('-created_at')[:5]

    dernieres_fnc_data = [{
        'id':      str(f.id),
        'numero':  f.numero,
        'libelle': f.libelle or f.description[:50],
        'gravite': f.gravite,
        'statut':    f.statut_ref.code if f.statut_ref else '',
        'date':    f.date_decouverte.date().isoformat() if f.date_decouverte else '',
        'processus': f.processus_ref.nom if f.processus_ref else '',
        'nb_actions': f.actions.count(),
    } for f in dernieres_fnc]

    # Impact sûreté
    impact_surete = fnc_qs.filter(
        impact_surete=True
    ).exclude(statut__in=['cloturee', 'annulee']).count()

    return Response({
        'fnc': {
            'total':    fnc_total,
            'ouvertes': fnc_ouvertes,
            'cloturees':fnc_cloturees,
            'par_statut': list(statuts),
            'par_gravite': list(gravites),
            'par_processus': list(processus),
        },
        'actions': {
            'total':    actions_total,
            'en_cours': actions_cours,
            'en_retard':actions_retard,
            'realisees':actions_realisees,
        },
        'impact_surete':  impact_surete,
        'dernieres_fnc':  dernieres_fnc_data,
        'mes_actions':    mes_actions_data,
    })
    
    
from .serializers import (
    NonConformiteListSerializer, NonConformiteDetailSerializer,
    ActionCorrectivelListSerializer, ActionCorrectivelDetailSerializer,
    Analyse5MSerializer, PieceJointeFNCSerializer, UserSerializer,
    CAPAListSerializer, CAPADetailSerializer,
    AuditListSerializer, AuditDetailSerializer,
    LigneChecklistSerializer, EcartAuditSerializer,
)

class AuditViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'type_audit', 'processus']
    search_fields      = ['reference', 'titre', 'audite']
    ordering           = ['-date_prevue']

    def get_queryset(self):
        qs = Audit.objects.select_related('auditeur').prefetch_related('checklist', 'ecarts')
        return self.filtrer_tenant_site(qs)

    def get_serializer_class(self):
        if self.action == 'list':
            return AuditListSerializer
        return AuditDetailSerializer

    def perform_create(self, serializer):
        serializer.save(**self.get_creation_kwargs())

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        audit          = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['planifie', 'en_cours', 'realise', 'clos', 'annule']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)
        audit.statut = nouveau_statut
        if nouveau_statut == 'realise':
            from datetime import date
            audit.date_realisation = date.today()
        audit.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})


class LigneChecklistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneChecklistSerializer
    filterset_fields   = ['audit', 'categorie', 'resultat']

    def get_queryset(self):
        profil = getattr(self.request.user, 'profil', None)
        qs = LigneChecklist.objects.select_related('audit')
        if profil:
            qs = qs.filter(audit__entreprise=profil.entreprise)
        return qs


class EcartAuditViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = EcartAuditSerializer
    filterset_fields   = ['audit', 'gravite', 'statut']

    def get_queryset(self):
        profil = getattr(self.request.user, 'profil', None)
        qs = EcartAudit.objects.select_related('audit', 'fnc', 'capa')
        if profil:
            qs = qs.filter(audit__entreprise=profil.entreprise)
        return qs
    
    

class PlanActionViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = PlanActionSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'priorite', 'type_action', 'realisateur', 'verificateur']
    search_fields      = ['reference', 'titre', 'description']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = PlanAction.objects.select_related(
            'realisateur', 'verificateur', 'createur',
            'fnc', 'capa', 'audit', 'risque'
        )
        return self.filtrer_tenant_site(qs)

    def perform_create(self, serializer):
        action = serializer.save(createur=self.request.user, **self.get_creation_kwargs())
        # Notification email au réalisateur
        if action.realisateur and action.realisateur.email:
            try:
                send_mail(
                    subject=f'[ERP] Nouvelle action assignée : {action.reference}',
                    message=f"""Bonjour {action.realisateur.first_name},

Une nouvelle action vous a été assignée :

Référence : {action.reference}
Titre : {action.titre}
Priorité : {action.get_priorite_display()}
Date prévue : {action.date_prevue or 'Non définie'}

Connectez-vous sur rgbsetup.fr pour consulter le détail.

Cordialement,
Le système ERP Qualité""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[action.realisateur.email],
                    fail_silently=True,
                )
            except Exception:
                pass

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        plan_action    = self.get_object()
        nouveau_statut = request.data.get('statut')
        commentaire    = request.data.get('commentaire', '')
        choix_valides  = ['todo', 'en_cours', 'realise', 'verifie', 'clos', 'annule']

        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)

        import datetime
        plan_action.statut = nouveau_statut
        if nouveau_statut == 'realise':
            plan_action.date_realisation = datetime.date.today()
            if commentaire:
                plan_action.commentaire_realisation = commentaire
            # Notifier le vérificateur
            if plan_action.verificateur and plan_action.verificateur.email:
                try:
                    send_mail(
                        subject=f'[ERP] Action à vérifier : {plan_action.reference}',
                        message=f"""Bonjour {plan_action.verificateur.first_name},

L'action {plan_action.reference} — {plan_action.titre} a été réalisée et est en attente de votre vérification.

Connectez-vous sur rgbsetup.fr pour vérifier.

Cordialement,
Le système ERP Qualité""",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[plan_action.verificateur.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass
        elif nouveau_statut == 'verifie':
            plan_action.date_verification = datetime.date.today()
            if commentaire:
                plan_action.commentaire_verification = commentaire

        plan_action.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})

    @action(detail=False, methods=['get'], url_path='kanban')
    def kanban(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        data = serializer.data
        return Response({
            'todo':     [a for a in data if a['statut'] == 'todo'],
            'en_cours': [a for a in data if a['statut'] == 'en_cours'],
            'realise':  [a for a in data if a['statut'] == 'realise'],
            'verifie':  [a for a in data if a['statut'] == 'verifie'],
            'clos':     [a for a in data if a['statut'] == 'clos'],
        })
        
        
class CommentaireFNCViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = CommentaireFNCSerializer
    filterset_fields   = ['fnc', 'type_comment']

    def get_queryset(self):
        profil = getattr(self.request.user, 'profil', None)
        qs = CommentaireFNC.objects.select_related('fnc', 'auteur')
        if profil:
            qs = qs.filter(fnc__entreprise_tenant=profil.entreprise)
        return qs

    def perform_create(self, serializer):
        serializer.save(auteur=self.request.user)


class PieceJointeFNCViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = PieceJointeFNCSerializer
    filterset_fields   = ['fnc', 'type_fichier']
    parser_classes     = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        profil = getattr(self.request.user, 'profil', None)
        qs = PieceJointeFNC.objects.select_related('fnc', 'uploaded_by')
        if profil:
            qs = qs.filter(fnc__entreprise_tenant=profil.entreprise)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            uploaded_by = self.request.user,
            taille      = self.request.FILES.get('fichier').size if self.request.FILES.get('fichier') else 0,
        )



class PieceJointeAnalyse5MViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = PieceJointeAnalyse5MSerializer
    filterset_fields   = ['analyse', 'type_fichier']
    filter_backends    = [DjangoFilterBackend]
    parser_classes     = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        profil     = getattr(self.request.user, 'profil', None)
        analyse_id = self.request.query_params.get('analyse')
        qs = PieceJointeAnalyse5M.objects.select_related('analyse', 'uploaded_by')
        if profil:
            qs = qs.filter(analyse__entreprise=profil.entreprise)
        if analyse_id:
            qs = qs.filter(analyse_id=analyse_id)
        return qs
    
    

class PieceJointeActionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = PieceJointeActionSerializer
    filterset_fields   = ['action', 'type_fichier']
    filter_backends    = [DjangoFilterBackend]
    parser_classes     = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        profil = getattr(self.request.user, 'profil', None)
        qs = PieceJointeAction.objects.select_related('action', 'uploaded_by')
        if profil:
            qs = qs.filter(action__entreprise=profil.entreprise)
        return qs
        
        
class ParametresEntrepriseViewSet(viewsets.ViewSet):
    """
    Paramètres QMS d'une entreprise (plus un singleton global — scopé sur
    request.user.profil.entreprise). Le numéro d'aperçu (`preview_numero`)
    est calculé pour un site précis : celui passé en `?site=<id>` si valide,
    sinon le site principal (ou premier site) de l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def _site_pour_apercu(self, request):
        from tenants.models import Site
        profil  = request.user.profil
        site_id = request.query_params.get('site') or request.data.get('site')
        if site_id:
            site = Site.objects.filter(pk=site_id, entreprise=profil.entreprise).first()
            if site:
                return site
        return (profil.sites_autorises.filter(est_principal=True).first()
                or profil.sites_autorises.first()
                or Site.objects.filter(entreprise=profil.entreprise, est_principal=True).first())

    def list(self, request):
        """GET /api/qms/parametres/?site=<id optionnel>"""
        obj  = ParametresEntreprise.get_pour_entreprise(request.user.profil.entreprise)
        site = self._site_pour_apercu(request)
        serializer = ParametresEntrepriseSerializer(obj, context={'request': request, 'site_preview': site})
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """PATCH /api/qms/parametres/1/"""
        verifier_admin_groupe_qms(request)
        obj  = ParametresEntreprise.get_pour_entreprise(request.user.profil.entreprise)
        site = self._site_pour_apercu(request)
        serializer = ParametresEntrepriseSerializer(
            obj, data=request.data, partial=True, context={'request': request, 'site_preview': site}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def update(self, request, pk=None):
        """PUT /api/qms/parametres/1/"""
        return self.partial_update(request, pk)

    @action(detail=False, methods=['post'], url_path='reset-compteur')
    def reset_compteur(self, request):
        """Remet à 1 le compteur d'un site (site_id dans le body, sinon le site d'aperçu par défaut)."""
        from tenants.models import Site
        profil = request.user.profil

        if not (profil.est_admin_groupe or profil.est_admin_site):
            return Response({'erreur': "Seul un administrateur peut réinitialiser un compteur."}, status=403)

        site = self._site_pour_apercu(request)
        if not site:
            return Response({'erreur': 'Aucun site à réinitialiser'}, status=400)

        if not profil.est_admin_groupe and not profil.sites_autorises.filter(pk=site.pk).exists():
            return Response({'erreur': "Vous ne pouvez réinitialiser que le compteur de vos propres sites."}, status=403)

        site.compteur_fnc_actuel = 1
        site.save(update_fields=['compteur_fnc_actuel'])

        obj = ParametresEntreprise.get_pour_entreprise(profil.entreprise)
        return Response({
            'message': f'Compteur de "{site.nom}" remis à 1',
            'preview': site.preview_numero_fnc(obj),
        })

    @action(detail=False, methods=['post'], url_path='upload-logo')
    def upload_logo(self, request):
        verifier_admin_groupe_qms(request)
        obj     = ParametresEntreprise.get_pour_entreprise(request.user.profil.entreprise)
        fichier = request.FILES.get('logo')
        if not fichier:
            return Response({'erreur': 'Fichier obligatoire'}, status=400)
        obj.logo = fichier
        obj.save()
        serializer = ParametresEntrepriseSerializer(obj, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='supprimer-logo')
    def supprimer_logo(self, request):
        verifier_admin_groupe_qms(request)
        obj      = ParametresEntreprise.get_pour_entreprise(request.user.profil.entreprise)
        obj.logo = None
        obj.save()
        return Response({'message': 'Logo supprimé'})
    
class SectionFNCViewSet(viewsets.ModelViewSet):
    """
    Sections du formulaire FNC — structure partagée par toute l'entreprise.
    Lecture ouverte à tous (nécessaire pour afficher/remplir les formulaires),
    gestion (créer/modifier/supprimer/activer/réordonner) réservée à l'Admin
    Groupe, puisqu'une modification ici change la structure des FNC sur
    tous les sites à la fois.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = SectionFNCSerializer
    pagination_class   = None
    ordering           = ['ordre', 'nom']

    def get_queryset(self):
        return SectionFNC.objects.all()

    def perform_create(self, serializer):
        verifier_admin_groupe_qms(self.request)
        import re
        nom  = serializer.validated_data.get('nom', '')
        code = serializer.validated_data.get('code', '')
        if not code:
            code = re.sub(r'[^a-z0-9]+', '_', nom.lower().strip()).strip('_')
            base_code = code
            counter   = 1
            while SectionFNC.objects.filter(code=code).exists():
                code = f"{base_code}_{counter}"
                counter += 1
        serializer.save(code=code)

    def perform_update(self, serializer):
        verifier_admin_groupe_qms(self.request)
        serializer.save()

    @action(detail=False, methods=['post'], url_path='reordonner')
    def reordonner(self, request):
        verifier_admin_groupe_qms(request)
        ids = request.data.get('ids', [])
        for i, section_id in enumerate(ids):
            SectionFNC.objects.filter(id=section_id).update(ordre=i)
        return Response({'message': 'Ordre mis à jour'})
    
    @action(detail=False, methods=['get'], url_path='structure-export')
    def structure_export(self, request):
        """Renvoie toutes les sections actives avec leurs champs (fixes + custom), triés."""
        sections = SectionFNC.objects.filter(actif=True).order_by('ordre', 'nom')
        serializer = SectionStructureSerializer(sections, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='toggle-actif')
    def toggle_actif(self, request, pk=None):
        verifier_admin_groupe_qms(request)
        section = self.get_object()
        section.actif = not section.actif
        section.save()
        return Response({
            'message': f'Section {"activée" if section.actif else "désactivée"}',
            'actif': section.actif,
        })

    def destroy(self, request, *args, **kwargs):
        verifier_admin_groupe_qms(request)
        section = self.get_object()
        if section.est_systeme:
            return Response({'erreur': 'Cette section système ne peut pas être supprimée.'}, status=400)
        nb_champs = section.champs.count()
        if nb_champs > 0:
            confirmer = request.query_params.get('confirmer', 'false')
            if confirmer != 'true':
                return Response({
                    'erreur': f'Cette section contient {nb_champs} champ(s). Ajoutez ?confirmer=true pour confirmer (les champs seront aussi supprimés).',
                    'nb_champs': nb_champs,
                }, status=400)
        section.delete()
        return Response({'message': 'Section supprimée'}, status=204)
    
    @action(detail=False, methods=['get'], url_path='structure-formulaire')
    def structure_formulaire(self, request):
        """
        Retourne la structure du formulaire.
        Les champs est_obligatoire_systeme=True sont toujours inclus,
        même si le template les masque.
        """
        template_id = request.query_params.get('template')
        
        # Charger toutes les sections actives avec leurs champs
        sections = SectionFNC.objects.filter(actif=True).prefetch_related(
            Prefetch('champs', queryset=ChampPersonnalise.objects.filter(actif=True).order_by('ordre'))
        ).order_by('ordre')

        result = []
        for section in sections:
            champs = list(section.champs.all())

            # Appliquer le filtre template si présent
            if template_id:
                try:
                    template = TemplateFormulaireFNC.objects.get(id=template_id)
                    config = template.configuration or {}
                    section_config = config.get(section.code, {})

                    # Section masquée par le template ?
                    if section_config.get('actif') is False:
                        # Garder quand même les champs système de cette section
                        champs = [c for c in champs if c.est_obligatoire_systeme]
                    else:
                        # Filtrer les champs selon le template, mais garder les champs système
                        champs_config = section_config.get('champs', {})
                        champs = [
                            c for c in champs
                            if c.est_obligatoire_systeme or champs_config.get(c.cle, True) is not False
                        ]
                except TemplateFormulaireFNC.DoesNotExist:
                    pass

            if not champs:
                continue

            result.append({
                'id':     str(section.id),
                'nom':    section.nom,
                'code':   section.code,
                'champs': [self._serialiser_champ(c) for c in champs],
            })

        return Response(result)

    def _serialiser_champ(self, champ):
        return {
            'id':                      str(champ.id),
            'nom':                     champ.nom,
            'cle':                     champ.cle,
            'origine':                 champ.origine,
            'cle_modele':              champ.cle_modele,
            'type_champ':              champ.type_champ,
            'type_rendu':              champ.type_rendu,
            'largeur_rendu':           champ.largeur_rendu,
            'obligatoire':             champ.obligatoire,
            'est_obligatoire_systeme': champ.est_obligatoire_systeme,
            'choix_resolus':           champ.get_choix(),
        }


def verifier_admin_groupe_qms(request):
    """Lève une PermissionDenied si l'utilisateur n'est pas Administrateur Groupe."""
    from rest_framework.exceptions import PermissionDenied
    profil = getattr(request.user, 'profil', None)
    if not profil or not profil.est_admin_groupe:
        raise PermissionDenied("Seul un administrateur groupe peut gérer les référentiels.")


class ReferentielViewSet(viewsets.ModelViewSet):
    """
    Référentiels QMS (Processus, Classifications, Origines, Statuts) —
    partagés par tous les sites de l'entreprise. La lecture reste ouverte
    à tout utilisateur connecté (nécessaire pour les listes déroulantes des
    formulaires FNC), mais la gestion (créer/modifier/supprimer/réordonner)
    est réservée à l'Administrateur Groupe : un changement ici impacte la
    cohérence du reporting sur tous les sites à la fois.
    """
    permission_classes = [IsAuthenticated]
    pagination_class   = None
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['nom', 'code']

    def perform_create(self, serializer):
        verifier_admin_groupe_qms(self.request)
        import re
        nom  = serializer.validated_data.get('nom', '')
        code = serializer.validated_data.get('code', '')
        if not code:
            code = re.sub(r'[^a-z0-9]+', '_', nom.lower().strip()).strip('_')
            base = code
            counter = 1
            while self.get_queryset().model.objects.filter(code=code).exists():
                code = f"{base}_{counter}"
                counter += 1
        serializer.save(code=code)

    def perform_update(self, serializer):
        verifier_admin_groupe_qms(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        verifier_admin_groupe_qms(self.request)
        instance.delete()

    @action(detail=True, methods=['post'], url_path='toggle-actif')
    def toggle_actif(self, request, pk=None):
        verifier_admin_groupe_qms(request)
        obj = self.get_object()
        obj.actif = not obj.actif
        obj.save()
        return Response({'actif': obj.actif})

    @action(detail=False, methods=['post'], url_path='reordonner')
    def reordonner(self, request):
        verifier_admin_groupe_qms(request)
        ids = request.data.get('ids', [])
        for i, obj_id in enumerate(ids):
            self.get_queryset().model.objects.filter(id=obj_id).update(ordre=i)
        return Response({'message': 'Ordre mis à jour'})


class ServiceProcessusViewSet(ReferentielViewSet):
    serializer_class = ServiceProcessusSerializer
    def get_queryset(self): return ServiceProcessus.objects.all()

class ClassificationFNCViewSet(ReferentielViewSet):
    serializer_class = ClassificationFNCSerializer
    def get_queryset(self): return ClassificationFNC.objects.all()

class OrigineEcartViewSet(ReferentielViewSet):
    serializer_class = OrigineEcartSerializer
    def get_queryset(self): return OrigineEcart.objects.all()

class StatutFNCViewSet(ReferentielViewSet):
    serializer_class = StatutFNCSerializer
    def get_queryset(self): return StatutFNC.objects.all()
    
    
    
class ChampPersonnaliseViewSet(viewsets.ModelViewSet):
    """
    Champs personnalisés du formulaire FNC — même logique que SectionFNCViewSet :
    lecture ouverte à tous, gestion réservée à l'Admin Groupe.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = ChampPersonnaliseSerializer
    pagination_class   = None
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['actif', 'section', 'type_champ']
    search_fields      = ['nom', 'cle']
    ordering           = ['section__ordre', 'ordre', 'nom']

    def get_queryset(self):
        return ChampPersonnalise.objects.all()

    def perform_create(self, serializer):
        verifier_admin_groupe_qms(self.request)
        # Générer la clé automatiquement depuis le nom si non fournie
        import re
        nom = serializer.validated_data.get('nom', '')
        cle = serializer.validated_data.get('cle', '')
        if not cle:
            cle = re.sub(r'[^a-z0-9]+', '_', nom.lower().strip()).strip('_')
            # Assurer l'unicité
            base_cle = cle
            counter  = 1
            while ChampPersonnalise.objects.filter(cle=cle).exists():
                cle = f"{base_cle}_{counter}"
                counter += 1
        serializer.save(cle=cle)

    def perform_update(self, serializer):
        verifier_admin_groupe_qms(self.request)
        serializer.save()

    @action(detail=True, methods=['post'], url_path='toggle-actif')
    def toggle_actif(self, request, pk=None):
        verifier_admin_groupe_qms(request)
        champ       = self.get_object()
        champ.actif = not champ.actif
        champ.save()
        return Response({
            'message': f'Champ {"activé" if champ.actif else "désactivé"}',
            'actif':   champ.actif,
        })

    @action(detail=False, methods=['post'], url_path='reordonner')
    def reordonner(self, request):
        """Reçoit une liste d'IDs dans l'ordre souhaité."""
        verifier_admin_groupe_qms(request)
        ids = request.data.get('ids', [])
        for i, champ_id in enumerate(ids):
            ChampPersonnalise.objects.filter(id=champ_id).update(ordre=i)
        return Response({'message': 'Ordre mis à jour'})

    def destroy(self, request, *args, **kwargs):
        verifier_admin_groupe_qms(request)
        champ = self.get_object()
        nb_valeurs = champ.valeurs.count()
        if nb_valeurs > 0:
            # Vérifier si l'utilisateur confirme la suppression
            confirmer = request.query_params.get('confirmer', 'false')
            if confirmer != 'true':
                return Response({
                    'erreur': f'Ce champ a {nb_valeurs} valeur(s) enregistrée(s). Ajoutez ?confirmer=true pour confirmer la suppression.',
                    'nb_valeurs': nb_valeurs,
                }, status=400)
        champ.delete()
        return Response({'message': 'Champ supprimé'}, status=204)


class ValeurChampFNCViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = ValeurChampFNCSerializer
    filterset_fields   = ['fnc', 'champ']

    def get_queryset(self):
        return ValeurChampFNC.objects.select_related('fnc', 'champ')

    @action(detail=False, methods=['post'], url_path='sauvegarder-tout')
    def sauvegarder_tout(self, request):
        """Sauvegarde toutes les valeurs d'une FNC en une seule requête."""
        fnc_id  = request.data.get('fnc_id')
        valeurs = request.data.get('valeurs', {})  # {champ_id: valeur}

        if not fnc_id:
            return Response({'erreur': 'fnc_id obligatoire'}, status=400)

        try:
            fnc = NonConformite.objects.get(id=fnc_id)
        except NonConformite.DoesNotExist:
            return Response({'erreur': 'FNC introuvable'}, status=404)

        resultats = []
        for champ_id, valeur in valeurs.items():
            try:
                champ = ChampPersonnalise.objects.get(id=champ_id)
                obj, created = ValeurChampFNC.objects.update_or_create(
                    fnc=fnc, champ=champ,
                    defaults={'valeur': str(valeur) if valeur is not None else ''}
                )
                resultats.append({
                    'champ_id':  str(champ.id),
                    'champ_nom': champ.nom,
                    'valeur':    obj.valeur,
                    'created':   created,
                })
            except ChampPersonnalise.DoesNotExist:
                continue

        return Response({
            'message':  f'{len(resultats)} valeur(s) sauvegardée(s)',
            'resultats': resultats,
        })
        
class TemplateExportFNCViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = TemplateExportFNCSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['format']
    search_fields      = ['nom', 'description']

    def get_queryset(self):
        # Chaque utilisateur voit uniquement ses templates
        return TemplateExportFNC.objects.filter(
            utilisateur=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        template = self.get_object()
        template.is_default = True
        template.save()
        return Response({'message': f'"{template.nom}" défini par défaut'})

    @action(detail=False, methods=['get'], url_path='default')
    def get_default(self, request):
        """Retourne le template par défaut de l'utilisateur."""
        template = TemplateExportFNC.objects.filter(
            utilisateur=request.user,
            is_default=True
        ).first()
        if not template:
            return Response(None)
        serializer = TemplateExportFNCSerializer(template)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='dupliquer')
    def dupliquer(self, request, pk=None):
        template = self.get_object()
        nouveau  = TemplateExportFNC.objects.create(
            nom           = f"{template.nom} (copie)",
            description   = template.description,
            format        = template.format,
            configuration = template.configuration,
            utilisateur   = request.user,
            is_default    = False,
        )
        serializer = TemplateExportFNCSerializer(nouveau)
        return Response(serializer.data)
    
class TemplateFormulaireFNCViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = TemplateFormulaireFNCSerializer
    pagination_class   = None
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['nom', 'description']
    ordering           = ['ordre', 'nom']

    def get_queryset(self):
        # Les templates sont partagés par toute l'entreprise
        profil = getattr(self.request.user, 'profil', None)
        if profil:
            # Retourner les templates de tous les users de la même entreprise
            users_entreprise = profil.entreprise.utilisateurs.values_list('user_id', flat=True)
            return TemplateFormulaireFNC.objects.filter(
                utilisateur_id__in=users_entreprise
            )
        return TemplateFormulaireFNC.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        template = self.get_object()
        template.is_default = True
        template.save()
        return Response({'message': f'"{template.nom}" défini par défaut'})

    @action(detail=False, methods=['get'], url_path='default')
    def get_default(self, request):
        template = TemplateFormulaireFNC.objects.filter(
            utilisateur=request.user, is_default=True
        ).first()
        if not template:
            return Response(None)
        serializer = TemplateFormulaireFNCSerializer(template)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='dupliquer')
    def dupliquer(self, request, pk=None):
        template = self.get_object()
        nouveau  = TemplateFormulaireFNC.objects.create(
            nom           = f"{template.nom} (copie)",
            description   = template.description,
            configuration = template.configuration,
            utilisateur   = request.user,
            is_default    = False,
        )
        serializer = TemplateFormulaireFNCSerializer(nouveau)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='reordonner')
    def reordonner(self, request):
        ids = request.data.get('ids', [])
        for i, template_id in enumerate(ids):
            TemplateFormulaireFNC.objects.filter(id=template_id).update(ordre=i)
        return Response({'message': 'Ordre mis à jour'})


class OptionListeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = OptionListeSerializer
    pagination_class   = None
    filterset_fields   = ['type_liste', 'actif']
    ordering           = ['type_liste', 'ordre', 'libelle']

    def get_queryset(self):
        return OptionListe.objects.all()

    def perform_create(self, serializer):
        import re
        libelle = serializer.validated_data.get('libelle', '')
        valeur  = serializer.validated_data.get('valeur', '')
        type_liste = serializer.validated_data.get('type_liste')
        if not valeur:
            valeur = re.sub(r'[^a-z0-9]+', '_', libelle.lower().strip()).strip('_')
            base_valeur = valeur
            counter = 1
            while OptionListe.objects.filter(type_liste=type_liste, valeur=valeur).exists():
                valeur = f"{base_valeur}_{counter}"
                counter += 1
        serializer.save(valeur=valeur)

    @action(detail=False, methods=['post'], url_path='reordonner')
    def reordonner(self, request):
        ids = request.data.get('ids', [])
        for i, option_id in enumerate(ids):
            OptionListe.objects.filter(id=option_id).update(ordre=i)
        return Response({'message': 'Ordre mis à jour'})

    @action(detail=True, methods=['post'], url_path='toggle-actif')
    def toggle_actif(self, request, pk=None):
        option = self.get_object()
        option.actif = not option.actif
        option.save()
        return Response({
            'message': f'Option {"activée" if option.actif else "désactivée"}',
            'actif': option.actif,
        })


class ConstatViewSet(TenantSiteFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = ConstatListSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'gravite', 'template']
    search_fields      = ['numero', 'description', 'lieu']
    ordering           = ['-date_creation']
    tenant_field       = 'entreprise'
    CHAMP_ENTREPRISE = 'entreprise'
    CHAMP_SITE       = 'site'  # si Constat n'a pas de site, mets None

    def get_queryset(self):
        profil = getattr(self.request.user, 'profil', None)
        qs = Constat.objects.select_related(
            'observateur', 'valide_par', 'template', 'fnc', 'entreprise'
        )
        if profil:
            qs = qs.filter(entreprise=profil.entreprise)
        return qs

    def perform_create(self, serializer):
        profil     = getattr(self.request.user, 'profil', None)
        entreprise = profil.entreprise if profil else None
        serializer.save(
            observateur = self.request.user,
            entreprise  = entreprise,
        )

    @action(detail=True, methods=['post'], url_path='valider')
    def valider(self, request, pk=None):
        constat    = self.get_object()
        statut     = request.data.get('statut')  # 'valide' ou 'rejete'
        commentaire = request.data.get('commentaire', '')

        if statut not in ['valide', 'rejete']:
            return Response({'erreur': 'Statut invalide'}, status=400)

        constat.statut                 = statut
        constat.valide_par             = request.user
        constat.commentaire_validation = commentaire
        constat.date_validation        = timezone.now()
        constat.save()

        return Response({'message': f'Constat {statut}'})

    @action(detail=True, methods=['post'], url_path='convertir-fnc')
    def convertir_fnc(self, request, pk=None):
        constat = self.get_object()

        if constat.statut != 'valide':
            return Response({'erreur': 'Le constat doit être validé avant conversion'}, status=400)

        if constat.fnc:
            return Response({'erreur': 'Ce constat a déjà une FNC associée'}, status=400)

        profil     = getattr(request.user, 'profil', None)
        entreprise = profil.entreprise if profil else None

        # Créer la FNC depuis le constat
        fnc = NonConformite.objects.create(
            libelle          = constat.description[:200],
            description      = constat.description,
            gravite          = constat.gravite,
            redacteur        = request.user,
            entreprise_tenant = entreprise,
        )

        constat.fnc    = fnc
        constat.statut = 'converti'
        constat.save()

        return Response({
            'message':  f'FNC {fnc.numero} créée depuis le constat {constat.numero}',
            'fnc_id':   str(fnc.id),
            'fnc_numero': fnc.numero,
        })

    @action(detail=False, methods=['get'], url_path='mes-constats')
    def mes_constats(self, request):
        constats = self.get_queryset().filter(observateur=request.user)
        serializer = self.get_serializer(constats, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        qs = self.get_queryset()
        return Response({
            'total':     qs.count(),
            'ouverts':   qs.filter(statut='ouvert').count(),
            'valides':   qs.filter(statut='valide').count(),
            'rejetes':   qs.filter(statut='rejete').count(),
            'convertis': qs.filter(statut='converti').count(),
        })