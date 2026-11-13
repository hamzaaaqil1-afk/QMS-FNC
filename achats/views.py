from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import datetime
from .models import (Fournisseur, EvaluationFournisseur, DemandeAchat, LigneDemandeAchat,
                     CommandeAchat, LigneCommandeAchat, BonReception, LigneBonReception)
from .serializers import (
    FournisseurListSerializer, FournisseurDetailSerializer,
    EvaluationFournisseurSerializer, DemandeAchatSerializer,
    LigneDemandeAchatSerializer, CommandeAchatListSerializer,
    CommandeAchatDetailSerializer, LigneCommandeAchatSerializer,
    BonReceptionSerializer, LigneBonReceptionSerializer,
)


class FournisseurViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'categorie']
    search_fields      = ['raison_sociale', 'reference', 'siret', 'ville']
    ordering           = ['raison_sociale']

    def get_queryset(self):
        return Fournisseur.objects.prefetch_related('evaluations', 'commandes')

    def get_serializer_class(self):
        if self.action == 'list':
            return FournisseurListSerializer
        return FournisseurDetailSerializer

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        fournisseurs = Fournisseur.objects.filter(statut='actif')
        commandes    = CommandeAchat.objects.all()
        today        = datetime.date.today()
        return Response({
            'total_fournisseurs': fournisseurs.count(),
            'actifs':             fournisseurs.filter(statut='actif').count(),
            'blacklistes':        Fournisseur.objects.filter(statut='blacklist').count(),
            'commandes_en_cours': commandes.filter(statut__in=['envoyee', 'confirmee', 'partielle']).count(),
            'commandes_retard':   sum(1 for c in commandes if c.est_en_retard),
            'da_en_attente':      DemandeAchat.objects.filter(statut='en_attente').count(),
            'receptions_jour':    BonReception.objects.filter(date_reception=today).count(),
        })


class EvaluationFournisseurViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = EvaluationFournisseurSerializer
    filterset_fields   = ['fournisseur']

    def get_queryset(self):
        return EvaluationFournisseur.objects.select_related('fournisseur', 'evaluateur', 'commande')

    def perform_create(self, serializer):
        serializer.save(evaluateur=self.request.user)


class DemandeAchatViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = DemandeAchatSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'urgence', 'demandeur']
    search_fields      = ['reference', 'titre']
    ordering           = ['-created_at']

    def get_queryset(self):
        return DemandeAchat.objects.select_related(
            'demandeur', 'approbateur', 'fournisseur_suggere'
        ).prefetch_related('lignes')

    def perform_create(self, serializer):
        serializer.save(demandeur=self.request.user)

    @action(detail=True, methods=['post'], url_path='approuver')
    def approuver(self, request, pk=None):
        da     = self.get_object()
        statut = request.data.get('statut')
        if statut not in ['approuvee', 'refusee']:
            return Response({'erreur': 'Statut invalide'}, status=400)
        da.statut                    = statut
        da.approbateur               = request.user
        da.date_approbation          = datetime.date.today()
        da.commentaire_approbateur   = request.data.get('commentaire', '')
        da.save()
        return Response({'message': f'Demande {statut}'})

    @action(detail=True, methods=['post'], url_path='convertir-commande')
    def convertir_commande(self, request, pk=None):
        da = self.get_object()
        if da.statut != 'approuvee':
            return Response({'erreur': 'La DA doit être approuvée'}, status=400)

        fournisseur_id = request.data.get('fournisseur')
        if not fournisseur_id:
            return Response({'erreur': 'Fournisseur obligatoire'}, status=400)

        try:
            fournisseur = Fournisseur.objects.get(id=fournisseur_id)
        except Fournisseur.DoesNotExist:
            return Response({'erreur': 'Fournisseur introuvable'}, status=404)

        commande = CommandeAchat.objects.create(
            fournisseur=fournisseur,
            demande=da,
            acheteur=request.user,
            date_livraison_prevue=da.date_besoin,
        )
        for ligne in da.lignes.all():
            LigneCommandeAchat.objects.create(
                commande=commande,
                designation=ligne.designation,
                reference_article=ligne.reference_article,
                quantite_commandee=ligne.quantite,
                unite=ligne.unite,
                prix_unitaire=ligne.prix_unitaire_estime or 0,
                ordre=ligne.ordre,
            )
        da.statut = 'commandee'
        da.save()
        return Response({'message': 'Commande créée', 'commande_id': str(commande.id)})


class LigneDemandeAchatViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneDemandeAchatSerializer
    filterset_fields   = ['demande']

    def get_queryset(self):
        return LigneDemandeAchat.objects.select_related('demande')


class CommandeAchatViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'fournisseur']
    search_fields      = ['reference', 'reference_fournisseur', 'fournisseur__raison_sociale']
    ordering           = ['-created_at']

    def get_queryset(self):
        return CommandeAchat.objects.select_related(
            'fournisseur', 'acheteur', 'demande'
        ).prefetch_related('lignes')

    def get_serializer_class(self):
        if self.action == 'list':
            return CommandeAchatListSerializer
        return CommandeAchatDetailSerializer

    def perform_create(self, serializer):
        serializer.save(acheteur=self.request.user)

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        commande       = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['brouillon', 'envoyee', 'confirmee', 'partielle', 'recue', 'annulee', 'facturee']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)
        commande.statut = nouveau_statut
        if nouveau_statut == 'recue':
            commande.date_livraison_reelle = datetime.date.today()
        commande.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})


class LigneCommandeAchatViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneCommandeAchatSerializer
    filterset_fields   = ['commande']

    def get_queryset(self):
        return LigneCommandeAchat.objects.select_related('commande')


class BonReceptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = BonReceptionSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['statut', 'commande']
    ordering           = ['-date_reception']

    def get_queryset(self):
        return BonReception.objects.select_related(
            'commande', 'commande__fournisseur', 'receptionnaire', 'fnc'
        ).prefetch_related('lignes')

    def perform_create(self, serializer):
        bon = serializer.save(receptionnaire=self.request.user)

        # Vérifier si des lignes sont non conformes -> créer FNC auto
        lignes_nc = bon.lignes.filter(statut='non_conforme')
        if lignes_nc.exists():
            from qms.models import NonConformite
            descriptions = ', '.join([l.ligne_commande.designation for l in lignes_nc])
            fnc = NonConformite.objects.create(
                libelle        = f"Non-conformité réception {bon.reference}",
                description    = f"Articles non conformes à la réception : {descriptions}",
                type_nc        = 'reception',
                origine_ecart  = 'fournisseur',
                gravite        = 'majeur',
                fournisseur    = bon.commande.fournisseur.raison_sociale,
                redacteur      = self.request.user,
            )
            bon.fnc    = fnc
            bon.statut = 'refuse' if bon.lignes.filter(statut='conforme').count() == 0 else 'partiel'
            bon.save()

            # Mettre à jour statut commande
            bon.commande.statut = 'partielle'
            bon.commande.save()
        else:
            bon.statut = 'accepte'
            bon.save()
            # Mettre à jour quantités reçues sur les lignes commande
            for ligne_br in bon.lignes.all():
                lca = ligne_br.ligne_commande
                lca.quantite_recue = float(lca.quantite_recue) + float(ligne_br.quantite_recue)
                lca.save()
            # Vérifier si tout est reçu
            commande = bon.commande
            toutes_recues = all(
                float(l.quantite_recue) >= float(l.quantite_commandee)
                for l in commande.lignes.all()
            )
            commande.statut = 'recue' if toutes_recues else 'partielle'
            if toutes_recues:
                commande.date_livraison_reelle = datetime.date.today()
            commande.save()


class LigneBonReceptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneBonReceptionSerializer
    filterset_fields   = ['bon_reception']

    def get_queryset(self):
        return LigneBonReception.objects.select_related('bon_reception', 'ligne_commande')