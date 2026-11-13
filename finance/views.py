from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q
import datetime
from .models import FactureClient, LigneFactureClient, FactureFournisseur, MouvementTresorerie
from .serializers import (
    FactureClientListSerializer, FactureClientDetailSerializer,
    LigneFactureClientSerializer, FactureFournisseurSerializer,
    MouvementTresorerieSerializer,
)


class FactureClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'client']
    search_fields      = ['reference', 'client__raison_sociale']
    ordering           = ['-created_at']

    def get_queryset(self):
        return FactureClient.objects.select_related('client', 'commande', 'createur').prefetch_related('lignes')

    def get_serializer_class(self):
        if self.action == 'list':
            return FactureClientListSerializer
        return FactureClientDetailSerializer

    def perform_create(self, serializer):
        serializer.save(createur=self.request.user)

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        facture        = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['brouillon', 'envoyee', 'payee', 'retard', 'annulee', 'partielle']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)

        facture.statut = nouveau_statut
        if nouveau_statut == 'payee':
            facture.date_paiement  = datetime.date.today()
            facture.montant_paye   = facture.montant_ttc
            facture.mode_paiement  = request.data.get('mode_paiement', '')
            facture.reference_paiement = request.data.get('reference_paiement', '')
            # Créer mouvement trésorerie automatique
            MouvementTresorerie.objects.create(
                type_mouvement  = 'encaissement',
                categorie       = 'vente',
                libelle         = f"Paiement facture {facture.reference} — {facture.client.raison_sociale}",
                montant         = facture.montant_ttc,
                date_mouvement  = datetime.date.today(),
                facture_client  = facture,
                saisi_par       = request.user,
            )
        facture.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        today    = datetime.date.today()
        factures = FactureClient.objects.all()
        ff       = FactureFournisseur.objects.all()
        mouvements = MouvementTresorerie.objects.all()

        ca_facture   = factures.exclude(statut='annulee').aggregate(s=Sum('montant_ttc'))['s'] or 0
        ca_encaisse  = factures.filter(statut='payee').aggregate(s=Sum('montant_ttc'))['s'] or 0
        en_retard_clients = factures.filter(statut__in=['envoyee', 'retard', 'partielle'], date_echeance__lt=today).count()

        depenses_fourn = ff.filter(statut='payee').aggregate(s=Sum('montant_ttc'))['s'] or 0
        ff_a_payer     = ff.filter(statut__in=['recue', 'validee']).aggregate(s=Sum('montant_ttc'))['s'] or 0

        encaissements = mouvements.filter(type_mouvement='encaissement').aggregate(s=Sum('montant'))['s'] or 0
        decaissements = mouvements.filter(type_mouvement='decaissement').aggregate(s=Sum('montant'))['s'] or 0
        solde_tresorerie = float(encaissements) - float(decaissements)

        return Response({
            'ca_facture':          float(ca_facture),
            'ca_encaisse':         float(ca_encaisse),
            'en_retard_clients':   en_retard_clients,
            'depenses_fourn':      float(depenses_fourn),
            'ff_a_payer':          float(ff_a_payer),
            'solde_tresorerie':    solde_tresorerie,
            'encaissements':       float(encaissements),
            'decaissements':       float(decaissements),
            'nb_factures_clients': factures.exclude(statut='annulee').count(),
            'nb_factures_fourn':   ff.exclude(statut='annulee').count(),
        })


class LigneFactureClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneFactureClientSerializer
    filterset_fields   = ['facture']

    def get_queryset(self):
        return LigneFactureClient.objects.select_related('facture')


class FactureFournisseurViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = FactureFournisseurSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'fournisseur']
    search_fields      = ['reference', 'reference_fournisseur', 'fournisseur__raison_sociale']
    ordering           = ['-created_at']

    def get_queryset(self):
        return FactureFournisseur.objects.select_related('fournisseur', 'commande_achat', 'validateur')

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        facture        = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['recue', 'validee', 'payee', 'contestee', 'annulee']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)

        facture.statut = nouveau_statut
        if nouveau_statut == 'validee':
            facture.validateur = request.user
        if nouveau_statut == 'payee':
            facture.date_paiement = datetime.date.today()
            facture.montant_paye  = facture.montant_ttc
            facture.mode_paiement = request.data.get('mode_paiement', '')
            # Créer mouvement trésorerie automatique
            MouvementTresorerie.objects.create(
                type_mouvement      = 'decaissement',
                categorie           = 'achat',
                libelle             = f"Paiement facture {facture.reference} — {facture.fournisseur.raison_sociale}",
                montant             = facture.montant_ttc,
                date_mouvement      = datetime.date.today(),
                facture_fournisseur = facture,
                saisi_par           = request.user,
            )
        if nouveau_statut == 'contestee':
            facture.motif_contestation = request.data.get('motif', '')
        facture.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})


class MouvementTresorerieViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = MouvementTresorerieSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['type_mouvement', 'categorie']
    search_fields      = ['reference', 'libelle']
    ordering           = ['-date_mouvement']

    def get_queryset(self):
        return MouvementTresorerie.objects.select_related('facture_client', 'facture_fournisseur', 'saisi_par')

    def perform_create(self, serializer):
        serializer.save(saisi_par=self.request.user)

    @action(detail=False, methods=['get'], url_path='solde')
    def solde(self, request):
        from django.db.models import Sum
        encaissements = MouvementTresorerie.objects.filter(type_mouvement='encaissement').aggregate(s=Sum('montant'))['s'] or 0
        decaissements = MouvementTresorerie.objects.filter(type_mouvement='decaissement').aggregate(s=Sum('montant'))['s'] or 0
        return Response({
            'encaissements': float(encaissements),
            'decaissements': float(decaissements),
            'solde':         float(encaissements) - float(decaissements),
        })