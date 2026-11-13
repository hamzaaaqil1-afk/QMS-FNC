from django.contrib import admin
from .models import Entreprise, ProfilUtilisateur

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'slug', 'plan', 'statut', 'date_creation']
    list_filter   = ['plan', 'statut']
    search_fields = ['nom', 'slug']

@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display  = ['user', 'entreprise', 'role', 'actif']
    list_filter   = ['role', 'actif', 'entreprise']