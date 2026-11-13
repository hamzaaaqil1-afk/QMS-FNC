from rest_framework import serializers
from .models import Employe, Competence, EmployeCompetence, Pointage, JourneeCalculee, DemandeConge, Formation


class CompetenceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Competence
        fields = '__all__'


class EmployeCompetenceSerializer(serializers.ModelSerializer):
    competence_nom  = serializers.CharField(source='competence.nom', read_only=True)
    competence_type = serializers.CharField(source='competence.type_competence', read_only=True)
    statut          = serializers.ReadOnlyField()

    class Meta:
        model  = EmployeCompetence
        fields = '__all__'


class EmployeListSerializer(serializers.ModelSerializer):
    nom_complet       = serializers.ReadOnlyField()
    anciennete_annees = serializers.ReadOnlyField()
    periode_essai_active = serializers.ReadOnlyField()
    manager_nom       = serializers.SerializerMethodField()
    nb_competences    = serializers.SerializerMethodField()

    class Meta:
        model  = Employe
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet',
            'poste', 'departement', 'categorie', 'equipe',
            'type_contrat', 'statut', 'date_embauche',
            'anciennete_annees', 'periode_essai_active',
            'badge_rfid', 'solde_cp', 'solde_rtt',
            'manager_nom', 'nb_competences', 'telephone', 'email',
        ]

    def get_manager_nom(self, obj):
        if obj.manager:
            return obj.manager.nom_complet
        return ''

    def get_nb_competences(self, obj):
        return obj.competences.count()


class EmployeDetailSerializer(EmployeListSerializer):
    competences = EmployeCompetenceSerializer(many=True, read_only=True)

    class Meta(EmployeListSerializer.Meta):
        fields = '__all__'


class PointageSerializer(serializers.ModelSerializer):
    employe_nom = serializers.CharField(source='employe.nom_complet', read_only=True)
    saisi_par_nom = serializers.SerializerMethodField()

    class Meta:
        model  = Pointage
        fields = '__all__'

    def get_saisi_par_nom(self, obj):
        if obj.saisi_par:
            return f"{obj.saisi_par.first_name} {obj.saisi_par.last_name}".strip() or obj.saisi_par.username
        return ''


class JourneeCalculeeSerializer(serializers.ModelSerializer):
    employe_nom = serializers.CharField(source='employe.nom_complet', read_only=True)

    class Meta:
        model  = JourneeCalculee
        fields = '__all__'


class DemandeCongeSerializer(serializers.ModelSerializer):
    employe_nom   = serializers.CharField(source='employe.nom_complet', read_only=True)
    valide_par_nom = serializers.SerializerMethodField()

    class Meta:
        model  = DemandeConge
        fields = '__all__'

    def get_valide_par_nom(self, obj):
        if obj.valide_par:
            return f"{obj.valide_par.first_name} {obj.valide_par.last_name}".strip() or obj.valide_par.username
        return ''


class FormationSerializer(serializers.ModelSerializer):
    competence_nom      = serializers.CharField(source='competence_acquise.nom', read_only=True)
    nb_participants     = serializers.SerializerMethodField()
    participants_detail = EmployeListSerializer(source='participants', many=True, read_only=True)

    class Meta:
        model  = Formation
        fields = '__all__'

    def get_nb_participants(self, obj):
        return obj.participants.count()