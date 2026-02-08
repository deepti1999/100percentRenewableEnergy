#!/usr/bin/env python
"""
Corrected Heat Balance Analysis
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print("="*80)
print("CORRECTED HEAT BALANCE ANALYSIS")
print("="*80)

v280 = VerbrauchData.objects.get(code='2.8.0')
v290 = VerbrauchData.objects.get(code='2.9.0')
v26 = VerbrauchData.objects.get(code='2.6')
v28 = VerbrauchData.objects.get(code='2.8')

r1041 = RenewableData.objects.get(code='10.4.1')
r1042 = RenewableData.objects.get(code='10.4.2')
r1043 = RenewableData.objects.get(code='10.4.3')

v280_val = float(v280.ziel)
v290_val = float(v290.ziel)
r1041_val = float(r1041.target_value)
r1042_val = float(r1042.target_value)
r1043_val = float(r1043.target_value)

print("\nTHE CORRECT COMPARISON:")
print("="*40)
print("\nDEMAND SIDE (Verbrauch):")
print(f"  2.8.0 (Waerme Endenergie)  = {v280_val:,.2f} GWh")
print(f"  2.9.0 (Strom Endenergie)   = {v290_val:,.2f} GWh")
print("\nSUPPLY SIDE (Renewable 10.4):")
print(f"  10.4.1 (Brennstoffe)       = {r1041_val:,.2f} GWh")
print(f"  10.4.2 (Waerme)            = {r1042_val:,.2f} GWh  <-- compare with 2.8.0")
print(f"  10.4.3 (Strom)             = {r1043_val:,.2f} GWh  <-- compare with 2.9.0")

gap_waerme = v280_val - r1042_val
gap_strom = v290_val - r1043_val

print("\n" + "="*80)
print("BALANCE CHECK:")
print("="*40)
print(f"\nWaerme: 2.8.0 vs 10.4.2")
print(f"  Demand:  {v280_val:,.2f} GWh")
print(f"  Supply:  {r1042_val:,.2f} GWh")
print(f"  Gap:     {gap_waerme:,.2f} GWh")

print(f"\nStrom: 2.9.0 vs 10.4.3")
print(f"  Demand:  {v290_val:,.2f} GWh")
print(f"  Supply:  {r1043_val:,.2f} GWh")
print(f"  Gap:     {gap_strom:,.2f} GWh")

# Calculate what 2.8 should be to balance 10.4.2
supply_waerme = r1042_val
base = float(v26.ziel)
target_28 = supply_waerme * 100 / base
current_28 = float(v28.ziel)

print("\n" + "="*80)
print("TO BALANCE WAERME (2.8.0 = 10.4.2):")
print("="*40)
print(f"\nWe need 2.8.0 = 10.4.2 = {supply_waerme:,.2f} GWh")
print(f"\nFormula: 2.8.0 = 2.6 x 2.8% / 100")
print(f"=> 2.8% = 10.4.2 x 100 / 2.6")
print(f"        = {supply_waerme:,.2f} x 100 / {base:,.2f}")
print(f"        = {target_28:.6f}%")
print(f"\nCurrent 2.8% = {current_28}%")
print(f"Required 2.8% = {target_28:.6f}%")
print(f"Change: {target_28 - current_28:+.6f}%")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print(f"""
The Waerme gap is only {gap_waerme:,.2f} GWh which is very small!
  2.8.0 (demand) = {v280_val:,.2f} GWh
  10.4.2 (supply) = {r1042_val:,.2f} GWh

This is almost balanced! The gap is {abs(gap_waerme/v280_val)*100:.4f}% of demand.

The 79.5% -> 79.47% change (0.03% difference) adjusts this small gap.

To make them exactly equal:
  Set 2.8 Ziel = {target_28:.6f}%
  This will make 2.8.0 = {base * target_28 / 100:,.2f} GWh = 10.4.2
""")
