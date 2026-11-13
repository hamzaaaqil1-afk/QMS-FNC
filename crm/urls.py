from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clients',      views.ClientViewSet,      basename='clients')
router.register(r'contacts',     views.ContactViewSet,     basename='contacts')
router.register(r'opportunites', views.OpportuniteViewSet, basename='opportunites')
router.register(r'devis',        views.DevisViewSet,       basename='devis')
router.register(r'commandes',    views.CommandeClientViewSet, basename='commandes')
router.register(r'reclamations', views.ReclamationClientViewSet, basename='reclamations')
router.register(r'lignes-devis',    views.LigneDevisViewSet,    basename='lignes-devis')
router.register(r'lignes-commandes',views.LigneCommandeViewSet, basename='lignes-commandes')

urlpatterns = [
    path('', include(router.urls)),
]