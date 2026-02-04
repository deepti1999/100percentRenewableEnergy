#!/usr/bin/env python
"""
Verify all RenewableData values match the Excel data from images
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def compare_values(db_val, excel_val, tolerance=0.01):
    """Compare two values ignoring minor differences and formatting"""
    if db_val is None and excel_val is None:
        return True
    if db_val is None or excel_val is None:
        return False
    
    # Convert to float
    try:
        db_float = float(db_val)
        excel_float = float(excel_val)
        
        # Check if values are close (within tolerance)
        if abs(db_float - excel_float) < tolerance:
            return True
        
        # Check percentage difference
        if excel_float != 0:
            pct_diff = abs((db_float - excel_float) / excel_float * 100)
            return pct_diff < 0.1  # Less than 0.1% difference
        
        return db_float == excel_float
    except (ValueError, TypeError):
        return str(db_val) == str(excel_val)

def verify_renewable_data():
    print("=" * 80)
    print("VERIFYING RENEWABLE DATA AGAINST EXCEL VALUES")
    print("=" * 80)
    
    # Get all renewable data from database
    all_renewables = RenewableData.objects.all().order_by('code')
    
    mismatches = []
    matches = 0
    total_checked = 0
    
    print("\nChecking all entries...")
    print("-" * 80)
    
    for renewable in all_renewables:
        total_checked += 1
        
        # Show entry
        status_display = f"{renewable.status_value:.3f}" if renewable.status_value is not None else "None"
        target_display = f"{renewable.target_value:.3f}" if renewable.target_value is not None else "None"
        
        # For now, just display all values for manual verification
        # Since we don't have the Excel file, we'll list all values
        print(f"{renewable.code:15s} | {renewable.name[:45]:45s} | Status: {status_display:15s} | Target: {target_display:15s}")
        matches += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY")
    print("=" * 80)
    print(f"Total entries: {total_checked}")
    print(f"All values displayed for manual verification against Excel images")
    print()
    print("To verify:")
    print("1. Compare Status column values with 'Status' column in Excel")
    print("2. Compare Target column values with 'Ziel' column in Excel")
    print("3. Ignore differences in decimal separators (. vs ,)")
    print()
    
    # Export to CSV for easier comparison
    print("Exporting to CSV for easier comparison...")
    with open('renewable_data_verification.csv', 'w') as f:
        f.write("Code,Name,Status,Target,Unit,Formula,Is_Fixed\n")
        for renewable in all_renewables:
            status = renewable.status_value if renewable.status_value is not None else ""
            target = renewable.target_value if renewable.target_value is not None else ""
            formula = renewable.formula if renewable.formula else ""
            f.write(f'"{renewable.code}","{renewable.name}",{status},{target},"{renewable.unit}","{formula}",{renewable.is_fixed}\n')
    
    print("✅ Exported to: renewable_data_verification.csv")
    print("   You can open this in Excel to compare side-by-side")

if __name__ == '__main__':
    verify_renewable_data()
