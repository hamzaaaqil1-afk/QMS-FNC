from rest_framework import serializers
from .models import Risque


class RisqueListSerializer(serializers.ModelSerializer):
    responsable_nom  = serializers.SerializerMethodField()
    redacteur_nom    = serializers.SerializerMethodField()
    ipr              = serializers.ReadOnlyField()
    ipr_residuel     = serializers.ReadOnlyField()
    niveau_criticite = serializers.ReadOnlyField()
    fnc_numero       = serializers.CharField(source='fnc.numero',    read_only=True)
    capa_reference   = serializers.CharField(source='capa.reference', read_only=True)
    audit_reference  = serializers.CharField(source='audit.reference', read_only=True)

    class Meta:
        model  = Risque
        fields = [
            'id', 'reference', 'titre', 'statut', 'categorie', 'processus',
            'gravite', 'occurrence', 'detectabilite', 'ipr', 'niveau_criticite',
            'gravite_residuelle', 'occurrence_residuelle', 'detectabilite_residuelle', 'ipr_residuel',
            'type_traitement', 'date_echeance',
            'responsable_nom', 'redacteur_nom',
            'fnc_numero', 'capa_reference', 'audit_reference',
            'created_at',
        ]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return f"{obj.responsable.first_name} {obj.responsable.last_name}".strip() or obj.responsable.username
        return ''

    def get_redacteur_nom(self, obj):
        if obj.redacteur:
            return f"{obj.redacteur.first_name} {obj.redacteur.last_name}".strip() or obj.redacteur.username
        return ''


class RisqueDetailSerializer(RisqueListSerializer):
    class Meta(RisqueListSerializer.Meta):
        fields = '__all__'