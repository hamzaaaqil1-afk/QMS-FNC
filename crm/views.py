from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client, Contact, Opportunite, Devis, LigneDevis, CommandeClient, LigneCommande, ReclamationClient
from .serializers import (
    ClientListSerializer, ClientDetailSerializer,
    ContactSerializer, OpportuniteSerializer,
    DevisListSerializer, DevisDetailSerializer, LigneDevisSerializer,
    CommandeClientListSerializer, CommandeClientDetailSerializer, LigneCommandeSerializer,
    ReclamationClientSerializer,
)


class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['segment', 'actif', 'pays']
    search_fields      = ['raison_sociale', 'reference', 'siret', 'ville']
    ordering           = ['raison_sociale']

    def get_queryset(self):
        return Client.objects.prefetch_related('contacts', 'commandes', 'reclamations').select_related('commercial')

    def get_serializer_class(self):
        if self.action == 'list':
            return ClientListSerializer
        return ClientDetailSerializer


class ContactViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = ContactSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['client', 'principal']
    search_fields      = ['nom', 'prenom', 'email']

    def get_queryset(self):
        return Contact.objects.select_related('client')


class OpportuniteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = OpportuniteSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'client', 'commercial']
    search_fields      = ['reference', 'titre', 'description']
    ordering           = ['-created_at']

    def get_queryset(self):
        return Opportunite.objects.select_related('client', 'contact', 'commercial')

    def perform_create(self, serializer):
        serializer.save(commercial=self.request.user)

    @action(detail=False, methods=['get'], url_path='kanban')
    def kanban(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        data = serializer.data
        return Response({
            'prospect': [o for o in data if o['statut'] == 'prospect'],
            'qualifie': [o for o in data if o['statut'] == 'qualifie'],
            'devis':    [o for o in data if o['statut'] == 'devis'],
            'gagne':    [o for o in data if o['statut'] == 'gagne'],
            'perdu':    [o for o in data if o['statut'] == 'perdu'],
        })

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        opp = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['prospect', 'qualifie', 'devis', 'gagne', 'perdu']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)
        opp.statut = nouveau_statut
        if nouveau_statut == 'perdu':
            opp.raison_perte = request.data.get('raison_perte', '')
        opp.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})


class DevisViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'client']
    search_fields      = ['reference', 'client__raison_sociale']
    ordering           = ['-created_at']

    def get_queryset(self):
        return Devis.objects.select_related('client', 'commercial', 'contact').prefetch_related('lignes')

    def get_serializer_class(self):
        if self.action == 'list':
            return DevisListSerializer
        return DevisDetailSerializer

    def perform_create(self, serializer):
        serializer.save(commercial=self.request.user)

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        devis = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['brouillon', 'envoye', 'accepte', 'refuse', 'expire']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)
        devis.statut = nouveau_statut
        devis.save()
        # Si accepté → créer commande automatiquement
        if nouveau_statut == 'accepte':
            commande = CommandeClient.objects.create(
                client=devis.client,
                devis=devis,
                contact=devis.contact,
                commercial=devis.commercial,
            )
            for ligne in devis.lignes.all():
                LigneCommande.objects.create(
                    commande=commande,
                    designation=ligne.designation,
                    reference_article=ligne.reference_article,
                    quantite_commandee=ligne.quantite,
                    unite=ligne.unite,
                    prix_unitaire=ligne.prix_unitaire,
                    delai_livraison=ligne.delai_livraison,
                    ordre=ligne.ordre,
                )
            return Response({'message': 'Devis accepté — commande créée', 'commande_id': str(commande.id)})
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})


class LigneDevisViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneDevisSerializer
    filterset_fields   = ['devis']

    def get_queryset(self):
        return LigneDevis.objects.select_related('devis')


class CommandeClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'client']
    search_fields      = ['reference', 'reference_client', 'client__raison_sociale']
    ordering           = ['-created_at']

    def get_queryset(self):
        return CommandeClient.objects.select_related('client', 'commercial', 'contact').prefetch_related('lignes')

    def get_serializer_class(self):
        if self.action == 'list':
            return CommandeClientListSerializer
        return CommandeClientDetailSerializer

    def perform_create(self, serializer):
        serializer.save(commercial=self.request.user)

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        commande = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['recue', 'confirmee', 'en_production', 'livree', 'annulee', 'facturee']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)
        commande.statut = nouveau_statut
        if nouveau_statut == 'livree':
            import datetime
            commande.date_livraison_reelle = datetime.date.today()
        commande.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})


class ReclamationClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = ReclamationClientSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'type_reclamation', 'gravite', 'client']
    search_fields      = ['reference', 'description', 'client__raison_sociale']
    ordering           = ['-created_at']

    def get_queryset(self):
        return ReclamationClient.objects.select_related('client', 'commande', 'contact', 'fnc')

    def perform_create(self, serializer):
        reclamation = serializer.save()
        # Créer FNC automatiquement si gravité majeure ou critique
        if reclamation.gravite in ['majeure', 'critique']:
            from qms.models import NonConformite
            fnc = NonConformite.objects.create(
                libelle=f"Réclamation client — {reclamation.client.raison_sociale}",
                description=reclamation.description,
                type_nc='reclamation_client',
                origine_ecart='client',
                gravite='critique' if reclamation.gravite == 'critique' else 'majeur',
                client=reclamation.client.raison_sociale,
                reclamation_client=True,
                redacteur=self.request.user,
            )
            reclamation.fnc = fnc
            reclamation.save()


class LigneCommandeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = LigneCommandeSerializer
    filterset_fields   = ['commande']

    def get_queryset(self):
        return LigneCommande.objects.select_related('commande')