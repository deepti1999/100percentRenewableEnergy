#!/usr/bin/env python3
"""
Test all the final fixes:
1. Decimal formatting fixed for 3.0 values
2. Missing entry 3.2.1.5 added
3. Formula for 3.2.1.5 implemented
4. All calculations working properly
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def test_decimal_formatting():
    """Test that 3.0 values no longer have decimals"""
    print("=== TESTING DECIMAL FORMATTING ===")
    entry_3_0 = VerbrauchData.objects.get(code='3.0')
    print(f"3.0 Status: {entry_3_0.status} (type: {type(entry_3_0.status)})")
    print(f"3.0 Ziel: {entry_3_0.ziel} (type: {type(entry_3_0.ziel)})")
    
    # Check that they are integers, not floats with decimals
    if isinstance(entry_3_0.status, int) or (isinstance(entry_3_0.status, float) and entry_3_0.status.is_integer()):
        print("✓ Status formatting correct")
    else:
        print("✗ Status still has decimal formatting")
    
    if isinstance(entry_3_0.ziel, int) or (isinstance(entry_3_0.ziel, float) and entry_3_0.ziel.is_integer()):
        print("✓ Ziel formatting correct")
    else:
        print("✗ Ziel still has decimal formatting")

def test_missing_entry():
    """Test that 3.2.1.5 entry exists"""
    print("\n=== TESTING MISSING ENTRY ===")
    try:
        entry = VerbrauchData.objects.get(code='3.2.1.5')
        print(f"✓ Found entry: {entry.code} - {entry.category}")
        print(f"  Is calculated: {entry.is_calculated}")
        return True
    except VerbrauchData.DoesNotExist:
        print("✗ Entry 3.2.1.5 not found")
        return False

def test_complete_structure():
    """Test the complete 3.2.x structure"""
    print("\n=== TESTING COMPLETE 3.2.x STRUCTURE ===")
    entries_3_2 = VerbrauchData.objects.filter(code__startswith='3.2').order_by('code')
    expected_codes = ['3.2', '3.2.0', '3.2.1', '3.2.1.5', '3.2.2', '3.2.3']
    
    actual_codes = [entry.code for entry in entries_3_2]
    print(f"Expected: {expected_codes}")
    print(f"Actual:   {actual_codes}")
    
    if actual_codes == expected_codes:
        print("✓ Structure complete and correct")
    else:
        print("✗ Structure mismatch")

def test_all_formulas():
    """Test all Prozesswärme formulas"""
    print("\n=== TESTING ALL FORMULAS ===")
    
    calculated_codes = ['3.1.0', '3.1.2', '3.2.0', '3.2.1.5', '3.2.3']
    
    for code in calculated_codes:
        entry = VerbrauchData.objects.filter(code=code).first()
        if entry:
            status_calc = entry.calculate_value()
            ziel_calc = entry.calculate_ziel_value()
            print(f"{code:8} Status calc: {status_calc:>10} | Ziel calc: {ziel_calc:>10}")
        else:
            print(f"{code:8} NOT FOUND")

if __name__ == '__main__':
    test_decimal_formatting()
    test_missing_entry()
    test_complete_structure()
    test_all_formulas()
    print("\n✓ ALL TESTS COMPLETED!")