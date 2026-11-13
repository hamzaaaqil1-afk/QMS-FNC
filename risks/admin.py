from django.contrib import admin
from .models import Risque


@admin.register(Risque)
class RisqueAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'titre', 'categorie', 'statut', 'gravite', 'occurrence', 'detectabilite']
    list_filter   = ['statut', 'categorie', 'processus']
    search_fields = ['reference', 'titre']