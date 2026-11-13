from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ServiceProcessusViewSet, ClassificationFNCViewSet, OrigineEcartViewSet, StatutFNCViewSet , CommentaireFNCViewSet,PieceJointeAnalyse5MViewSet, PieceJointeActionViewSet,OptionListeViewSet,  PieceJointeFNCViewSet, SectionFNCViewSet,ParametresEntrepriseViewSet, ChampPersonnaliseViewSet, ValeurChampFNCViewSet,TemplateFormulaireFNCViewSet, TemplateExportFNCViewSet

router = DefaultRouter()

router.register(r'referentiel/processus',       ServiceProcessusViewSet,  basename='ref-processus')
router.register(r'referentiel/classifications',  ClassificationFNCViewSet, basename='ref-classifications')
router.register(r'referentiel/origines',         OrigineEcartViewSet,      basename='ref-origines')
router.register(r'referentiel/statuts',          StatutFNCViewSet,         basename='ref-statuts')
router.register(r'fnc',            views.NonConformiteViewSet,     basename='fnc')
router.register(r'actions',        views.ActionCorrectivelViewSet, basename='actions')
router.register(r'analyses-5m',    views.Analyse5MViewSet,         basename='analyses-5m')
router.register(r'pieces-jointes', views.PieceJointeFNCViewSet,    basename='pieces-jointes')
router.register(r'utilisateurs',   views.UserViewSet,              basename='utilisateurs')
router.register(r'capa', views.CAPAViewSet, basename='capa')
router.register(r'pieces-jointes-analyse5m', PieceJointeAnalyse5MViewSet, basename='pieces-jointes-analyse5m')
router.register(r'pieces-jointes-action',    PieceJointeActionViewSet,    basename='pieces-jointes-action')
router.register(r'audits',    views.AuditViewSet,          basename='audits')
router.register(r'templates-export', TemplateExportFNCViewSet, basename='templates-export')
router.register(r'checklist', views.LigneChecklistViewSet, basename='checklist')
router.register(r'ecarts',    views.EcartAuditViewSet,     basename='ecarts')
router.register(r'options-listes', OptionListeViewSet, basename='options-listes')
router.register(r'plan-actions', views.PlanActionViewSet, basename='plan-actions')
router.register(r'parametres', ParametresEntrepriseViewSet, basename='parametres')
router.register(r'templates-formulaire', TemplateFormulaireFNCViewSet, basename='templates-formulaire')
router.register(r'champs-custom', ChampPersonnaliseViewSet, basename='champs-custom')
router.register(r'valeurs-champs', ValeurChampFNCViewSet,   basename='valeurs-champs')
router.register(r'constats', views.ConstatViewSet, basename='constats')

router.register(r'commentaires-fnc',   CommentaireFNCViewSet,   basename='commentaires-fnc')
router.register(r'pieces-jointes-fnc', PieceJointeFNCViewSet,   basename='pieces-jointes-fnc')
router.register(r'sections-fnc', SectionFNCViewSet, basename='sections-fnc')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.dashboard_qms, name='dashboard-qms'),
]

