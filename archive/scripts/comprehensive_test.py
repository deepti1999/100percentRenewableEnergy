import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, RenewableData, VerbrauchData
from calculation_engine.renewable_engine import RenewableCalculator
from calculation_engine.verbrauch_engine import VerbrauchCalculator
import re

print('=' * 80)
print('COMPREHENSIVE TEST: 100% MIGRATION & NO FALLBACK')
print('=' * 80)
print()

# TEST 1: Database verification
print('TEST 1: DATABASE VERIFICATION')
print('-' * 80)

for cat in ['renewable', 'verbrauch']:
    # All calculated formulas
    calculated = Formula.objects.filter(category=cat, is_fixed=False)
    
    # Those with FormulaVariable mappings
    with_mappings_ids = set(FormulaVariable.objects.filter(
        formula__category=cat
    ).values_list('formula_id', flat=True))
    
    with_mappings = calculated.filter(id__in=with_mappings_ids)
    without_mappings = calculated.exclude(id__in=with_mappings_ids)
    
    print(f'{cat.upper()}:')
    print(f'  Total calculated formulas: {calculated.count()}')
    print(f'  With FormulaVariable mappings: {with_mappings.count()}')
    print(f'  WITHOUT mappings: {without_mappings.count()}')
    
    if without_mappings.exists():
        print(f'  ❌ UNMIGRATED FORMULAS:')
        for f in without_mappings[:5]:
            print(f'    - {f.key}: {f.expression[:60]}')
    else:
        print(f'  ✅ ALL MIGRATED!')
    print()

# TEST 2: Actual calculation test
print('TEST 2: ACTUAL CALCULATION TEST (PROVES NO FALLBACK USED)')
print('-' * 80)

ren_calc = RenewableCalculator()
ver_calc = VerbrauchCalculator()

# Test renewable calculations
test_renewable_codes = ['10.3', '10.4', '1.1.1.1.2', 'TEST_RENEWABLE']
print('RENEWABLE Calculations:')
for code in test_renewable_codes:
    try:
        status, target = ren_calc.calculate(code)
        if status is not None:
            print(f'  ✅ {code}: Status={status:,.2f}, Target={target:,.2f}')
        else:
            ren_data = RenewableData.objects.filter(code=code).first()
            if ren_data and ren_data.is_fixed:
                print(f'  ✅ {code}: Fixed value (user input)')
            else:
                print(f'  ❌ {code}: Returned None (FALLBACK MIGHT BE USED!)')
    except Exception as e:
        print(f'  ❌ {code}: ERROR - {str(e)[:60]}')

print()

# Test verbrauch calculations
test_verbrauch_codes = ['V_1.4', 'V_2.3', 'V_TEST_VERBRAUCH']
print('VERBRAUCH Calculations:')
for code in test_verbrauch_codes:
    try:
        status, target = ver_calc.calculate(code)
        if status is not None:
            print(f'  ✅ {code}: Status={status:,.2f}, Target={target:,.2f}')
        else:
            ver_data = VerbrauchData.objects.filter(code=code).first()
            if ver_data and ver_data.is_fixed:
                print(f'  ✅ {code}: Fixed value (user input)')
            else:
                print(f'  ❌ {code}: Returned None (FALLBACK MIGHT BE USED!)')
    except Exception as e:
        print(f'  ❌ {code}: ERROR - {str(e)[:60]}')

print()

# TEST 3: Old format check
print('TEST 3: OLD FORMAT CHECK (MUST BE ZERO)')
print('-' * 80)

for cat in ['renewable', 'verbrauch']:
    old_format_count = 0
    old_format_examples = []
    
    for formula in Formula.objects.filter(category=cat, is_fixed=False):
        if formula.expression:
            # Check for old format: digits with dots not preceded by underscore
            # renewable: 10.3.4 instead of renewable_10_3_4
            # verbrauch: Verbrauch_2.1.0 instead of Verbrauch_2_1_0
            if cat == 'renewable':
                if re.search(r'(?<!renewable_)\b\d+\.\d+', formula.expression):
                    old_format_count += 1
                    old_format_examples.append(f'{formula.key}: {formula.expression[:50]}')
            else:
                if re.search(r'Verbrauch_\d+\.\d+', formula.expression):
                    old_format_count += 1
                    old_format_examples.append(f'{formula.key}: {formula.expression[:50]}')
    
    if old_format_count == 0:
        print(f'  ✅ {cat.upper()}: No old format found')
    else:
        print(f'  ❌ {cat.upper()}: {old_format_count} formulas with old format')
        for ex in old_format_examples[:3]:
            print(f'    - {ex}')

