import uuid
from django.db import models
from django.contrib.auth.models import User


class FactureClient(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoyee',   'Envoyée'),
        ('payee',     'Payée'),
        ('retard',    'En retard'),
        ('annulee',   'Annulée'),
        ('partielle', 'Payée partiellement'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('virement',  'Virement bancaire'),
        ('cheque',    'Chèque'),
        ('especes',   'Espèces'),
        ('cb',        'Carte bancaire'),
        ('prelevement','Prélèvement'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference        = models.CharField(max_length=20, unique=True, blank=True)
    commande         = models.ForeignKey('crm.CommandeClient', on_delete=models.SET_NULL, null=True, blank=True, related_name='factures')
    client           = models.ForeignKey('crm.Client', on_delete=models.CASCADE, related_name='factures')
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    # Dates
    date_emission    = models.DateField(auto_now_add=True)
    date_echeance    = models.DateField(null=True, blank=True)
    date_paiement    = models.DateField(null=True, blank=True)

    # Montants
    montant_ht       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taux_tva         = models.DecimalField(max_digits=5,  decimal_places=2, default=20)
    montant_tva      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_ttc      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_paye     = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Paiement
    mode_paiement    = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, blank=True)
    reference_paiement = models.CharField(max_length=100, blank=True)

    notes            = models.TextField(blank=True)
    conditions       = models.TextField(blank=True, default='Paiement à 30 jours fin de mois.')
    createur         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures_creees')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_factures_clients'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = FactureClient.objects.filter(reference__startswith=f'FC-{year}-').count()
            self.reference = f'FC-{year}-{str(last + 1).zfill(4)}'
        # Calcul automatique TVA et TTC
        self.montant_tva = float(self.montant_ht) * float(self.taux_tva) / 100
        self.montant_ttc = float(self.montant_ht) + float(self.montant_tva)
        # Statut retard automatique
        import datetime
        if self.statut == 'envoyee' and self.date_echeance:
            if self.date_echeance < datetime.date.today():
                self.statut = 'retard'
        super().save(*args, **kwargs)

    @property
    def montant_restant(self):
        return float(self.montant_ttc) - float(self.montant_paye)

    @property
    def est_en_retard(self):
        import datetime
        if self.date_echeance and self.statut in ['envoyee', 'retard', 'partielle']:
            return self.date_echeance < datetime.date.today()
        return False

    def __str__(self):
        return f"{self.reference} — {self.client.raison_sociale}"


class LigneFactureClient(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facture          = models.ForeignKey(FactureClient, on_delete=models.CASCADE, related_name='lignes')
    designation      = models.CharField(max_length=200)
    reference_article= models.CharField(max_length=100, blank=True)
    quantite         = models.DecimalField(max_digits=10, decimal_places=2)
    unite            = models.CharField(max_length=20, default='pce')
    prix_unitaire    = models.DecimalField(max_digits=10, decimal_places=2)
    remise           = models.DecimalField(max_digits=5,  decimal_places=2, default=0)
    ordre            = models.IntegerField(default=0)

    class Meta:
        db_table = 'finance_lignes_factures_clients'
        ordering = ['ordre']

    @property
    def montant_ht(self):
        return float(self.quantite) * float(self.prix_unitaire) * (1 - float(self.remise) / 100)

    def __str__(self):
        return f"{self.facture.reference} — {self.designation}"


class FactureFournisseur(models.Model):
    STATUT_CHOICES = [
        ('recue',      'Reçue'),
        ('validee',    'Validée'),
        ('payee',      'Payée'),
        ('contestee',  'Contestée'),
        ('annulee',    'Annulée'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference        = models.CharField(max_length=20, unique=True, blank=True)
    reference_fournisseur = models.CharField(max_length=100, blank=True)
    commande_achat   = models.ForeignKey('achats.CommandeAchat', on_delete=models.SET_NULL, null=True, blank=True, related_name='factures')
    fournisseur      = models.ForeignKey('achats.Fournisseur', on_delete=models.CASCADE, related_name='factures')
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='recue')

    # Dates
    date_reception   = models.DateField(auto_now_add=True)
    date_echeance    = models.DateField(null=True, blank=True)
    date_paiement    = models.DateField(null=True, blank=True)

    # Montants
    montant_ht       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taux_tva         = models.DecimalField(max_digits=5,  decimal_places=2, default=20)
    montant_tva      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_ttc      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_paye     = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    mode_paiement    = models.CharField(max_length=20, blank=True)
    notes            = models.TextField(blank=True)
    motif_contestation = models.TextField(blank=True)
    validateur       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures_fournisseur_validees')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_factures_fournisseurs'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = FactureFournisseur.objects.filter(reference__startswith=f'FF-{year}-').count()
            self.reference = f'FF-{year}-{str(last + 1).zfill(4)}'
        self.montant_tva = float(self.montant_ht) * float(self.taux_tva) / 100
        self.montant_ttc = float(self.montant_ht) + float(self.montant_tva)
        super().save(*args, **kwargs)

    @property
    def est_en_retard(self):
        import datetime
        if self.date_echeance and self.statut in ['recue', 'validee']:
            return self.date_echeance < datetime.date.today()
        return False

    def __str__(self):
        return f"{self.reference} — {self.fournisseur.raison_sociale}"


class MouvementTresorerie(models.Model):
    TYPE_CHOICES = [
        ('encaissement', 'Encaissement'),
        ('decaissement', 'Décaissement'),
    ]
    CATEGORIE_CHOICES = [
        ('vente',         'Vente client'),
        ('achat',         'Achat fournisseur'),
        ('salaire',       'Salaire'),
        ('loyer',         'Loyer'),
        ('investissement','Investissement'),
        ('impot',         'Impôt / Taxe'),
        ('frais_bancaire','Frais bancaires'),
        ('autre',         'Autre'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference        = models.CharField(max_length=20, unique=True, blank=True)
    type_mouvement   = models.CharField(max_length=20, choices=TYPE_CHOICES)
    categorie        = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='autre')
    libelle          = models.CharField(max_length=200)
    montant          = models.DecimalField(max_digits=12, decimal_places=2)
    date_mouvement   = models.DateField()
    date_valeur      = models.DateField(null=True, blank=True)

    # Liens optionnels
    facture_client   = models.ForeignKey(FactureClient, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements')
    facture_fournisseur = models.ForeignKey(FactureFournisseur, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements')

    notes            = models.TextField(blank=True)
    saisi_par        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_mouvements_tresorerie'
        ordering = ['-date_mouvement']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = MouvementTresorerie.objects.filter(reference__startswith=f'MVT-{year}-').count()
            self.reference = f'MVT-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.libelle}"