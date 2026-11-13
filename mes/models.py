import uuid
from django.db import models
from django.contrib.auth.models import User


# ─────────────────────────────────────────────
# POSTES DE CHARGE / MACHINES
# ─────────────────────────────────────────────
class PosteCharge(models.Model):
    TYPE_CHOICES = [
        ('machine',       'Machine'),
        ('poste_manuel',  'Poste manuel'),
        ('sous_traitance','Sous-traitance'),
        ('controle',      'Contrôle qualité'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code                = models.CharField(max_length=20, unique=True)
    libelle             = models.CharField(max_length=200)
    type_poste          = models.CharField(max_length=20, choices=TYPE_CHOICES, default='machine')
    description         = models.TextField(blank=True)
    taux_horaire        = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    capacite_heures_jour= models.DecimalField(max_digits=5, decimal_places=2, default=8)
    actif               = models.BooleanField(default=True)
    notes               = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mes_postes_charge'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.libelle}"


# ─────────────────────────────────────────────
# ARTICLES (bibliothèque)
# ─────────────────────────────────────────────
class Article(models.Model):
    TYPE_CHOICES = [
        ('produit_fini',     'Produit fini'),
        ('semi_fini',        'Semi-fini / Sous-ensemble'),
        ('matiere_premiere', 'Matière première'),
        ('composant',        'Composant acheté'),
        ('consommable',      'Consommable'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference       = models.CharField(max_length=100, unique=True)
    designation     = models.CharField(max_length=200)
    type_article    = models.CharField(max_length=20, choices=TYPE_CHOICES, default='produit_fini')
    unite           = models.CharField(max_length=20, default='pce')
    prix_revient    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_actuel    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_mini      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description     = models.TextField(blank=True)
    actif           = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mes_articles'
        ordering = ['reference']

    def __str__(self):
        return f"{self.reference} — {self.designation}"


# ─────────────────────────────────────────────
# GAMME STANDARD (bibliothèque)
# ─────────────────────────────────────────────
class GammeStandard(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article     = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='gammes', null=True, blank=True)
    code        = models.CharField(max_length=50, unique=True)
    libelle     = models.CharField(max_length=200)
    version     = models.CharField(max_length=10, default='1')
    active      = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mes_gammes_standard'

    def __str__(self):
        return f"{self.code} — {self.libelle}"


class OperationStandard(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gamme           = models.ForeignKey(GammeStandard, on_delete=models.CASCADE, related_name='operations')
    numero          = models.IntegerField()
    libelle         = models.CharField(max_length=200)
    poste_charge    = models.ForeignKey(PosteCharge, on_delete=models.SET_NULL, null=True, blank=True)
    temps_preparation = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='Minutes')
    temps_unitaire  = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='Minutes par pièce')
    instructions    = models.TextField(blank=True)
    ordre           = models.IntegerField(default=0)

    class Meta:
        db_table = 'mes_operations_standard'
        ordering = ['ordre', 'numero']

    def __str__(self):
        return f"{self.gamme.code} — Op.{self.numero} {self.libelle}"


# ─────────────────────────────────────────────
# NOMENCLATURE STANDARD (bibliothèque)
# ─────────────────────────────────────────────
class NomenclatureStandard(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article     = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='nomenclatures')
    composant   = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='utilise_dans')
    quantite    = models.DecimalField(max_digits=10, decimal_places=4)
    unite       = models.CharField(max_length=20, default='pce')
    ordre       = models.IntegerField(default=0)
    notes       = models.TextField(blank=True)

    class Meta:
        db_table = 'mes_nomenclatures_standard'
        ordering = ['ordre']

    def __str__(self):
        return f"{self.article.reference} → {self.composant.reference}"


# ─────────────────────────────────────────────
# ORDRES DE FABRICATION
# ─────────────────────────────────────────────
class OrdreFabrication(models.Model):
    STATUT_CHOICES = [
        ('preparation',  'En préparation'),
        ('lance',        'Lancé'),
        ('en_attente',   'En attente appro.'),
        ('en_cours',     'En cours de production'),
        ('termine',      'Terminé'),
        ('cloture',      'Clôturé'),
        ('annule',       'Annulé'),
    ]
    PRIORITE_CHOICES = [
        ('normale',   'Normale'),
        ('haute',     'Haute'),
        ('urgente',   'Urgente'),
        ('critique',  'Critique'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference           = models.CharField(max_length=20, unique=True, blank=True)
    article             = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordres_fabrication')
    designation         = models.CharField(max_length=200)
    commande_client     = models.ForeignKey('crm.CommandeClient', on_delete=models.SET_NULL, null=True, blank=True, related_name='ordres_fabrication')
    reference_client    = models.CharField(max_length=100, blank=True)
    statut              = models.CharField(max_length=20, choices=STATUT_CHOICES, default='preparation')
    priorite            = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='normale')

    # Quantités
    quantite_lancee     = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_fabriquee  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantite_rebut      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unite               = models.CharField(max_length=20, default='pce')

    # Dates
    date_creation       = models.DateField(auto_now_add=True)
    date_debut_prevue   = models.DateField(null=True, blank=True)
    date_fin_prevue     = models.DateField(null=True, blank=True)
    date_debut_reelle   = models.DateField(null=True, blank=True)
    date_fin_reelle     = models.DateField(null=True, blank=True)

    # Responsables
    responsable         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='of_responsable')
    createur            = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='of_createur')

    # Gamme et nomenclature source
    gamme_source        = models.ForeignKey(GammeStandard, on_delete=models.SET_NULL, null=True, blank=True)

    notes               = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mes_ordres_fabrication'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = OrdreFabrication.objects.filter(reference__startswith=f'OF-{year}-').count()
            self.reference = f'OF-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    @property
    def avancement_pct(self):
        if float(self.quantite_lancee) > 0:
            return round(float(self.quantite_fabriquee) / float(self.quantite_lancee) * 100, 1)
        return 0

    @property
    def est_en_retard(self):
        import datetime
        if self.date_fin_prevue and self.statut not in ['termine', 'cloture', 'annule']:
            return self.date_fin_prevue < datetime.date.today()
        return False

    @property
    def taux_rebut(self):
        total = float(self.quantite_fabriquee) + float(self.quantite_rebut)
        if total > 0:
            return round(float(self.quantite_rebut) / total * 100, 1)
        return 0

    @property
    def temps_prevu_total(self):
        return sum(op.temps_total_prevu for op in self.operations.all())

    @property
    def temps_reel_total(self):
        return sum(float(op.temps_reel or 0) for op in self.operations.all())

    def __str__(self):
        return f"{self.reference} — {self.designation}"


# ─────────────────────────────────────────────
# OPÉRATIONS DE LA GAMME OF
# ─────────────────────────────────────────────
class OperationOF(models.Model):
    STATUT_CHOICES = [
        ('en_attente',  'En attente'),
        ('en_cours',    'En cours'),
        ('terminee',    'Terminée'),
        ('bloquee',     'Bloquée'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    of                  = models.ForeignKey(OrdreFabrication, on_delete=models.CASCADE, related_name='operations')
    numero              = models.IntegerField()
    libelle             = models.CharField(max_length=200)
    poste_charge        = models.ForeignKey(PosteCharge, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations_of')
    statut              = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    # Temps
    temps_preparation   = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='Minutes')
    temps_unitaire      = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='Minutes/pièce')
    temps_reel          = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='Minutes réelles')

    # Quantités
    quantite_prevue     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantite_realisee   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantite_rebut      = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Dates
    date_debut_prevue   = models.DateField(null=True, blank=True)
    date_fin_prevue     = models.DateField(null=True, blank=True)
    date_debut_reelle   = models.DateTimeField(null=True, blank=True)
    date_fin_reelle     = models.DateTimeField(null=True, blank=True)

    # Opérateur assigné
    operateur           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations_assignees')

    instructions        = models.TextField(blank=True)
    ordre               = models.IntegerField(default=0)

    class Meta:
        db_table = 'mes_operations_of'
        ordering = ['ordre', 'numero']

    @property
    def temps_total_prevu(self):
        return float(self.temps_preparation) + float(self.temps_unitaire) * float(self.quantite_prevue or self.of.quantite_lancee)

    @property
    def ecart_temps(self):
        return float(self.temps_reel) - self.temps_total_prevu

    @property
    def cout_prevu(self):
        if self.poste_charge:
            return (self.temps_total_prevu / 60) * float(self.poste_charge.taux_horaire)
        return 0

    @property
    def cout_reel(self):
        if self.poste_charge:
            return (float(self.temps_reel) / 60) * float(self.poste_charge.taux_horaire)
        return 0

    def __str__(self):
        return f"{self.of.reference} — Op.{self.numero} {self.libelle}"


# ─────────────────────────────────────────────
# NOMENCLATURE OF
# ─────────────────────────────────────────────
class LigneNomenclatureOF(models.Model):
    TYPE_CHOICES = [
        ('matiere',    'Matière première'),
        ('composant',  'Composant acheté'),
        ('semi_fini',  'Semi-fini'),
        ('consommable','Consommable'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    of                  = models.ForeignKey(OrdreFabrication, on_delete=models.CASCADE, related_name='nomenclature')
    article             = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='utilisations_of')
    designation         = models.CharField(max_length=200)
    reference_article   = models.CharField(max_length=100, blank=True)
    type_composant      = models.CharField(max_length=20, choices=TYPE_CHOICES, default='matiere')
    quantite_necessaire = models.DecimalField(max_digits=10, decimal_places=4)
    quantite_consommee  = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    unite               = models.CharField(max_length=20, default='pce')
    disponible          = models.BooleanField(default=False)
    notes               = models.TextField(blank=True)
    ordre               = models.IntegerField(default=0)

    class Meta:
        db_table = 'mes_nomenclature_of'
        ordering = ['ordre']

    @property
    def manquant(self):
        return max(0, float(self.quantite_necessaire) - float(self.quantite_consommee))

    def __str__(self):
        return f"{self.of.reference} — {self.designation}"


# ─────────────────────────────────────────────
# POINTAGES OPÉRATEUR
# ─────────────────────────────────────────────
class PointageProduction(models.Model):
    TYPE_CHOICES = [
        ('debut',  'Début opération'),
        ('fin',    'Fin opération'),
        ('pause',  'Pause'),
        ('arret',  'Arrêt'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation           = models.ForeignKey(OperationOF, on_delete=models.CASCADE, related_name='pointages')
    operateur           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pointages_production')
    type_pointage       = models.CharField(max_length=10, choices=TYPE_CHOICES, default='debut')
    timestamp           = models.DateTimeField()
    quantite_produite   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantite_rebut      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    motif_rebut         = models.CharField(max_length=200, blank=True)
    notes               = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mes_pointages_production'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.operation} — {self.type_pointage} — {self.timestamp}"


# ─────────────────────────────────────────────
# ARRÊTS MACHINE / INCIDENTS
# ─────────────────────────────────────────────
class ArretMachine(models.Model):
    TYPE_CHOICES = [
        ('panne',        'Panne machine'),
        ('maintenance',  'Maintenance préventive'),
        ('reglage',      'Réglage / changement série'),
        ('manque_appro', 'Manque d\'approvisionnement'),
        ('qualite',      'Problème qualité'),
        ('autre',        'Autre'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poste_charge    = models.ForeignKey(PosteCharge, on_delete=models.CASCADE, related_name='arrets')
    operation       = models.ForeignKey(OperationOF, on_delete=models.SET_NULL, null=True, blank=True, related_name='arrets')
    type_arret      = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_debut      = models.DateTimeField()
    date_fin        = models.DateTimeField(null=True, blank=True)
    duree_minutes   = models.IntegerField(default=0)
    description     = models.TextField(blank=True)
    action_corrective = models.TextField(blank=True)
    saisi_par       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mes_arrets_machine'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.poste_charge.libelle} — {self.type_arret} — {self.date_debut}"