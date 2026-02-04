#!/usr/bin/env python
"""
Fix all problematic formulas in RenewableData
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def fix_formulas():
    print("=" * 80)
    print("FIXING FORMULAS")
    print("=" * 80)
    
    fixes = [
        # Fix AUTOMATIC formulas to proper LandUse_ format
        {
            'code': '1.2',
            'old_formula': 'AUTOMATIC from LandUse 2.1',
            'new_formula': 'LandUse_2.1',
            'reason': 'AUTOMATIC format not recognized, should be LandUse_X'
        },
        {
            'code': '2.1.1',
            'old_formula': 'AUTOMATIC from LandUse 5.1',
            'new_formula': 'LandUse_5.1',
            'reason': 'AUTOMATIC format not recognized, should be LandUse_X'
        },
        {
            'code': '4.1.1.1',
            'old_formula': 'AUTOMATIC from LandUse 3.1',
            'new_formula': 'LandUse_3.1',
            'reason': 'AUTOMATIC format not recognized, should be LandUse_X'
        },
        {
            'code': '4.1.2.1',
            'old_formula': 'AUTOMATIC from LandUse 2.2.5',
            'new_formula': 'LandUse_2.2.5',
            'reason': 'AUTOMATIC format not recognized, should be LandUse_X'
        },
        {
            'code': '4.2.1',
            'old_formula': 'AUTOMATIC from LandUse 2.2.1',
            'new_formula': 'LandUse_2.2.1',
            'reason': 'AUTOMATIC format not recognized, should be LandUse_X'
        },
        {
            'code': '5.1',
            'old_formula': 'AUTOMATIC from LandUse 2.2.2',
            'new_formula': 'LandUse_2.2.2',
            'reason': 'AUTOMATIC format not recognized, should be LandUse_X'
        },
        # Fix formula with wrong LandUse reference
        {
            'code': '1.1.1.1.2',
            'old_formula': 'LandUse_1.1 * 1.1.1.1 / 100 * 1.1.1.1.1 / 1000',
            'new_formula': '1.1 * 1.1.1.1 / 100 * 1.1.1.1.1 / 1000',
            'reason': 'LandUse_1.1 should be renewable code 1.1 (Solare Dachflächen)'
        },
    ]
    
    updated_count = 0
    
    for fix in fixes:
        try:
            renewable = RenewableData.objects.get(code=fix['code'])
            
            print(f"\n📝 Fixing {fix['code']}: {renewable.name}")
            print(f"   Old formula: {renewable.formula}")
            print(f"   New formula: {fix['new_formula']}")
            print(f"   Reason: {fix['reason']}")
            
            if renewable.formula == fix['old_formula']:
                renewable.formula = fix['new_formula']
                renewable.save()
                print(f"   ✅ Updated successfully")
                updated_count += 1
            else:
                print(f"   ⚠️  Skipped - current formula doesn't match expected")
                print(f"   Current: {renewable.formula}")
                
        except RenewableData.DoesNotExist:
            print(f"   ❌ Code {fix['code']} not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: Updated {updated_count} formulas")
    print("=" * 80)
    
    # Note about ordering issues
    print("\n📌 NOTE: Formulas 9.1 and 9.2.1.5 reference child codes that need to be")
    print("   calculated first. The view now processes renewables in code order,")
    print("   so child codes (9.1.1, 9.1.2, etc.) will be calculated before parent")
    print("   codes (9.1), which will resolve the 'code not found' warnings.")

if __name__ == '__main__':
    fix_formulas()
