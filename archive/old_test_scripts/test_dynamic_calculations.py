#!/usr/bin/env python
"""
Test script to verify that renewable energy formulas are calculating dynamically.
This will test if changing one value causes dependent values to update.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, LandUse, VerbrauchData

def test_dynamic_calculations():
    print("=" * 80)
    print("TESTING DYNAMIC FORMULA CALCULATIONS")
    print("=" * 80)
    
    # Build shared lookup dictionaries (like the view does)
    status_lookup = {}
    target_lookup = {}
    calculation_cache = {}
    
    # Load VerbrauchData once
    print("\n1. Loading VerbrauchData...")
    verbrauch_count = 0
    for verbrauch in VerbrauchData.objects.all():
        if verbrauch.status is not None:
            status_lookup[verbrauch.code] = float(verbrauch.status)
        if verbrauch.ziel is not None:
            target_lookup[verbrauch.code] = float(verbrauch.ziel)
        verbrauch_count += 1
    print(f"   Loaded {verbrauch_count} VerbrauchData entries")
    
    # Load LandUse data once
    print("\n2. Loading LandUse...")
    landuse_count = 0
    for landuse in LandUse.objects.all():
        if landuse.status_ha is not None:
            status_lookup[str(landuse.code)] = float(landuse.status_ha)
        if landuse.target_ha is not None:
            target_lookup[str(landuse.code)] = float(landuse.target_ha)
        landuse_count += 1
    print(f"   Loaded {landuse_count} LandUse entries")
    
    # Load RenewableData (fixed values first)
    print("\n3. Loading RenewableData...")
    renewables = list(RenewableData.objects.all().order_by('code'))
    for renewable in renewables:
        if renewable.is_fixed:
            if renewable.status_value is not None:
                status_lookup[renewable.code] = float(renewable.status_value)
            if renewable.target_value is not None:
                target_lookup[renewable.code] = float(renewable.target_value)
    print(f"   Loaded {len(renewables)} RenewableData entries")
    
    # Test calculation for entries with formulas
    print("\n4. Testing formula calculations...")
    print("-" * 80)
    
    calculated_count = 0
    fixed_count = 0
    error_count = 0
    
    for renewable in renewables[:20]:  # Test first 20 entries
        if renewable.is_fixed:
            fixed_count += 1
            print(f"\n✓ {renewable.code:15s} | {renewable.name[:40]:40s}")
            print(f"  FIXED: Status={renewable.status_value}, Target={renewable.target_value}")
        elif renewable.formula:
            try:
                calc_status, calc_target = renewable.get_calculated_values(
                    _cache=calculation_cache,
                    status_lookup=status_lookup,
                    target_lookup=target_lookup
                )
                calculated_count += 1
                
                print(f"\n⚡ {renewable.code:15s} | {renewable.name[:40]:40s}")
                print(f"  Formula: {renewable.formula[:60]}")
                print(f"  Stored:     Status={renewable.status_value}, Target={renewable.target_value}")
                print(f"  Calculated: Status={calc_status}, Target={calc_target}")
                
                # Check if calculated matches stored
                if calc_status is not None and renewable.status_value is not None:
                    diff = abs(float(calc_status) - float(renewable.status_value))
                    if diff > 0.01:
                        print(f"  ⚠️  WARNING: Difference of {diff} between stored and calculated!")
                
                # Update lookup for dependent calculations
                if calc_status is not None:
                    status_lookup[renewable.code] = float(calc_status)
                if calc_target is not None:
                    target_lookup[renewable.code] = float(calc_target)
                    
            except Exception as e:
                error_count += 1
                print(f"\n❌ {renewable.code:15s} | {renewable.name[:40]:40s}")
                print(f"  ERROR: {str(e)}")
        else:
            print(f"\n• {renewable.code:15s} | {renewable.name[:40]:40s}")
            print(f"  No formula, no fixed - using stored values")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total entries tested: {min(20, len(renewables))}")
    print(f"Fixed values: {fixed_count}")
    print(f"Calculated formulas: {calculated_count}")
    print(f"Errors: {error_count}")
    print()
    
    # Test a specific dependency chain
    print("\n" + "=" * 80)
    print("TESTING DEPENDENCY CHAIN")
    print("=" * 80)
    
    # Find entries that depend on LandUse
    landuse_dependent = []
    for renewable in renewables:
        if renewable.formula and 'LandUse' in renewable.formula:
            landuse_dependent.append(renewable)
    
    print(f"\nFound {len(landuse_dependent)} entries with LandUse dependencies:")
    for renewable in landuse_dependent[:5]:
        print(f"  {renewable.code}: {renewable.formula[:60]}")
    
    print("\n✅ Test complete!")

if __name__ == '__main__':
    test_dynamic_calculations()
