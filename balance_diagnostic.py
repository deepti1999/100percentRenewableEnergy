#!/usr/bin/env python
"""
CLEAR BALANCE DIAGNOSTIC
========================
Shows exactly what changes when you press Balance button.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData, LandUse

print("="*80)
print("CURRENT STATE - BEFORE BALANCE")
print("="*80)

# Get current key values
lu21 = LandUse.objects.get(code='LU_2.1')
v26 = VerbrauchData.objects.get(code='2.6')
v28 = VerbrauchData.objects.get(code='2.8')
v280 = VerbrauchData.objects.get(code='2.8.0')
v7 = VerbrauchData.objects.get(code='7')  # Endenergieverbrauch

r101 = RenewableData.objects.get(code='10.1')
r104 = RenewableData.objects.get(code='10.4')
r1042 = RenewableData.objects.get(code='10.4.2')
r912 = RenewableData.objects.get(code='9.1.2')

print("\n📊 KEY VALUES:")
print("-" * 60)
print(f"LU_2.1 (Solar Freifl.)     = {float(lu21.target_ha):,.2f} ha")
print(f"9.1.2 (Solar Ziel)         = {float(r912.target_value):,.2f} GWh")
print(f"2.8 (Wärme %)              = {float(v28.ziel):.6f}%")
print(f"2.8.0 (Wärme Demand)       = {float(v280.ziel):,.2f} GWh")
print(f"10.4.2 (Wärme Supply)      = {float(r1042.target_value):,.2f} GWh")
print(f"10.1 (Total Renewable)     = {float(r101.target_value):,.2f} GWh")
print(f"7 (Endenergieverbrauch)    = {float(v7.ziel):,.2f} GWh")

# Calculate gaps
total_demand = float(v7.ziel)
total_supply = float(r101.target_value)
energy_gap = total_demand - total_supply

heat_demand = float(v280.ziel)
heat_supply = float(r1042.target_value)
heat_gap = heat_demand - heat_supply

print("\n⚖️ BALANCE STATUS:")
print("-" * 60)
print(f"ELECTRICITY (Total):")
print(f"  Demand (7):      {total_demand:,.2f} GWh")
print(f"  Supply (10.1):   {total_supply:,.2f} GWh")
print(f"  Gap:             {energy_gap:,.2f} GWh {'✓' if abs(energy_gap) < 100 else '✗ NEEDS BALANCE'}")

print(f"\nHEAT (Gebäudewärme):")
print(f"  Demand (2.8.0):  {heat_demand:,.2f} GWh")
print(f"  Supply (10.4.2): {heat_supply:,.2f} GWh")
print(f"  Gap:             {heat_gap:,.2f} GWh {'✓' if abs(heat_gap) < 10 else '✗ NEEDS BALANCE'}")

# Now calculate what WILL change
print("\n" + "="*80)
print("WHAT BALANCE BUTTON WILL DO")
print("="*80)

# 1. For Electricity Balance (LU_2.1 adjustment)
# We need 10.1 = Demand (7)
# The relationship is complex, but roughly:
# More LU_2.1 → More 9.1.2 → More 10.1

# 2. For Heat Balance (2.8% adjustment)
# new_2.8% = 10.4.2 * 100 / 2.6
new_28_percent = float(r1042.target_value) * 100 / float(v26.ziel)
change_28 = new_28_percent - float(v28.ziel)

print(f"\n1️⃣ ELECTRICITY BALANCE (adjusts LU_2.1):")
print(f"   Current LU_2.1:  {float(lu21.target_ha):,.2f} ha")
print(f"   Energy Gap:      {energy_gap:,.2f} GWh")
if abs(energy_gap) < 100:
    print(f"   Action: Already balanced, no change needed")
else:
    direction = "INCREASE" if energy_gap > 0 else "DECREASE"
    print(f"   Action: {direction} LU_2.1 to generate {'more' if energy_gap > 0 else 'less'} solar energy")
    print(f"   (Exact value calculated by goal-seek algorithm)")

print(f"\n2️⃣ HEAT BALANCE (adjusts 2.8%):")
print(f"   Current 2.8%:    {float(v28.ziel):.6f}%")
print(f"   Required 2.8%:   {new_28_percent:.6f}%")
print(f"   Change:          {change_28:+.6f}%")
if abs(heat_gap) < 10:
    print(f"   Action: Already balanced, minimal change")
else:
    print(f"   Action: Set 2.8 Ziel = {new_28_percent:.6f}%")
    print(f"           This makes 2.8.0 = {float(v26.ziel) * new_28_percent / 100:,.2f} GWh = 10.4.2")

print("\n" + "="*80)
print("THE BALANCE FLOW")
print("="*80)
print("""
When you press BALANCE button:

┌─────────────────────────────────────────────────────────────┐
│ STEP 1: ELECTRICITY BALANCE                                 │
│ ─────────────────────────────────────────────────────────── │
│ Goal: Make 10.1 (supply) = 7 (demand)                       │
│                                                             │
│ How:  Adjust LU_2.1 (Solar Freiflächen ha)                  │
│       ↓                                                     │
│       Changes 9.1.2 (Solar Ziel)                            │
│       ↓                                                     │
│       Changes 10.1 (Total Renewable)                        │
│       ↓                                                     │
│       Gap becomes 0                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: WS STORAGE BALANCE                                  │
│ ─────────────────────────────────────────────────────────── │
│ Goal: Make LadezustandNetto (row 366) = 0                   │
│                                                             │
│ How:  Adjust Stromverbr.Raumw.korr                          │
│       (ensures seasonal storage balances over year)         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: HEAT BALANCE                                        │
│ ─────────────────────────────────────────────────────────── │
│ Goal: Make 2.8.0 (demand) = 10.4.2 (supply)                 │
│                                                             │
│ How:  Calculate new 2.8% = 10.4.2 × 100 / 2.6               │
│       ↓                                                     │
│       Update 2.8 Ziel with new percentage                   │
│       ↓                                                     │
│       2.8.0 recalculates = 2.6 × new_2.8% / 100             │
│       ↓                                                     │
│       2.8.0 now equals 10.4.2 ✓                             │
└─────────────────────────────────────────────────────────────┘
""")

print("\n" + "="*80)
print("AFTER BALANCE - VALUES STAY STABLE")
print("="*80)
print("""
Once balanced:
- Pressing SAVE keeps all values
- Values remain stable until you change an INPUT
- If you change Verbrauch, you need to press Balance again

The key is:
1. LU_2.1 determines electricity production (supply)
2. 2.8% determines heat demand split
3. Both are adjusted to match supply = demand
""")
