from rest_framework import serializers
from .models import (Fournisseur, EvaluationFournisseur, DemandeAchat, LigneDemandeAchat,
                     CommandeAchat, LigneCommandeAchat, BonReception, LigneBonReception)


class EvaluationFournisseurSerializer(serializers.ModelSerializer):
    note_globale    = serializers.ReadOnlyField()
    evaluateur_nom  = serializers.SerializerMethodField()

    class Meta:
        model  = EvaluationFournisseur
        fields = '__all__'

    def get_evaluateur_nom(self, obj):
        if obj.evaluateur:
            return f"{obj.evaluateur.first_name} {obj.evaluateur.last_name}".strip() or obj.evaluateur.username
        return ''


class FournisseurListSerializer(serializers.ModelSerializer):
    nb_commandes = serializers.SerializerMethodField()

    class Meta:
        model  = Fournisseur
        fields = [
            'id', 'reference', 'raison_sociale', 'categorie', 'statut',
            'ville', 'pays', 'telephone', 'email',
            'delai_livraison_jours', 'note_qualite', 'note_delai',
            'note_prix', 'note_globale', 'nb_commandes',
        ]

    def get_nb_commandes(self, obj):
        return obj.commandes.count()


class FournisseurDetailSerializer(FournisseurListSerializer):
    evaluations = EvaluationFournisseurSerializer(many=True, read_only=True)

    class Meta(FournisseurListSerializer.Meta):
        fields = '__all__'


class LigneDemandeAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LigneDemandeAchat
        fields = '__all__'


class DemandeAchatSerializer(serializers.ModelSerializer):
    demandeur_nom   = serializers.SerializerMethodField()
    approbateur_nom = serializers.SerializerMethodField()
    fournisseur_nom = serializers.CharField(source='fournisseur_suggere.raison_sociale', read_only=True)
    montant_total   = serializers.ReadOnlyField()
    lignes          = LigneDemandeAchatSerializer(many=True, read_only=True)
    nb_lignes       = serializers.SerializerMethodField()

    class Meta:
        model  = DemandeAchat
        fields = '__all__'

    def get_demandeur_nom(self, obj):
        if obj.demandeur:
            return f"{obj.demandeur.first_name} {obj.demandeur.last_name}".strip() or obj.demandeur.username
        return ''

    def get_approbateur_nom(self, obj):
        if obj.approbateur:
            return f"{obj.approbateur.first_name} {obj.approbateur.last_name}".strip() or obj.approbateur.username
        return ''

    def get_nb_lignes(self, obj):
        return obj.lignes.count()


class LigneCommandeAchatSerializer(serializers.ModelSerializer):
    montant_ht       = serializers.ReadOnlyField()
    reste_a_recevoir = serializers.ReadOnlyField()

    class Meta:
        model  = LigneCommandeAchat
        fields = '__all__'


class CommandeAchatListSerializer(serializers.ModelSerializer):
    fournisseur_nom = serializers.CharField(source='fournisseur.raison_sociale', read_only=True)
    acheteur_nom    = serializers.SerializerMethodField()
    montant_ht      = serializers.ReadOnlyField()
    montant_ttc     = serializers.ReadOnlyField()
    est_en_retard   = serializers.ReadOnlyField()
    nb_lignes       = serializers.SerializerMethodField()

    class Meta:
        model  = CommandeAchat
        fields = [
            'id', 'reference', 'fournisseur', 'fournisseur_nom',
            'statut', 'date_commande', 'date_livraison_prevue',
            'date_livraison_reelle', 'montant_ht', 'montant_ttc',
            'est_en_retard', 'acheteur_nom', 'nb_lignes',
            'reference_fournisseur',
        ]

    def get_acheteur_nom(self, obj):
        if obj.acheteur:
            return f"{obj.acheteur.first_name} {obj.acheteur.last_name}".strip() or obj.acheteur.username
        return ''

    def get_nb_lignes(self, obj):
        return obj.lignes.count()


class CommandeAchatDetailSerializer(CommandeAchatListSerializer):
    lignes = LigneCommandeAchatSerializer(many=True, read_only=True)

    class Meta(CommandeAchatListSerializer.Meta):
        fields = '__all__'


class LigneBonReceptionSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='ligne_commande.designation', read_only=True)

    class Meta:
        model  = LigneBonReception
        fields = '__all__'


class BonReceptionSerializer(serializers.ModelSerializer):
    commande_ref       = serializers.CharField(source='commande.reference', read_only=True)
    fournisseur_nom    = serializers.CharField(source='commande.fournisseur.raison_sociale', read_only=True)
    receptionnaire_nom = serializers.SerializerMethodField()
    lignes             = LigneBonReceptionSerializer(many=True, read_only=True)
    fnc_numero         = serializers.CharField(source='fnc.numero', read_only=True)

    class Meta:
        model  = BonReception
        fields = '__all__'

    def get_receptionnaire_nom(self, obj):
        if obj.receptionnaire:
            return f"{obj.receptionnaire.first_name} {obj.receptionnaire.last_name}".strip() or obj.receptionnaire.username
        return ''