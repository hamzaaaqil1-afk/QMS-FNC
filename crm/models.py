import uuid
from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    SEGMENT_CHOICES = [
        ('grand_compte', 'Grand compte'),
        ('pme',          'PME'),
        ('particulier',  'Particulier'),
        ('public',       'Secteur public'),
    ]
    PAYS_CHOICES = [
        ('FR', 'France'),
        ('BE', 'Belgique'),
        ('CH', 'Suisse'),
        ('DE', 'Allemagne'),
        ('ES', 'Espagne'),
        ('IT', 'Italie'),
        ('OTHER', 'Autre'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference      = models.CharField(max_length=20, unique=True, blank=True)
    raison_sociale = models.CharField(max_length=200)
    siret          = models.CharField(max_length=20, blank=True)
    secteur        = models.CharField(max_length=100, blank=True)
    segment        = models.CharField(max_length=20, choices=SEGMENT_CHOICES, default='pme')

    # Adresse
    adresse        = models.CharField(max_length=200, blank=True)
    code_postal    = models.CharField(max_length=10, blank=True)
    ville          = models.CharField(max_length=100, blank=True)
    pays           = models.CharField(max_length=10, choices=PAYS_CHOICES, default='FR')

    # Contact général
    telephone      = models.CharField(max_length=20, blank=True)
    email          = models.EmailField(blank=True)
    site_web       = models.URLField(blank=True)

    # Infos commerciales
    commercial     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')
    actif          = models.BooleanField(default=True)
    notes          = models.TextField(blank=True)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_clients'
        ordering = ['raison_sociale']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = Client.objects.filter(reference__startswith=f'CLI-{year}-').count()
            self.reference = f'CLI-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.raison_sociale


class Contact(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client     = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    nom        = models.CharField(max_length=100)
    prenom     = models.CharField(max_length=100, blank=True)
    fonction   = models.CharField(max_length=100, blank=True)
    email      = models.EmailField(blank=True)
    telephone  = models.CharField(max_length=20, blank=True)
    principal  = models.BooleanField(default=False)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_contacts'
        ordering = ['-principal', 'nom']

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.client.raison_sociale}"


class Opportunite(models.Model):
    STATUT_CHOICES = [
        ('prospect',  'Prospect'),
        ('qualifie',  'Qualifié'),
        ('devis',     'Devis envoyé'),
        ('gagne',     'Gagné'),
        ('perdu',     'Perdu'),
    ]
    SOURCE_CHOICES = [
        ('entrant',    'Entrant'),
        ('prospection','Prospection'),
        ('referral',   'Recommandation'),
        ('salon',      'Salon / Événement'),
        ('autre',      'Autre'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference           = models.CharField(max_length=20, unique=True, blank=True)
    client              = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='opportunites')
    contact             = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunites')
    titre               = models.CharField(max_length=200)
    description         = models.TextField(blank=True)
    statut              = models.CharField(max_length=20, choices=STATUT_CHOICES, default='prospect')
    source              = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True)
    valeur_estimee      = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    probabilite         = models.IntegerField(default=50)
    date_closing_prevue = models.DateField(null=True, blank=True)
    date_closing_reelle = models.DateField(null=True, blank=True)
    commercial          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunites')
    raison_perte        = models.TextField(blank=True)
    notes               = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_opportunites'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = Opportunite.objects.filter(reference__startswith=f'OPP-{year}-').count()
            self.reference = f'OPP-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.titre}"


class Devis(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye',    'Envoyé'),
        ('accepte',   'Accepté'),
        ('refuse',    'Refusé'),
        ('expire',    'Expiré'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference       = models.CharField(max_length=20, unique=True, blank=True)
    client          = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='devis')
    opportunite     = models.ForeignKey(Opportunite, on_delete=models.SET_NULL, null=True, blank=True, related_name='devis')
    contact         = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='devis')
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_emission   = models.DateField(auto_now_add=True)
    date_validite   = models.DateField(null=True, blank=True)
    remise_globale  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes           = models.TextField(blank=True)
    conditions      = models.TextField(blank=True)
    commercial      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='devis')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_devis'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = Devis.objects.filter(reference__startswith=f'DEV-{year}-').count()
            self.reference = f'DEV-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    @property
    def montant_ht(self):
        total = sum(l.montant_ht for l in self.lignes.all())
        return float(total) * (1 - float(self.remise_globale) / 100)

    @property
    def montant_tva(self):
        return self.montant_ht * 20 / 100

    @property
    def montant_ttc(self):
        return self.montant_ht + self.montant_tva


class LigneDevis(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devis            = models.ForeignKey(Devis, on_delete=models.CASCADE, related_name='lignes')
    designation      = models.CharField(max_length=200)
    reference_article= models.CharField(max_length=100, blank=True)
    quantite         = models.DecimalField(max_digits=10, decimal_places=2)
    unite            = models.CharField(max_length=20, default='pce')
    prix_unitaire    = models.DecimalField(max_digits=10, decimal_places=2)
    remise           = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    delai_livraison  = models.IntegerField(null=True, blank=True)
    ordre            = models.IntegerField(default=0)

    class Meta:
        db_table = 'crm_lignes_devis'
        ordering = ['ordre']

    @property
    def montant_ht(self):
        return float(self.quantite) * float(self.prix_unitaire) * (1 - float(self.remise) / 100)

    def __str__(self):
        return f"{self.devis.reference} — {self.designation}"


class CommandeClient(models.Model):
    STATUT_CHOICES = [
        ('recue',          'Reçue'),
        ('confirmee',      'Confirmée'),
        ('en_production',  'En production'),
        ('livree',         'Livrée'),
        ('annulee',        'Annulée'),
        ('facturee',       'Facturée'),
    ]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference            = models.CharField(max_length=20, unique=True, blank=True)
    client               = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    devis                = models.ForeignKey(Devis, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes')
    contact              = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes')
    reference_client     = models.CharField(max_length=100, blank=True)
    statut               = models.CharField(max_length=20, choices=STATUT_CHOICES, default='recue')
    date_commande        = models.DateField(auto_now_add=True)
    date_livraison_prevue= models.DateField(null=True, blank=True)
    date_livraison_reelle= models.DateField(null=True, blank=True)
    adresse_livraison    = models.TextField(blank=True)
    notes                = models.TextField(blank=True)
    commercial           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_clients')
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_commandes_clients'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = CommandeClient.objects.filter(reference__startswith=f'CC-{year}-').count()
            self.reference = f'CC-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    @property
    def montant_total(self):
        return sum(l.montant_ht for l in self.lignes.all())

    def __str__(self):
        return self.reference


class LigneCommande(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commande            = models.ForeignKey(CommandeClient, on_delete=models.CASCADE, related_name='lignes')
    designation         = models.CharField(max_length=200)
    reference_article   = models.CharField(max_length=100, blank=True)
    quantite_commandee  = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_livree     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unite               = models.CharField(max_length=20, default='pce')
    prix_unitaire       = models.DecimalField(max_digits=10, decimal_places=2)
    delai_livraison     = models.IntegerField(null=True, blank=True)
    ordre               = models.IntegerField(default=0)

    class Meta:
        db_table = 'crm_lignes_commandes'
        ordering = ['ordre']

    @property
    def montant_ht(self):
        return float(self.quantite_commandee) * float(self.prix_unitaire)

    @property
    def reste_a_livrer(self):
        return float(self.quantite_commandee) - float(self.quantite_livree)

    def __str__(self):
        return f"{self.commande.reference} — {self.designation}"


class ReclamationClient(models.Model):
    TYPE_CHOICES = [
        ('qualite',    'Qualité'),
        ('delai',      'Délai'),
        ('facturation','Facturation'),
        ('autre',      'Autre'),
    ]
    GRAVITE_CHOICES = [
        ('mineure',   'Mineure'),
        ('majeure',   'Majeure'),
        ('critique',  'Critique'),
    ]
    STATUT_CHOICES = [
        ('ouverte',   'Ouverte'),
        ('en_cours',  'En cours'),
        ('cloturee',  'Clôturée'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference   = models.CharField(max_length=20, unique=True, blank=True)
    client      = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reclamations')
    commande    = models.ForeignKey(CommandeClient, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamations')
    contact     = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamations')
    type_reclamation = models.CharField(max_length=20, choices=TYPE_CHOICES)
    gravite     = models.CharField(max_length=20, choices=GRAVITE_CHOICES, default='mineure')
    statut      = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ouverte')
    description = models.TextField()
    date_reclamation = models.DateField(auto_now_add=True)
    fnc         = models.ForeignKey('qms.NonConformite', on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamations_client')
    satisfaction_client = models.IntegerField(null=True, blank=True)  # 1-5
    commentaire_cloture = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_reclamations'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            year = datetime.date.today().year
            last = ReclamationClient.objects.filter(reference__startswith=f'REC-{year}-').count()
            self.reference = f'REC-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.client.raison_sociale}"