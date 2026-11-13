from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employes',    views.EmployeViewSet,    basename='employes')
router.register(r'competences', views.CompetenceViewSet, basename='competences')
router.register(r'pointages',   views.PointageViewSet,   basename='pointages')
router.register(r'journees',    views.JourneeViewSet,    basename='journees')
router.register(r'conges',      views.DemandeCongeViewSet, basename='conges')
router.register(r'formations',  views.FormationViewSet,  basename='formations')

urlpatterns = [
    path('', include(router.urls)),
]