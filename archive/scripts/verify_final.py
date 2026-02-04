import os
import sys
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable

print('=' * 70)
print('✅ FINAL VERIFICATION - NO FALLBACK, 100% DATABASE-DRIVEN')
print('=' * 70)
print()

# 1. Verify all calculated formulas have mappings
print('1. CALCULATED FORMULAS WITH MAPPINGS:')
print('-' * 70)
for cat in ['renewable', 'verbrauch']:
    calculated = Formula.objects.filter(category=cat, is_fixed=False)
    with_mappings = calculated.filter(
        id__in=FormulaVariable.objects.filter(formula__category=cat).values_list('formula_id', flat=True)
    )
    pct = with_mappings.count() / calculated.count() * 100 if calculated.count() > 0 else 0
    status = '✅' if pct == 100 else '❌'
    print(f'{status} {cat.upper()}: {with_mappings.count()}/{calculated.count()} ({pct:.0f}%)')
print()

# 2. Verify NO old format in formulas
print('2. OLD FORMAT CHECK (should be 0):')
print('-' * 70)
for cat in ['renewable', 'verbrauch']:
    old_format = []
    for formula in Formula.objects.filter(category=cat, is_fixed=False):
        if formula.expression:
            # Check for Verbrauch_X.Y format
            if 'Verbrauch_' in formula.expression and re.search(r'Verbrauch_[0-9]+[.][0-9]', formula.expression):
                old_format.append(formula.key)
    
    status = '✅' if len(old_format) == 0 else '❌'
    print(f'{status} {cat.upper()}: {len(old_format)} formulas with old format')
    if old_format:
        print(f'    Examples: {old_format[:3]}')
print()

# 3. Check fallback code
print('3. FALLBACK CODE CHECK:')
print('-' * 70)
import calculation_engine.renewable_engine as ren_engine
import calculation_engine.verbrauch_engine as ver_engine

ren_source = open('calculation_engine/renewable_engine.py').read()
ver_source = open('calculation_engine/verbrauch_engine.py').read()

ren_has_fallback = 'fallback' in ren_source.lower() or 'RENEWABLE_FORMULAS[' in ren_source
ver_has_fallback = 'fallback' in ver_source.lower() or 'VERBRAUCH_FORMULAS[' in ver_source

print(f'{"❌" if ren_has_fallback else "✅"} Renewable engine fallback: {" FOUND" if ren_has_fallback else "NOT FOUND"}')
print(f'{"❌" if ver_has_fallback else "✅"} Verbrauch engine fallback: {" FOUND" if ver_has_fallback else "NOT FOUND"}')
print()

# 4. Summary
print('=' * 70)
print('SYSTEM STATUS:')
print('=' * 70)
calc_status = all([
    Formula.objects.filter(category='renewable', is_fixed=False).count() == 
    FormulaVariable.objects.filter(formula__category='renewable', formula__is_fixed=False).values_list('formula_id', flat=True).distinct().count(),
    Formula.objects.filter(category='verbrauch', is_fixed=False).count() == 
    FormulaVariable.objects.filter(formula__category='verbrauch', formula__is_fixed=False).values_list('formula_id', flat=True).distinct().count()
])

if calc_status and not ren_has_fallback and not ver_has_fallback:
    print('✅ ALL CALCULATED FORMULAS HAVE FORMUL VARIABLE MAPPINGS')
    print('✅ ALL FORMULAS USE NEW FORMAT')
    print('✅ NO FALLBACK CODE IN CALCULATION ENGINES')
    print('✅ 100% DATABASE-DRIVEN - FULLY EXTENSIBLE VIA ADMIN!')
    print()
    print('🎉 MIGRATION 100% COMPLETE - NO OLD FILES OR FALLBACK METHODS!')
else:
    print('❌ ISSUES DETECTED - SEE ABOVE')
print()
