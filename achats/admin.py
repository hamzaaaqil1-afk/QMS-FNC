from django.contrib import admin
from .models import Fournisseur, EvaluationFournisseur, DemandeAchat, CommandeAchat, BonReception

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'raison_sociale', 'categorie', 'statut', 'note_globale']
    list_filter   = ['statut', 'categorie']
    search_fields = ['raison_sociale', 'reference']

@admin.register(DemandeAchat)
class DemandeAchatAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'titre', 'statut', 'urgence', 'date_demande']
    list_filter   = ['statut', 'urgence']

@admin.register(CommandeAchat)
class CommandeAchatAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'fournisseur', 'statut', 'date_commande']
    list_filter   = ['statut']

@admin.register(BonReception)
class BonReceptionAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'commande', 'statut', 'date_reception']
    list_filter   = ['statut']