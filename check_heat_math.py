#!/usr/bin/env python
"""
Deep analysis of heat balance math
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print("="*80)
print("UNDERSTANDING THE HEAT BALANCE MATH")
print("="*80)

# Key Verbrauch values
v28 = VerbrauchData.objects.get(code='2.8')
v280 = VerbrauchData.objects.get(code='2.8.0')
v290 = VerbrauchData.objects.get(code='2.9.0')
v292 = VerbrauchData.objects.get(code='2.9.2')

print("\nVERBRAUCH (DEMAND) SIDE:")
print("-" * 40)
print(f"2.8 (davon Waerme %)         Status: {v28.status}%   Ziel: {v28.ziel}%")
print(f"2.8.0 (Endenergie)           Status: {v280.status}   Ziel: {v280.ziel}")
print(f"2.9.0 (WP-Stromaufnahme)     Status: {v290.status}   Ziel: {v290.ziel}")
print(f"2.9.2                        Status: {v292.status}   Ziel: {v292.ziel}")

# Key Renewable values
r104 = RenewableData.objects.get(code='10.4')
r1041 = RenewableData.objects.get(code='10.4.1')
r1042 = RenewableData.objects.get(code='10.4.2')
r1043 = RenewableData.objects.get(code='10.4.3')
r1022 = RenewableData.objects.get(code='10.2.2')

print("\nRENEWABLE (SUPPLY) SIDE:")
print("-" * 40)
print(f"10.4 (Gebaeudewaerme total)  Target: {r104.target_value:,.2f} GWh")
print(f"  10.4.1 (Brennstoffe)       Target: {r1041.target_value:,.2f} GWh")
print(f"  10.4.2 (Waerme)            Target: {r1042.target_value:,.2f} GWh")
print(f"  10.4.3 (Strom)             Target: {r1043.target_value:,.2f} GWh")
print(f"10.2.2 (davon Strom %)       Target: {r1022.target_value}%")

# Balance check
demand = float(v280.ziel)
supply = float(r104.target_value)
gap = demand - supply

print("\n" + "="*80)
print("BALANCE CHECK")
print("="*80)
print(f"DEMAND  (2.8.0 Ziel):  {demand:,.2f} GWh")
print(f"SUPPLY  (10.4 Target): {supply:,.2f} GWh")
print(f"GAP:                   {gap:,.2f} GWh")

# Now trace how 2.8.0 is calculated
print("\n" + "="*80)
print("HOW 2.8.0 (DEMAND) IS CALCULATED")
print("="*80)
print(f"2.8.0 formula: {v280.formula if hasattr(v280, 'formula') else 'Check DB'}")

# Check what 2.8 percentage affects
# 2.8.0 = some_base * 2.8 / 100?
# Let's check parent codes
v2 = VerbrauchData.objects.filter(code='2').first()
v27 = VerbrauchData.objects.filter(code='2.7').first()
v25 = VerbrauchData.objects.filter(code='2.5').first()
v26 = VerbrauchData.objects.filter(code='2.6').first()

print("\nRelated Verbrauch values:")
if v2: print(f"2:   Status={v2.status}, Ziel={v2.ziel}")
if v25: print(f"2.5: Status={v25.status}, Ziel={v25.ziel}")
if v26: print(f"2.6: Status={v26.status}, Ziel={v26.ziel}")
if v27: print(f"2.7: Status={v27.status}, Ziel={v27.ziel}")
print(f"2.8: Status={v28.status}, Ziel={v28.ziel}")

# Check how 10.4.2 uses 7.1.x which comes from Verbrauch
print("\n" + "="*80)
print("KEY DEPENDENCIES")
print("="*80)

r71 = RenewableData.objects.get(code='7.1')
r712 = RenewableData.objects.get(code='7.1.2')
r7123 = RenewableData.objects.get(code='7.1.2.3')
r714 = RenewableData.objects.get(code='7.1.4')
r7143 = RenewableData.objects.get(code='7.1.4.3')

print(f"\n7.1 (WP-Antriebsstrom) = {r71.target_value:,.2f} GWh")
print(f"  Formula: {r71.formula}")
print(f"\n7.1.2 (WP-Luft Antriebsstrom) = {r712.target_value:,.2f} GWh")
print(f"  Formula: {r712.formula}")
print(f"\n7.1.2.3 (Waermegewinn Luft) = {r7123.target_value:,.2f} GWh")
print(f"  Formula: {r7123.formula}")
print(f"\n7.1.4.3 (Waermegewinn Erdreich) = {r7143.target_value:,.2f} GWh")
print(f"  Formula: {r7143.formula}")

# THE MATH
print("\n" + "="*80)
print("THE BALANCE MATH")
print("="*80)
print("""
Current situation:
- 10.4 (supply) > 2.8.0 (demand) by {gap:,.0f} GWh

10.4 = 10.4.1 + 10.4.2 + 10.4.3
     = 0 + 527,760 + 136,038 = 663,798 GWh

2.8.0 (demand) = 527,562 GWh

The issue is 10.4.3 (davon Strom) = 136,038 GWh is ADDING to supply
but it should not be counted as heat supply since it's electricity!

To balance, we need either:
1. Reduce 10.4 supply (reduce 10.4.2 or 10.4.3)
2. Increase 2.8.0 demand

The 79.5% -> 79.47% change affects the calculation chain:
- 2.8 percentage is used to calculate 2.8.0
- When 2.8 changes, 2.8.0 changes
- This affects the demand side

Let me trace the exact relationship...
""".format(gap=gap))

# Check formulas in database
from simulator.models import Formula
formulas_28 = Formula.objects.filter(key__icontains='2_8').all()
print("\nFormulas related to 2.8:")
for f in formulas_28[:10]:
    print(f"  {f.key}: {f.expression[:60] if f.expression else 'None'}...")
