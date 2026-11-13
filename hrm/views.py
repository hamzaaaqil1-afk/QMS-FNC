from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Employe, Competence, EmployeCompetence, Pointage, JourneeCalculee, DemandeConge, Formation
from .serializers import (
    EmployeListSerializer, EmployeDetailSerializer,
    CompetenceSerializer, EmployeCompetenceSerializer,
    PointageSerializer, JourneeCalculeeSerializer,
    DemandeCongeSerializer, FormationSerializer,
)
import datetime


class EmployeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'categorie', 'equipe', 'type_contrat', 'departement']
    search_fields      = ['nom', 'prenom', 'matricule', 'poste', 'badge_rfid']
    ordering           = ['nom', 'prenom']

    def get_queryset(self):
        return Employe.objects.select_related('manager', 'user').prefetch_related('competences')

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeListSerializer
        return EmployeDetailSerializer

    @action(detail=False, methods=['get'], url_path='presents')
    def presents(self, request):
        today = datetime.date.today()
        # Employes ayant une entree aujourd'hui sans sortie
        from django.db.models import Exists, OuterRef
        entrees = Pointage.objects.filter(
            employe=OuterRef('pk'),
            timestamp__date=today,
            type_pointage='entree',
            valide=True,
        )
        sorties = Pointage.objects.filter(
            employe=OuterRef('pk'),
            timestamp__date=today,
            type_pointage='sortie',
            valide=True,
        )
        employes_presents = Employe.objects.filter(
            Exists(entrees)
        ).exclude(Exists(sorties))
        serializer = EmployeListSerializer(employes_presents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        today = datetime.date.today()
        employes = Employe.objects.all()

        # Habilitations expirant dans 60 jours
        date_alerte = today + datetime.timedelta(days=60)
        habilitations_alertes = EmployeCompetence.objects.filter(
            date_expiration__lte=date_alerte,
            date_expiration__gte=today,
        ).count()
        habilitations_expirees = EmployeCompetence.objects.filter(
            date_expiration__lt=today,
        ).count()

        # Periodes essai se terminant dans 30 jours
        date_essai = today + datetime.timedelta(days=30)
        periodes_essai = employes.filter(
            date_fin_periode_essai__gte=today,
            date_fin_periode_essai__lte=date_essai,
        ).count()

        # Conges en cours
        conges_en_cours = DemandeConge.objects.filter(
            statut='approuve',
            date_debut__lte=today,
            date_fin__gte=today,
        ).count()

        return Response({
            'total_employes':        employes.count(),
            'actifs':                employes.filter(statut='actif').count(),
            'en_conge':              employes.filter(statut='conge').count(),
            'en_maladie':            employes.filter(statut='maladie').count(),
            'bureau':                employes.filter(categorie='bureau').count(),
            'atelier':               employes.filter(categorie='atelier').count(),
            'habilitations_alertes': habilitations_alertes,
            'habilitations_expirees':habilitations_expirees,
            'periodes_essai_fin':    periodes_essai,
            'conges_en_cours':       conges_en_cours,
            'conges_attente':        DemandeConge.objects.filter(statut='en_attente').count(),
        })


class CompetenceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = CompetenceSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['type_competence', 'obligatoire']
    search_fields      = ['nom', 'description']

    def get_queryset(self):
        return Competence.objects.all()


class PointageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = PointageSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['employe', 'type_pointage', 'source', 'valide']
    ordering           = ['-timestamp']

    def get_queryset(self):
        return Pointage.objects.select_related('employe', 'saisi_par')

    @action(detail=False, methods=['post'], url_path='badge')
    def badge(self, request):
        badge_rfid = request.data.get('badge_rfid')
        if not badge_rfid:
            return Response({'erreur': 'Badge RFID requis'}, status=400)
        try:
            employe = Employe.objects.get(badge_rfid=badge_rfid, statut='actif')
        except Employe.DoesNotExist:
            return Response({'erreur': 'Badge non reconnu'}, status=404)

        # Determiner entree ou sortie
        today = datetime.date.today()
        dernier_pointage = Pointage.objects.filter(
            employe=employe,
            timestamp__date=today,
            valide=True,
        ).order_by('-timestamp').first()

        if dernier_pointage and dernier_pointage.type_pointage == 'entree':
            type_pointage = 'sortie'
        else:
            type_pointage = 'entree'

        pointage = Pointage.objects.create(
            employe=employe,
            type_pointage=type_pointage,
            timestamp=timezone.now(),
            source='rfid',
        )

        return Response({
            'employe':       employe.nom_complet,
            'matricule':     employe.matricule,
            'type_pointage': type_pointage,
            'timestamp':     pointage.timestamp,
            'message':       f"{'Entrée' if type_pointage == 'entree' else 'Sortie'} enregistrée pour {employe.nom_complet}",
        })


class JourneeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = JourneeCalculeeSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['employe', 'statut', 'date']
    ordering           = ['-date']

    def get_queryset(self):
        return JourneeCalculee.objects.select_related('employe', 'valide_par')


class DemandeCongeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = DemandeCongeSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'type_conge', 'employe']
    search_fields      = ['reference', 'employe__nom', 'employe__prenom']
    ordering           = ['-created_at']

    def get_queryset(self):
        return DemandeConge.objects.select_related('employe', 'valide_par')

    @action(detail=True, methods=['post'], url_path='valider')
    def valider(self, request, pk=None):
        conge  = self.get_object()
        statut = request.data.get('statut')
        if statut not in ['approuve', 'refuse']:
            return Response({'erreur': 'Statut invalide'}, status=400)
        conge.statut                 = statut
        conge.valide_par             = request.user
        conge.date_validation        = timezone.now()
        conge.commentaire_manager    = request.data.get('commentaire', '')
        conge.save()

        # Si approuve -> deduire solde
        if statut == 'approuve':
            if conge.type_conge == 'cp':
                conge.employe.solde_cp = max(0, float(conge.employe.solde_cp) - float(conge.nb_jours))
                conge.employe.save()
            elif conge.type_conge == 'rtt':
                conge.employe.solde_rtt = max(0, float(conge.employe.solde_rtt) - float(conge.nb_jours))
                conge.employe.save()

        return Response({'message': f'Congé {statut}'})


class FormationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = FormationSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'type_formation']
    search_fields      = ['reference', 'titre', 'organisme']
    ordering           = ['-date_prevue']

    def get_queryset(self):
        return Formation.objects.select_related('competence_acquise').prefetch_related('participants')