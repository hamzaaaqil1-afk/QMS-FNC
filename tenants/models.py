import uuid
from django.db import models
from django.contrib.auth.models import User


class Entreprise(models.Model):
    """
    Représente un client Defex (un tenant).
    L'ERP rgbsetup actuel (Herakles) deviendra l'entreprise n°1.
    """
    PLAN_CHOICES = [
        ('essai',      'Essai gratuit'),
        ('starter',    'Starter'),
        ('pro',        'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    STATUT_CHOICES = [
        ('active',    'Active'),
        ('suspendue', 'Suspendue'),
        ('essai',     'En essai'),
        ('annulee',   'Annulée'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom             = models.CharField(max_length=200)
    slug            = models.SlugField(max_length=100, unique=True)  # ex: herakles, acierplus
    siret           = models.CharField(max_length=20, blank=True)

    plan            = models.CharField(max_length=20, choices=PLAN_CHOICES, default='essai')
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='essai')

    # Contact principal
    email_contact   = models.EmailField(blank=True)
    telephone       = models.CharField(max_length=20, blank=True)

    # Branding (pour personnaliser l'espace client plus tard)
    logo            = models.ImageField(upload_to='tenants/logos/', null=True, blank=True)
    couleur_principale = models.CharField(max_length=10, default='#0F172A')

    # Limites du plan (utile pour facturation/quotas plus tard)
    max_utilisateurs = models.IntegerField(default=5)

    date_creation    = models.DateTimeField(auto_now_add=True)
    date_essai_fin   = models.DateField(null=True, blank=True)

    notes           = models.TextField(blank=True)

    class Meta:
        db_table = 'tenants_entreprises'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Site(models.Model):
    """
    Un site physique (usine, atelier, établissement) rattaché à une entreprise.
    Chaque entreprise a au moins un site (créé automatiquement à la migration
    pour les entreprises existantes, marqué comme site principal).
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise    = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='sites')
    nom           = models.CharField(max_length=200)
    code          = models.CharField(max_length=20, help_text="Code court, ex: LYON, NANTES — utilisé dans la numérotation des FNC")
    adresse       = models.CharField(max_length=300, blank=True)
    est_principal = models.BooleanField(default=False, help_text="Site par défaut de l'entreprise")
    actif         = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    # Compteur de numérotation FNC propre à ce site (le format vient de
    # ParametresEntreprise, mais chaque site incrémente sa propre séquence
    # — évite les collisions entre sites et permet de savoir d'où vient
    # une FNC rien qu'en lisant son numéro).
    compteur_fnc_actuel         = models.IntegerField(default=1)
    compteur_fnc_derniere_annee = models.IntegerField(null=True, blank=True)
    compteur_fnc_dernier_mois   = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'tenants_sites'
        ordering = ['nom']
        unique_together = ['entreprise', 'code']

    def __str__(self):
        return f"{self.nom} — {self.entreprise.nom}"

    def generer_numero_fnc(self, params):
        """
        Génère le prochain numéro de FNC pour CE site, selon le format
        défini au niveau entreprise (params: ParametresEntreprise), mais
        avec un compteur propre à ce site.
        """
        import datetime
        from django.db import transaction

        with transaction.atomic():
            # verrouille la ligne le temps de l'incrément pour éviter deux
            # FNC créées en même temps sur le même site avec le même numéro
            site = Site.objects.select_for_update().get(pk=self.pk)
            today = datetime.date.today()

            if params.remise_a_zero == 'annuel' and site.compteur_fnc_derniere_annee != today.year:
                site.compteur_fnc_actuel = 1
                site.compteur_fnc_derniere_annee = today.year
            elif params.remise_a_zero == 'mensuel' and (
                site.compteur_fnc_derniere_annee != today.year or site.compteur_fnc_dernier_mois != today.month
            ):
                site.compteur_fnc_actuel = 1
                site.compteur_fnc_derniere_annee = today.year
                site.compteur_fnc_dernier_mois = today.month

            sep      = params.separateur
            compteur = str(site.compteur_fnc_actuel).zfill(params.longueur_compteur)
            parties  = [params.prefixe]

            if params.inclure_code_site:
                parties.append(site.code)
            if params.utiliser_annee:
                parties.append(str(today.year))
            if params.utiliser_mois:
                parties.append(str(today.month).zfill(2))

            parties.append(compteur)
            numero = sep.join(parties)

            site.compteur_fnc_actuel += 1
            site.save(update_fields=['compteur_fnc_actuel', 'compteur_fnc_derniere_annee', 'compteur_fnc_dernier_mois'])

            # Répercute l'état sur l'instance appelante (self) pour cohérence
            self.compteur_fnc_actuel = site.compteur_fnc_actuel
            self.compteur_fnc_derniere_annee = site.compteur_fnc_derniere_annee
            self.compteur_fnc_dernier_mois = site.compteur_fnc_dernier_mois

            return numero

    def preview_numero_fnc(self, params):
        """Aperçu du prochain numéro pour ce site, sans incrémenter."""
        import datetime
        today    = datetime.date.today()
        sep      = params.separateur
        compteur = str(self.compteur_fnc_actuel).zfill(params.longueur_compteur)
        parties  = [params.prefixe]
        if params.inclure_code_site:
            parties.append(self.code)
        if params.utiliser_annee:
            parties.append(str(today.year))
        if params.utiliser_mois:
            parties.append(str(today.month).zfill(2))
        parties.append(compteur)
        return sep.join(parties)


class ProfilUtilisateur(models.Model):
    ROLE_CHOICES = [
        ('admin',       'Administrateur entreprise'),
        ('qualite',     'Responsable Qualité'),
        ('production',  'Production'),
        ('lecture',     'Lecture seule'),
    ]

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user               = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    entreprise         = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='utilisateurs')
    role               = models.CharField(max_length=20, choices=ROLE_CHOICES, default='production')
    role_personnalise  = models.ForeignKey('RolePersonnalise', on_delete=models.SET_NULL,
                           null=True, blank=True, related_name='utilisateurs')
    sites_autorises    = models.ManyToManyField(Site, blank=True, related_name='utilisateurs_autorises',
                           help_text="Sites auxquels cet utilisateur a accès. Vide = aucun site (à assigner).")
    actif              = models.BooleanField(default=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenants_profils_utilisateurs'

    def __str__(self):
        return f"{self.user.username} — {self.entreprise.nom} ({self.role})"

    def a_permission(self, code_permission):
        """Vérifie si cet utilisateur a une permission donnée."""
        if self.role_personnalise:
            if self.role_personnalise.est_admin:
                return True
            return self.role_personnalise.permissions.filter(code=code_permission).exists()
        # Fallback sur les anciens rôles fixes
        if self.role == 'admin':
            return True
        return False

    @property
    def est_admin_groupe(self):
        """
        Administrateur Groupe : toutes les permissions QMS + accès à tous les
        sites de l'entreprise, sans avoir à les cocher un par un.
        """
        if self.role_personnalise:
            return self.role_personnalise.est_admin and self.role_personnalise.acces_tous_sites
        # Rétrocompatibilité : l'ancien rôle fixe 'admin' se comporte comme un Admin Groupe
        return self.role == 'admin'

    @property
    def est_admin_site(self):
        """
        Administrateur Site : toutes les permissions QMS, mais limité aux
        sites listés dans sites_autorises (comme un utilisateur normal).
        """
        if self.role_personnalise:
            return self.role_personnalise.est_admin and not self.role_personnalise.acces_tous_sites
        return False

    def a_acces_site(self, site):
        """Vérifie si cet utilisateur a accès à un site donné."""
        if self.est_admin_groupe:
            return True
        return self.sites_autorises.filter(pk=site.pk).exists()

    @property
    def sites_ids_autorises(self):
        """Liste des IDs de sites accessibles — pratique pour filtrer un queryset."""
        return list(self.sites_autorises.values_list('id', flat=True))

    def assigner_role(self, role, auto_accorder_site=True):
        """
        Assigne un rôle à ce profil en garantissant l'invariant :
        un rôle propre à un site implique que ce profil a accès à ce site.

        Si `role` a un site et que ce profil n'y a pas encore accès :
        - auto_accorder_site=True  -> le site est ajouté automatiquement
        - auto_accorder_site=False -> lève ValueError
        """
        if role is not None and role.site_id is not None:
            if not self.sites_autorises.filter(pk=role.site_id).exists():
                if not auto_accorder_site:
                    raise ValueError(
                        f'Le rôle "{role.nom}" est propre au site "{role.site.nom}" ; '
                        "cet utilisateur doit avoir accès à ce site."
                    )
                self.sites_autorises.add(role.site)
        self.role_personnalise = role
        self.save(update_fields=['role_personnalise'])

    def synchroniser_sites(self, nouveaux_sites):
        """
        Remplace l'ensemble des sites autorisés par `nouveaux_sites` (iterable
        de Site). Si le rôle actuel de ce profil est propre à un site retiré
        de cette liste, le rôle est remis à None — un utilisateur ne peut
        jamais garder un rôle pour un site auquel il n'a plus accès.
        """
        nouveaux_ids = {s.pk for s in nouveaux_sites}
        if (self.role_personnalise
                and self.role_personnalise.site_id
                and self.role_personnalise.site_id not in nouveaux_ids):
            self.role_personnalise = None
            self.save(update_fields=['role_personnalise'])
        self.sites_autorises.set(nouveaux_sites)


class Permission(models.Model):
    """
    Liste fixe des permissions disponibles dans le système.
    Définie par les développeurs, pas modifiable par les clients.
    """
    MODULE_CHOICES = [
        ('qms',     'Qualité (QMS)'),
        ('rh',      'Ressources Humaines'),
        ('finance', 'Finance'),
        ('mes',     'Production (MES)'),
        ('admin',   'Administration'),
    ]

    code        = models.CharField(max_length=100, unique=True)  # ex: qms.creer_fnc
    libelle     = models.CharField(max_length=200)               # ex: Créer une FNC
    module      = models.CharField(max_length=20, choices=MODULE_CHOICES)
    description = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = 'tenants_permissions'
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.code} — {self.libelle}"


class RolePersonnalise(models.Model):
    """
    Rôle créé par l'admin d'une entreprise, avec ses propres permissions.

    Le champ `site` définit la portée du rôle :
    - None  -> rôle global, visible et assignable sur tous les sites de l'entreprise.
    - <Site> -> rôle propre à ce site uniquement, visible et assignable
      seulement pour ce site. Un Administrateur Site ne peut créer/gérer
      que des rôles rattachés à l'un de ses propres sites.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise       = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='roles')
    site             = models.ForeignKey('Site', on_delete=models.SET_NULL, null=True, blank=True,
                          related_name='roles',
                          help_text="Vide = rôle global (tous les sites). Sinon, rôle propre à ce site.")
    nom              = models.CharField(max_length=100)
    description      = models.CharField(max_length=200, blank=True)
    permissions      = models.ManyToManyField(Permission, blank=True, related_name='roles')
    est_admin        = models.BooleanField(default=False, verbose_name="Rôle administrateur (toutes les permissions QMS)")
    acces_tous_sites = models.BooleanField(default=False, verbose_name="Accès à tous les sites de l'entreprise (Administrateur Groupe)",
                          help_text="Si coché avec 'Rôle administrateur' : Administrateur Groupe. "
                                    "Si décoché : Administrateur Site, limité aux sites assignés à l'utilisateur.")
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenants_roles'
        ordering = ['nom']
        unique_together = ['entreprise', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.entreprise.nom})"


class InvitationUtilisateur(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise  = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='invitations')
    site        = models.ForeignKey('Site', on_delete=models.SET_NULL, null=True, blank=True,
                    related_name='invitations',
                    help_text="Site auquel l'utilisateur sera rattaché à l'acceptation. "
                              "Si vide : site principal de l'entreprise par défaut.")
    email       = models.EmailField()
    prenom      = models.CharField(max_length=100)
    nom         = models.CharField(max_length=100)
    role        = models.ForeignKey('RolePersonnalise', on_delete=models.SET_NULL, null=True, blank=True)
    token       = models.UUIDField(default=uuid.uuid4, unique=True)
    acceptee    = models.BooleanField(default=False)
    expire_le   = models.DateTimeField()
    invite_par  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitations_envoyees')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenants_invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation {self.email} — {self.entreprise.nom}"

    @property
    def est_expiree(self):
        from django.utils import timezone
        return timezone.now() > self.expire_le