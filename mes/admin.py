from django.contrib import admin
from .models import (PosteCharge, Article, GammeStandard, OperationStandard,
                     NomenclatureStandard, OrdreFabrication, OperationOF,
                     LigneNomenclatureOF, PointageProduction, ArretMachine)

@admin.register(PosteCharge)
class PosteChargeAdmin(admin.ModelAdmin):
    list_display  = ['code', 'libelle', 'type_poste', 'taux_horaire', 'actif']
    list_filter   = ['type_poste', 'actif']

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'designation', 'type_article', 'stock_actuel']
    list_filter   = ['type_article', 'actif']
    search_fields = ['reference', 'designation']

@admin.register(GammeStandard)
class GammeAdmin(admin.ModelAdmin):
    list_display  = ['code', 'libelle', 'article', 'version', 'active']

@admin.register(OrdreFabrication)
class OFAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'designation', 'statut', 'priorite', 'quantite_lancee', 'date_fin_prevue']
    list_filter   = ['statut', 'priorite']
    search_fields = ['reference', 'designation']

@admin.register(OperationOF)
class OperationOFAdmin(admin.ModelAdmin):
    list_display  = ['of', 'numero', 'libelle', 'poste_charge', 'statut']
    list_filter   = ['statut']

@admin.register(PointageProduction)
class PointageAdmin(admin.ModelAdmin):
    list_display  = ['operation', 'operateur', 'type_pointage', 'timestamp', 'quantite_produite']
    list_filter   = ['type_pointage']

@admin.register(ArretMachine)
class ArretAdmin(admin.ModelAdmin):
    list_display  = ['poste_charge', 'type_arret', 'date_debut', 'duree_minutes']
    list_filter   = ['type_arret']