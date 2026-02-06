#!/usr/bin/env python3
"""Check Gebäudewärme balance"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from simulator.models import RenewableData

print('=== GEBÄUDEWÄRME OVERVIEW ===')

# Check Verbrauch
try:
    r = RenewableData.objects.get(code='2.8.0')
    print(f'Verbrauch (2.8.0): Status={r.status_value:,.2f}, Target={r.target_value:,.2f}')
except:
    print('2.8.0 NOT FOUND')

# Check Renewable Total
try:
    r = RenewableData.objects.get(code='10.4')
    print(f'Erneuerbar Total (10.4): Status={r.status_value:,.2f}, Target={r.target_value:,.2f}')
except:
    print('10.4 NOT FOUND')

try:
    r = RenewableData.objects.get(code='10.4.2')
    print(f'Erneuerbar excl Abwärme (10.4.2): Status={r.status_value:,.2f}, Target={r.target_value:,.2f}')
except:
    print('10.4.2 NOT FOUND')

print()
print('=== ABWÄRME COMPONENTS (Ziel formula) ===')
abwaerme_codes = ['4.3.3.4', '4.4.2', '5.4.2.4', '6.1.3.2.4']
total_ab = 0
for code in abwaerme_codes:
    try:
        r = RenewableData.objects.get(code=code)
        val = r.status_value or 0
        print(f'  {code}: status = {val:,.2f}')
        total_ab += val
    except:
        print(f'  {code}: NOT FOUND')
print(f'Total Abwärme: {total_ab:,.2f}')

print()
print('=== HEAT SOURCES THAT COULD BE INCREASED ===')
# Check main heat sources
heat_sources = [
    ('4.3', 'Erdgas KWK'),
    ('4.3.3', 'Erdgas Wärmenetze (KWK)'),
    ('4.4', 'Erdgas Wärmenetze (Kessel)'),
    ('5.4', 'Biogene fest Wärmenetze'),
    ('5.4.2', 'Biogene fest Wärmenetze KWK'),
    ('6.1.3.2', 'Biogene flüssig Wärmenetze'),
    ('7.1', 'Solarthermie'),
    ('7.2', 'Wärmepumpen'),
    ('7.3', 'Geothermie'),
]
for code, name in heat_sources:
    try:
        r = RenewableData.objects.get(code=code)
        print(f'{code} ({name}): Status={r.status_value:,.2f}, Target={r.target_value:,.2f}')
    except:
        pass

print()
print('=== BALANCE CALCULATION ===')
try:
    verbrauch = RenewableData.objects.get(code='2.8.0').status_value or 0
    renewable = RenewableData.objects.get(code='10.4').status_value or 0
    
    print(f'Verbrauch: {verbrauch:,.2f}')
    print(f'Erneuerbar: {renewable:,.2f}')
    print(f'Abwärme: {total_ab:,.2f}')
    print(f'Total Coverage: {renewable + total_ab:,.2f}')
    print(f'Gap (fossil needed): {verbrauch - renewable - total_ab:,.2f}')
except Exception as e:
    print(f'Error: {e}')
