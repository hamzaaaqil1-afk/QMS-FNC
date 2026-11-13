from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Risque
from .serializers import RisqueListSerializer, RisqueDetailSerializer


class RisqueViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['statut', 'categorie', 'processus', 'type_traitement']
    search_fields      = ['reference', 'titre', 'description']
    ordering           = ['-created_at']

    def get_queryset(self):
        return Risque.objects.select_related('responsable', 'redacteur', 'fnc', 'capa', 'audit')

    def get_serializer_class(self):
        if self.action == 'list':
            return RisqueListSerializer
        return RisqueDetailSerializer

    def perform_create(self, serializer):
        serializer.save(redacteur=self.request.user)

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        risque = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix_valides  = ['identifie', 'en_cours', 'traite', 'accepte', 'clos']
        if nouveau_statut not in choix_valides:
            return Response({'erreur': 'Statut invalide'}, status=400)
        risque.statut = nouveau_statut
        risque.save()
        return Response({'message': f'Statut mis à jour : {nouveau_statut}'})

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        risques = Risque.objects.all()
        return Response({
            'total':          risques.count(),
            'identifie':      risques.filter(statut='identifie').count(),
            'en_cours':       risques.filter(statut='en_cours').count(),
            'traite':         risques.filter(statut='traite').count(),
            'clos':           risques.filter(statut='clos').count(),
            'inacceptable':   sum(1 for r in risques if r.niveau_criticite == 'inacceptable'),
            'tolerable':      sum(1 for r in risques if r.niveau_criticite == 'tolerable'),
            'acceptable':     sum(1 for r in risques if r.niveau_criticite == 'acceptable'),
        })