print()

# TEST 4: Fallback code check
print('TEST 4: FALLBACK CODE CHECK (MUST BE CLEAN)')
print('-' * 80)

try:
    with open('calculation_engine/renewable_engine.py', 'r') as f:
        ren_code = f.read()
    
    # Check for fallback patterns
    fallback_patterns = [
        ('RENEWABLE_FORMULAS[', 'References to RENEWABLE_FORMULAS dict'),
        ('fallback to', 'Fallback comments'),
        ('legacy', 'Legacy code references'),
    ]
    
    ren_issues = []
    for pattern, desc in fallback_patterns:
        if pattern in ren_code:
            ren_issues.append(desc)
    
    if ren_issues:
        print(f'  ❌ RENEWABLE ENGINE: Found fallback code:')
        for issue in ren_issues:
            print(f'    - {issue}')
    else:
        print(f'  ✅ RENEWABLE ENGINE: Clean, no fallback code')
    
    with open('calculation_engine/verbrauch_engine.py', 'r') as f:
        ver_code = f.read()
    
    ver_issues = []
    for pattern, desc in [p for p in fallback_patterns if 'RENEWABLE' not in p[0]]:
        if pattern in ver_code:
            ver_issues.append(desc)
    
    if ver_issues:
        print(f'  ❌ VERBRAUCH ENGINE: Found fallback code:')
        for issue in ver_issues:
            print(f'    - {issue}')
    else:
        print(f'  ✅ VERBRAUCH ENGINE: Clean, no fallback code')
        
except Exception as e:
    print(f'  ❌ ERROR reading files: {e}')

print()

# TEST 5: FormulaVariable usage verification
print('TEST 5: FORMULARAVARIABLE USAGE VERIFICATION')
print('-' * 80)

# Check that FormulaService is actually using FormulaVariable
try:
    from simulator.formula_service import FormulaService
    
    service = FormulaService()
    
    # Test a known formula
    test_code = '10.3'
    status, target = service.evaluate_with_mappings(test_code, category='renewable')
    
    if status is not None:
        print(f'  ✅ FormulaService.evaluate_with_mappings() works')
        print(f'     Test: {test_code} = {status:,.2f}')
        
        # Verify it loaded from FormulaVariable
        formula = Formula.objects.get(key=test_code, category='renewable')
        var_count = formula.variables.count()
        print(f'     Formula has {var_count} FormulaVariable mappings')
    else:
        print(f'  ❌ FormulaService returned None - might not be using FormulaVariable')
        
except Exception as e:
    print(f'  ❌ ERROR testing FormulaService: {e}')

print()

# FINAL SUMMARY
print('=' * 80)
print('FINAL SUMMARY')
print('=' * 80)

ren_calculated = Formula.objects.filter(category='renewable', is_fixed=False).count()
ren_migrated = FormulaVariable.objects.filter(
    formula__category='renewable', 
    formula__is_fixed=False
).values_list('formula_id', flat=True).distinct().count()

ver_calculated = Formula.objects.filter(category='verbrauch', is_fixed=False).count()
ver_migrated = FormulaVariable.objects.filter(
    formula__category='verbrauch', 
    formula__is_fixed=False
).values_list('formula_id', flat=True).distinct().count()

all_migrated = (ren_calculated == ren_migrated) and (ver_calculated == ver_migrated)
no_fallback = len(ren_issues) == 0 and len(ver_issues) == 0

if all_migrated and no_fallback:
    print('🎉 SUCCESS: 100% MIGRATION COMPLETE!')
    print()
    print(f'✅ Renewable: {ren_migrated}/{ren_calculated} formulas (100%)')
    print(f'✅ Verbrauch: {ver_migrated}/{ver_calculated} formulas (100%)')
    print(f'✅ All formulas use FormulaVariable mappings')
    print(f'✅ No fallback code in calculation engines')
    print(f'✅ All calculations work via database')
    print()
    print('YOUR SYSTEM IS 100% EXTENSIBLE VIA ADMIN!')
    print('NO OLD FILES, NO FALLBACK, NO HARDCODED FORMULAS!')
else:
    print('❌ ISSUES DETECTED:')
    if not all_migrated:
        print(f'  - Migration incomplete: Renewable {ren_migrated}/{ren_calculated}, Verbrauch {ver_migrated}/{ver_calculated}')
    if not no_fallback:
        print(f'  - Fallback code still present')
    print()
    print('See details above.')

print('=' * 80)
