from django.db import models
from django.contrib.auth.models import User
import uuid


PROCESSUS_CHOICES = [
    ('achats',          'Achats'),
    ('bureau_etudes',   "Bureau d'études"),
    ('qualite',         'Qualité'),
    ('methodes',        'Méthodes'),
    ('production',      'Production'),
    ('soudage',         'Cellule soudage'),
    ('sous_traitance',  'Sous-Traitance'),
    ('charge_affaires', "Chargé d'affaires"),
    ('fournisseur',     'Fournisseur'),
]

STATUT_FNC = [
    ('brouillon',        'Brouillon'),
    ('ouverte',          'Ouverte'),
    ('en_cours_analyse', "En cours d'analyse"),
    ('en_cours_traitement', 'En cours de traitement'),
    ('en_attente',       'En attente vérification'),
    ('cloturee',         'Clôturée'),
    ('annulee',          'Annulée'),
]

GRAVITE_CHOICES = [
    ('mineure',  'Mineure'),
    ('majeure',  'Majeure'),
    ('critique', 'Critique'),
]

ORIGINE_ECART = [
    ('interne',     'Interne'),
    ('fournisseur', 'Fournisseur / S-T'),
    ('client',      'Client'),
    ('conception',  'Conception'),
]

TYPE_NC = [
    ('produit',   'Produit'),
    ('securite',  'Sécurité'),
    ('document',  'Documentation'),
    ('systeme',   'Système'),
]

RECLAMATION_CLIENT = [
    ('oui', 'Oui'),
    ('non', 'Non'),
]

STATUT_ACTION = [
    ('en_cours',  'En cours'),
    ('realisee',  'Réalisée'),
    ('en_retard', 'En retard'),
    ('annulee',   'Annulée'),
]

TYPE_ACTION = [
    ('corrective', 'Corrective'),
    ('curative',   'Curative'),
    ('preventive', 'Préventive'),
]

CATEGORIE_5M = [
    ('main_oeuvre', "Main-d'œuvre"),
    ('matiere',     'Matière'),
    ('methode',     'Méthode'),
    ('milieu',      'Milieu'),
    ('machine',     'Machine'),
]

STATUT_5M = [
    ('ouvert', 'Ouvert'),
    ('traite', 'Traité'),
    ('clos',   'Clos'),
]

