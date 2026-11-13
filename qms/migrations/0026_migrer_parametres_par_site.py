"""
Migration qms auto-suffisante : NE PAS générer via makemigrations pour ce
changement précis — écrite à la main pour garantir l'ordre correct des
opérations (ajout des nouveaux champs -> transfert des données -> suppression
des anciens champs). Si makemigrations qms tourne avant ce fichier, il
regroupera AddField et RemoveField dans la même migration sans étape de
transfert entre les deux, et les anciennes valeurs de compteur seraient
perdues avant d'avoir pu être copiées sur le site principal.

⚠️ Adapte les deux entrées `dependencies` ci-dessous :
  - 'qms', ... -> le nom de ta dernière migration qms actuelle
    (celle qui a ajouté site sur NonConformite/Audit/CAPA/etc., ex: 0025_backfill_site_qms)
  - 'tenants', ... -> le nom de la migration tenants qui ajoute
    compteur_fnc_actuel / compteur_fnc_derniere_annee / compteur_fnc_dernier_mois
    sur Site (générée normalement via `python manage.py makemigrations tenants`,
    à faire AVANT celle-ci)
"""

from django.db import migrations, models
import django.db.models.deletion


def migrer_parametres(apps, schema_editor):
    ParametresEntreprise = apps.get_model('qms', 'ParametresEntreprise')
    Entreprise = apps.get_model('tenants', 'Entreprise')
    Site = apps.get_model('tenants', 'Site')

    herakles = Entreprise.objects.filter(nom='Herakles').first()
    if not herakles:
        return

    params = ParametresEntreprise.objects.first()
    if not params:
        return

    ancien_compteur = params.compteur_actuel
    ancienne_annee  = params.derniere_annee
    ancien_mois     = params.dernier_mois

    params.entreprise = herakles
    params.save()

    site_principal = Site.objects.filter(entreprise=herakles, est_principal=True).first()
    if site_principal:
        site_principal.compteur_fnc_actuel = ancien_compteur or 1
        site_principal.compteur_fnc_derniere_annee = ancienne_annee
        site_principal.compteur_fnc_dernier_mois = ancien_mois
        site_principal.save(update_fields=[
            'compteur_fnc_actuel', 'compteur_fnc_derniere_annee', 'compteur_fnc_dernier_mois'
        ])


def revenir_en_arriere(apps, schema_editor):
    pass  # pas de retour en arrière propre pour ce transfert de données


class Migration(migrations.Migration):

    dependencies = [
        ('qms', '0025_backfill_site_qms'),
        ('tenants', '0009_site_compteur_fnc_actuel_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parametresentreprise',
            name='entreprise',
            field=models.OneToOneField(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='parametres_qms', to='tenants.entreprise',
            ),
        ),
        migrations.AddField(
            model_name='parametresentreprise',
            name='inclure_code_site',
            field=models.BooleanField(
                default=True,
                help_text="Ex: NC-LYON-2026-06-0001. Recommandé en multi-site pour identifier "
                          "l'origine d'une FNC directement depuis son numéro.",
                verbose_name='Inclure le code du site dans le numéro',
            ),
        ),

        # ── Transfert des données AVANT de supprimer les anciens champs ────
        migrations.RunPython(migrer_parametres, revenir_en_arriere),

        migrations.RemoveField(model_name='parametresentreprise', name='compteur_actuel'),
        migrations.RemoveField(model_name='parametresentreprise', name='derniere_annee'),
        migrations.RemoveField(model_name='parametresentreprise', name='dernier_mois'),
    ]