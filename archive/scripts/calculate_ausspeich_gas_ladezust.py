#!/usr/bin/env python3
"""
Calculate Ausspeich. Gas and Ladezust.Burtto columns for WSData.

Formulas:
1. Ausspeich. Gas = 0 (for all rows)

2. Ladezust.Burtto (cumulative):
   Day 1 = Ladezust.Burtto(day 367) + Einspeich(day1) - Ausspeich.Rückverstr(day1) - Ausspeich.Gas(day1)
   Day 2 = Ladezust.Burtto(day1) + Einspeich(day2) - Ausspeich.Rückverstr(day2) - Ausspeich.Gas(day2)
   Day 3 = Ladezust.Burtto(day2) + Einspeich(day3) - Ausspeich.Rückverstr(day3) - Ausspeich.Gas(day3)
   ...and so on
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.ws_models import WSData

def calculate_ausspeich_gas_and_ladezust():
    """Calculate Ausspeich. Gas and Ladezust.Burtto for all rows"""
    
    print("=" * 80)
    print("CALCULATING AUSSPEICH. GAS AND LADEZUST.BURTTO")
    print("=" * 80)
    print()
    
    # Get all rows
    all_rows = WSData.objects.all().order_by('tag_im_jahr')
    
    # Step 1: Set Ausspeich. Gas = 0 for all rows
    print("Step 1: Setting Ausspeich. Gas = 0 for all rows...")
    for row in all_rows:
        row.ausspeich_gas = 0
        row.save()
    print("✓ Done")
    print()
    
    # Step 2: Get row 367 Ladezust.Burtto (initial value)
    try:
        row_367 = all_rows.get(tag_im_jahr=367)
        if row_367.ladezust_burtto is None:
            # Set initial value to 0 if not set
            row_367.ladezust_burtto = 0
            row_367.save()
        ladezust_previous = row_367.ladezust_burtto
        print(f"Step 2: Initial Ladezust.Burtto (row 367) = {ladezust_previous:,.2f}")
        print()
    except WSData.DoesNotExist:
        print("⚠ Row 367 doesn't exist, using 0 as initial value")
        ladezust_previous = 0
        print()
    
    # Step 3: Calculate Ladezust.Burtto cumulatively for days 1-365
    print("Step 3: Calculating Ladezust.Burtto cumulatively...")
    daily_rows = all_rows.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    
    for row in daily_rows:
        einspeich = row.einspeich if row.einspeich is not None else 0
        ausspeich_rueck = row.ausspeich_rueckverstr if row.ausspeich_rueckverstr is not None else 0
        ausspeich_gas = row.ausspeich_gas if row.ausspeich_gas is not None else 0
        
        # Formula: Ladezust.Burtto(current) = Ladezust.Burtto(previous) + Einspeich - Ausspeich.Rückverstr - Ausspeich.Gas
        row.ladezust_burtto = ladezust_previous + einspeich - ausspeich_rueck - ausspeich_gas
        row.save()
        
        if row.tag_im_jahr <= 3:
            print(f"Day {row.tag_im_jahr}: {ladezust_previous:,.2f} + {einspeich:,.2f} - {ausspeich_rueck:,.2f} - {ausspeich_gas:,.2f}")
            print(f"         Ladezust.Burtto = {row.ladezust_burtto:,.2f}")
            print()
        
        # Update previous for next iteration
        ladezust_previous = row.ladezust_burtto
    
    # Step 4: Set row 366 to the final value from day 365
    try:
        row_365 = all_rows.get(tag_im_jahr=365)
        row_366 = all_rows.get(tag_im_jahr=366)
        row_366.ladezust_burtto = row_365.ladezust_burtto
        row_366.save()
        print(f"Row 366: Ladezust.Burtto (final from day 365) = {row_366.ladezust_burtto:,.2f}")
        print()
    except WSData.DoesNotExist:
        pass
    
    print("=" * 80)
    print(f"✓ Ausspeich. Gas: All rows = 0")
    print(f"✓ Ladezust.Burtto: Calculated cumulatively for days 1-365")
    print("=" * 80)

if __name__ == "__main__":
    calculate_ausspeich_gas_and_ladezust()
