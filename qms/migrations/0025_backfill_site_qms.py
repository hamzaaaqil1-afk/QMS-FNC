"""
Migration de rétrocompatibilité : backfill du champ `site` sur les modèles
QMS existants, en le déduisant du site principal de l'entreprise de chaque
ligne.

À placer APRÈS la migration de schéma générée par
`python manage.py makemigrations qms` (celle qui ajoute le champ `site`
sur NonConformite, Analyse5M, ActionCorrective, CAPA, Audit, PlanAction).

⚠️ Adapte `dependencies` ci-dessous avec le nom exact de cette migration.
"""

from django.db import migrations


def backfill_site(apps, schema_editor):
    Site             = apps.get_model('tenants', 'Site')
    NonConformite    = apps.get_model('qms', 'NonConformite')
    Analyse5M        = apps.get_model('qms', 'Analyse5M')
    ActionCorrective = apps.get_model('qms', 'ActionCorrective')
    CAPA             = apps.get_model('qms', 'CAPA')
    Audit            = apps.get_model('qms', 'Audit')
    PlanAction       = apps.get_model('qms', 'PlanAction')

    # Cache : entreprise_id -> Site principal, pour éviter une requête par ligne
    sites_principaux = {
        s.entreprise_id: s for s in Site.objects.filter(est_principal=True)
    }

    # NonConformite utilise le champ entreprise_tenant (nom différent des autres)
    for nc in NonConformite.objects.exclude(entreprise_tenant__isnull=True).exclude(site__isnull=False):
        site = sites_principaux.get(nc.entreprise_tenant_id)
        if site:
            nc.site = site
            nc.save(update_fields=['site'])

    # Les autres modèles utilisent tous un champ `entreprise` classique
    for modele in (Analyse5M, ActionCorrective, CAPA, Audit, PlanAction):
        for obj in modele.objects.exclude(entreprise__isnull=True).exclude(site__isnull=False):
            site = sites_principaux.get(obj.entreprise_id)
            if site:
                obj.site = site
                obj.save(update_fields=['site'])


def revenir_en_arriere(apps, schema_editor):
    # Rien à défaire explicitement : le champ `site` lui-même est supprimé
    # par le rollback de la migration de schéma correspondante.
    pass


class Migration(migrations.Migration):

    dependencies = [
        # ⚠️ À adapter : nom exact de ta migration qms générée par makemigrations
        # (celle qui ajoute le champ site sur les 6 modèles).
        ('qms', '0024_actioncorrective_site_analyse5m_site_audit_site_and_more'),
        ('tenants', '0005_creer_site_principal'),
    ]

    operations = [
        migrations.RunPython(backfill_site, revenir_en_arriere),
    ]