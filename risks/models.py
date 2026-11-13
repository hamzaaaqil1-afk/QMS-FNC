import uuid
from django.db import models
from django.contrib.auth.models import User


class Risque(models.Model):
    STATUT_CHOICES = [
        ('identifie',  'Identifié'),
        ('en_cours',   'En cours de traitement'),
        ('traite',     'Traité'),
        ('accepte',    'Accepté'),
        ('clos',       'Clos'),
    ]
    TRAITEMENT_CHOICES = [
        ('eviter',     'Éviter'),
        ('reduire',    'Réduire'),
        ('transferer', 'Transférer'),
        ('accepter',   'Accepter'),
    ]
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
        ('rh',              'Ressources humaines'),
        ('finance',         'Finance'),
        ('informatique',    'Informatique'),
    ]
    CATEGORIE_CHOICES = [
        ('qualite',      'Qualité'),
        ('operationnel', 'Opérationnel'),
        ('securite',     'Sécurité'),
        ('financier',    'Financier'),
        ('rh',           'Ressources humaines'),
        ('informatique', 'Informatique'),
        ('juridique',    'Juridique'),
        ('environnement','Environnement'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference        = models.CharField(max_length=20, unique=True, blank=True)
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='identifie')
    categorie        = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='qualite')

    # Identification AMDEC
    titre            = models.CharField(max_length=200)
    description      = models.TextField(blank=True)
    processus        = models.CharField(max_length=50, choices=PROCESSUS_CHOICES, blank=True)
    fonction         = models.CharField(max_length=200, blank=True)
    mode_defaillance = models.TextField(blank=True)
    effet_defaillance= models.TextField(blank=True)
    cause_defaillance= models.TextField(blank=True)
    controles_actuels= models.TextField(blank=True)

    # Cotation initiale AMDEC (G x O x D = IPR)
    gravite          = models.IntegerField(default=1)
    occurrence       = models.IntegerField(default=1)
    detectabilite    = models.IntegerField(default=1)

    # Cotation résiduelle (après actions)
    gravite_residuelle       = models.IntegerField(null=True, blank=True)
    occurrence_residuelle    = models.IntegerField(null=True, blank=True)
    detectabilite_residuelle = models.IntegerField(null=True, blank=True)

    # Traitement
    type_traitement  = models.CharField(max_length=20, choices=TRAITEMENT_CHOICES, blank=True)
    action_maitrise  = models.TextField(blank=True)
    responsable      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='risques_responsable')
    date_echeance    = models.DateField(null=True, blank=True)

    # Liens QMS (imports circulaires évités avec strings)
    fnc              = models.ForeignKey('qms.NonConformite', on_delete=models.SET_NULL, null=True, blank=True, related_name='risques')
    capa             = models.ForeignKey('qms.CAPA',          on_delete=models.SET_NULL, null=True, blank=True, related_name='risques')
    audit            = models.ForeignKey('qms.Audit',         on_delete=models.SET_NULL, null=True, blank=True, related_name='risques')

    redacteur        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='risques_rediges')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'risks_risques'
        ordering = ['-created_at']

    @property
    def ipr(self):
        return self.gravite * self.occurrence * self.detectabilite

    @property
    def ipr_residuel(self):
        if all([self.gravite_residuelle, self.occurrence_residuelle, self.detectabilite_residuelle]):
            return self.gravite_residuelle * self.occurrence_residuelle * self.detectabilite_residuelle
        return None

    @property
    def niveau_criticite(self):
        ipr = self.ipr
        if ipr <= 20:  return 'acceptable'
        if ipr <= 60:  return 'tolerable'
        return 'inacceptable'

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = Risque.objects.filter(reference__startswith=f'RSQ-{year}-').count()
            self.reference = f'RSQ-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.titre}"