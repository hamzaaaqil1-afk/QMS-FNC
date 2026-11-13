from django.contrib import admin
from .models import Client, Contact, Opportunite, Devis, LigneDevis, CommandeClient, LigneCommande, ReclamationClient

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'raison_sociale', 'segment', 'ville', 'actif']
    list_filter   = ['segment', 'actif', 'pays']
    search_fields = ['raison_sociale', 'reference', 'siret']

@admin.register(Opportunite)
class OpportuniteAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'titre', 'client', 'statut', 'valeur_estimee']
    list_filter   = ['statut']

@admin.register(Devis)
class DevisAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'client', 'statut', 'date_emission']
    list_filter   = ['statut']

@admin.register(CommandeClient)
class CommandeClientAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'client', 'statut', 'date_commande']
    list_filter   = ['statut']

@admin.register(ReclamationClient)
class ReclamationClientAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'client', 'type_reclamation', 'gravite', 'statut']
    list_filter   = ['statut', 'gravite']