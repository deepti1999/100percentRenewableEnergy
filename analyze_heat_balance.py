#!/usr/bin/env python
"""
Analyze Gebäudewärme balance chain:
- How 10.4, 10.4.2, 10.4.3 are calculated
- How they relate to Verbrauch 2.8
- How 7.1 (Wärmepumpen) connects both
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print("="*80)
print("GEBÄUDEWÄRME BALANCE ANALYSIS")
print("="*80)

# ============================================================================
# VERBRAUCH SIDE (DEMAND)
# ============================================================================
print("\n" + "="*80)
print("VERBRAUCH (DEMAND) SIDE")
print("="*80)

# Check codes around 2.8.x
print("\n--- Verbrauch 2.8.x codes ---")
for code in ['2.8', '2.8.0', '2.8.1', '2.8.2', '2.8.3', '2.8.4', '2.8.5', '2.8.6', '2.8.7']:
    v = VerbrauchData.objects.filter(code=code).first()
    if v:
        print(f"{code}: {v.category}")
        print(f"   Status: {v.status}, Ziel: {v.ziel}")

# Look for "verlustarm" percentage fields
print("\n--- Looking for percentage fields (79.5% mentioned) ---")
# Search all verbrauch that might have the percentage
all_verbrauch = VerbrauchData.objects.all()
for v in all_verbrauch:
    if v.ziel and 79 < float(v.ziel) < 80:
        print(f"{v.code}: {v.category} = Ziel:{v.ziel}")
    if v.status and 79 < float(v.status) < 80:
        print(f"{v.code}: {v.category} = Status:{v.status}")

# ============================================================================
# RENEWABLE SIDE (SUPPLY)  
# ============================================================================
print("\n" + "="*80)
print("RENEWABLE (SUPPLY) SIDE - Gebäudewärme")
print("="*80)

# 10.4 and its components
for code in ['10.4', '10.4.1', '10.4.2', '10.4.3']:
    r = RenewableData.objects.filter(code=code).first()
    if r:
        print(f"\n{code} - {r.name}")
        print(f"   Status: {r.status_value}")
        print(f"   Target: {r.target_value}")
        print(f"   Formula: {r.formula if r.formula else 'NONE'}")

# ============================================================================
# 7.1 WÄRMEPUMPEN (Heat Pumps) - connects Verbrauch to Renewable
# ============================================================================
print("\n" + "="*80)
print("7.1 WÄRMEPUMPEN (Heat Pumps)")
print("="*80)

for code in ['7.1', '7.1.1', '7.1.2', '7.1.2.1', '7.1.2.2', '7.1.2.3', '7.1.3', '7.1.4', '7.1.4.1', '7.1.4.2', '7.1.4.3']:
    r = RenewableData.objects.filter(code=code).first()
    if r:
        print(f"\n{code} - {r.name}")
        print(f"   Status: {r.status_value}")
        print(f"   Target: {r.target_value}")
        print(f"   Formula: {r.formula if r.formula else 'NONE'}")

# ============================================================================
# BALANCE CHECK
# ============================================================================
print("\n" + "="*80)
print("GEBÄUDEWÄRME BALANCE CHECK")
print("="*80)

# Demand - try both 2.8 and 2.8.0
v28 = VerbrauchData.objects.filter(code='2.8').first()
v280 = VerbrauchData.objects.filter(code='2.8.0').first()

demand = v280.ziel if v280 and v280.ziel else (v28.ziel if v28 and v28.ziel else 0)
print(f"\nDEMAND (Verbrauch Ziel): {float(demand):,.2f} GWh")

# Supply (10.4)
r104 = RenewableData.objects.filter(code='10.4').first()
supply = r104.target_value if r104 and r104.target_value else 0
print(f"SUPPLY (10.4 Target):    {float(supply):,.2f} GWh")

gap = float(demand) - float(supply)
print(f"\nGAP (Demand - Supply):   {gap:,.2f} GWh")

# ============================================================================
# FORMULAS BREAKDOWN
# ============================================================================
print("\n" + "="*80)
print("10.4.2 FORMULA COMPONENTS (davon Wärme)")
print("="*80)

r1042 = RenewableData.objects.filter(code='10.4.2').first()
print(f"\n10.4.2 Formula: {r1042.formula if r1042 else 'N/A'}")
print(f"10.4.2 Target:  {r1042.target_value if r1042 else 'N/A'}")

# Components
components = ['1.1.1.1.2', '7.1.2.3', '7.1.4.3', '5.4.2.4', '6.1.3.2.4', '8.2', '4.4.2', '9.3.2.1']
print("\nComponents:")
total = 0
for code in components:
    r = RenewableData.objects.filter(code=code).first()
    val = r.target_value if r and r.target_value else 0
    print(f"  {code}: {float(val):,.2f} GWh - {r.name if r else 'N/A'}")
    total += float(val)
print(f"\nSUM: {total:,.2f} GWh")

print("\n" + "="*80)
print("10.4.3 FORMULA (davon Strom)")
print("="*80)

r1043 = RenewableData.objects.filter(code='10.4.3').first()
print(f"\n10.4.3 - {r1043.name if r1043 else 'N/A'}")
print(f"Formula: {r1043.formula if r1043 else 'N/A'}")
print(f"Target:  {r1043.target_value if r1043 else 'N/A'}")

# What feeds into 10.4.3?
print("\n--- Looking at what affects 10.4.3 ---")
# 10.4.3 usually = Verbrauch * percentage
# Let's check if there's a verbrauch_* reference in formula
if r1043 and r1043.formula:
    print(f"Formula breakdown: {r1043.formula}")
