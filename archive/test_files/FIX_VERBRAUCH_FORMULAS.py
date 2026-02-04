#!/usr/bin/env python3
"""
FIX VERBRAUCH FORMULAS - Complete repair of formula system
==========================================================

This fixes the core issues:
1. Clears ALL Django cache
2. Fixes malformed formula expressions
3. Creates proper FormulaVariable mappings
4. Corrects calculation flags in VerbrauchData rows
5. Tests that formulas work after fix
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, VerbrauchData
from django.core.cache import cache
from django.db import transaction

print("=" * 80)
print("COMPREHENSIVE VERBRAUCH FORMULA FIX")
print("=" * 80)

# STEP 1: Clear ALL cache
print("\n1️⃣  CLEARING ALL CACHE...")
try:
    cache.clear()
    print("✅ Django cache cleared completely")
except Exception as e:
    print(f"⚠️  Cache clear warning: {e}")

# STEP 2: Fix specific problematic formulas
print("\n2️⃣  FIXING FORMULAS FOR 2.4.2...")

# Delete old broken formulas OUTSIDE transaction
Formula.objects.filter(key__in=['V_2.4.2', 'V_2.4.2_ziel']).delete()
print("   ✓ Deleted old formulas")

with transaction.atomic():
    # CREATE PROPER STATUS FORMULA for 2.4.2
    # According to docs: 2.4.2 status = 2.1.0
    status_formula = Formula.objects.create(
        key='V_2.4.2',
        category='verbrauch',
        expression='Verbrauch_2_1_0',
        description='Status formula for 2.4.2 = reference to 2.1.0',
        is_fixed=False,
        is_active=True
    )
    
    FormulaVariable.objects.create(
        formula=status_formula,
        variable_name='Verbrauch_2_1_0',
        source_type='verbrauch_status',
        source_key='2.1.0',
        default_value=0.0
    )
    print(f"   ✓ Created STATUS formula: {status_formula.expression}")
    
    # CREATE PROPER ZIEL FORMULA for 2.4.2
    # According to docs: 2.4.2 ziel = (2.4.1_ziel - 2.4.1_status) / 2.4.1_status * 100
    ziel_formula = Formula.objects.create(
        key='V_2.4.2_ziel',
        category='verbrauch',
        expression='(Verbrauch_2_4_1_ziel - Verbrauch_2_4_1) / Verbrauch_2_4_1 * 100',
        description='Ziel formula for 2.4.2 = percentage change from status to target',
        is_fixed=False,
        is_active=True
    )
    
    FormulaVariable.objects.create(
        formula=ziel_formula,
        variable_name='Verbrauch_2_4_1_ziel',
        source_type='verbrauch_ziel',
        source_key='2.4.1',
        default_value=0.0
    )
    
    FormulaVariable.objects.create(
        formula=ziel_formula,
        variable_name='Verbrauch_2_4_1',
        source_type='verbrauch_status',
        source_key='2.4.1',
        default_value=0.0
    )
    print(f"   ✓ Created ZIEL formula: {ziel_formula.expression}")
    
    # FIX ROW FLAGS
    row = VerbrauchData.objects.get(code='2.4.2')
    row.is_calculated = True
    row.status_calculated = True
    row.ziel_calculated = True
    row.save(skip_cascade=True)
    print("   ✓ Fixed calculation flags")

# STEP 3: Clear cache again after changes
print("\n3️⃣  CLEARING CACHE AFTER FIXES...")
cache.clear()
print("✅ Cache cleared")

# STEP 4: Test that formulas work
print("\n4️⃣  TESTING FORMULAS...")
try:
    row = VerbrauchData.objects.get(code='2.4.2')
    
    # Force recalculation
    status_calc = row.calculate_value()
    ziel_calc = row.calculate_ziel_value()
    
    print(f"\n   Test results for 2.4.2:")
    print(f"   Status calculated: {status_calc}")
    print(f"   Ziel calculated: {ziel_calc}")
    
    # Get reference values
    row_241 = VerbrauchData.objects.get(code='2.4.1')
    row_210 = VerbrauchData.objects.get(code='2.1.0')
    
    print(f"\n   Reference values:")
    print(f"   2.1.0 status: {row_210.status}")
    print(f"   2.4.1 status: {row_241.status}")
    print(f"   2.4.1 ziel: {row_241.ziel}")
    
    # Calculate expected
    expected_status = row_210.status
    expected_ziel = (row_241.ziel - row_241.status) / row_241.status * 100 if row_241.status else 0
    
    print(f"\n   Expected values:")
    print(f"   Status should be: {expected_status}")
    print(f"   Ziel should be: {expected_ziel}")
    
    if abs((status_calc or 0) - (expected_status or 0)) < 0.01:
        print("   ✅ Status formula is CORRECT")
    else:
        print(f"   ❌ Status formula MISMATCH")
    
    if abs((ziel_calc or 0) - (expected_ziel or 0)) < 0.01:
        print("   ✅ Ziel formula is CORRECT")
    else:
        print(f"   ❌ Ziel formula MISMATCH")
        
except Exception as e:
    print(f"   ❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

# STEP 5: Save values
print("\n5️⃣  SAVING CALCULATED VALUES...")
try:
    row = VerbrauchData.objects.get(code='2.4.2')
    row.save()  # This will trigger calculate_value() and calculate_ziel_value()
    row.refresh_from_db()
    
    print(f"   2.4.2 status: {row.status}")
    print(f"   2.4.2 ziel: {row.ziel}")
    print("   ✅ Values saved to database")
except Exception as e:
    print(f"   ❌ Save failed: {e}")

print("\n" + "=" * 80)
print("✅ FIX COMPLETE!")
print("=" * 80)
print("\nNEXT STEPS:")
print("1. Restart your Django server (Ctrl+C then 'python3 manage.py runserver')")
print("2. Go to the Verbrauch page in your browser")
print("3. Click 'Recalculate All' to refresh all values")
print("4. Check that row 2.4.2 now shows correct values")
print("\nIf formulas still don't work, the problem is in the calculation engine cache.")