class ServiceProcessus(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom         = models.CharField(max_length=100)
    code        = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.CharField(max_length=200, blank=True)
    actif       = models.BooleanField(default=True)
    ordre       = models.IntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qms_services_processus'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom


class ClassificationFNC(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom         = models.CharField(max_length=100)
    code        = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.CharField(max_length=200, blank=True)
    actif       = models.BooleanField(default=True)
    ordre       = models.IntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qms_classifications_fnc'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom


class OrigineEcart(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom         = models.CharField(max_length=100)
    code        = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.CharField(max_length=200, blank=True)
    actif       = models.BooleanField(default=True)
    ordre       = models.IntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qms_origines_ecart'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom


class StatutFNC(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom             = models.CharField(max_length=100)
    code            = models.SlugField(max_length=100, unique=True, blank=True)
    description     = models.CharField(max_length=200, blank=True)
    actif           = models.BooleanField(default=True)
    ordre           = models.IntegerField(default=0)
    est_final       = models.BooleanField(default=False, verbose_name="Statut final (ex: Clôturée)")
    est_annulation  = models.BooleanField(default=False, verbose_name="Statut d'annulation")
    couleur         = models.CharField(max_length=7, default='#6B7280', verbose_name="Couleur hex (#RRGGBB)")
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qms_statuts_fnc'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom
    
    
class NonConformite(models.Model):
    # Colonnes existantes dans PostgreSQL
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TYPE_FNC_CHOICES = [
    ('nc_produit',   'NC Produit'),
    ('nc_processus', 'NC Processus'),
    ('nc_systeme',   'NC Système'),
                        ]
    entreprise_tenant = models.ForeignKey('tenants.Entreprise', on_delete=models.CASCADE, null=True, blank=True, db_column='entreprise_tenant_id',related_name='non_conformites')
    site              = models.ForeignKey('tenants.Site', on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='non_conformites', verbose_name="Site")
    numero            = models.CharField(max_length=50, unique=True, verbose_name="N°")
    type_fnc = models.CharField(
    max_length=20,
    choices=TYPE_FNC_CHOICES,
    default='nc_produit',
    verbose_name="Type de non-conformité"
        )   
    description       = models.TextField(verbose_name="Description NC")
    gravite           = models.CharField(max_length=20, choices=GRAVITE_CHOICES, verbose_name="Gravité")
    statut_ref          = models.ForeignKey('StatutFNC', on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='fncs')
    date_decouverte   = models.DateTimeField(verbose_name="Date de découverte")
    date_prevue       = models.DateTimeField(null=True, blank=True, verbose_name="Date prévue")
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)
    notes              = models.TextField(blank=True)
    
    # Colonnes ajoutées via SQL
    libelle             = models.CharField(max_length=255, blank=True, verbose_name="Libellé de l'écart")
    type_nc             = models.CharField(max_length=30, choices=TYPE_NC, blank=True)
    origine_ecart_ref   = models.ForeignKey('OrigineEcart', on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='fncs')
    classification_ref  = models.ForeignKey('ClassificationFNC', on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='fncs')
    processus_ref       = models.ForeignKey('ServiceProcessus', on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='fncs')
    type_piece          = models.CharField(max_length=100, blank=True)
    qte_nc              = models.IntegerField(null=True, blank=True)
    qte_totale          = models.IntegerField(null=True, blank=True)
    numero_of           = models.CharField(max_length=50, blank=True)
    document_reference  = models.CharField(max_length=100, blank=True)
    client              = models.CharField(max_length=100, blank=True)
    fournisseur         = models.CharField(max_length=100, blank=True)
    reclamation_client  = models.CharField(max_length=5, choices=RECLAMATION_CLIENT, blank=True)
    avis_client_requis  = models.CharField(max_length=5, choices=RECLAMATION_CLIENT, blank=True)
    origine_cause       = models.CharField(max_length=100, blank=True)
    score_gravite       = models.FloatField(null=True, blank=True)
    score_detection     = models.FloatField(null=True, blank=True)
    score_impact        = models.FloatField(null=True, blank=True)
    criticite           = models.FloatField(null=True, blank=True)
    impact_surete       = models.BooleanField(default=False)
    eip                 = models.CharField(max_length=50, blank=True)
    redacteur           = models.ForeignKey(
                            User, on_delete=models.PROTECT,
                            null=True, blank=True,
                            db_column='redacteur_id',
                            related_name='fnc_redigees')
 # Workflow
    responsable_user = models.ForeignKey(
                        User, on_delete=models.SET_NULL,
                        null=True, blank=True,
                        db_column='responsable_user_id',
                        related_name='fnc_responsable')
    verificateur     = models.ForeignKey(
                        User, on_delete=models.SET_NULL,
                        null=True, blank=True,
                        related_name='fnc_verificateur')

    # Dates enrichies
    date_echeance    = models.DateField(null=True, blank=True)
    date_traitement  = models.DateField(null=True, blank=True)
    date_cloture     = models.DateField(null=True, blank=True)

    # Traitement
    action_immediate     = models.TextField(blank=True)
    decision             = models.CharField(max_length=20, blank=True, choices=[
        ('attente',      'En attente'),
        ('retouche',     'Retouche'),
        ('rebut',        'Rebut'),
        ('acceptation',  'Acceptation dérogation'),
        ('retour_fourn', 'Retour fournisseur'),
    ])
    cout_non_qualite     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Clôture
    efficacite_verifiee  = models.BooleanField(default=False)
    commentaire_cloture  = models.TextField(blank=True)
    
     # Liens automatiques
    capa_generee       = models.BooleanField(default=False)
    
    # Analyse causes
    cause_racine       = models.TextField(blank=True)
    methode_analyse    = models.CharField(max_length=50, blank=True, default='5M')


    
    class Meta:
        db_table = 'non_conformites'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.numero} — {self.libelle}"

    def save(self, *args, **kwargs):
        if not self.numero:
            try:
                params = ParametresEntreprise.get_pour_entreprise(self.entreprise_tenant)
                if self.site:
                    self.numero = self.site.generer_numero_fnc(params)
                else:
                    # Pas de site renseigné (cas limite) : fallback daté, à éviter en usage normal
                    from datetime import date
                    year  = date.today().year
                    count = NonConformite.objects.filter(created_at__year=year).count() + 1
                    self.numero = f"{params.prefixe}-{year}-{count:04d}"
            except Exception:
                from datetime import date
                year  = date.today().year
                count = NonConformite.objects.filter(created_at__year=year).count() + 1
                self.numero = f"NC-{year}-{count:04d}"
        if self.score_gravite and self.score_detection and self.score_impact:
            self.criticite = round(
                self.score_gravite * self.score_detection * self.score_impact, 2
            )
        super().save(*args, **kwargs)

    @property
    def est_en_retard(self):
        from datetime import date
        if not self.date_echeance:
            return False
        if self.statut_ref and (self.statut_ref.est_final or self.statut_ref.est_annulation):
            return False
        return self.date_echeance < date.today()

    @property
    def delai_resolution_jours(self):
        if self.date_cloture and self.date_decouverte:
            return (self.date_cloture - self.date_decouverte.date()).days
        return None


# la classe PieceJointeFNC:
class PieceJointeFNC(models.Model):
    TYPE_CHOICES = [
        ('photo',    'Photo du défaut'),
        ('document', 'Document'),
        ('rapport',  'Rapport'),
        ('autre',    'Autre'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fnc          = models.ForeignKey(NonConformite, on_delete=models.CASCADE,
                     related_name='pieces_jointes')
    nom_fichier  = models.CharField(max_length=255)
    type_fichier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='photo')
    fichier      = models.FileField(upload_to='qms/fnc/attachments/')
    taille       = models.IntegerField(default=0)
    uploaded_at  = models.DateTimeField(auto_now_add=True)
    uploaded_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'qms_pieces_jointes_fnc'

    def __str__(self):
        return self.nom_fichier

class PieceJointeAnalyse5M(models.Model):
    TYPE_CHOICES = [
        ('photo',    'Photo'),
        ('document', 'Document'),
        ('rapport',  'Rapport'),
        ('autre',    'Autre'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analyse      = models.ForeignKey('Analyse5M', on_delete=models.CASCADE,
                     related_name='pieces_jointes')
    nom_fichier  = models.CharField(max_length=255)
    type_fichier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='document')
    fichier      = models.FileField(upload_to='qms/analyse5m/attachments/')
    taille       = models.IntegerField(default=0)
    uploaded_at  = models.DateTimeField(auto_now_add=True)
    uploaded_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'qms_pieces_jointes_analyse5m'

    def __str__(self):
        return self.nom_fichier


class PieceJointeAction(models.Model):
    TYPE_CHOICES = [
        ('photo',    'Photo'),
        ('document', 'Document'),
        ('rapport',  'Rapport'),
        ('autre',    'Autre'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action       = models.ForeignKey('ActionCorrective', on_delete=models.CASCADE,
                     related_name='pieces_jointes')
    nom_fichier  = models.CharField(max_length=255)
    type_fichier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='document')
    fichier      = models.FileField(upload_to='qms/actions/attachments/')
    taille       = models.IntegerField(default=0)
    uploaded_at  = models.DateTimeField(auto_now_add=True)
    uploaded_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'qms_pieces_jointes_action'

    def __str__(self):
        return self.nom_fichier


class CommentaireFNC(models.Model):
    TYPE_CHOICES = [
        ('commentaire',  'Commentaire'),
        ('action',       'Action réalisée'),
        ('verification', 'Vérification'),
        ('cloture',      'Clôture'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fnc          = models.ForeignKey(NonConformite, on_delete=models.CASCADE,
                     related_name='commentaires')
    auteur       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    contenu      = models.TextField()
    type_comment = models.CharField(max_length=20, choices=TYPE_CHOICES, default='commentaire')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qms_commentaires_fnc'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.fnc.numero} — {self.auteur}"

class Analyse5M(models.Model):
    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise        = models.ForeignKey('tenants.Entreprise', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    site                  = models.ForeignKey('tenants.Site', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reference             = models.CharField(max_length=50, unique=True)
    fnc                   = models.ForeignKey(NonConformite, on_delete=models.CASCADE, related_name='analyses_5m')
    categorie             = models.CharField(max_length=20, choices=CATEGORIE_5M)
    cause_analysee        = models.TextField()
    cause_racine          = models.CharField(max_length=100, blank=True)
    processus_responsable = models.CharField(max_length=30, choices=PROCESSUS_CHOICES, blank=True)
    commentaire           = models.TextField(blank=True)
    date_analyse          = models.DateField(null=True, blank=True)
    statut                = models.CharField(max_length=20, choices=STATUT_5M, default='ouvert')
    created_at            = models.DateTimeField(auto_now_add=True)
    # ── Méthode des 5 Pourquoi ────────────────────────────────────────────
    pourquoi_1 = models.TextField(blank=True, verbose_name="Pourquoi 1")
    pourquoi_2 = models.TextField(blank=True, verbose_name="Pourquoi 2")
    pourquoi_3 = models.TextField(blank=True, verbose_name="Pourquoi 3")
    pourquoi_4 = models.TextField(blank=True, verbose_name="Pourquoi 4")
    pourquoi_5 = models.TextField(blank=True, verbose_name="Pourquoi 5 — Cause racine reelle")

    # ── Scoring (1 à 5) ───────────────────────────────────────────────────
    frequence     = models.IntegerField(default=1, verbose_name="Frequence (1-5)")
    detectabilite = models.IntegerField(default=1, verbose_name="Detectabilite (1-5)")
    gravite_cause = models.IntegerField(default=1, verbose_name="Gravite cause (1-5)")

    # ── Responsable et dates ──────────────────────────────────────────────
    responsable_analyse = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analyses_5m_responsable',
        verbose_name="Responsable de l'analyse"
    )
    date_cloture_prevue = models.DateField(null=True, blank=True,
        verbose_name="Date de cloture prevue")

    # ── Validation ────────────────────────────────────────────────────────
    efficacite_verifiee = models.BooleanField(default=False,
        verbose_name="Efficacite verifiee apres traitement")
    date_verification   = models.DateField(null=True, blank=True,
        verbose_name="Date de verification")

    @property
    def criticite_cause(self):
        return self.frequence * self.detectabilite * self.gravite_cause

    class Meta:
        db_table = 'qms_analyse_5m'
        ordering = ['categorie']

    def __str__(self):
        return f"{self.reference} — {self.get_categorie_display()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from datetime import date
            year  = date.today().year
            count = Analyse5M.objects.filter(created_at__year=year).count() + 1
            self.reference = f"5M-{year}-{count:04d}"
        super().save(*args, **kwargs)


class ActionCorrective(models.Model):
    SOURCE_TYPE = [
        ('fnc',        'Non-Conformité'),
        ('audit',      'Audit'),
        ('capa',       'CAPA'),
        ('standalone', 'Standalone'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise   = models.ForeignKey('tenants.Entreprise', on_delete=models.CASCADE,
                     null=True, blank=True, related_name='+')
    site         = models.ForeignKey('tenants.Site', on_delete=models.SET_NULL,
                     null=True, blank=True, related_name='+')
    reference    = models.CharField(max_length=50, unique=True)

    # Source de déclenchement
    source_type  = models.CharField(max_length=20, choices=SOURCE_TYPE, default='fnc')
    fnc          = models.ForeignKey(NonConformite, on_delete=models.CASCADE,
                     null=True, blank=True, related_name='actions')
    audit_ref    = models.ForeignKey('Audit', on_delete=models.SET_NULL,
                     null=True, blank=True, related_name='actions')
    capa_ref     = models.ForeignKey('CAPA', on_delete=models.SET_NULL,
                     null=True, blank=True, related_name='actions')

    # Description
    description  = models.TextField()
    type_action  = models.CharField(max_length=20, choices=TYPE_ACTION)
    processus_ref = models.ForeignKey('ServiceProcessus', on_delete=models.SET_NULL,
                     null=True, blank=True, related_name='actions',
                     verbose_name="Processus")

    # Responsable & délai
    responsable      = models.ForeignKey(User, on_delete=models.PROTECT,
                         related_name='actions_responsable')
    date_echeance    = models.DateField()
    date_cloture     = models.DateField(null=True, blank=True)

    # Résultat
    resultat         = models.TextField(blank=True)
    statut           = models.CharField(max_length=20, choices=STATUT_ACTION, default='en_cours')

    # Coûts
    heures_investies = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    cout_materiel    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cout_estime      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Lien cause 5M
    ref_cause        = models.ForeignKey('Analyse5M', on_delete=models.SET_NULL,
                         null=True, blank=True, related_name='actions')

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'qms_actions_correctives'
        ordering = ['date_echeance']

    def __str__(self):
        return f"{self.reference} — {self.description[:50]}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from datetime import date
            year  = date.today().year
            count = ActionCorrective.objects.filter(created_at__year=year).count() + 1
            self.reference = f"ACT-{year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def est_en_retard(self):
        from datetime import date
        return self.statut == 'en_cours' and self.date_echeance < date.today()
    
    

class CAPA(models.Model):
    STATUT_CHOICES = [
        ('ouvert',      'Ouvert'),
        ('en_cours',    'En cours'),
        ('verification','En vérification'),
        ('clos',        'Clos'),
        ('annule',      'Annulé'),
    ]
    TYPE_CHOICES = [
        ('corrective',  'Corrective'),
        ('preventive',  'Préventive'),
        ('mixte',       'Mixte (CA+PA)'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise        = models.ForeignKey('tenants.Entreprise', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    site              = models.ForeignKey('tenants.Site', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reference        = models.CharField(max_length=20, unique=True, blank=True)
    fnc              = models.ForeignKey(NonConformite, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas')
    type_capa        = models.CharField(max_length=20, choices=TYPE_CHOICES, default='mixte')
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ouvert')
    
    # Étape 1 — Identification
    titre            = models.CharField(max_length=200)
    description      = models.TextField()
    date_detection   = models.DateField()
    detecte_par      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_detectees')
    
    # Étape 2 — Confinement
    action_confinement = models.TextField(blank=True)
    date_confinement   = models.DateField(null=True, blank=True)
    
    # Étape 3 — Analyse causes (liée aux Analyse5M)
    description_cause  = models.TextField(blank=True)
    cause_racine       = models.TextField(blank=True)
    
    # Étape 4+5 — Actions (liées aux ActionCorrective)
    description_action_corrective  = models.TextField(blank=True)
    description_action_preventive  = models.TextField(blank=True)
    
    # Étape 6 — Mise en œuvre
    responsable      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_responsable')
    date_echeance    = models.DateField(null=True, blank=True)
    
    # Étape 7 — Vérification efficacité
    verification_efficacite = models.TextField(blank=True)
    date_verification       = models.DateField(null=True, blank=True)
    verificateur     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_verification')
    resultat_verification = models.CharField(max_length=20, choices=[
        ('efficace',     'Efficace'),
        ('non_efficace', 'Non efficace'),
        ('en_attente',   'En attente'),
    ], blank=True)
    
    # Étape 8 — Clôture
    date_cloture     = models.DateField(null=True, blank=True)
    validateur       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_validees')
    commentaire_cloture = models.TextField(blank=True)
    
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'qms_capa'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            year = self.created_at.year if self.created_at else __import__('datetime').date.today().year
            last = CAPA.objects.filter(reference__startswith=f'CAPA-{year}-').count()
            self.reference = f'CAPA-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference   




class Audit(models.Model):
    TYPE_CHOICES = [
        ('interne',     'Audit interne'),
        ('fournisseur', 'Audit fournisseur'),
    ]
    STATUT_CHOICES = [
        ('planifie',   'Planifié'),
        ('en_cours',   'En cours'),
        ('realise',    'Réalisé'),
        ('clos',       'Clos'),
        ('annule',     'Annulé'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise        = models.ForeignKey('tenants.Entreprise', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    site              = models.ForeignKey('tenants.Site', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reference        = models.CharField(max_length=20, unique=True, blank=True)
    type_audit       = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifie')
    titre            = models.CharField(max_length=200)
    objectif         = models.TextField(blank=True)

    # Planification
    date_prevue      = models.DateField()
    date_realisation = models.DateField(null=True, blank=True)
    auditeur         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audits_conduits')
    audite           = models.CharField(max_length=200, blank=True)  # service ou fournisseur audité
    processus = models.CharField(max_length=50, choices=PROCESSUS_CHOICES, blank=True)

    # Résultat
    conclusion       = models.TextField(blank=True)
    nb_ecarts_majeurs  = models.IntegerField(default=0)
    nb_ecarts_mineurs  = models.IntegerField(default=0)
    nb_points_forts    = models.IntegerField(default=0)
    resultat         = models.CharField(max_length=20, choices=[
        ('satisfaisant',     'Satisfaisant'),
        ('a_ameliorer',      'À améliorer'),
        ('non_satisfaisant', 'Non satisfaisant'),
    ], blank=True)

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'qms_audits'
        ordering = ['-date_prevue']

    def save(self, *args, **kwargs):
        if not self.reference:
            year = __import__('datetime').date.today().year
            last = Audit.objects.filter(reference__startswith=f'AUD-{year}-').count()
            self.reference = f'AUD-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


class LigneChecklist(models.Model):
    CATEGORIE_CHOICES = [
        ('documentation',  'Documentation'),
        ('processus',      'Processus'),
        ('competences',    'Compétences'),
        ('infrastructure', 'Infrastructure'),
        ('mesure',         'Mesure et surveillance'),
        ('amelioration',   'Amélioration'),
        ('libre',          'Point libre'),
    ]
    RESULTAT_CHOICES = [
        ('conforme',        'Conforme'),
        ('ecart_mineur',    'Écart mineur'),
        ('ecart_majeur',    'Écart majeur'),
        ('non_applicable',  'Non applicable'),
        ('point_fort',      'Point fort'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit       = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='checklist')
    categorie   = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='libre')
    question    = models.TextField()
    reference_iso = models.CharField(max_length=20, blank=True)  # ex: 8.5.1
    resultat    = models.CharField(max_length=20, choices=RESULTAT_CHOICES, blank=True)
    commentaire = models.TextField(blank=True)
    ordre       = models.IntegerField(default=0)

    class Meta:
        db_table = 'qms_audit_checklist'
        ordering = ['ordre']

    def __str__(self):
        return f"{self.audit.reference} - {self.question[:50]}"


class EcartAudit(models.Model):
    GRAVITE_CHOICES = [
        ('mineur', 'Écart mineur'),
        ('majeur', 'Écart majeur'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit       = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='ecarts')
    reference   = models.CharField(max_length=20, blank=True)
    gravite     = models.CharField(max_length=10, choices=GRAVITE_CHOICES)
    description = models.TextField()
    exigence_iso = models.CharField(max_length=20, blank=True)  # ex: 8.5.1
    processus   = models.CharField(max_length=50, blank=True)
    delai_correction = models.DateField(null=True, blank=True)
    fnc         = models.ForeignKey(NonConformite, on_delete=models.SET_NULL, null=True, blank=True, related_name='ecarts_audit')
    capa        = models.ForeignKey(CAPA, on_delete=models.SET_NULL, null=True, blank=True, related_name='ecarts_audit')
    statut      = models.CharField(max_length=20, choices=[
        ('ouvert',  'Ouvert'),
        ('en_cours','En cours'),
        ('clos',    'Clos'),
    ], default='ouvert')

    class Meta:
        db_table = 'qms_audit_ecarts'
        ordering = ['-gravite']

    def save(self, *args, **kwargs):
        if not self.reference:
            last = EcartAudit.objects.filter(audit=self.audit).count()
            self.reference = f'{self.audit.reference}-E{str(last + 1).zfill(2)}'
        super().save(*args, **kwargs)
        
        
        
class PlanAction(models.Model):
    TYPE_CHOICES = [
        ('action',    'Action'),
        ('document',  'Document à produire'),
        ('formation', 'Formation'),
        ('audit',     'Audit interne'),
        ('mesure',    'Mesure / Indicateur'),
    ]
    STATUT_CHOICES = [
        ('todo',      'À faire'),
        ('en_cours',  'En cours'),
        ('realise',   'Réalisé'),
        ('verifie',   'Vérifié'),
        ('clos',      'Clos'),
        ('annule',    'Annulé'),
    ]
    PRIORITE_CHOICES = [
        ('faible',    'Faible'),
        ('normale',   'Normale'),
        ('haute',     'Haute'),
        ('critique',  'Critique'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise        = models.ForeignKey('tenants.Entreprise', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    site              = models.ForeignKey('tenants.Site', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reference    = models.CharField(max_length=20, unique=True, blank=True)
    titre        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    type_action  = models.CharField(max_length=20, choices=TYPE_CHOICES, default='action')
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default='todo')
    priorite     = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='normale')

    # Personnes
    realisateur  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_a_realiser')
    verificateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_a_verifier')
    createur     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_creees')

    # Dates
    date_prevue      = models.DateField(null=True, blank=True)
    date_realisation = models.DateField(null=True, blank=True)
    date_verification= models.DateField(null=True, blank=True)

    # Commentaires
    commentaire_realisation  = models.TextField(blank=True)
    commentaire_verification = models.TextField(blank=True)

    # Liens QMS
    fnc   = models.ForeignKey('NonConformite', on_delete=models.SET_NULL, null=True, blank=True, related_name='plan_actions')
    capa  = models.ForeignKey('CAPA',          on_delete=models.SET_NULL, null=True, blank=True, related_name='plan_actions')
    audit = models.ForeignKey('Audit',         on_delete=models.SET_NULL, null=True, blank=True, related_name='plan_actions')


    # Lien Risques
    risque = models.ForeignKey('risks.Risque', on_delete=models.SET_NULL, null=True, blank=True, related_name='plan_actions')

    processus    = models.CharField(max_length=50, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'qms_plan_actions'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = PlanAction.objects.filter(reference__startswith=f'PA-{year}-').count()
            self.reference = f'PA-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.titre}"

    @property
    def est_en_retard(self):
        import datetime
        if self.date_prevue and self.statut not in ['clos', 'annule', 'verifie']:
            return self.date_prevue < datetime.date.today()
        return False
    
class ParametresEntreprise(models.Model):
    SEPARATEUR_CHOICES = [
        ('-', 'Tiret  ( - )'),
        ('/', 'Slash  ( / )'),
        ('.', 'Point  ( . )'),
        ('_', 'Underscore  ( _ )'),
    ]
    REMISE_ZERO_CHOICES = [
        ('jamais',   'Jamais'),
        ('annuel',   'Chaque année'),
        ('mensuel',  'Chaque mois'),
    ]

    # ── Portée ────────────────────────────────────────────────────────────
    entreprise          = models.OneToOneField('tenants.Entreprise', on_delete=models.CASCADE,
                             related_name='parametres_qms', null=True, blank=True)

    # ── Numérotation FNC (format commun à l'entreprise) ─────────────────────
    # Le compteur lui-même est propre à chaque site (voir Site.compteur_fnc_actuel) ;
    # ces champs ne définissent QUE le format du numéro.
    prefixe            = models.CharField(max_length=10, default='NC')
    utiliser_annee     = models.BooleanField(default=True)
    utiliser_mois      = models.BooleanField(default=False)
    inclure_code_site  = models.BooleanField(default=True, verbose_name="Inclure le code du site dans le numéro",
                            help_text="Ex: NC-LYON-2026-06-0001. Recommandé en multi-site pour identifier "
                                      "l'origine d'une FNC directement depuis son numéro.")
    separateur         = models.CharField(max_length=2, choices=SEPARATEUR_CHOICES, default='-')
    longueur_compteur  = models.IntegerField(default=4)
    remise_a_zero      = models.CharField(max_length=10, choices=REMISE_ZERO_CHOICES, default='annuel')

    # ── Informations entreprise ───────────────────────────────────────────
    nom_entreprise     = models.CharField(max_length=200, default='ERP Industriel')
    logo               = models.ImageField(upload_to='qms/logo/', null=True, blank=True)
    adresse            = models.TextField(blank=True)
    telephone          = models.CharField(max_length=30, blank=True)
    email_contact      = models.EmailField(blank=True)
    site_web           = models.URLField(blank=True)

    # ── Export documents ──────────────────────────────────────────────────
    reference_doc      = models.CharField(max_length=50, default='QMS-FNC-01')
    version_doc        = models.CharField(max_length=20, default='V1.0')
    pied_de_page       = models.CharField(max_length=200, blank=True)
    afficher_nom_pied        = models.BooleanField(default=True, verbose_name="Afficher le nom entreprise en pied de page")
    afficher_adresse_pied    = models.BooleanField(default=True, verbose_name="Afficher l'adresse en pied de page")
    afficher_reference_pied  = models.BooleanField(default=True, verbose_name="Afficher reference/version en pied de page")
    afficher_date_pied       = models.BooleanField(default=True, verbose_name="Afficher la date de generation en pied de page")
    afficher_confidentiel    = models.BooleanField(default=True, verbose_name="Afficher la mention CONFIDENTIEL")

    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'qms_parametres_entreprise'

    def __str__(self):
        return self.nom_entreprise

    @classmethod
    def get_pour_entreprise(cls, entreprise):
        """Retourne (en le créant si besoin) les paramètres de CETTE entreprise."""
        obj, _ = cls.objects.get_or_create(
            entreprise=entreprise,
            defaults={'nom_entreprise': entreprise.nom},
        )
        return obj
    
    
class SectionFNC(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom         = models.CharField(max_length=100, verbose_name="Nom de la section")
    code        = models.SlugField(max_length=100, unique=True, verbose_name="Code technique")
    icone       = models.CharField(max_length=20, default='custom')
    ordre       = models.IntegerField(default=0)
    actif       = models.BooleanField(default=True)
    est_systeme = models.BooleanField(default=False, verbose_name="Section système (non supprimable)")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qms_sections_fnc'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom
    
        
class ChampPersonnalise(models.Model):
    TYPE_CHOICES = [
        ('text',     'Texte court'),
        ('textarea', 'Texte long'),
        ('number',   'Nombre'),
        ('date',     'Date'),
        ('boolean',  'Oui / Non'),
        ('choix',    'Liste de choix'),
    ]
    SOURCE_CHOICES = [
        ('manuel', 'Liste manuelle'),
        ('client', 'Clients (CRM)'),
        ('fournisseur', 'Fournisseurs (Achats)'),
        ('user', 'Utilisateurs'),
    ]
    ORIGINE_CHOICES = [
        ('modele', 'Champ du modèle FNC'),
        ('custom', 'Champ personnalisé'),
    ]
    TYPE_RENDU_CHOICES = [
        ('texte',           'Texte simple'),
        ('texte_long',      'Bloc de texte long'),
        ('date',             'Date'),
        ('booleen',          'Oui / Non'),
        ('choix',            'Liste de choix'),
        ('tableau_actions',  'Tableau des actions correctives'),
        ('bloc_signature',   'Bloc signatures'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom              = models.CharField(max_length=100, verbose_name="Nom du champ")
    cle              = models.SlugField(max_length=100, unique=True, verbose_name="Clé unique")
    type_champ       = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')
    obligatoire      = models.BooleanField(default=False)
    actif            = models.BooleanField(default=True)
    ordre            = models.IntegerField(default=0)
    options          = models.JSONField(null=True, blank=True, verbose_name="Options (mode manuel)")
    source_dynamique = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manuel',
                          verbose_name="Source de la liste (mode choix)")
    section          = models.ForeignKey('SectionFNC', on_delete=models.CASCADE, related_name='champs',
                          null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    origine          = models.CharField(max_length=10, choices=ORIGINE_CHOICES, default='custom',
                          verbose_name="Origine du champ")
    cle_modele       = models.CharField(max_length=100, blank=True, null=True,
                          verbose_name="Attribut du modèle NonConformite (si origine=modele)")
    type_rendu       = models.CharField(max_length=20, choices=TYPE_RENDU_CHOICES, default='texte',
                          verbose_name="Type de rendu PDF/Word")
    largeur_rendu    = models.CharField(max_length=10, default='pleine',
                          choices=[('pleine', 'Pleine largeur'), ('moitie', 'Demi largeur')],
                          verbose_name="Largeur d'affichage")
    hauteur_bloc     = models.IntegerField(null=True, blank=True,
                          verbose_name="Hauteur du bloc en mm (texte_long uniquement)")
    source_referentiel = models.CharField(
        max_length=30, blank=True, null=True,
        choices=[
            ('processus',      'Processus'),
            ('classifications', 'Classifications'),
            ('origines',        'Origines écart'),
            ('statuts',         'Statuts FNC'),
        ],
        verbose_name="Source référentiel (si type choix depuis table référentielle)"
    )
    est_obligatoire_systeme = models.BooleanField(
        default=False,
        help_text="Si True, ce champ est toujours visible, même avec un template"
    )
    config_colonnes    = models.JSONField(null=True, blank=True,
                          verbose_name="Colonnes actives (tableau_actions uniquement)")
    config_signataires = models.JSONField(null=True, blank=True,
                          verbose_name="Signataires configures (bloc_signature uniquement)")
    
    class Meta:
        db_table = 'qms_champs_personnalises'
        ordering = ['section__ordre', 'ordre', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.type_champ})"

    def get_choix(self):
        """Retourne la liste des choix disponibles, selon la source configurée."""

        # ── Cas spéciaux : champs FK/choices fixes du modèle NonConformite ──
        if self.cle_modele == 'gravite':
            return [
                {'valeur': 'mineure',  'libelle': 'Mineure'},
                {'valeur': 'majeure',  'libelle': 'Majeure'},
                {'valeur': 'critique', 'libelle': 'Critique'},
            ]
        if self.cle_modele == 'type_nc':
            return [
                {'valeur': 'produit',  'libelle': 'Produit'},
                {'valeur': 'securite', 'libelle': 'Sécurité'},
                {'valeur': 'document', 'libelle': 'Documentation'},
                {'valeur': 'systeme',  'libelle': 'Système'},
            ]

        # ── Référentiels depuis les tables de référence ──
        if self.source_referentiel:
            if self.source_referentiel == 'processus':
                return [{'valeur': o.code, 'libelle': o.nom}
                        for o in ServiceProcessus.objects.filter(actif=True).order_by('ordre', 'nom')]
            if self.source_referentiel == 'classifications':
                return [{'valeur': o.code, 'libelle': o.nom}
                        for o in ClassificationFNC.objects.filter(actif=True).order_by('ordre', 'nom')]
            if self.source_referentiel == 'origines':
                return [{'valeur': o.code, 'libelle': o.nom}
                        for o in OrigineEcart.objects.filter(actif=True).order_by('ordre', 'nom')]
            if self.source_referentiel == 'statuts':
                return [{'valeur': o.code, 'libelle': o.nom}
                        for o in StatutFNC.objects.filter(actif=True).order_by('ordre', 'nom')]

        # ── Sources dynamiques ──
        if self.source_dynamique == 'user':
            return [
                {'valeur': str(u.id), 'libelle': u.get_full_name() or u.username}
                for u in User.objects.filter(is_active=True).order_by('first_name', 'last_name')
            ]
        if self.source_dynamique == 'client':
            from crm.models import Client
            return [{'valeur': str(c.id), 'libelle': c.raison_sociale}
                    for c in Client.objects.filter(actif=True).order_by('raison_sociale')]
        if self.source_dynamique == 'fournisseur':
            from achats.models import Fournisseur
            return [{'valeur': str(f.id), 'libelle': f.raison_sociale}
                    for f in Fournisseur.objects.filter(statut='actif').order_by('raison_sociale')]

        # ── Liste manuelle (options JSON) ──
        if self.type_champ == 'choix' and self.source_dynamique == 'manuel':
            return self.options or []

        # ── Fallback : lire les choices Django du modèle ──
        if self.cle_modele:
            try:
                from django.apps import apps
                model = apps.get_model('qms', 'NonConformite')
                field = model._meta.get_field(self.cle_modele)
                if hasattr(field, 'choices') and field.choices:
                    return [{'valeur': v, 'libelle': l} for v, l in field.choices]
            except Exception:
                pass

        return []

    def get_valeur_pour_fnc(self, fnc):
            if self.origine == 'modele':
                if not self.cle_modele:
                    return None

                # Pour les champs branchés sur un référentiel, lire la FK _ref
                if self.source_referentiel:
                    ref_field = f'{self.cle_modele}_ref'
                    ref_obj = getattr(fnc, ref_field, None)
                    return ref_obj.nom if ref_obj else None

                valeur = getattr(fnc, self.cle_modele, None)
                display_method = f'get_{self.cle_modele}_display'
                if hasattr(fnc, display_method):
                    return getattr(fnc, display_method)()
                if hasattr(valeur, 'get_full_name'):
                    return valeur.get_full_name() or str(valeur)
                return valeur
            else:
                v = self.valeurs.filter(fnc=fnc).first()
                if not v:
                    return None
                if self.type_champ == 'boolean':
                    return 'Oui' if v.valeur == 'true' else 'Non'
                return v.valeur
            
class ValeurChampFNC(models.Model):
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fnc     = models.ForeignKey(
                NonConformite, on_delete=models.CASCADE,
                related_name='valeurs_champs_custom'
              )
    champ   = models.ForeignKey(
                ChampPersonnalise, on_delete=models.CASCADE,
                related_name='valeurs'
              )
    valeur  = models.TextField(blank=True)

    class Meta:
        db_table = 'qms_valeurs_champs_fnc'
        unique_together = ['fnc', 'champ']

    def __str__(self):
        return f"{self.fnc.numero} — {self.champ.nom} : {self.valeur}"
    
    
class TemplateExportFNC(models.Model):
    FORMAT_CHOICES = [
        ('pdf',  'PDF'),
        ('word', 'Word'),
        ('both', 'PDF et Word'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom         = models.CharField(max_length=100, verbose_name="Nom du template")
    description = models.CharField(max_length=200, blank=True)
    format      = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='both')
    utilisateur = models.ForeignKey(
                    User, on_delete=models.CASCADE,
                    related_name='templates_export_fnc'
                  )
    # JSON contenant les sections et champs cochés
    # Exemple :
    # {
    #   "identification": {
    #     "actif": true,
    #     "champs": {
    #       "libelle": true,
    #       "redacteur": true,
    #       "date_decouverte": true,
    #       "responsable": false,
    #       "date_echeance": true
    #     }
    #   },
    #   "classification": { "actif": true, "champs": {...} },
    #   ...
    # }
    configuration = models.JSONField(default=dict)
    is_default    = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'qms_templates_export_fnc'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.utilisateur.username})"

    def save(self, *args, **kwargs):
        # Si ce template est défini par défaut, enlever le défaut des autres
        if self.is_default:
            TemplateExportFNC.objects.filter(
                utilisateur=self.utilisateur,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class TemplateFormulaireFNC(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom         = models.CharField(max_length=100, verbose_name="Nom du formulaire")
    description = models.CharField(max_length=200, blank=True)
    utilisateur = models.ForeignKey(
                    User, on_delete=models.CASCADE,
                    related_name='templates_formulaire_fnc'
                  )
    # JSON contenant les sections et champs actifs pour ce formulaire
    # Même structure que TemplateExportFNC.configuration :
    # { "identification": {"actif": true, "champs": {"fixe_libelle": true, ...}}, ... }
    configuration = models.JSONField(default=dict)
    is_default    = models.BooleanField(default=False)
    ordre         = models.IntegerField(default=0)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
    
    type_objet = models.CharField(
        max_length=20,
        choices=[
            ('nc_produit',   'NC Produit'),
            ('nc_processus', 'NC Processus'),
            ('nc_systeme',   'NC Système'),
            ('constat',      'Formulaire Constat'),
        ],
        default='nc_produit'
    )
    
    class Meta:
        db_table = 'qms_templates_formulaire_fnc'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.utilisateur.username})"

    def save(self, *args, **kwargs):
        if self.is_default:
            TemplateFormulaireFNC.objects.filter(
                utilisateur=self.utilisateur,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

class OptionListe(models.Model):
    TYPE_CHOICES = [
        ('cause_racine', 'Cause racine'),
        ('processus',    'Processus'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_liste = models.CharField(max_length=30, choices=TYPE_CHOICES)
    valeur     = models.CharField(max_length=100, verbose_name="Valeur technique")
    libelle    = models.CharField(max_length=150, verbose_name="Libellé affiché")
    ordre      = models.IntegerField(default=0)
    actif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qms_options_listes'
        ordering = ['type_liste', 'ordre', 'libelle']
        unique_together = ['type_liste', 'valeur']

    def __str__(self):
        return f"{self.get_type_liste_display()} — {self.libelle}"
    
class Constat(models.Model):
    STATUT_CHOICES = [
        ('ouvert',   'Ouvert'),
        ('valide',   'Validé'),
        ('rejete',   'Rejeté'),
        ('converti', 'Converti en FNC'),
        ('annule',   'Annulé'),
    ]
    GRAVITE_CHOICES = [
        ('faible', 'Faible'),
        ('moyen',  'Moyen'),
        ('eleve',  'Élevé'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero      = models.CharField(max_length=20, unique=True, blank=True)
    entreprise  = models.ForeignKey(
                    'tenants.Entreprise', on_delete=models.CASCADE,
                    related_name='constats', null=True, blank=True)

    # Champs fixes
    description = models.TextField()
    lieu        = models.CharField(max_length=200, blank=True)
    gravite     = models.CharField(max_length=10, choices=GRAVITE_CHOICES, default='faible')
    statut      = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ouvert')

    # Template utilisé pour la saisie
    template    = models.ForeignKey(
                    'TemplateFormulaireFNC', on_delete=models.SET_NULL,
                    null=True, blank=True, related_name='constats')

    # Champs custom (valeurs des champs configurés par l'admin)
    valeurs_custom = models.JSONField(default=dict, blank=True)

    # Observateur
    observateur = models.ForeignKey(
                    User, on_delete=models.SET_NULL, null=True,
                    related_name='constats_crees')

    # Validation RQ
    valide_par  = models.ForeignKey(
                    User, on_delete=models.SET_NULL, null=True, blank=True,
                    related_name='constats_valides')
    commentaire_validation = models.TextField(blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    # Lien FNC si converti
    fnc         = models.OneToOneField(
                    'NonConformite', on_delete=models.SET_NULL,
                    null=True, blank=True, related_name='constat_source')

    date_creation = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'qms_constats'
        ordering = ['-date_creation']

    def save(self, *args, **kwargs):
        if not self.numero:
            from datetime import date
            year  = date.today().year
            count = Constat.objects.filter(date_creation__year=year).count() + 1
            self.numero = f'CST-{year}-{count:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} — {self.description[:50]}"