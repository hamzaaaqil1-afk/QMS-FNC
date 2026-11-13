from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'fournisseurs',       views.FournisseurViewSet,          basename='fournisseurs')
router.register(r'evaluations',        views.EvaluationFournisseurViewSet, basename='evaluations')
router.register(r'demandes',           views.DemandeAchatViewSet,          basename='demandes')
router.register(r'lignes-demandes',    views.LigneDemandeAchatViewSet,     basename='lignes-demandes')
router.register(r'commandes',          views.CommandeAchatViewSet,         basename='commandes')
router.register(r'lignes-commandes',   views.LigneCommandeAchatViewSet,    basename='lignes-commandes')
router.register(r'receptions',         views.BonReceptionViewSet,          basename='receptions')
router.register(r'lignes-receptions',  views.LigneBonReceptionViewSet,     basename='lignes-receptions')

urlpatterns = [
    path('', include(router.urls)),
]