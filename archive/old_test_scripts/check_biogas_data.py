import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Check all biogas entries and their complete data
biogas_entries = RenewableData.objects.filter(code__startswith='5.').order_by('code')
print(f'Found {biogas_entries.count()} biogas entries:')

# Focus on the problematic ones
for entry in biogas_entries.filter(code__in=['5.2', '5.3']):
    print(f'{entry.code}: {entry.name}')
    print(f'  category: "{entry.category}"')
    print(f'  subcategory: "{entry.subcategory}"') 
    print(f'  status_value: {entry.status_value}')
    print(f'  target_value: {entry.target_value}')
    print(f'  unit: "{entry.unit}"')
    print(f'  formula: "{entry.formula}"')
    print(f'  is_fixed: {entry.is_fixed}')
    print()

print("\nChecking if category/subcategory are properly set...")
all_biogas = RenewableData.objects.filter(code__startswith='5.')
for entry in all_biogas:
    if not entry.category or not entry.subcategory:
        print(f"Missing category/subcategory: {entry.code} - category='{entry.category}', subcategory='{entry.subcategory}'")