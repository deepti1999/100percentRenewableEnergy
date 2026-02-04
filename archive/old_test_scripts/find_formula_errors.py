#!/usr/bin/env python
"""
Find all formula errors in RenewableData
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, LandUse, VerbrauchData

def find_formula_errors():
    print("=" * 80)
    print("FINDING FORMULA ERRORS")
    print("=" * 80)
    
    # Build shared lookup dictionaries
    status_lookup = {}
    target_lookup = {}
    calculation_cache = {}
    
    # Load VerbrauchData
    for verbrauch in VerbrauchData.objects.all():
        if verbrauch.status is not None:
            status_lookup[verbrauch.code] = float(verbrauch.status)
        if verbrauch.ziel is not None:
            target_lookup[verbrauch.code] = float(verbrauch.ziel)
    
    # Load LandUse data
    available_landuse = set()
    for landuse in LandUse.objects.all():
        available_landuse.add(str(landuse.code))
        if landuse.status_ha is not None:
            status_lookup[str(landuse.code)] = float(landuse.status_ha)
        if landuse.target_ha is not None:
            target_lookup[str(landuse.code)] = float(landuse.target_ha)
    
    print(f"\nAvailable LandUse codes: {sorted(available_landuse)}")
    print()
    
    # Check all renewable formulas
    renewables = list(RenewableData.objects.all().order_by('code'))
    
    # First, load all fixed values
    for renewable in renewables:
        if renewable.is_fixed:
            if renewable.status_value is not None:
                status_lookup[renewable.code] = float(renewable.status_value)
            if renewable.target_value is not None:
                target_lookup[renewable.code] = float(renewable.target_value)
    
    errors = []
    warnings = []
    
    print("Checking formulas...")
    print("-" * 80)
    
    for renewable in renewables:
        if not renewable.formula or renewable.is_fixed:
            continue
            
        formula = renewable.formula
        issues = []
        
        # Check for LandUse references
        if 'LandUse_' in formula:
            import re
            landuse_refs = re.findall(r'LandUse_(\d+(?:\.\d+)*)', formula)
            for ref in landuse_refs:
                if ref not in available_landuse:
                    issues.append(f"LandUse_{ref} doesn't exist (available: {sorted(available_landuse)})")
        
        # Check for code references
        import re
        code_refs = re.findall(r'\b(\d+\.\d+(?:\.\d+)*)\b', formula)
        for ref in code_refs:
            if ref not in status_lookup and ref not in [renewable.code]:
                # Check if it's a VerbrauchData code
                try:
                    VerbrauchData.objects.get(code=ref)
                except VerbrauchData.DoesNotExist:
                    # Check if it's another RenewableData code
                    try:
                        RenewableData.objects.get(code=ref)
                    except RenewableData.DoesNotExist:
                        issues.append(f"Code {ref} not found in any data source")
        
        # Try to calculate
        try:
            calc_status, calc_target = renewable.get_calculated_values(
                _cache=calculation_cache,
                status_lookup=status_lookup,
                target_lookup=target_lookup
            )
            
            if calc_status is None and calc_target is None:
                if not issues:
                    issues.append("Calculation returned None but no obvious error found")
                    
            # Update lookup for dependent calculations
            if calc_status is not None:
                status_lookup[renewable.code] = float(calc_status)
            if calc_target is not None:
                target_lookup[renewable.code] = float(calc_target)
                
        except Exception as e:
            issues.append(f"Exception: {str(e)}")
        
        if issues:
            error_entry = {
                'code': renewable.code,
                'name': renewable.name,
                'formula': formula,
                'issues': issues
            }
            
            if calc_status is None and calc_target is None:
                errors.append(error_entry)
            else:
                warnings.append(error_entry)
    
    # Print errors
    if errors:
        print("\n❌ ERRORS (calculation returned None):")
        print("=" * 80)
        for err in errors:
            print(f"\nCode: {err['code']}")
            print(f"Name: {err['name']}")
            print(f"Formula: {err['formula']}")
            for issue in err['issues']:
                print(f"  ⚠️  {issue}")
    
    # Print warnings
    if warnings:
        print("\n⚠️  WARNINGS (calculation succeeded but has issues):")
        print("=" * 80)
        for warn in warnings:
            print(f"\nCode: {warn['code']}")
            print(f"Name: {warn['name']}")
            print(f"Formula: {warn['formula']}")
            for issue in warn['issues']:
                print(f"  ⚠️  {issue}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(errors)} errors, {len(warnings)} warnings")
    print("=" * 80)
    
    return errors

if __name__ == '__main__':
    find_formula_errors()
