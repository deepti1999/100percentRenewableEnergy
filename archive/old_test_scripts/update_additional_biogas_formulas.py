import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Set formulas for the additional calculated biogas entries
additional_formula_updates = {
    '5.4.2.4': '5.4 * 5.4.2 / 100 * 5.4.2.3 / 100 * 5.4.2.1 / 100',
    '5.4.3.2': '5.4 * 5.4.3 / 100 * 5.4.3.1 / 100',
    '5.4.4.2': '5.4 * 5.4.4 / 100 * 5.4.4.1 / 100'
}

for code, formula in additional_formula_updates.items():
    try:
        entry = RenewableData.objects.get(code=code)
        entry.formula = formula
        entry.save()
        print(f'Updated {code}: formula = {formula}')
    except RenewableData.DoesNotExist:
        print(f'Entry {code} not found')

print('✅ Additional biogas calculation formulas updated!')