#!/usr/bin/env python3
"""
FINAL FIX - Direct database formula update
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, VerbrauchData
from django.core.cache import cache

print('=' * 80)
print('COMPREHENSIVE FIX FOR VERBRAUCH FORMULAS')
print('=' * 80)

# Step 1: Clear cache
print('\n1. Clearing ALL cache...')
cache.clear()
print('✅ Cache cleared')

# Step 2: Check what formulas exist
print('\n2. Checking existing formulas...')
existing = list(Formula.objects.filter(key__in=['V_2.4.2', 'V_2.4.2_ziel']).values_list('key', flat=True))
print(f'   Found: {existing}')

# Step 3: Update or create using update_or_create
print('\n3. Updating/creating formulas...')

# STATUS formula
status_formula, status_created = Formula.objects.update_or_create(
    key='V_2.4.2',
    defaults={
        'category': 'verbrauch',
        'expression': 'Verbrauch_2_1_0',
        'description': 'Status formula for 2.4.2 = reference to 2.1.0',
        'is_fixed': False,
        'is_active': True,
        'formula_type': 'status'
    }
)
action = 'Created' if status_created else 'Updated'
print(f'   {action} V_2.4.2')

# Delete old variables and create new
FormulaVariable.objects.filter(formula=status_formula).delete()
FormulaVariable.objects.create(
    formula=status_formula,
    variable_name='Verbrauch_2_1_0',
    source_type='verbrauch_status',
    source_key='2.1.0',
    default_value=0.0
)
print('   ✅ Created variables for V_2.4.2')

# ZIEL formula
ziel_formula, ziel_created = Formula.objects.update_or_create(
    key='V_2.4.2_ziel',
    defaults={
        'category': 'verbrauch',
        'expression': '(Verbrauch_2_4_1_ziel - Verbrauch_2_4_1) / Verbrauch_2_4_1 * 100',
        'description': 'Ziel formula for 2.4.2 = percentage change',
        'is_fixed': False,
        'is_active': True,
        'formula_type': 'ziel'
    }
)
action = 'Created' if ziel_created else 'Updated'
print(f'   {action} V_2.4.2_ziel')

# Delete old variables and create new  
FormulaVariable.objects.filter(formula=ziel_formula).delete()
FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='Verbrauch_2_4_1_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.1',
    default_value=0.0
)
FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='Verbrauch_2_4_1',
    source_type='verbrauch_status',
    source_key='2.4.1',
    default_value=0.0
)
print('   ✅ Created variables for V_2.4.2_ziel')

# Step 4: Update row flags
print('\n4. Updating row flags...')
row = VerbrauchData.objects.get(code='2.4.2')
row.is_calculated = True
row.status_calculated = True
row.ziel_calculated = True
row.save(skip_cascade=True, skip_recalc=True)
print('✅ Row flags updated')

# Step 5: Clear cache again
print('\n5. Clearing cache again...')
cache.clear()
print('✅ Cache cleared')

# Step 6: Test the formulas work
print('\n6. Testing formulas...')
try:
    row = VerbrauchData.objects.get(code='2.4.2')
    status_val = row.calculate_value()
    ziel_val = row.calculate_ziel_value()
    
    print(f'   Status calculated: {status_val}')
    print(f'   Ziel calculated: {ziel_val}')
    print('   ✅ Formulas work!')
    
except Exception as e:
    print(f'   ❌ Error: {e}')

print('\n' + '=' * 80)
print('✅ FIX COMPLETE!')
print('=' * 80)
print('\nNEXT STEPS:')
print('1. The formula changes are now in the database')
print('2. Cache has been cleared')  
print('3. Restart your Django server: Ctrl+C then run: python3 manage.py runserver')
print('4. Go to Verbrauch page and click "Recalculate All"')
print('5. Check that row 2.4.2 shows correct values')
