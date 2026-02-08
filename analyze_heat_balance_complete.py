#!/usr/bin/env python
"""
Complete Gebäudewärme balance analysis
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print("="*80)
print("COMPLETE GEBAUDEWÄRME BALANCE ANALYSIS")
print("="*80)

# Get all key values
v26 = VerbrauchData.objects.get(code='2.6')   # Base (Endenergie total)
v27 = VerbrauchData.objects.get(code='2.7')   # Brennstoffe %
v28 = VerbrauchData.objects.get(code='2.8')   # Wärme % (79.5%)
v29 = VerbrauchData.objects.get(code='2.9')   # Strom %
v280 = VerbrauchData.objects.get(code='2.8.0') # Wärme Endenergie
v290 = VerbrauchData.objects.get(code='2.9.0') # Strom Endenergie

v26_ziel = float(v26.ziel)
v27_ziel = float(v27.ziel)
v28_ziel = float(v28.ziel)
v29_ziel = float(v29.ziel)
v280_ziel = float(v280.ziel)
v290_ziel = float(v290.ziel)

print("\nVERBRAUCH CALCULATION CHAIN:")
print("="*40)
print(f"2.6 (Endenergie gesamt)     = {v26_ziel:,.2f} GWh")
print(f"2.7 (Brennstoffe %)         = {v27_ziel}%")
print(f"2.8 (Wärme %)               = {v28_ziel}%  <-- KEY ADJUSTMENT")
print(f"2.9 (Strom %)               = {v29_ziel}%")
print()
print(f"2.8.0 = 2.6 x 2.8 / 100")
print(f"      = {v26_ziel:,.2f} x {v28_ziel} / 100")
print(f"      = {v26_ziel * v28_ziel / 100:,.2f} GWh")
print(f"  (Actual in DB: {v280_ziel:,.2f} GWh)")
print()
print(f"2.9.0 = 2.6 x 2.9 / 100")
print(f"      = {v26_ziel:,.2f} x {v29_ziel} / 100")
print(f"      = {v26_ziel * v29_ziel / 100:,.2f} GWh")
print(f"  (Actual in DB: {v290_ziel:,.2f} GWh)")

# Renewable side
r104 = RenewableData.objects.get(code='10.4')
r1041 = RenewableData.objects.get(code='10.4.1')
r1042 = RenewableData.objects.get(code='10.4.2')
r1043 = RenewableData.objects.get(code='10.4.3')

r104_val = float(r104.target_value)
r1041_val = float(r1041.target_value)
r1042_val = float(r1042.target_value)
r1043_val = float(r1043.target_value)

print("\n" + "="*80)
print("RENEWABLE SUPPLY:")
print("="*40)
print(f"10.4 (Gebäudewärme total)   = {r104_val:,.2f} GWh")
print(f"  10.4.1 (Brennstoffe)      = {r1041_val:,.2f} GWh")
print(f"  10.4.2 (Wärme)            = {r1042_val:,.2f} GWh")
print(f"  10.4.3 (Strom)            = {r1043_val:,.2f} GWh")

# Current gap
demand = v280_ziel
supply = r104_val
gap = demand - supply

print("\n" + "="*80)
print("CURRENT BALANCE:")
print("="*40)
print(f"DEMAND  (2.8.0):  {demand:,.2f} GWh")
print(f"SUPPLY  (10.4):   {supply:,.2f} GWh")
print(f"GAP:              {gap:,.2f} GWh")
if gap > 0:
    print("Gap is POSITIVE (need more supply)")
else:
    print("Gap is NEGATIVE (too much supply)")

# Calculate required 2.8 to balance
# We need: 2.8.0 = 10.4 (supply)
# So: 2.6 * new_2.8 / 100 = 10.4
# new_2.8 = 10.4 * 100 / 2.6
target_28 = supply * 100 / v26_ziel

print("\n" + "="*80)
print("TO BALANCE HEAT:")
print("="*40)
print(f"We need 2.8.0 (demand) = 10.4 (supply) = {supply:,.2f} GWh")
print()
print(f"Since 2.8.0 = 2.6 x 2.8% / 100")
print(f"=> new 2.8% = 10.4 x 100 / 2.6")
print(f"           = {supply:,.2f} x 100 / {v26_ziel:,.2f}")
print(f"           = {target_28:.6f}%")
print()
print(f"Current 2.8% = {v28_ziel}%")
print(f"Required 2.8% = {target_28:.6f}%")
print(f"Change needed = {target_28 - v28_ziel:.6f}%")

print("\n" + "="*80)
print("THE BALANCE ALGORITHM:")
print("="*80)
print("""
When the Balance button is pressed:

1. First, electricity is balanced (by adjusting LandUse for solar/wind)
   - This changes 9.1.2 (Solar) or 9.1.1 (Wind)
   - WS 365 calculation updates 9.3.1, 9.3.4
   - This affects 9.3.2.1 which is part of 10.4.2

2. Then, heat should be balanced by adjusting 2.8 Ziel %:
   - Calculate new 2.8% = 10.4 (supply) * 100 / 2.6 (base)
   - Update 2.8 Ziel to this new percentage
   - Recalculate 2.8.0 = 2.6 x new_2.8% / 100
   - Now 2.8.0 (demand) = 10.4 (supply)

The formula is simple:
  new_2.8_percent = 10.4_target * 100 / 2.6_ziel
""")

# Show what the button should do
print("\n" + "="*80)
print("IMPLEMENTATION:")
print("="*80)
print(f"""
def balance_heat():
    # Get current values
    v26 = VerbrauchData.objects.get(code='2.6')
    r104 = RenewableData.objects.get(code='10.4')
    
    # Calculate required percentage
    supply = float(r104.target_value)
    base = float(v26.ziel)
    new_percent = supply * 100 / base
    
    # Update 2.8 Ziel
    v28 = VerbrauchData.objects.get(code='2.8')
    v28.ziel = new_percent
    v28.save()
    
    # Trigger recalculation of 2.8.0
    # (This should happen automatically via formula)
    
Current values:
  10.4 (supply) = {supply:,.2f} GWh
  2.6 (base)    = {v26_ziel:,.2f} GWh
  New 2.8%      = {target_28:.6f}%
""")
