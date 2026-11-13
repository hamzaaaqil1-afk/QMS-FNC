from django.contrib import admin
from .models import NonConformite, ActionCorrective, Analyse5M, PieceJointeFNC
from .models import NonConformite, ActionCorrective, Analyse5M, PieceJointeFNC, CAPA
from .models import NonConformite, ActionCorrective, Analyse5M, PieceJointeFNC, CAPA, Audit, LigneChecklist, EcartAudit

@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'titre', 'type_audit', 'statut', 'date_prevue']
    list_filter   = ['statut', 'type_audit']
    search_fields = ['reference', 'titre']

@admin.register(CAPA)
class CAPAAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'titre', 'type_capa', 'statut', 'date_echeance']
    list_filter   = ['statut', 'type_capa']
    search_fields = ['reference', 'titre']

@admin.register(NonConformite)
class NonConformiteAdmin(admin.ModelAdmin):
    list_display  = ['numero', 'libelle', 'gravite', 'statut_ref', 'processus_ref', 'client', 'created_at']
    list_filter   = ['statut_ref', 'gravite', 'processus_ref', 'type_nc']
    search_fields = ['numero', 'libelle', 'description', 'client']
    ordering      = ['-created_at']


@admin.register(ActionCorrective)
class ActionCorrectivelAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'fnc', 'type_action', 'processus_ref', 'responsable', 'statut', 'date_echeance']
    list_filter   = ['statut', 'type_action', 'processus_ref']
    search_fields = ['reference', 'description']


@admin.register(Analyse5M)
class Analyse5MAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'fnc', 'categorie', 'processus_responsable', 'statut']
    list_filter   = ['categorie', 'statut']


@admin.register(PieceJointeFNC)
class PieceJointeFNCAdmin(admin.ModelAdmin):
    list_display = ['nom_fichier', 'fnc', 'uploaded_at']