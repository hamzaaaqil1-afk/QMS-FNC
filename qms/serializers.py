
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ParametresEntreprise
from .models import (
    NonConformite, ActionCorrective, Analyse5M, PieceJointeFNC,PieceJointeAnalyse5M,PieceJointeAction,
    CAPA, Audit, LigneChecklist, EcartAudit, PlanAction,TemplateFormulaireFNC,Constat,
    CommentaireFNC,ServiceProcessus, ClassificationFNC, OrigineEcart, StatutFNC
)
from .models import (
    NonConformite, ActionCorrective, Analyse5M, PieceJointeFNC,SectionFNC,PieceJointeAnalyse5M,PieceJointeAction,TemplateFormulaireFNC,
    CAPA, Audit, LigneChecklist, EcartAudit, PlanAction , ChampPersonnalise, ValeurChampFNC, TemplateExportFNC,OptionListe
)




class TemplateExportFNCSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.SerializerMethodField()
    nb_sections_actives = serializers.SerializerMethodField()

    class Meta:
        model  = TemplateExportFNC
        fields = [
            'id', 'nom', 'description', 'format',
            'configuration', 'is_default',
            'utilisateur', 'utilisateur_nom',
            'nb_sections_actives',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['utilisateur', 'created_at', 'updated_at']

    def get_utilisateur_nom(self, obj):
        return obj.utilisateur.get_full_name() or obj.utilisateur.username

    def get_nb_sections_actives(self, obj):
        config = obj.configuration or {}
        return sum(1 for s in config.values() if s.get('actif', True))

class TemplateFormulaireFNCSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TemplateFormulaireFNC
        fields = ['id', 'nom', 'description', 'type_objet', 'configuration', 'is_default', 'ordre', 'created_at', 'updated_at']

class ServiceProcessusSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ServiceProcessus
        fields = ['id', 'nom', 'code', 'description', 'actif', 'ordre', 'created_at']

class ClassificationFNCSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ClassificationFNC
        fields = ['id', 'nom', 'code', 'description', 'actif', 'ordre', 'created_at']

class OrigineEcartSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrigineEcart
        fields = ['id', 'nom', 'code', 'description', 'actif', 'ordre', 'created_at']

class StatutFNCSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StatutFNC
        fields = ['id', 'nom', 'code', 'description', 'actif', 'ordre',
                  'est_final', 'est_annulation', 'couleur', 'created_at']
   
class OptionListeSerializer(serializers.ModelSerializer):
    type_liste_label = serializers.SerializerMethodField()

    class Meta:
        model  = OptionListe
        fields = ['id', 'type_liste', 'type_liste_label', 'valeur', 'libelle', 'ordre', 'actif', 'created_at']

    def get_type_liste_label(self, obj):
        return obj.get_type_liste_display()   
    
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class PieceJointeFNCSerializer(serializers.ModelSerializer):
    uploaded_by_nom = serializers.SerializerMethodField()
    url_fichier     = serializers.SerializerMethodField()

    class Meta:
        model  = PieceJointeFNC
        fields = ['id', 'fnc', 'nom_fichier', 'type_fichier', 'fichier',
                  'taille', 'uploaded_at', 'uploaded_by', 'uploaded_by_nom', 'url_fichier']

    def get_uploaded_by_nom(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return ''

    def get_url_fichier(self, obj):
        request = self.context.get('request')
        if obj.fichier and request:
            return request.build_absolute_uri(obj.fichier.url)
        return ''
    
class PieceJointeAnalyse5MSerializer(serializers.ModelSerializer):
    uploaded_by_nom = serializers.SerializerMethodField()
    url_fichier     = serializers.SerializerMethodField()
    nom_fichier     = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model  = PieceJointeAnalyse5M
        fields = ['id', 'analyse', 'nom_fichier', 'type_fichier', 'fichier',
                  'taille', 'uploaded_at', 'uploaded_by', 'uploaded_by_nom',  'url_fichier']

    def get_uploaded_by_nom(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return ''


    def get_url_fichier(self, obj):
        request = self.context.get('request')
        if obj.fichier and request:
            return request.build_absolute_uri(obj.fichier.url)
        return ''


class PieceJointeActionSerializer(serializers.ModelSerializer):
    uploaded_by_nom = serializers.SerializerMethodField()
    url_fichier     = serializers.SerializerMethodField()
    nom_fichier     = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model  = PieceJointeAction
        fields = ['id', 'action', 'nom_fichier', 'type_fichier', 'fichier',
                  'taille', 'uploaded_at', 'uploaded_by', 'uploaded_by_nom', 'url_fichier']

    def get_uploaded_by_nom(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return ''

    def get_url_fichier(self, obj):
        request = self.context.get('request')
        if obj.fichier and request:
            return request.build_absolute_uri(obj.fichier.url)
        return ''
    

class CommentaireFNCSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.SerializerMethodField()

    class Meta:
        model  = CommentaireFNC
        fields = ['id', 'fnc', 'auteur', 'auteur_nom', 'contenu', 'type_comment', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_auteur_nom(self, obj):
        if obj.auteur:
            return f"{obj.auteur.first_name} {obj.auteur.last_name}".strip() or obj.auteur.username
        return ''
    

class Analyse5MSerializer(serializers.ModelSerializer):
    categorie_label     = serializers.CharField(source='get_categorie_display', read_only=True)
    processus_label     = serializers.CharField(source='get_processus_responsable_display', read_only=True)
    statut_label        = serializers.CharField(source='get_statut_display', read_only=True)
    nb_actions          = serializers.SerializerMethodField()
    nb_pieces_jointes   = serializers.SerializerMethodField()  # ICI
    criticite_cause     = serializers.ReadOnlyField()
    responsable_analyse_nom = serializers.SerializerMethodField()
    
    def get_nb_pieces_jointes(self, obj):
        return obj.pieces_jointes.count()
    
    class Meta:
        model  = Analyse5M
        fields = [
            'id', 'reference', 'fnc',
            'categorie', 'categorie_label',
            'cause_analysee', 'cause_racine',
            'processus_responsable', 'processus_label',
            'commentaire', 'date_analyse',
            'statut', 'statut_label',
            'nb_actions', 'created_at','nb_pieces_jointes',
            # Nouveaux champs
            'pourquoi_1', 'pourquoi_2', 'pourquoi_3', 'pourquoi_4', 'pourquoi_5',
            'frequence', 'detectabilite', 'gravite_cause', 'criticite_cause',
            'responsable_analyse', 'responsable_analyse_nom',
            'date_cloture_prevue', 'efficacite_verifiee', 'date_verification',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'criticite_cause']

    def get_nb_actions(self, obj):
        return obj.actions.count()

    def get_responsable_analyse_nom(self, obj):
        if obj.responsable_analyse:
            return obj.responsable_analyse.get_full_name() or obj.responsable_analyse.username
        return ''

class ActionCorrectivelListSerializer(serializers.ModelSerializer):
    responsable_nom   = serializers.SerializerMethodField()
    type_action_label = serializers.CharField(source='get_type_action_display', read_only=True)
    statut_label      = serializers.CharField(source='get_statut_display', read_only=True)
    source_type_label = serializers.CharField(source='get_source_type_display', read_only=True)
    processus_label   = serializers.SerializerMethodField()
    est_en_retard     = serializers.BooleanField(read_only=True)
    fnc_numero = serializers.SerializerMethodField()
    

    class Meta:
        model  = ActionCorrective
        fields = [
            'id', 'reference',
            'source_type', 'source_type_label',
            'fnc', 'audit_ref', 'capa_ref',
            'description', 'type_action', 'type_action_label',
            'processus_ref', 'processus_label',
            'responsable', 'responsable_nom',
            'date_echeance', 'date_cloture','fnc_numero',
            'resultat', 'statut', 'statut_label',
            'heures_investies', 'cout_materiel', 'cout_estime',
            'ref_cause', 'est_en_retard', 'created_at', 'updated_at',
        ]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return obj.responsable.get_full_name() or obj.responsable.username
        return ''

    def get_fnc_numero(self, obj):
        return obj.fnc.numero if obj.fnc else None
    
    def get_processus_label(self, obj):
        return obj.processus_ref.nom if obj.processus_ref else ''
    
    
class ActionCorrectivelDetailSerializer(serializers.ModelSerializer):
    responsable_nom   = serializers.SerializerMethodField()
    type_action_label = serializers.CharField(source='get_type_action_display', read_only=True)
    statut_label      = serializers.CharField(source='get_statut_display', read_only=True)
    source_type_label = serializers.CharField(source='get_source_type_display', read_only=True)
    processus_label   = serializers.SerializerMethodField()
    est_en_retard     = serializers.BooleanField(read_only=True)
    ref_cause_detail  = Analyse5MSerializer(source='ref_cause', read_only=True)
    fnc_numero = serializers.SerializerMethodField()


    class Meta:
        model  = ActionCorrective
        fields = [
            'id', 'reference',
            'source_type', 'source_type_label',
            'fnc', 'audit_ref', 'capa_ref','fnc_numero',
            'description', 'type_action', 'type_action_label',
            'processus_ref', 'processus_label',
            'responsable', 'responsable_nom',
            'date_echeance', 'date_cloture',
            'resultat', 'statut', 'statut_label', 'est_en_retard',
            'heures_investies', 'cout_materiel', 'cout_estime',
            'ref_cause', 'ref_cause_detail',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return obj.responsable.get_full_name() or obj.responsable.username
        return ''
    
    def get_fnc_numero(self, obj):
        return obj.fnc.numero if obj.fnc else None
    def get_fnc_numero(self, obj):
        return obj.fnc.numero if obj.fnc else None
    def get_processus_label(self, obj):
        return obj.processus_ref.nom if obj.processus_ref else ''

class StatutFNCMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StatutFNC
        fields = ['id', 'code', 'nom', 'couleur', 'est_final', 'est_annulation']
        
        
class NonConformiteListSerializer(serializers.ModelSerializer):
    statut_ref_detail = StatutFNCMiniSerializer(source='statut_ref', read_only=True)
    redacteur_nom     = serializers.SerializerMethodField()
    responsable_nom   = serializers.SerializerMethodField()
    statut_label      = serializers.SerializerMethodField()
    gravite_label     = serializers.CharField(source='get_gravite_display', read_only=True)
    processus_label   = serializers.SerializerMethodField()
    classification_label = serializers.SerializerMethodField()
    origine_label     = serializers.SerializerMethodField()
    nb_actions        = serializers.SerializerMethodField()
    nb_causes         = serializers.SerializerMethodField()
    est_en_retard     = serializers.ReadOnlyField()
    nb_commentaires   = serializers.SerializerMethodField()
    nb_pieces_jointes = serializers.SerializerMethodField()

    class Meta:
        model  = NonConformite
        fields = [
            'id', 'numero', 'libelle', 'description','type_fnc','statut_ref_detail',
            'date_decouverte', 'date_prevue', 'date_echeance', 'date_cloture',
            'gravite', 'gravite_label',
            'statut_ref', 'statut_label',
            'type_nc', 'origine_ecart_ref', 'origine_label',
            'processus_ref', 'processus_label',
            'client', 'fournisseur',
            'criticite', 'classification_ref', 'classification_label',
            'decision', 'cout_non_qualite',
            'est_en_retard', 'capa_generee',
            'redacteur', 'redacteur_nom',
            'responsable_user', 'responsable_nom',
            'nb_actions', 'nb_causes',
            'nb_commentaires', 'nb_pieces_jointes',
            'created_at',
        ]

    def get_redacteur_nom(self, obj):
        if obj.redacteur:
            return f"{obj.redacteur.first_name} {obj.redacteur.last_name}".strip() or obj.redacteur.username
        return ''

    def get_responsable_nom(self, obj):
        if obj.responsable_user:
            return f"{obj.responsable_user.first_name} {obj.responsable_user.last_name}".strip() or obj.responsable_user.username
        return ''

    def get_statut_label(self, obj):
        return obj.statut_ref.nom if obj.statut_ref else ''

    def get_processus_label(self, obj):
        return obj.processus_ref.nom if obj.processus_ref else ''

    def get_classification_label(self, obj):
        return obj.classification_ref.nom if obj.classification_ref else ''

    def get_origine_label(self, obj):
        return obj.origine_ecart_ref.nom if obj.origine_ecart_ref else ''

    def get_nb_actions(self, obj):
        return obj.actions.count() if hasattr(obj, 'actions') else 0

    def get_nb_causes(self, obj):
        return obj.analyses_5m.count() if hasattr(obj, 'analyses_5m') else 0

    def get_nb_commentaires(self, obj):
        return obj.commentaires.count() if hasattr(obj, 'commentaires') else 0

    def get_nb_pieces_jointes(self, obj):
        return obj.pieces_jointes.count() if hasattr(obj, 'pieces_jointes') else 0
    

    
class NonConformiteDetailSerializer(NonConformiteListSerializer):
    actions        = ActionCorrectivelListSerializer(many=True, read_only=True)
    analyses_5m    = Analyse5MSerializer(many=True, read_only=True)
    pieces_jointes = PieceJointeFNCSerializer(many=True, read_only=True)
    commentaires   = CommentaireFNCSerializer(many=True, read_only=True)
    verificateur_nom = serializers.SerializerMethodField()
    type_nc_label    = serializers.SerializerMethodField()

    class Meta(NonConformiteListSerializer.Meta):
        fields = NonConformiteListSerializer.Meta.fields + [
            'type_nc', 'type_nc_label','type_fnc',
            'type_piece', 'qte_nc', 'qte_totale',
            'numero_of', 'document_reference',
            'reclamation_client', 'avis_client_requis',
            'action_immediate', 'origine_cause',
            'score_gravite', 'score_detection', 'score_impact',
            'impact_surete', 'eip',
            'efficacite_verifiee', 'commentaire_cloture',
            'date_traitement',
            'verificateur', 'verificateur_nom',
            'actions', 'analyses_5m', 'pieces_jointes', 'commentaires',
            'updated_at',
        ]
        read_only_fields = ['id', 'numero', 'criticite', 'created_at', 'updated_at']
        extra_kwargs = {
            'description':     {'required': False},
            'gravite':         {'required': False},
            'date_decouverte': {'required': False},
            'libelle':         {'required': False},
            'redacteur':       {'required': False},
        }

    def get_verificateur_nom(self, obj):
        if obj.verificateur:
            return obj.verificateur.get_full_name() or obj.verificateur.username
        return ''

    def get_type_nc_label(self, obj):
        return obj.get_type_nc_display() if hasattr(obj, 'get_type_nc_display') else ''
    

    

class CAPAListSerializer(serializers.ModelSerializer):
    fnc_numero          = serializers.CharField(source='fnc.numero', read_only=True)
    responsable_nom     = serializers.SerializerMethodField()
    detecte_par_nom     = serializers.SerializerMethodField()
    est_en_retard       = serializers.SerializerMethodField()
    type_capa_label     = serializers.CharField(source='get_type_capa_display', read_only=True)
    statut_label        = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model  = CAPA
        fields = [
            'id', 'reference', 'titre', 'type_capa', 'type_capa_label',
            'statut', 'statut_label', 'fnc_numero', 'date_detection',
            'date_echeance', 'responsable_nom', 'detecte_par_nom', 'est_en_retard',
        ]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return f"{obj.responsable.first_name} {obj.responsable.last_name}".strip() or obj.responsable.username
        return ''

    def get_detecte_par_nom(self, obj):
        if obj.detecte_par:
            return f"{obj.detecte_par.first_name} {obj.detecte_par.last_name}".strip() or obj.detecte_par.username
        return ''

    def get_est_en_retard(self, obj):
        from datetime import date
        if obj.date_echeance and obj.statut not in ['clos', 'annule']:
            return obj.date_echeance < date.today()
        return False


class CAPADetailSerializer(CAPAListSerializer):
    class Meta(CAPAListSerializer.Meta):
        fields = '__all__'
        
class LigneChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LigneChecklist
        fields = '__all__'


class EcartAuditSerializer(serializers.ModelSerializer):
    fnc_numero  = serializers.CharField(source='fnc.numero', read_only=True)
    capa_reference = serializers.CharField(source='capa.reference', read_only=True)

    class Meta:
        model  = EcartAudit
        fields = '__all__'


class AuditListSerializer(serializers.ModelSerializer):
    auditeur_nom    = serializers.SerializerMethodField()
    type_audit_label = serializers.CharField(source='get_type_audit_display', read_only=True)
    statut_label    = serializers.CharField(source='get_statut_display', read_only=True)
    nb_ecarts       = serializers.SerializerMethodField()

    class Meta:
        model  = Audit
        fields = [
            'id', 'reference', 'titre', 'type_audit', 'type_audit_label',
            'statut', 'statut_label', 'date_prevue', 'date_realisation',
            'auditeur_nom', 'audite', 'processus', 'resultat',
            'nb_ecarts_majeurs', 'nb_ecarts_mineurs', 'nb_ecarts',
        ]

    def get_auditeur_nom(self, obj):
        if obj.auditeur:
            return f"{obj.auditeur.first_name} {obj.auditeur.last_name}".strip() or obj.auditeur.username
        return ''

    def get_nb_ecarts(self, obj):
        return obj.nb_ecarts_majeurs + obj.nb_ecarts_mineurs


class AuditDetailSerializer(AuditListSerializer):
    checklist = LigneChecklistSerializer(many=True, read_only=True)
    ecarts    = EcartAuditSerializer(many=True, read_only=True)

    class Meta(AuditListSerializer.Meta):
        fields = '__all__'
        
class PlanActionSerializer(serializers.ModelSerializer):
    realisateur_nom  = serializers.SerializerMethodField()
    verificateur_nom = serializers.SerializerMethodField()
    createur_nom     = serializers.SerializerMethodField()
    est_en_retard    = serializers.ReadOnlyField()
    fnc_numero       = serializers.CharField(source='fnc.numero',      read_only=True)
    capa_reference   = serializers.CharField(source='capa.reference',  read_only=True)
    audit_reference  = serializers.CharField(source='audit.reference', read_only=True)
    risque_reference = serializers.CharField(source='risque.reference',read_only=True)

    class Meta:
        model  = PlanAction
        fields = '__all__'

    def get_realisateur_nom(self, obj):
        if obj.realisateur:
            return f"{obj.realisateur.first_name} {obj.realisateur.last_name}".strip() or obj.realisateur.username
        return ''

    def get_verificateur_nom(self, obj):
        if obj.verificateur:
            return f"{obj.verificateur.first_name} {obj.verificateur.last_name}".strip() or obj.verificateur.username
        return ''

    def get_createur_nom(self, obj):
        if obj.createur:
            return f"{obj.createur.first_name} {obj.createur.last_name}".strip() or obj.createur.username
        return ''


class ParametresEntrepriseSerializer(serializers.ModelSerializer):
    preview_numero      = serializers.SerializerMethodField()
    site_preview_nom    = serializers.SerializerMethodField()
    logo_url            = serializers.SerializerMethodField()
    site_web            = serializers.URLField(required=False, allow_blank=True)
    email_contact       = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model  = ParametresEntreprise
        fields = [
            'id',
            # Numérotation (format commun à l'entreprise ; le compteur lui-même vit sur Site)
            'prefixe', 'utiliser_annee', 'utiliser_mois', 'inclure_code_site',
            'separateur', 'longueur_compteur', 'remise_a_zero',
            # Entreprise
            'nom_entreprise', 'logo', 'logo_url',
            'adresse', 'telephone', 'email_contact', 'site_web',
            # Export
            'reference_doc', 'version_doc', 'pied_de_page', 'afficher_nom_pied', 'afficher_adresse_pied',
            'afficher_reference_pied', 'afficher_date_pied', 'afficher_confidentiel',
            # Computed — aperçu calculé pour un site précis (voir contexte 'site_preview')
            'preview_numero', 'site_preview_nom', 'updated_at',
        ]

    def get_preview_numero(self, obj):
        site = self.context.get('site_preview')
        if not site:
            return None
        return site.preview_numero_fnc(obj)

    def get_site_preview_nom(self, obj):
        site = self.context.get('site_preview')
        return site.nom if site else None

    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
class SectionFNCSerializer(serializers.ModelSerializer):
    nb_champs = serializers.SerializerMethodField()
    code      = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model  = SectionFNC
        fields = [
            'id', 'nom', 'code', 'icone', 'ordre', 'actif',
            'est_systeme', 'nb_champs', 'created_at',
        ]

    def get_nb_champs(self, obj):
        return obj.champs.count()

class ChampPersonnaliseSerializer(serializers.ModelSerializer):
    type_champ_label   = serializers.SerializerMethodField()
    section_label       = serializers.SerializerMethodField()
    source_dynamique_label = serializers.SerializerMethodField()
    nb_valeurs          = serializers.SerializerMethodField()
    choix_resolus       = serializers.SerializerMethodField()
    cle                 = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model  = ChampPersonnalise
        fields = [
            'id', 'nom', 'cle', 'type_champ', 'type_champ_label',
            'obligatoire', 'actif', 'ordre', 'options',
            'source_dynamique', 'source_dynamique_label', 'choix_resolus',
            'section', 'section_label', 'nb_valeurs', 'created_at',
            'type_rendu', 'config_colonnes', 'config_signataires',
        ]

    def get_type_champ_label(self, obj):
        return obj.get_type_champ_display()

    def get_section_label(self, obj):
        return obj.section.nom if obj.section else None

    def get_source_dynamique_label(self, obj):
        return obj.get_source_dynamique_display()

    def get_nb_valeurs(self, obj):
        return obj.valeurs.count()

    def get_choix_resolus(self, obj):
        return obj.get_choix()


class ChampStructureSerializer(serializers.ModelSerializer):
    """Représentation d'un champ pour la structure d'export (fixe ou custom, unifié)."""
    type_rendu_label = serializers.SerializerMethodField()
    choix_resolus     = serializers.SerializerMethodField()

    class Meta:
        model  = ChampPersonnalise
        fields = [
            'id', 'nom', 'cle', 'origine', 'cle_modele',
            'type_champ', 'type_rendu', 'type_rendu_label',
            'largeur_rendu', 'hauteur_bloc', 'obligatoire',
            'ordre', 'choix_resolus',
        ]

    def get_type_rendu_label(self, obj):
        return obj.get_type_rendu_display()

    def get_choix_resolus(self, obj):
        return obj.get_choix()


class SectionStructureSerializer(serializers.ModelSerializer):
    """Section avec tous ses champs (fixes + custom) triés, pour la structure d'export."""
    champs = serializers.SerializerMethodField()

    class Meta:
        model  = SectionFNC
        fields = ['id', 'nom', 'code', 'ordre', 'champs']

    def get_champs(self, obj):
        champs = obj.champs.filter(actif=True).order_by('ordre', 'nom')
        return ChampStructureSerializer(champs, many=True).data
    

class ValeurChampFNCSerializer(serializers.ModelSerializer):
    champ_nom      = serializers.SerializerMethodField()
    champ_type     = serializers.SerializerMethodField()
    champ_options  = serializers.SerializerMethodField()
    champ_section  = serializers.SerializerMethodField()

    class Meta:
        model  = ValeurChampFNC
        fields = [
            'id', 'fnc', 'champ', 'valeur',
            'champ_nom', 'champ_type', 'champ_options', 'champ_section',
        ]

    def get_champ_nom(self, obj):
        return obj.champ.nom

    def get_champ_type(self, obj):
        return obj.champ.type_champ

    def get_champ_options(self, obj):
        return obj.champ.options

    def get_champ_section(self, obj):
        return obj.champ.section.nom if obj.champ.section else None
    
class ConstatListSerializer(serializers.ModelSerializer):
    observateur_nom = serializers.SerializerMethodField()
    valide_par_nom  = serializers.SerializerMethodField()
    template_nom    = serializers.CharField(source='template.nom', read_only=True)
    fnc_numero      = serializers.CharField(source='fnc.numero', read_only=True)

    class Meta:
        model  = Constat
        fields = [
            'id', 'numero', 'description', 'lieu', 'gravite', 'statut',
            'template', 'template_nom', 'valeurs_custom',
            'observateur', 'observateur_nom',
            'valide_par', 'valide_par_nom',
            'commentaire_validation', 'date_validation',
            'fnc', 'fnc_numero', 'date_creation',
        ]

    def get_observateur_nom(self, obj):
        if obj.observateur:
            return obj.observateur.get_full_name() or obj.observateur.username
        return ''

    def get_valide_par_nom(self, obj):
        if obj.valide_par:
            return obj.valide_par.get_full_name() or obj.valide_par.username
        return ''