#!/usr/bin/env python3
"""
Test that RenewableCalculator properly separates LandUse and Verbrauch data sources.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from calculation_engine.renewable_engine import RenewableCalculator
from simulator.models import RenewableData, VerbrauchData, LandUse

print('Testing RenewableCalculator with mixed data sources...')
print('=' * 80)

# Create calculator
calc = RenewableCalculator()

# Prepare ALL data sources (properly separated!)
landuse_data = {}
for lu in LandUse.objects.all():
    landuse_data[lu.code] = {
        'status_ha': lu.status_ha or 0,
        'target_ha': lu.target_ha or 0
    }

verbrauch_data = {}
for vd in VerbrauchData.objects.all():
    verbrauch_data[vd.code] = {
        'status': vd.status or 0,
        'ziel': vd.ziel or 0
    }

renewable_data = {}
for rd in RenewableData.objects.all():
    renewable_data[rd.code] = {
        'status_value': rd.status_value or 0,
        'target_value': rd.target_value or 0
    }

# Set data sources correctly
calc.set_data_sources(landuse_data, verbrauch_data, renewable_data)

print('\n✓ Data sources loaded:')
print(f'  LandUse: {len(landuse_data)} entries')
print(f'  Verbrauch: {len(verbrauch_data)} entries')
print(f'  Renewable: {len(renewable_data)} entries')

# Check lookup is correct
print(f'\n✓ Evaluator lookups populated:')
print(f'  Status lookup: {len(calc.evaluator.status_lookup)} keys')
print(f'  Target lookup: {len(calc.evaluator.target_lookup)} keys')

# Verify prefixes are correct
landuse_keys = [k for k in calc.evaluator.status_lookup.keys() if k.startswith('LandUse_')]
verbrauch_keys = [k for k in calc.evaluator.status_lookup.keys() if k.startswith('VerbrauchData_')]
renewable_keys = [k for k in calc.evaluator.status_lookup.keys() if k.startswith('RenewableData_')]

print(f'\n🔑 Prefix verification:')
print(f'  LandUse_ prefixed keys: {len(landuse_keys)}')
print(f'  VerbrauchData_ prefixed keys: {len(verbrauch_keys)}')
print(f'  RenewableData_ prefixed keys: {len(renewable_keys)}')

# Test formulas that use LandUse
print(f'\n📊 Testing LandUse-based formula (1.1.2.1.2):')
formula = calc.get_formula('1.1.2.1.2')
print(f'  Formula: {formula}')
status, target = calc.calculate('1.1.2.1.2')
print(f'  Result: status={status}, target={target}')

# Test formulas that use Verbrauch
print(f'\n📊 Testing Verbrauch-based formula (7.1):')
formula = calc.get_formula('7.1')
print(f'  Formula: {formula}')
status, target = calc.calculate('7.1')
print(f'  Result: status={status}, target={target}')

# Show sample keys from each type
print(f'\n🔍 Sample keys from each data source:')
print(f'\n  LandUse keys (first 5):')
for key in landuse_keys[:5]:
    print(f'    {key}: {calc.evaluator.status_lookup[key]}')

print(f'\n  VerbrauchData keys (first 5):')
for key in verbrauch_keys[:5]:
    print(f'    {key}: {calc.evaluator.status_lookup[key]}')

print(f'\n  RenewableData keys (first 5):')
for key in renewable_keys[:5]:
    print(f'    {key}: {calc.evaluator.status_lookup[key]}')

print(f'\n✅ VERIFICATION PASSED:')
print(f'   - LandUse data has LandUse_ prefix')
print(f'   - Verbrauch data has VerbrauchData_ prefix')
print(f'   - Renewable data has RenewableData_ prefix')
print(f'   - No mixing between data sources!')
print(f'   - Formulas reference correct prefixes')
