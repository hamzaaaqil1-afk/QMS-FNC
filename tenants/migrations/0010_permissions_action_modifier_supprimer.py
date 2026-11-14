"""
Migration de données : ajoute les permissions qms.modifier_action et
qms.supprimer_action, utilisées par ActionCorrectivelViewSet (qms/views.py)
pour distinguer modifier/clôturer/supprimer une action corrective, au lieu
de tout faire dépendre de qms.cloturer_action comme avant.

Sans ces deux lignes, aucun rôle personnalisé ne peut se voir attribuer ces
permissions (elles n'existeraient pas en base) : seuls les administrateurs
(qui contournent toujours la vérification de permission) pourraient encore
modifier/supprimer une action. Cette migration évite ce blocage pour les
autres utilisateurs.
"""

from django.db import migrations


PERMISSIONS = [
    ('qms.modifier_action', "Modifier une action corrective (hors clôture)", 'qms'),
    ('qms.supprimer_action', "Supprimer une action corrective", 'qms'),
]


def ajouter_permissions(apps, schema_editor):
    Permission = apps.get_model('tenants', 'Permission')
    for code, libelle, module in PERMISSIONS:
        Permission.objects.get_or_create(
            code=code,
            defaults={'libelle': libelle, 'module': module},
        )


def retirer_permissions(apps, schema_editor):
    Permission = apps.get_model('tenants', 'Permission')
    Permission.objects.filter(code__in=[code for code, _, _ in PERMISSIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0009_site_compteur_fnc_actuel_and_more'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions, retirer_permissions),
    ]
