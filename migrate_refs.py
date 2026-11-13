import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from qms.models import NonConformite, ServiceProcessus, ClassificationFNC, OrigineEcart, StatutFNC

processus_map = {o.code: o for o in ServiceProcessus.objects.all()}
classif_map   = {o.code: o for o in ClassificationFNC.objects.all()}
origine_map   = {o.code: o for o in OrigineEcart.objects.all()}
statut_map    = {o.code: o for o in StatutFNC.objects.all()}

print('Processus disponibles:', list(processus_map.keys()))
print('Classifications disponibles:', list(classif_map.keys()))
print('Origines disponibles:', list(origine_map.keys()))
print('Statuts disponibles:', list(statut_map.keys()))

ok = 0
manquants = []

for fnc in NonConformite.objects.all():
    modifie = False

    if fnc.processus and not fnc.processus_ref_id:
        ref = processus_map.get(fnc.processus)
        if ref:
            fnc.processus_ref = ref
            modifie = True
        else:
            manquants.append(f'FNC {fnc.numero} processus={fnc.processus}')

    if fnc.classification and not fnc.classification_ref_id:
        ref = classif_map.get(fnc.classification.lower())
        if ref:
            fnc.classification_ref = ref
            modifie = True
        else:
            manquants.append(f'FNC {fnc.numero} classification={fnc.classification}')

    if fnc.origine_ecart and not fnc.origine_ecart_ref_id:
        ref = origine_map.get(fnc.origine_ecart)
        if ref:
            fnc.origine_ecart_ref = ref
            modifie = True
        else:
            manquants.append(f'FNC {fnc.numero} origine={fnc.origine_ecart}')

    if fnc.statut and not fnc.statut_ref_id:
        ref = statut_map.get(fnc.statut)
        if ref:
            fnc.statut_ref = ref
            modifie = True
        else:
            manquants.append(f'FNC {fnc.numero} statut={fnc.statut}')

    if modifie:
        fnc.save(update_fields=['processus_ref', 'classification_ref', 'origine_ecart_ref', 'statut_ref'])
        ok += 1

print(f'\nFNC mises a jour: {ok}')
print(f'Valeurs non trouvees: {len(manquants)}')
for m in manquants:
    print(' -', m)