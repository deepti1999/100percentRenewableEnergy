"""
Fix all broken formulas in RenewableData sections 1-9
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('='*80)
print('FIXING ALL BROKEN FORMULAS')
print('='*80)

fixes = []

# 1. Fix formulas with variable names - convert to code references
print('\n1. Fixing formulas with variable names...')

# Pattern: Bruttostromerzeugung/Vollbetriebsstunden
# Need to find what these codes are for each section

variable_formulas = {
    '1.1.2.1.2.2': {
        'old': 'Bruttostromerzeugung/Vollbetriebsstunden',
        'new': '1.1.2.1.2.1 / 1.1.2.1.1',  # electricity / operating hours
        'description': 'PV Freiflächen installed power'
    },
    '1.2.1.2.2': {
        'old': 'Bruttostromerzeugung/Vollbetriebsstunden',
        'new': '1.2.1.2.1 / 1.2.1.1',  # electricity / operating hours
        'description': 'PV Dachflächen installed power'
    },
}

for code, fix_data in variable_formulas.items():
    item = RenewableData.objects.filter(code=code).first()
    if item:
        item.formula = fix_data['new']
        item.save()
        print(f"  ✓ {code}: {fix_data['description']}")
        print(f"    Old: {fix_data['old']}")
        print(f"    New: {fix_data['new']}")
        
        # Test
        calc_s, calc_t = item.get_calculated_values()
        print(f"    Result: S={calc_s}, T={calc_t}")
        fixes.append(code)

# 2. Fix CALCULATED_ placeholders in section 4 (biomass)
print('\n2. Fixing section 4 biomass formulas...')

section_4_formulas = {
    '4.1.1.1.1.2': {
        'formula': '4.1.1.1.1.1 * 4.1.1.1.1 / 100',
        'description': 'Energy wood from forestry'
    },
    '4.1.2.1.2': {
        'formula': '4.1.2.1.1 * 4.1.2.1 / 100',
        'description': 'Energy wood from landscape'
    },
    '4.1.3': {
        'formula': '4.1.1.1.1.2 + 4.1.2.1.2',
        'description': 'Total energy wood'
    },
    '4.2.1.1.2': {
        'formula': '4.2.1.1.1 * 4.2.1.1 / 100',
        'description': 'Straw fuel'
    },
    '4.3': {
        'formula': '4.1.3 + 4.2.1.1.2',
        'description': 'Total solid biofuel (NAWARO)'
    },
    '4.3.1': {
        'formula': '4.3 * 4.1.3.1 / 100',
        'description': 'For building heat'
    },
    '4.3.2': {
        'formula': '4.3 * 4.1.3.2 / 100',
        'description': 'For process heat'
    },
    '4.3.3': {
        'formula': '4.3 * 4.1.3.3 / 100',
        'description': 'For electricity'
    },
    '4.3.3.4': {
        'formula': '4.3.3.2 * 4.3.3.3 / 4.3.3.1',
        'description': 'CHP district heat'
    },
    '4.3.4': {
        'formula': '4.3 * 4.1.3.4 / 100',
        'description': 'For heating plants'
    },
    '4.3.4.2': {
        'formula': '4.3.4 * 4.3.4.1 / 100',
        'description': 'Heating plant district heat'
    },
    '4.4': {
        'formula': '4.4.1 + 4.4.2',
        'description': 'Biogenic waste (solid)'
    },
}

for code, fix_data in section_4_formulas.items():
    item = RenewableData.objects.filter(code=code).first()
    if item:
        old_formula = item.formula
        item.formula = fix_data['formula']
        item.save()
        print(f"  ✓ {code}: {fix_data['description']}")
        print(f"    Old: {old_formula}")
        print(f"    New: {fix_data['formula']}")
        
        # Test
        try:
            calc_s, calc_t = item.get_calculated_values()
            if calc_s is not None or calc_t is not None:
                s_gwh = calc_s / 1000 if calc_s and calc_s > 1000 else calc_s
                t_gwh = calc_t / 1000 if calc_t and calc_t > 1000 else calc_t
                print(f"    Result: S={s_gwh:.3f} GWh, T={t_gwh:.3f} GWh")
            else:
                print(f"    Result: None (missing parent data)")
        except Exception as e:
            print(f"    Error: {e}")
        fixes.append(code)

print('\n' + '='*80)
print(f'FIXED {len(fixes)} FORMULAS')
print('='*80)

# Now test if 4.3.4.2 gives us the 3.034 GWh
print('\nTesting 4.3.4.2 (biomass district heat):')
item = RenewableData.objects.filter(code='4.3.4.2').first()
if item:
    calc_s, calc_t = item.get_calculated_values()
    if calc_s:
        s_gwh = calc_s / 1000 if calc_s > 1000 else calc_s
        print(f'  Calculated: {s_gwh:.3f} GWh')
        print(f'  Expected: 3.034 GWh')
        if abs(s_gwh - 3.034) < 0.1:
            print('  ✓ MATCH!')
        else:
            print(f'  ✗ Difference: {abs(s_gwh - 3.034):.3f} GWh')
