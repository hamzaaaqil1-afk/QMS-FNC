from rest_framework import serializers
from .models import (PosteCharge, Article, GammeStandard, OperationStandard,
                     NomenclatureStandard, OrdreFabrication, OperationOF,
                     LigneNomenclatureOF, PointageProduction, ArretMachine)


class PosteChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PosteCharge
        fields = '__all__'


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Article
        fields = '__all__'


class OperationStandardSerializer(serializers.ModelSerializer):
    poste_libelle = serializers.CharField(source='poste_charge.libelle', read_only=True)

    class Meta:
        model  = OperationStandard
        fields = '__all__'


class GammeStandardSerializer(serializers.ModelSerializer):
    operations     = OperationStandardSerializer(many=True, read_only=True)
    article_ref    = serializers.CharField(source='article.reference', read_only=True)
    nb_operations  = serializers.SerializerMethodField()

    class Meta:
        model  = GammeStandard
        fields = '__all__'

    def get_nb_operations(self, obj):
        return obj.operations.count()


class NomenclatureStandardSerializer(serializers.ModelSerializer):
    composant_ref  = serializers.CharField(source='composant.reference', read_only=True)
    composant_nom  = serializers.CharField(source='composant.designation', read_only=True)

    class Meta:
        model  = NomenclatureStandard
        fields = '__all__'


class OperationOFSerializer(serializers.ModelSerializer):
    poste_libelle      = serializers.CharField(source='poste_charge.libelle', read_only=True)
    operateur_nom      = serializers.SerializerMethodField()
    temps_total_prevu  = serializers.ReadOnlyField()
    ecart_temps        = serializers.ReadOnlyField()
    cout_prevu         = serializers.ReadOnlyField()
    cout_reel          = serializers.ReadOnlyField()

    class Meta:
        model  = OperationOF
        fields = '__all__'

    def get_operateur_nom(self, obj):
        if obj.operateur:
            return f"{obj.operateur.first_name} {obj.operateur.last_name}".strip() or obj.operateur.username
        return ''


class LigneNomenclatureOFSerializer(serializers.ModelSerializer):
    article_ref  = serializers.CharField(source='article.reference', read_only=True)
    manquant     = serializers.ReadOnlyField()

    class Meta:
        model  = LigneNomenclatureOF
        fields = '__all__'


class PointageProductionSerializer(serializers.ModelSerializer):
    operateur_nom   = serializers.SerializerMethodField()
    operation_lib   = serializers.CharField(source='operation.libelle', read_only=True)
    of_reference    = serializers.CharField(source='operation.of.reference', read_only=True)

    class Meta:
        model  = PointageProduction
        fields = '__all__'

    def get_operateur_nom(self, obj):
        if obj.operateur:
            return f"{obj.operateur.first_name} {obj.operateur.last_name}".strip() or obj.operateur.username
        return ''


class OFListSerializer(serializers.ModelSerializer):
    article_ref        = serializers.CharField(source='article.reference', read_only=True)
    commande_ref       = serializers.CharField(source='commande_client.reference', read_only=True)
    responsable_nom    = serializers.SerializerMethodField()
    avancement_pct     = serializers.ReadOnlyField()
    est_en_retard      = serializers.ReadOnlyField()
    taux_rebut         = serializers.ReadOnlyField()
    temps_prevu_total  = serializers.ReadOnlyField()
    temps_reel_total   = serializers.ReadOnlyField()
    nb_operations      = serializers.SerializerMethodField()
    nb_manquants       = serializers.SerializerMethodField()

    class Meta:
        model  = OrdreFabrication
        fields = [
            'id', 'reference', 'designation', 'article_ref', 'commande_ref',
            'statut', 'priorite', 'quantite_lancee', 'quantite_fabriquee',
            'quantite_rebut', 'unite', 'avancement_pct', 'taux_rebut',
            'est_en_retard', 'date_debut_prevue', 'date_fin_prevue',
            'date_debut_reelle', 'date_fin_reelle', 'responsable_nom',
            'temps_prevu_total', 'temps_reel_total', 'nb_operations',
            'nb_manquants', 'created_at',
        ]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return f"{obj.responsable.first_name} {obj.responsable.last_name}".strip() or obj.responsable.username
        return ''

    def get_nb_operations(self, obj):
        return obj.operations.count()

    def get_nb_manquants(self, obj):
        return obj.nomenclature.filter(disponible=False).count()


class OFDetailSerializer(OFListSerializer):
    operations  = OperationOFSerializer(many=True, read_only=True)
    nomenclature = LigneNomenclatureOFSerializer(many=True, read_only=True)

    class Meta(OFListSerializer.Meta):
        fields = '__all__'


class ArretMachineSerializer(serializers.ModelSerializer):
    poste_libelle = serializers.CharField(source='poste_charge.libelle', read_only=True)

    class Meta:
        model  = ArretMachine
        fields = '__all__'