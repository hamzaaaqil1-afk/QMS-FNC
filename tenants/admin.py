from django.contrib import admin
from .models import Entreprise, ProfilUtilisateur, Permission, RolePersonnalise, Site

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'slug', 'plan', 'statut', 'date_creation']
    list_filter   = ['plan', 'statut']
    search_fields = ['nom', 'slug']

@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display  = ['user', 'entreprise', 'role', 'actif']
    list_filter   = ['role', 'actif', 'entreprise']

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display  = ['code', 'module', 'libelle']
    list_filter   = ['module']
    search_fields = ['code', 'libelle']

@admin.register(RolePersonnalise)
class RolePersonnaliseAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'entreprise', 'site', 'est_admin', 'acces_tous_sites']
    list_filter   = ['entreprise', 'est_admin']
    search_fields = ['nom']

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'code', 'entreprise', 'est_principal', 'actif']
    list_filter   = ['entreprise', 'actif']
    search_fields = ['nom', 'code']