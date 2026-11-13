from django.contrib import admin
from .models import FactureClient, LigneFactureClient, FactureFournisseur, MouvementTresorerie

@admin.register(FactureClient)
class FactureClientAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'client', 'statut', 'montant_ttc', 'date_echeance']
    list_filter   = ['statut']
    search_fields = ['reference', 'client__raison_sociale']

@admin.register(FactureFournisseur)
class FactureFournisseurAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'fournisseur', 'statut', 'montant_ttc', 'date_echeance']
    list_filter   = ['statut']

@admin.register(MouvementTresorerie)
class MouvementTresorerieAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'libelle', 'type_mouvement', 'montant', 'date_mouvement']
    list_filter   = ['type_mouvement', 'categorie']