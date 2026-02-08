#!/usr/bin/env python
"""
CLEAR EXPLANATION: What happens when balance button is pressed

This shows EXACTLY what values change and by how much.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData, LandUse
from decimal import Decimal

print("="*70)
print("CURRENT STATE (BEFORE BALANCE)")
print("="*70)

# Get current values
lu_2_1 = LandUse.objects.get(code='LU_2.1')
v28 = VerbrauchData.objects.get(code='2.8')
v26 = VerbrauchData.objects.get(code='2.6')
v280 = VerbrauchData.objects.get(code='2.8.0')
v290 = VerbrauchData.objects.get(code='2.9.0')
r10_4_2 = RenewableData.objects.get(code='10.4.2')

# Strom (Electricity)
electricity_demand = float(v290.ziel or 0)  # 2.9.0

# Wärme (Heat)
heat_demand = float(v280.ziel or 0)  # 2.8.0
heat_supply = float(r10_4_2.target_value or 0)  # 10.4.2

print(f"\n📊 STROM (Electricity):")
print(f"   - Demand (2.9.0):  {v290.ziel:,.2f} GWh")
print(f"   - Supply comes from solar land (LU 2.1)")
print(f"   - Current LU_2.1: {float(lu_2_1.target_ha or 0):,.2f} ha")

print(f"\n🔥 WÄRME (Heat - Gebäudewärme):")
print(f"   - Demand (2.8.0):  {heat_demand:,.2f} GWh")
print(f"   - Supply (10.4.2): {heat_supply:,.2f} GWh")
print(f"   - Gap: {heat_supply - heat_demand:,.2f} GWh")
print(f"   - Current 2.8%:   {float(v28.ziel):,.6f}%")

# What needs to change for Wärme balance
# Formula: new_2.8% = 10.4.2 × 100 / 2.6
base = float(v26.ziel)  # 2.6
supply = heat_supply    # 10.4.2
required_28_percent = (supply * 100) / base

print("\n" + "="*70)
print("WHAT CHANGES WHEN BALANCE BUTTON IS PRESSED")
print("="*70)

print(f"\n1️⃣  STEP 1: Energy Balance (LU 2.1)")
print(f"    LU 2.1 adjusts to match electricity demand/supply")
print(f"    (The exact change depends on complex 9.x calculations)")

print(f"\n2️⃣  STEP 2: WS Storage Balance")
print(f"    Various 9.x storage values adjust")

print(f"\n3️⃣  STEP 3: Heat Balance (Wärme) - NEW!")
print(f"    To make Demand (2.8.0) = Supply (10.4.2):")
print(f"    ")
print(f"    Formula: new_2.8% = 10.4.2 × 100 / 2.6")
print(f"           = {supply:,.2f} × 100 / {base:,.2f}")
print(f"           = {required_28_percent:.6f}%")
print(f"    ")
print(f"    Current 2.8%:  {float(v28.ziel):.6f}%")
print(f"    Required 2.8%: {required_28_percent:.6f}%")
print(f"    CHANGE:        {required_28_percent - float(v28.ziel):+.6f}%")

# Calculate new 2.8.0 after balance
new_280 = base * required_28_percent / 100
print(f"    ")
print(f"    After balance:")
print(f"    - 2.8.0 becomes: {base} × {required_28_percent:.6f} / 100 = {new_280:,.2f} GWh")
print(f"    - This equals 10.4.2: {supply:,.2f} GWh ✅")

print("\n" + "="*70)
print("WHY IS IT STABLE?")
print("="*70)
print("""
When you press Save after Balance:

1. 2.8% is saved with the new value (e.g., 78.54%)
2. 2.8.0 is RECALCULATED from formula: 2.8.0 = 2.6 × 2.8% / 100
3. Since we set 2.8% so that 2.8.0 = 10.4.2, after recalculation:
   - 2.8.0 = 10.4.2 (still balanced!)
4. 10.4.2 only changes if its input components change
   - Main volatile component is 9.3.2.1
   - 9.3.2.1 = 9.3.1 × 9.3.2 / 100
   - 9.3.1 comes from WS calculation (Step 2 balances this)
   
So as long as WS balance runs before Heat balance, everything stays stable!
""")
