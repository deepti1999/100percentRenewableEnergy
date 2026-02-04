#!/usr/bin/env python3
"""
Fix the final two issues:
1. Remove decimal formatting from 3.0 values (555.395 → 555395)
2. Add missing entry between 3.2.1 and 3.2.2 (should be 3.2.1.5 calculated result)
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def fix_decimal_formatting():
    """Fix 3.0 values - remove decimal points"""
    print("=== FIXING DECIMAL FORMATTING FOR 3.0 VALUES ===")
    
    entry_3_0 = VerbrauchData.objects.get(code='3.0')
    print(f"Before: Status={entry_3_0.status}, Ziel={entry_3_0.ziel}")
    
    # Convert to integers (remove decimal)
    if entry_3_0.status:
        entry_3_0.status = int(float(entry_3_0.status))
    if entry_3_0.ziel:
        entry_3_0.ziel = int(float(entry_3_0.ziel))
    
    entry_3_0.save()
    print(f"After: Status={entry_3_0.status}, Ziel={entry_3_0.ziel}")
    print("✓ Decimal formatting fixed")

def add_missing_entry():
    """Add missing calculated entry between 3.2.1 and 3.2.2"""
    print("\n=== ADDING MISSING ENTRY 3.2.1.5 ===")
    
    # Check if entry already exists
    if VerbrauchData.objects.filter(code='3.2.1.5').exists():
        print("Entry 3.2.1.5 already exists")
        return
    
    # Create the missing calculated entry
    new_entry = VerbrauchData.objects.create(
        code='3.2.1.5',
        category='=',  # Calculated entry marker
        unit='GWh/a',  # Same unit as others
        status=None,   # Will be calculated
        ziel=None,     # Will be calculated
        is_calculated=True
    )
    
    print(f"✓ Created entry: {new_entry.code} - {new_entry.category}")

def show_final_structure():
    """Show the final 3.2.x structure"""
    print("\n=== FINAL 3.2.x STRUCTURE ===")
    entries_3_2 = VerbrauchData.objects.filter(code__startswith='3.2').order_by('code')
    for entry in entries_3_2:
        calc_status = '[CALC]' if entry.is_calculated else '[FIXED]'
        print(f'{entry.code:8} {entry.category:45} {calc_status:8}')

if __name__ == '__main__':
    fix_decimal_formatting()
    add_missing_entry()
    show_final_structure()
    print("\n✓ All final issues fixed!")