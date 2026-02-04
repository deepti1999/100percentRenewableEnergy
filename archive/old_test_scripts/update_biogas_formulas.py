import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Set formulas for calculated biogas entries
formula_updates = {
    '5.1.2': '5.1 * 5.1.1 / 1000',
    '5.4': '5.1.2 + 5.2 + 5.3', 
    '5.4.1.1': '5.4 * 5.4.1 / 100',
    '5.4.2.2': '5.4 * 5.4.2 / 100 * 5.4.2.1 / 100'
}

for code, formula in formula_updates.items():
    try:
        entry = RenewableData.objects.get(code=code)
        entry.formula = formula
        entry.save()
        print(f'Updated {code}: formula = {formula}')
    except RenewableData.DoesNotExist:
        print(f'Entry {code} not found')

print('✅ Biogas calculation formulas updated!')