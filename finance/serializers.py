from rest_framework import serializers
from .models import FactureClient, LigneFactureClient, FactureFournisseur, MouvementTresorerie


class LigneFactureClientSerializer(serializers.ModelSerializer):
    montant_ht = serializers.ReadOnlyField()

    class Meta:
        model  = LigneFactureClient
        fields = '__all__'


class FactureClientListSerializer(serializers.ModelSerializer):
    client_nom      = serializers.CharField(source='client.raison_sociale', read_only=True)
    createur_nom    = serializers.SerializerMethodField()
    montant_restant = serializers.ReadOnlyField()
    est_en_retard   = serializers.ReadOnlyField()

    class Meta:
        model  = FactureClient
        fields = [
            'id', 'reference', 'client', 'client_nom', 'statut',
            'date_emission', 'date_echeance', 'date_paiement',
            'montant_ht', 'montant_tva', 'montant_ttc',
            'montant_paye', 'montant_restant', 'est_en_retard',
            'createur_nom', 'created_at',
        ]

    def get_createur_nom(self, obj):
        if obj.createur:
            return f"{obj.createur.first_name} {obj.createur.last_name}".strip() or obj.createur.username
        return ''


class FactureClientDetailSerializer(FactureClientListSerializer):
    lignes = LigneFactureClientSerializer(many=True, read_only=True)

    class Meta(FactureClientListSerializer.Meta):
        fields = '__all__'


class FactureFournisseurSerializer(serializers.ModelSerializer):
    fournisseur_nom   = serializers.CharField(source='fournisseur.raison_sociale', read_only=True)
    commande_ref      = serializers.CharField(source='commande_achat.reference', read_only=True)
    est_en_retard     = serializers.ReadOnlyField()
    validateur_nom    = serializers.SerializerMethodField()

    class Meta:
        model  = FactureFournisseur
        fields = '__all__'

    def get_validateur_nom(self, obj):
        if obj.validateur:
            return f"{obj.validateur.first_name} {obj.validateur.last_name}".strip() or obj.validateur.username
        return ''


class MouvementTresorerieSerializer(serializers.ModelSerializer):
    facture_client_ref      = serializers.CharField(source='facture_client.reference', read_only=True)
    facture_fournisseur_ref = serializers.CharField(source='facture_fournisseur.reference', read_only=True)
    saisi_par_nom           = serializers.SerializerMethodField()

    class Meta:
        model  = MouvementTresorerie
        fields = '__all__'

    def get_saisi_par_nom(self, obj):
        if obj.saisi_par:
            return f"{obj.saisi_par.first_name} {obj.saisi_par.last_name}".strip() or obj.saisi_par.username
        return ''