import uuid
from django.db import models
from django.contrib.auth.models import User


class Fournisseur(models.Model):
    STATUT_CHOICES = [
        ('actif',    'Actif'),
        ('inactif',  'Inactif'),
        ('blacklist','Blacklisté'),
    ]
    CATEGORIE_CHOICES = [
        ('matiere_premiere', 'Matière première'),
        ('composant',        'Composant'),
        ('sous_traitance',   'Sous-traitance'),
        ('service',          'Service'),
        ('consommable',      'Consommable'),
        ('equipement',       'Équipement'),
        ('autre',            'Autre'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference      = models.CharField(max_length=20, unique=True, blank=True)
    raison_sociale = models.CharField(max_length=200)
    siret          = models.CharField(max_length=20, blank=True)
    categorie      = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='matiere_premiere')
    statut         = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')

    # Adresse
    adresse        = models.CharField(max_length=200, blank=True)
    code_postal    = models.CharField(max_length=10, blank=True)
    ville          = models.CharField(max_length=100, blank=True)
    pays           = models.CharField(max_length=50, default='France')

    # Contact
    telephone      = models.CharField(max_length=20, blank=True)
    email          = models.EmailField(blank=True)
    site_web       = models.URLField(blank=True)
    contact_principal = models.CharField(max_length=200, blank=True)

    # Conditions commerciales
    delai_livraison_jours = models.IntegerField(default=0)
    conditions_paiement   = models.CharField(max_length=100, blank=True)
    remise_habituelle     = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    devise                = models.CharField(max_length=10, default='EUR')

    # Évaluation globale (calculée)
    note_qualite  = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    note_delai    = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    note_prix     = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    note_globale  = models.DecimalField(max_digits=3, decimal_places=1, default=0)

    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'achats_fournisseurs'
        ordering = ['raison_sociale']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = Fournisseur.objects.filter(reference__startswith=f'FOU-{year}-').count()
            self.reference = f'FOU-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.raison_sociale}"


class EvaluationFournisseur(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fournisseur   = models.ForeignKey(Fournisseur, on_delete=models.CASCADE, related_name='evaluations')
    date_evaluation = models.DateField(auto_now_add=True)
    evaluateur    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    commande      = models.ForeignKey('CommandeAchat', on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluations')

    note_qualite  = models.IntegerField()   # 1-5
    note_delai    = models.IntegerField()   # 1-5
    note_prix     = models.IntegerField()   # 1-5
    note_service  = models.IntegerField()   # 1-5
    commentaire   = models.TextField(blank=True)

    class Meta:
        db_table = 'achats_evaluations_fournisseurs'
        ordering = ['-date_evaluation']

    @property
    def note_globale(self):
        return round((self.note_qualite + self.note_delai + self.note_prix + self.note_service) / 4, 1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculer la note globale du fournisseur
        evals = EvaluationFournisseur.objects.filter(fournisseur=self.fournisseur)
        if evals.exists():
            self.fournisseur.note_qualite = round(sum(e.note_qualite for e in evals) / evals.count(), 1)
            self.fournisseur.note_delai   = round(sum(e.note_delai   for e in evals) / evals.count(), 1)
            self.fournisseur.note_prix    = round(sum(e.note_prix    for e in evals) / evals.count(), 1)
            self.fournisseur.note_globale = round(sum(e.note_globale for e in evals) / evals.count(), 1)
            self.fournisseur.save()

    def __str__(self):
        return f"{self.fournisseur.raison_sociale} — {self.date_evaluation}"


class DemandeAchat(models.Model):
    STATUT_CHOICES = [
        ('brouillon',  'Brouillon'),
        ('en_attente', 'En attente validation'),
        ('approuvee',  'Approuvée'),
        ('refusee',    'Refusée'),
        ('commandee',  'Commandée'),
        ('annulee',    'Annulée'),
    ]
    URGENCE_CHOICES = [
        ('normale',  'Normale'),
        ('urgente',  'Urgente'),
        ('critique', 'Critique'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference    = models.CharField(max_length=20, unique=True, blank=True)
    titre        = models.CharField(max_length=200)
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    urgence      = models.CharField(max_length=20, choices=URGENCE_CHOICES, default='normale')
    demandeur    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_achat')
    approbateur  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approbations_achat')
    date_demande = models.DateField(auto_now_add=True)
    date_besoin  = models.DateField(null=True, blank=True)
    date_approbation = models.DateField(null=True, blank=True)
    fournisseur_suggere = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes')
    motif        = models.TextField(blank=True)
    commentaire_approbateur = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'achats_demandes_achat'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = DemandeAchat.objects.filter(reference__startswith=f'DA-{year}-').count()
            self.reference = f'DA-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    @property
    def montant_total(self):
        return sum(float(l.quantite) * float(l.prix_unitaire_estime) for l in self.lignes.all() if l.prix_unitaire_estime)

    def __str__(self):
        return f"{self.reference} — {self.titre}"


class LigneDemandeAchat(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    demande          = models.ForeignKey(DemandeAchat, on_delete=models.CASCADE, related_name='lignes')
    designation      = models.CharField(max_length=200)
    reference_article= models.CharField(max_length=100, blank=True)
    quantite         = models.DecimalField(max_digits=10, decimal_places=2)
    unite            = models.CharField(max_length=20, default='pce')
    prix_unitaire_estime = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ordre            = models.IntegerField(default=0)

    class Meta:
        db_table = 'achats_lignes_demandes'
        ordering = ['ordre']

    def __str__(self):
        return f"{self.demande.reference} — {self.designation}"


class CommandeAchat(models.Model):
    STATUT_CHOICES = [
        ('brouillon',  'Brouillon'),
        ('envoyee',    'Envoyée'),
        ('confirmee',  'Confirmée'),
        ('partielle',  'Reçue partiellement'),
        ('recue',      'Reçue complètement'),
        ('annulee',    'Annulée'),
        ('facturee',   'Facturée'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference      = models.CharField(max_length=20, unique=True, blank=True)
    fournisseur    = models.ForeignKey(Fournisseur, on_delete=models.CASCADE, related_name='commandes')
    demande        = models.ForeignKey(DemandeAchat, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes')
    statut         = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_commande  = models.DateField(auto_now_add=True)
    date_livraison_prevue = models.DateField(null=True, blank=True)
    date_livraison_reelle = models.DateField(null=True, blank=True)
    reference_fournisseur = models.CharField(max_length=100, blank=True)
    acheteur       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_achat')
    remise_globale = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes          = models.TextField(blank=True)
    conditions_paiement = models.CharField(max_length=100, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'achats_commandes_achat'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = CommandeAchat.objects.filter(reference__startswith=f'CA-{year}-').count()
            self.reference = f'CA-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    @property
    def montant_ht(self):
        total = sum(float(l.quantite_commandee) * float(l.prix_unitaire) for l in self.lignes.all())
        return total * (1 - float(self.remise_globale) / 100)

    @property
    def montant_tva(self):
        return self.montant_ht * 0.20

    @property
    def montant_ttc(self):
        return self.montant_ht + self.montant_tva

    @property
    def est_en_retard(self):
        import datetime
        if self.date_livraison_prevue and self.statut not in ['recue', 'annulee', 'facturee']:
            return self.date_livraison_prevue < datetime.date.today()
        return False

    def __str__(self):
        return f"{self.reference} — {self.fournisseur.raison_sociale}"


class LigneCommandeAchat(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commande            = models.ForeignKey(CommandeAchat, on_delete=models.CASCADE, related_name='lignes')
    designation         = models.CharField(max_length=200)
    reference_article   = models.CharField(max_length=100, blank=True)
    quantite_commandee  = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_recue      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unite               = models.CharField(max_length=20, default='pce')
    prix_unitaire       = models.DecimalField(max_digits=10, decimal_places=2)
    delai_livraison     = models.IntegerField(null=True, blank=True)
    ordre               = models.IntegerField(default=0)

    class Meta:
        db_table = 'achats_lignes_commandes_achat'
        ordering = ['ordre']

    @property
    def montant_ht(self):
        return float(self.quantite_commandee) * float(self.prix_unitaire)

    @property
    def reste_a_recevoir(self):
        return float(self.quantite_commandee) - float(self.quantite_recue)

    def __str__(self):
        return f"{self.commande.reference} — {self.designation}"


class BonReception(models.Model):
    STATUT_CHOICES = [
        ('en_cours',  'En cours de contrôle'),
        ('accepte',   'Accepté'),
        ('partiel',   'Accepté partiellement'),
        ('refuse',    'Refusé'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference    = models.CharField(max_length=20, unique=True, blank=True)
    commande     = models.ForeignKey(CommandeAchat, on_delete=models.CASCADE, related_name='receptions')
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    date_reception = models.DateField(auto_now_add=True)
    receptionnaire = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='receptions')
    notes        = models.TextField(blank=True)
    fnc          = models.ForeignKey('qms.NonConformite', on_delete=models.SET_NULL, null=True, blank=True, related_name='receptions_achat')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'achats_bons_reception'
        ordering = ['-date_reception']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = BonReception.objects.filter(reference__startswith=f'BR-{year}-').count()
            self.reference = f'BR-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.commande.reference}"


class LigneBonReception(models.Model):
    STATUT_CHOICES = [
        ('conforme',     'Conforme'),
        ('non_conforme', 'Non conforme'),
        ('partiel',      'Partiel'),
    ]

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bon_reception      = models.ForeignKey(BonReception, on_delete=models.CASCADE, related_name='lignes')
    ligne_commande     = models.ForeignKey(LigneCommandeAchat, on_delete=models.CASCADE, related_name='receptions')
    quantite_recue     = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_conforme  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut             = models.CharField(max_length=20, choices=STATUT_CHOICES, default='conforme')
    motif_non_conformite = models.TextField(blank=True)

    class Meta:
        db_table = 'achats_lignes_reception'

    def __str__(self):
        return f"{self.bon_reception.reference} — {self.ligne_commande.designation}"