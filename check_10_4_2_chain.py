#!/usr/bin/env python
"""
Check how 9.3.2.1 is calculated and how it affects 10.4.2
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print("="*70)
print("HOW 10.4.2 TARGET VALUE IS CALCULATED")
print("="*70)

# Check 10.4.2
r1042 = RenewableData.objects.filter(code='10.4.2').first()
if r1042:
    print(f'\n=== 10.4.2 - {r1042.name} ===')
    print(f'Status Value: {r1042.status_value}')
    print(f'Target Value: {r1042.target_value}')
    print(f'Formula: {r1042.formula}')

print("\n" + "="*70)
print("COMPONENTS OF 10.4.2 FORMULA")
print("="*70)

# Components of 10.4.2
components = {
    '1.1.1.1.2': 'Solar thermal (Gebäudewärme)',
    '7.1.2.3': 'Wärmegewinn aus der Luft',
    '7.1.4.3': 'Wärmegewinn Erdreich/Grundwasser',
    '5.4.2.4': 'Gebäudewärme (Biogas)',
    '6.1.3.2.4': 'Gebäudewärme (Holz)',
    '8.2': 'Gebäudewärmebereitstellung',
    '4.4.2': 'Wärmenetze GW',
    '9.3.2.1': 'Gebäudewärme (Seasonal Storage)'  # THIS IS THE KEY ONE!
}

total = 0
print()
for code, description in components.items():
    r = RenewableData.objects.filter(code=code).first()
    if r:
        val = r.target_value if r.target_value else 0
        print(f'{code:15} = {val:12.2f} GWh  ({description})')
        print(f'                Formula: {r.formula if r.formula else "NONE (fixed or manual)"}')
        total += float(val)
    else:
        print(f'{code:15} = NOT FOUND')
    print()

print("="*70)
print(f'SUM:            = {total:12.2f} GWh')
print(f'10.4.2 target:  = {r1042.target_value if r1042 else "N/A"} GWh')
print("="*70)

# Now check the 9.3.x hierarchy
print("\n" + "="*70)
print("9.3.x HIERARCHY (from WS 365-day calculation)")
print("="*70)

codes_93 = ['9.3', '9.3.1', '9.3.1.1', '9.3.1.2', '9.3.2', '9.3.2.1', '9.3.3', '9.3.4']

for code in codes_93:
    r = RenewableData.objects.filter(code=code).first()
    if r:
        print(f'\n{code}: {r.name}')
        print(f'   Status: {r.status_value}')
        print(f'   Target: {r.target_value}')
        print(f'   Formula: {r.formula if r.formula else "NONE (fixed/from WS 365)"}')

print("\n" + "="*70)
print("KEY INSIGHT:")
print("="*70)
print("""
When the Balance button is pressed:
1. The system adjusts LandUse (solar/wind area)
2. This changes 9.1.2 (Solar Ziel) or 9.1.1 (Wind Ziel)
3. WS 365 calculation runs and updates 9.3.1 and 9.3.4
4. 9.3.1 affects 9.3.2 and 9.3.2.1 through formulas
5. 9.3.2.1 is one of the components of 10.4.2
6. Therefore, 10.4.2 changes!

The chain is:
LandUse -> 9.1.x -> WS 365 -> 9.3.1/9.3.4 -> 9.3.2.1 -> 10.4.2
""")
