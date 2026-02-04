#!/usr/bin/env python
"""
Test LandUse → Renewable Cascade Update
========================================
This tests if changing LandUse values triggers updates in Renewable records.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse, RenewableData

print("=" * 80)
print("LANDUSE CASCADE TEST")
print("=" * 80)
print()

# Find a LandUse that has renewable dependents
print("1. Finding LandUse with Renewable dependents:")
print("-" * 80)

# Check LU_2.1 (Wind area) which should affect renewable wind production
test_code = 'LU_2.1'
try:
    landuse = LandUse.objects.get(code=test_code)
    print(f"✅ Found: {landuse.code} - {landuse.name}")
    print(f"   Current status_ha: {landuse.status_ha:,.0f}")
    print(f"   Current target_ha: {landuse.target_ha:,.0f}")
    print()
    
    # Find renewable records that reference this LandUse
    print("2. Finding dependent Renewable records:")
    print("-" * 80)
    
    # Check for references in formulas
    renewables = RenewableData.objects.filter(
        formula__icontains=f'LandUse_{test_code}'
    ) | RenewableData.objects.filter(
        formula__icontains='LandUse_2.1'
    )
    
    if renewables.exists():
        print(f"✅ Found {renewables.count()} dependent renewable records:")
        for r in renewables[:5]:
            print(f"   - {r.code}: {r.name}")
            print(f"     Status: {r.status_value}, Target: {r.target_value}")
        print()
    else:
        print("⚠️  No renewable records found with direct formula references")
        print("   Checking FormulaVariable mappings...")
        
        from simulator.models import Formula, FormulaVariable
        fv_formulas = Formula.objects.filter(
            category='renewable',
            variables__source_type__in=['landuse_status', 'landuse_target'],
            variables__source_key__in=[test_code, 'LU_2.1', '2.1']
        ).distinct()
        
        if fv_formulas.exists():
            print(f"✅ Found {fv_formulas.count()} formulas via FormulaVariable:")
            for f in fv_formulas[:5]:
                print(f"   - {f.key}: {f.expression}")
            print()
        else:
            print("❌ No FormulaVariable mappings found either")
            print()
    
    # Test the cascade
    print("3. Testing Cascade Update:")
    print("-" * 80)
    print(f"Changing {landuse.code} status_ha...")
    
    old_value = landuse.status_ha
    new_value = old_value * 1.01  # Increase by 1%
    
    print(f"   Old: {old_value:,.2f}")
    print(f"   New: {new_value:,.2f}")
    
    landuse.status_ha = new_value
    landuse.save()
    
    print("✅ Saved! Cascade should have triggered.")
    print()
    
    # Revert
    landuse.status_ha = old_value
    landuse.save()
    print(f"✅ Reverted to original value: {old_value:,.2f}")
    
except LandUse.DoesNotExist:
    print(f"❌ LandUse {test_code} not found")

print()
print("=" * 80)
print("HOW TO VERIFY CASCADE WORKS:")
print("=" * 80)
print()
print("Option 1: Via Django Admin")
print("  1. Go to Admin → Land uses")
print("  2. Find a row like LU_2.1 (Solare Freiflächen)")
print("  3. Change status_ha value (e.g., add 1000)")
print("  4. Click 'Save'")
print("  5. Go to Renewable Energy page")
print("  6. Check if dependent rows updated")
print()
print("Option 2: Check Terminal Output")
print("  - When you save in admin, look for console messages:")
print("    '✅ Recalculated X renewable items dependent on LU_X.X'")
print()
print("Option 3: Use Admin Action")
print("  1. Go to Admin → Land uses")
print("  2. Select one or more rows")
print("  3. Actions → '🔄 Trigger cascade update to Renewable data'")
print("  4. Click 'Go'")
print()
