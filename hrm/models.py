import uuid
from django.db import models
from django.contrib.auth.models import User


class Employe(models.Model):
    TYPE_CONTRAT_CHOICES = [
        ('cdi',          'CDI'),
        ('cdd',          'CDD'),
        ('interim',      'Intérim'),
        ('apprentissage','Apprentissage'),
        ('stage',        'Stage'),
    ]
    STATUT_CHOICES = [
        ('actif',    'Actif'),
        ('inactif',  'Inactif'),
        ('conge',    'En congé'),
        ('maladie',  'En maladie'),
    ]
    CATEGORIE_CHOICES = [
        ('bureau',  'Bureau'),
        ('atelier', 'Atelier'),
        ('cadre',   'Cadre'),
    ]
    EQUIPE_CHOICES = [
        ('journee', 'Journée (9h-17h)'),
        ('matin',   'Matin (6h-14h)'),
        ('aprem',   'Après-midi (14h-22h)'),
        ('nuit',    'Nuit (22h-6h)'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matricule        = models.CharField(max_length=20, unique=True, blank=True)
    user             = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employe')

    # Informations personnelles
    nom              = models.CharField(max_length=100)
    prenom           = models.CharField(max_length=100)
    date_naissance   = models.DateField(null=True, blank=True)
    lieu_naissance   = models.CharField(max_length=100, blank=True)
    nationalite      = models.CharField(max_length=50, blank=True)
    adresse          = models.TextField(blank=True)
    telephone        = models.CharField(max_length=20, blank=True)
    email            = models.EmailField(blank=True)
    contact_urgence  = models.CharField(max_length=200, blank=True)

    # Informations professionnelles
    poste            = models.CharField(max_length=100)
    departement      = models.CharField(max_length=100, blank=True)
    categorie        = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='atelier')
    equipe           = models.CharField(max_length=20, choices=EQUIPE_CHOICES, default='journee')
    type_contrat     = models.CharField(max_length=20, choices=TYPE_CONTRAT_CHOICES, default='cdi')
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    date_embauche    = models.DateField()
    date_fin_contrat = models.DateField(null=True, blank=True)
    date_fin_periode_essai = models.DateField(null=True, blank=True)
    salaire_base     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    manager          = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='equipe_manager')

    # Pointage RFID
    badge_rfid       = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Conges
    solde_cp         = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    solde_rtt        = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hrm_employes'
        ordering = ['nom', 'prenom']

    def save(self, *args, **kwargs):
        if not self.matricule:
            import datetime
            year = datetime.date.today().year
            last = Employe.objects.filter(matricule__startswith=f'EMP-{year}-').count()
            self.matricule = f'EMP-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def anciennete_annees(self):
        import datetime
        if self.date_embauche:
            delta = datetime.date.today() - self.date_embauche
            return round(delta.days / 365.25, 1)
        return 0

    @property
    def periode_essai_active(self):
        import datetime
        if self.date_fin_periode_essai:
            return self.date_fin_periode_essai >= datetime.date.today()
        return False

    def __str__(self):
        return f"{self.matricule} — {self.nom_complet}"


class Competence(models.Model):
    TYPE_CHOICES = [
        ('metier',       'Compétence métier'),
        ('habilitation', 'Habilitation'),
        ('caces',        'CACES'),
        ('securite',     'Sécurité'),
        ('qualite',      'Qualité'),
        ('informatique', 'Informatique'),
        ('langue',       'Langue'),
        ('autre',        'Autre'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom         = models.CharField(max_length=200)
    type_competence = models.CharField(max_length=20, choices=TYPE_CHOICES, default='metier')
    description = models.TextField(blank=True)
    duree_validite_mois = models.IntegerField(null=True, blank=True)  # null = illimitee
    obligatoire = models.BooleanField(default=False)

    class Meta:
        db_table = 'hrm_competences'
        ordering = ['type_competence', 'nom']

    def __str__(self):
        return self.nom


class EmployeCompetence(models.Model):
    STATUT_CHOICES = [
        ('valide',  'Valide'),
        ('expire',  'Expiré'),
        ('bientot', 'Bientôt expiré'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employe         = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='competences')
    competence      = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='employes')
    date_obtention  = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)
    organisme       = models.CharField(max_length=200, blank=True)
    numero_certificat = models.CharField(max_length=100, blank=True)
    notes           = models.TextField(blank=True)

    class Meta:
        db_table = 'hrm_employe_competences'
        ordering = ['-date_obtention']
        unique_together = ['employe', 'competence']

    @property
    def statut(self):
        import datetime
        if not self.date_expiration:
            return 'valide'
        today = datetime.date.today()
        delta = (self.date_expiration - today).days
        if delta < 0:
            return 'expire'
        if delta <= 60:
            return 'bientot'
        return 'valide'

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.competence.nom}"


