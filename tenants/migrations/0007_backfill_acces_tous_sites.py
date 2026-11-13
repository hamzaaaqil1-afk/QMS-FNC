"""
Migration : ajoute RolePersonnalise.acces_tous_sites et InvitationUtilisateur.site.

Le schéma (AddField) sera généré par `python manage.py makemigrations tenants`.
Ce fichier ne contient QUE la partie données (RunPython) : place-le après la
migration de schéma générée, en adaptant `dependencies` ci-dessous.

Backfill : tout rôle existant avec est_admin=True passe automatiquement à
acces_tous_sites=True, pour préserver exactement le comportement actuel
(avant ce changement, est_admin donnait accès à tous les sites).
"""

from django.db import migrations


def backfill_acces_tous_sites(apps, schema_editor):
    RolePersonnalise = apps.get_model('tenants', 'RolePersonnalise')
    RolePersonnalise.objects.filter(est_admin=True).update(acces_tous_sites=True)


def revenir_en_arriere(apps, schema_editor):
    RolePersonnalise = apps.get_model('tenants', 'RolePersonnalise')
    RolePersonnalise.objects.filter(est_admin=True).update(acces_tous_sites=False)


class Migration(migrations.Migration):

    dependencies = [
        # ⚠️ À adapter : nom exact de ta migration tenants générée par makemigrations
        # (celle qui ajoute acces_tous_sites et site).
        ('tenants', '0006_invitationutilisateur_site_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_acces_tous_sites, revenir_en_arriere),
    ]