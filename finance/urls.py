from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'factures-clients',      views.FactureClientViewSet,      basename='factures-clients')
router.register(r'lignes-factures',       views.LigneFactureClientViewSet, basename='lignes-factures')
router.register(r'factures-fournisseurs', views.FactureFournisseurViewSet,  basename='factures-fournisseurs')
router.register(r'tresorerie',            views.MouvementTresorerieViewSet, basename='tresorerie')

urlpatterns = [
    path('', include(router.urls)),
]   