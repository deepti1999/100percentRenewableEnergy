#!/usr/bin/env python3
"""
Calculate Mangel-Last, Brennstoff-Ausgleichs-Strom, and Speicher-Ausgl-Strom columns for WSData.

Formulas:
1. Mangel-Last = Stromverbr.Raumw.korr. - Direktverbr. Strom

2. Brennstoff-Ausgleichs-Strom = (Bio_S / MangelLast_366) × MangelLast_current_row
   Where:
   - Bio_S = RenewableData code 4.4.1 (Bedarfs-Kraftwerke Biobrennstoffe from WS diagram)
   - MangelLast_366 = Sum of Mangel-Last for days 1-365
   - MangelLast_current_row = Mangel-Last for current row

3. Speicher-Ausgl-Strom = Mangel-Last - Brennstoff-Ausgleichs-Strom
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.ws_models import WSData
from simulator.models import RenewableData

def calculate_mangel_brennstoff():
    """Calculate Mangel-Last and Brennstoff-Ausgleichs-Strom for all 366 rows"""
    
    print("=" * 80)
    print("CALCULATING MANGEL-LAST AND BRENNSTOFF-AUSGLEICHS-STROM")
    print("=" * 80)
    
    # Get Bio S value from WS Annual Electricity diagram
    try:
        bio_renewable = RenewableData.objects.get(code='4.4.1')
        bio_s_value = float(bio_renewable.target_value) if bio_renewable.target_value is not None else 0
    except RenewableData.DoesNotExist:
        bio_s_value = 0
    
    print(f"\nBio S value (4.4.1 Ziel): {bio_s_value:,.2f}")
    print()
    
    # Get all rows
    all_rows = WSData.objects.all().order_by('tag_im_jahr')
    daily_rows = all_rows.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    
    # Step 1: Calculate Mangel-Last for all rows (1-365)
    print("Step 1: Calculating Mangel-Last...")
    mangel_last_sum = 0
    
    for row in daily_rows:
        stromverbr = row.stromverbr_raumwaerm_korr if row.stromverbr_raumwaerm_korr is not None else 0
        direktverbr = row.direktverbr_strom if row.direktverbr_strom is not None else 0
        
        row.mangel_last = stromverbr - direktverbr
        row.save()
        
        mangel_last_sum += row.mangel_last
        
        if row.tag_im_jahr <= 3:
            print(f"Row {row.tag_im_jahr:3d}: Stromverbr={stromverbr:12,.2f}, Direktverbr={direktverbr:12,.2f}")
            print(f"          Mangel-Last = {row.mangel_last:,.2f}")
            print()
    
    # Row 366 Mangel-Last = sum of rows 1-365
    try:
        row_366 = all_rows.get(tag_im_jahr=366)
        row_366.mangel_last = mangel_last_sum
        row_366.save()
        print(f"Row 366: Mangel-Last (sum) = {mangel_last_sum:,.2f}")
        print()
    except WSData.DoesNotExist:
        row_366 = None
    
    # Step 2: Calculate Brennstoff-Ausgleichs-Strom for all rows (1-365)
    print("Step 2: Calculating Brennstoff-Ausgleichs-Strom...")
    brennstoff_sum = 0
    speicher_sum = 0
    
    if mangel_last_sum > 0:
        for row in daily_rows:
            # Formula: (Bio_S / MangelLast_366) × MangelLast_current_row
            row.brennstoff_ausgleichs_strom = (bio_s_value / mangel_last_sum) * row.mangel_last
            
            # Calculate Speicher-Ausgl-Strom: Mangel-Last - Brennstoff-Ausgleichs-Strom
            row.speicher_ausgl_strom = row.mangel_last - row.brennstoff_ausgleichs_strom
            row.save()
            
            brennstoff_sum += row.brennstoff_ausgleichs_strom
            speicher_sum += row.speicher_ausgl_strom
            
            if row.tag_im_jahr <= 3:
                print(f"Row {row.tag_im_jahr:3d}: ({bio_s_value:,.2f} / {mangel_last_sum:,.2f}) × {row.mangel_last:,.2f}")
                print(f"          Brennstoff-Ausgleichs-Strom = {row.brennstoff_ausgleichs_strom:,.2f}")
                print(f"          Speicher-Ausgl-Strom = {row.speicher_ausgl_strom:,.2f}")
                print()
        
        # Row 366: sums of rows 1-365
        if row_366:
            row_366.brennstoff_ausgleichs_strom = brennstoff_sum
            row_366.speicher_ausgl_strom = speicher_sum
            row_366.save()
            print(f"Row 366: Brennstoff-Ausgleichs-Strom (sum) = {brennstoff_sum:,.2f}")
            print(f"Row 366: Speicher-Ausgl-Strom (sum) = {speicher_sum:,.2f}")
            print()
    else:
        print("⚠ MangelLast_366 is 0, cannot calculate Brennstoff-Ausgleichs-Strom")
    
    print("=" * 80)
    print(f"✓ Mangel-Last row 366: {mangel_last_sum:,.2f}")
    print(f"✓ Brennstoff-Ausgleichs-Strom row 366: {brennstoff_sum:,.2f}")
    print(f"✓ Speicher-Ausgl-Strom row 366: {speicher_sum:,.2f}")
    print(f"✓ Verification: Brennstoff should equal Bio S = {bio_s_value:,.2f}")
    print(f"✓ Verification: Mangel-Last = Brennstoff + Speicher ({mangel_last_sum:,.2f} = {brennstoff_sum:,.2f} + {speicher_sum:,.2f})")
    print("=" * 80)

if __name__ == "__main__":
    calculate_mangel_brennstoff()