class Pointage(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    SOURCE_CHOICES = [
        ('rfid',       'Badge RFID'),
        ('manuel',     'Manuel'),
        ('correction', 'Correction'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employe    = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='pointages')
    type_pointage = models.CharField(max_length=10, choices=TYPE_CHOICES)
    timestamp  = models.DateTimeField()
    source     = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='rfid')
    valide     = models.BooleanField(default=True)
    note       = models.CharField(max_length=200, blank=True)
    saisi_par  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pointages_saisis')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hrm_pointages'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.type_pointage} — {self.timestamp}"


class JourneeCalculee(models.Model):
    STATUT_CHOICES = [
        ('normal',    'Normal'),
        ('retard',    'Retard'),
        ('absence',   'Absence'),
        ('heures_sup','Heures sup'),
        ('conge',     'Congé'),
        ('maladie',   'Maladie'),
        ('ferie',     'Jour férié'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employe         = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='journees')
    date            = models.DateField()
    heure_entree    = models.TimeField(null=True, blank=True)
    heure_sortie    = models.TimeField(null=True, blank=True)
    heures_theoriques = models.DecimalField(max_digits=4, decimal_places=2, default=8)
    heures_reelles  = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    heures_sup      = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    retard_minutes  = models.IntegerField(default=0)
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='normal')
    valide_par      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='journees_validees')
    note            = models.TextField(blank=True)

    class Meta:
        db_table = 'hrm_journees_calculees'
        ordering = ['-date']
        unique_together = ['employe', 'date']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.date}"


class DemandeConge(models.Model):
    TYPE_CHOICES = [
        ('cp',              'Congés payés'),
        ('rtt',             'RTT'),
        ('maladie',         'Maladie'),
        ('accident_travail','Accident travail'),
        ('maternite',       'Maternité'),
        ('paternite',       'Paternité'),
        ('sans_solde',      'Sans solde'),
        ('autre',           'Autre'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve',   'Approuvé'),
        ('refuse',     'Refusé'),
        ('annule',     'Annulé'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference    = models.CharField(max_length=20, unique=True, blank=True)
    employe      = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='conges')
    type_conge   = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_debut   = models.DateField()
    date_fin     = models.DateField()
    nb_jours     = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    motif        = models.TextField(blank=True)
    commentaire_manager = models.TextField(blank=True)
    valide_par   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_valides')
    date_validation = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hrm_demandes_conges'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = DemandeConge.objects.filter(reference__startswith=f'CNG-{year}-').count()
            self.reference = f'CNG-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.employe.nom_complet}"


class Formation(models.Model):
    STATUT_CHOICES = [
        ('planifiee',  'Planifiée'),
        ('en_cours',   'En cours'),
        ('realisee',   'Réalisée'),
        ('annulee',    'Annulée'),
    ]
    TYPE_CHOICES = [
        ('interne',   'Interne'),
        ('externe',   'Externe'),
        ('elearning', 'E-learning'),
        ('terrain',   'Sur le terrain'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference    = models.CharField(max_length=20, unique=True, blank=True)
    titre        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    type_formation = models.CharField(max_length=20, choices=TYPE_CHOICES, default='externe')
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifiee')
    date_prevue  = models.DateField()
    date_realisation = models.DateField(null=True, blank=True)
    organisme    = models.CharField(max_length=200, blank=True)
    lieu         = models.CharField(max_length=200, blank=True)
    duree_heures = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    cout         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    participants = models.ManyToManyField(Employe, blank=True, related_name='formations')
    competence_acquise = models.ForeignKey(Competence, on_delete=models.SET_NULL, null=True, blank=True, related_name='formations')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hrm_formations'
        ordering = ['-date_prevue']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = Formation.objects.filter(reference__startswith=f'FOR-{year}-').count()
            self.reference = f'FOR-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.titre}"