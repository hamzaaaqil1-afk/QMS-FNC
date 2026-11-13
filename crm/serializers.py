from rest_framework import serializers
from .models import Client, Contact, Opportunite, Devis, LigneDevis, CommandeClient, LigneCommande, ReclamationClient


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Contact
        fields = '__all__'


class ClientListSerializer(serializers.ModelSerializer):
    commercial_nom = serializers.SerializerMethodField()
    nb_commandes   = serializers.SerializerMethodField()
    nb_reclamations= serializers.SerializerMethodField()

    class Meta:
        model  = Client
        fields = [
            'id', 'reference', 'raison_sociale', 'siret', 'secteur',
            'segment', 'ville', 'pays', 'telephone', 'email',
            'commercial_nom', 'actif', 'nb_commandes', 'nb_reclamations', 'created_at',
        ]

    def get_commercial_nom(self, obj):
        if obj.commercial:
            return f"{obj.commercial.first_name} {obj.commercial.last_name}".strip() or obj.commercial.username
        return ''

    def get_nb_commandes(self, obj):
        return obj.commandes.count()

    def get_nb_reclamations(self, obj):
        return obj.reclamations.filter(statut__in=['ouverte', 'en_cours']).count()


class ClientDetailSerializer(ClientListSerializer):
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta(ClientListSerializer.Meta):
        fields = '__all__'


class OpportuniteSerializer(serializers.ModelSerializer):
    client_nom     = serializers.CharField(source='client.raison_sociale', read_only=True)
    commercial_nom = serializers.SerializerMethodField()
    contact_nom    = serializers.SerializerMethodField()

    class Meta:
        model  = Opportunite
        fields = '__all__'

    def get_commercial_nom(self, obj):
        if obj.commercial:
            return f"{obj.commercial.first_name} {obj.commercial.last_name}".strip() or obj.commercial.username
        return ''

    def get_contact_nom(self, obj):
        if obj.contact:
            return f"{obj.contact.prenom} {obj.contact.nom}".strip()
        return ''


class LigneDevisSerializer(serializers.ModelSerializer):
    montant_ht = serializers.ReadOnlyField()

    class Meta:
        model  = LigneDevis
        fields = '__all__'


class DevisListSerializer(serializers.ModelSerializer):
    client_nom  = serializers.CharField(source='client.raison_sociale', read_only=True)
    montant_ht  = serializers.ReadOnlyField()
    montant_ttc = serializers.ReadOnlyField()
    commercial_nom = serializers.SerializerMethodField()

    class Meta:
        model  = Devis
        fields = [
            'id', 'reference', 'client', 'client_nom', 'statut',
            'date_emission', 'date_validite', 'remise_globale',
            'montant_ht', 'montant_ttc', 'commercial_nom', 'created_at',
        ]

    def get_commercial_nom(self, obj):
        if obj.commercial:
            return f"{obj.commercial.first_name} {obj.commercial.last_name}".strip() or obj.commercial.username
        return ''


class DevisDetailSerializer(DevisListSerializer):
    lignes      = LigneDevisSerializer(many=True, read_only=True)
    montant_tva = serializers.ReadOnlyField()

    class Meta(DevisListSerializer.Meta):
        fields = '__all__'


class LigneCommandeSerializer(serializers.ModelSerializer):
    montant_ht      = serializers.ReadOnlyField()
    reste_a_livrer  = serializers.ReadOnlyField()

    class Meta:
        model  = LigneCommande
        fields = '__all__'


class CommandeClientListSerializer(serializers.ModelSerializer):
    client_nom     = serializers.CharField(source='client.raison_sociale', read_only=True)
    montant_total  = serializers.ReadOnlyField()
    commercial_nom = serializers.SerializerMethodField()
    nb_lignes      = serializers.SerializerMethodField()

    class Meta:
        model  = CommandeClient
        fields = [
            'id', 'reference', 'client', 'client_nom', 'statut',
            'date_commande', 'date_livraison_prevue', 'date_livraison_reelle',
            'montant_total', 'commercial_nom', 'nb_lignes',
            'reference_client', 'created_at',
        ]

    def get_commercial_nom(self, obj):
        if obj.commercial:
            return f"{obj.commercial.first_name} {obj.commercial.last_name}".strip() or obj.commercial.username
        return ''

    def get_nb_lignes(self, obj):
        return obj.lignes.count()


class CommandeClientDetailSerializer(CommandeClientListSerializer):
    lignes = LigneCommandeSerializer(many=True, read_only=True)

    class Meta(CommandeClientListSerializer.Meta):
        fields = '__all__'


class ReclamationClientSerializer(serializers.ModelSerializer):
    client_nom  = serializers.CharField(source='client.raison_sociale', read_only=True)
    fnc_numero  = serializers.CharField(source='fnc.numero', read_only=True)
    commande_ref= serializers.CharField(source='commande.reference', read_only=True)

    class Meta:
        model  = ReclamationClient
        fields = '__all__'