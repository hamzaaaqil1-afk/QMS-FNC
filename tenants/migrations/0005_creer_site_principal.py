"""
Migration de rétrocompatibilité multi-site.

Pour chaque Entreprise existante :
  1. Crée un Site "Site principal" (code PRINCIPAL, est_principal=True)
  2. Rattache tous les ProfilUtilisateur de cette entreprise à ce site
     via sites_autorises

Cette migration doit être placée APRÈS la migration qui crée le modèle
Site et le champ ProfilUtilisateur.sites_autorises (générée normalement
par `python manage.py makemigrations tenants`).

IMPORTANT : renomme ce fichier en respectant la convention Django
(ex: 0009_creer_site_principal.py) et vérifie que `dependencies` ci-dessous
pointe bien vers ta dernière migration de tenants (celle qui contient
le CreateModel Site + AddField sites_autorises).
"""

from django.db import migrations


def creer_sites_principaux(apps, schema_editor):
    Entreprise = apps.get_model('tenants', 'Entreprise')
    Site = apps.get_model('tenants', 'Site')
    ProfilUtilisateur = apps.get_model('tenants', 'ProfilUtilisateur')

    for entreprise in Entreprise.objects.all():
        site, cree = Site.objects.get_or_create(
            entreprise=entreprise,
            code='PRINCIPAL',
            defaults={
                'nom': 'Site principal',
                'est_principal': True,
                'actif': True,
            },
        )

        # Rattache tous les utilisateurs existants de cette entreprise à ce site
        profils = ProfilUtilisateur.objects.filter(entreprise=entreprise)
        for profil in profils:
            profil.sites_autorises.add(site)


def revenir_en_arriere(apps, schema_editor):
    # Suppression des sites créés par cette migration (les M2M partent en cascade)
    Site = apps.get_model('tenants', 'Site')
    Site.objects.filter(code='PRINCIPAL', est_principal=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        # ⚠️ À adapter : mets ici le nom exact de ta dernière migration
        # tenants générée par makemigrations (celle qui crée Site et
        # ajoute sites_autorises sur ProfilUtilisateur).
        ('tenants', '0004_site_profilutilisateur_sites_autorises'),
    ]

    operations = [
        migrations.RunPython(creer_sites_principaux, revenir_en_arriere),
    ]