from django.contrib import admin
from .models import Employe, Competence, EmployeCompetence, Pointage, JourneeCalculee, DemandeConge, Formation

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display  = ['matricule', 'nom', 'prenom', 'poste', 'categorie', 'statut']
    list_filter   = ['statut', 'categorie', 'equipe', 'type_contrat']
    search_fields = ['nom', 'prenom', 'matricule']

@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'type_competence', 'duree_validite_mois', 'obligatoire']
    list_filter   = ['type_competence', 'obligatoire']

@admin.register(DemandeConge)
class DemandeCongeAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'employe', 'type_conge', 'date_debut', 'date_fin', 'statut']
    list_filter   = ['statut', 'type_conge']

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'titre', 'type_formation', 'statut', 'date_prevue']
    list_filter   = ['statut', 'type_formation']

@admin.register(Pointage)
class PointageAdmin(admin.ModelAdmin):
    list_display  = ['employe', 'type_pointage', 'timestamp', 'source']
    list_filter   = ['type_pointage', 'source']