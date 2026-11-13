from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'postes',             views.PosteChargeViewSet,        basename='postes')
router.register(r'articles',           views.ArticleViewSet,            basename='articles')
router.register(r'gammes',             views.GammeStandardViewSet,      basename='gammes')
router.register(r'operations-std',     views.OperationStandardViewSet,  basename='operations-std')
router.register(r'nomenclatures-std',  views.NomenclatureStandardViewSet, basename='nomenclatures-std')
router.register(r'of',                 views.OFViewSet,                 basename='of')
router.register(r'operations-of',      views.OperationOFViewSet,        basename='operations-of')
router.register(r'nomenclature-of',    views.LigneNomenclatureOFViewSet, basename='nomenclature-of')
router.register(r'pointages',          views.PointageProductionViewSet, basename='pointages')
router.register(r'arrets',             views.ArretMachineViewSet,       basename='arrets')

urlpatterns = [
    path('', include(router.urls)),
]