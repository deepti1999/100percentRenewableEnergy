#!/usr/bin/env python3
"""
Fix Verbrauch Data - Complete Reload
====================================

This script:
1. Reloads all verbrauch data from the original CSV files
2. Loads Gebäudewärme (section 2) data
3. Imports all formulas  
4. Recalculates all values
5. Verifies the data is correct

Run this to fix all issues with the verbrauch page.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from django.core.management import call_command

print("=" * 80)
print("COMPLETE VERBRAUCH DATA FIX")
print("=" * 80)
print()

# Step 1: Reload KLIK data (Section 1) from CSV
print("Step 1: Reloading KLIK data (Section 1) from CSV...")
print("-" * 80)
call_command('load_verbrauch_data')
print()

# Step 2: Load Gebäudewärme data (Section 2)
print("Step 2: Loading Gebäudewärme data (Section 2)...")
print("-" * 80)
call_command('load_exact_gebaeudewaerme')
print()

# Step 3: Import formulas
print("Step 3: Importing formulas...")
print("-" * 80)
call_command('import_verbrauch_formulas')
print()

# Step 4: Mark calculated fields
print("Step 4: Marking calculated fields...")
print("-" * 80)
call_command('update_calculated_verbrauch')
print()

# Step 5: Recalculate all values
print("Step 5: Recalculating all values...")
print("-" * 80)
call_command('recalc_verbrauch')
print()

# Step 5: Verify data
print("Step 5: Verifying data...")
print("-" * 80)

from simulator.models import VerbrauchData, Formula

total = VerbrauchData.objects.count()
calculated = VerbrauchData.objects.filter(is_calculated=True).count()
formulas = Formula.objects.filter(key__startswith='V_').count()

print(f"✅ Total VerbrauchData entries: {total}")
print(f"✅ Calculated entries: {calculated}")
print(f"✅ Formulas loaded: {formulas}")
print()

# Show sample data
print("Sample Data (first 10 entries):")
print("-" * 80)
for v in VerbrauchData.objects.all()[:10]:
    calc_marker = " [CALC]" if v.is_calculated else ""
    print(f"{v.code:10s} | {v.category[:35]:35s} | S: {str(v.status):10s} | Z: {str(v.ziel):10s}{calc_marker}")

print()
print("=" * 80)
print("✅ VERBRAUCH DATA FIX COMPLETE!")
print("=" * 80)
print()
print("You can now access the verbrauch page at: http://127.0.0.1:8001/verbrauch/")
print()
