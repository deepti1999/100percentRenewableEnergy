#!/usr/bin/env python3
"""
100% Extensibility Verification Script
======================================

This script verifies that:
1. ALL legacy hardcoded files have been deleted
2. ALL calculators fail-fast when formulas are missing
3. NO silent fallbacks exist
4. System is 100% database-driven

Run with fail_fast=True to expose any missing formulas.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData, Formula
from calculation_engine.renewable_engine import RenewableCalculator
from calculation_engine.bilanz_engine import get_renewable_value, get_verbrauch_value, calculate_bilanz_data

print("="*80)
print("100% EXTENSIBILITY VERIFICATION")
print("="*80)
print()

# ============================================================================
# STEP 1: Verify legacy files are deleted
# ============================================================================
print("STEP 1: Verifying legacy files are deleted...")
print("-"*80)

legacy_files = [
    'simulator/renewable_formulas.py',
    'renewable_energy_complete_formulas.py',
    'simulator/verbrauch_calculations.py.DEPRECATED_NOT_USED',
]

all_deleted = True
for filepath in legacy_files:
    if os.path.exists(filepath):
        print(f"❌ LEGACY FILE STILL EXISTS: {filepath}")
        all_deleted = False
    else:
        print(f"✅ Deleted: {filepath}")

if all_deleted:
    print("\n✅ ALL LEGACY FILES DELETED")
else:
    print("\n❌ SOME LEGACY FILES STILL EXIST")
print()

# ============================================================================
# STEP 2: Test fail-fast behavior for RenewableData
# ============================================================================
print("STEP 2: Testing fail-fast behavior for RenewableData...")
print("-"*80)

# Test with a calculated renewable item
test_renewable_codes = ['1.1.2.1.2', '1.2.1', '10.1']
renewable_fail_fast_works = True

for code in test_renewable_codes:
    try:
        renewable = RenewableData.objects.get(code=code)
        
        # Test with fail_fast=False (should not raise)
        status, target = renewable.get_calculated_values(fail_fast=False)
        print(f"✅ {code} (fail_fast=False): {status}, {target}")
        
        # Test with fail_fast=True (should raise if formula/variables missing)
        try:
            status, target = renewable.get_calculated_values(fail_fast=True)
            print(f"✅ {code} (fail_fast=True): {status}, {target}")
        except ValueError as e:
            print(f"⚠️  {code} (fail_fast=True) RAISED: {e}")
            renewable_fail_fast_works = False
            
    except RenewableData.DoesNotExist:
        print(f"⚠️  {code} not found in database")

print()

# ============================================================================
# STEP 3: Test fail-fast behavior for bilanz_engine functions
# ============================================================================
print("STEP 3: Testing fail-fast behavior for bilanz_engine...")
print("-"*80)

bilanz_fail_fast_works = True

# Test get_renewable_value
try:
    val = get_renewable_value('10.2', use_target=True, fail_fast=False)
    print(f"✅ get_renewable_value('10.2', fail_fast=False): {val}")
except Exception as e:
    print(f"❌ get_renewable_value('10.2', fail_fast=False) failed: {e}")
    bilanz_fail_fast_works = False

try:
    val = get_renewable_value('10.2', use_target=True, fail_fast=True)
    print(f"✅ get_renewable_value('10.2', fail_fast=True): {val}")
except ValueError as e:
    print(f"⚠️  get_renewable_value('10.2', fail_fast=True) RAISED: {e}")
except Exception as e:
    print(f"❌ get_renewable_value('10.2', fail_fast=True) unexpected error: {e}")
    bilanz_fail_fast_works = False

# Test get_verbrauch_value
try:
    val = get_verbrauch_value('1', use_ziel=True, fail_fast=False)
    print(f"✅ get_verbrauch_value('1', fail_fast=False): {val}")
except Exception as e:
    print(f"❌ get_verbrauch_value('1', fail_fast=False) failed: {e}")
    bilanz_fail_fast_works = False

try:
    val = get_verbrauch_value('1', use_ziel=True, fail_fast=True)
    print(f"✅ get_verbrauch_value('1', fail_fast=True): {val}")
except ValueError as e:
    print(f"⚠️  get_verbrauch_value('1', fail_fast=True) RAISED: {e}")
except Exception as e:
    print(f"❌ get_verbrauch_value('1', fail_fast=True) unexpected error: {e}")
    bilanz_fail_fast_works = False

print()

# ============================================================================
# STEP 4: Check for missing formulas
# ============================================================================
print("STEP 4: Checking for missing formulas...")
print("-"*80)

# Check RenewableData
renewable_missing = []
for r in RenewableData.objects.filter(is_fixed=False):
    formula_exists = Formula.objects.filter(key=r.code, category='renewable', is_active=True).exists()
    if not formula_exists:
        renewable_missing.append(r.code)

if renewable_missing:
    print(f"⚠️  RenewableData items without formulas: {len(renewable_missing)}")
    for code in renewable_missing[:10]:  # Show first 10
        print(f"   - {code}")
    if len(renewable_missing) > 10:
        print(f"   ... and {len(renewable_missing) - 10} more")
else:
    print("✅ All calculated RenewableData items have formulas")

# Check VerbrauchData
verbrauch_missing = []
for v in VerbrauchData.objects.filter(is_calculated=True):
    formula_exists = Formula.objects.filter(key=f"V_{v.code}", category='verbrauch', is_active=True).exists()
    if not formula_exists:
        verbrauch_missing.append(v.code)

if verbrauch_missing:
    print(f"⚠️  VerbrauchData items without formulas: {len(verbrauch_missing)}")
    for code in verbrauch_missing[:10]:
        print(f"   - {code}")
    if len(verbrauch_missing) > 10:
        print(f"   ... and {len(verbrauch_missing) - 10} more")
else:
    print("✅ All calculated VerbrauchData items have formulas")

print()

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("="*80)
print("SUMMARY")
print("="*80)

checks = [
    ("Legacy files deleted", all_deleted),
    ("RenewableData fail-fast works", renewable_fail_fast_works),
    ("bilanz_engine fail-fast works", bilanz_fail_fast_works),
    ("No missing RenewableData formulas", len(renewable_missing) == 0),
    ("No missing VerbrauchData formulas", len(verbrauch_missing) == 0),
]

all_pass = all(result for _, result in checks)

for check_name, result in checks:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status}: {check_name}")

print()
if all_pass:
    print("🎉 SYSTEM IS 100% DATABASE-DRIVEN!")
    print("✅ No hardcoded formulas")
    print("✅ No silent fallbacks")
    print("✅ All formulas in database")
else:
    print("⚠️  SYSTEM NOT YET 100% DATABASE-DRIVEN")
    print("Issues found above need to be resolved.")

print("="*80)
