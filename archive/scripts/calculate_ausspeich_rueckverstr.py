#!/usr/bin/env python3
"""
Calculate Ausspeich.Rückverstr. column for WSData.

Formula:
Ausspeich.Rückverstr. = Speicher-Ausgl-Strom / t1

Where:
- t1 = 0.585 (58.5%) - Gas to Power efficiency from WS Annual Electricity diagram
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.ws_models import WSData

# Constant from WS1 Annual Electricity Flow Diagram
T1_EFFICIENCY = 0.585  # Gas to Power efficiency (58.5%)

def calculate_ausspeich_rueckverstr():
    """Calculate Ausspeich.Rückverstr. for all 366 rows"""
    
    print("=" * 80)
    print("CALCULATING AUSSPEICH.RÜCKVERSTR.")
    print("=" * 80)
    print(f"\nConstant from WS1 Annual Electricity Diagram:")
    print(f"  t1 (Gas to Power): {T1_EFFICIENCY * 100}% = {T1_EFFICIENCY}")
    print()
    
    # Get all rows
    all_rows = WSData.objects.all().order_by('tag_im_jahr')
    daily_rows = all_rows.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    
    ausspeich_sum = 0
    
    for row in daily_rows:
        speicher = row.speicher_ausgl_strom if row.speicher_ausgl_strom is not None else 0
        
        # Formula: Speicher-Ausgl-Strom / t1
        row.ausspeich_rueckverstr = speicher / T1_EFFICIENCY
        row.save()
        
        ausspeich_sum += row.ausspeich_rueckverstr
        
        if row.tag_im_jahr <= 3:
            print(f"Row {row.tag_im_jahr:3d}: Speicher-Ausgl-Strom = {speicher:,.2f}")
            print(f"          Ausspeich.Rückverstr. = {speicher:,.2f} / {T1_EFFICIENCY} = {row.ausspeich_rueckverstr:,.2f}")
            print()
    
    # Row 366 = sum of rows 1-365
    try:
        row_366 = all_rows.get(tag_im_jahr=366)
        row_366.ausspeich_rueckverstr = ausspeich_sum
        row_366.save()
        print(f"Row 366: Ausspeich.Rückverstr. (sum) = {ausspeich_sum:,.2f}")
        print()
    except WSData.DoesNotExist:
        pass
    
    print("=" * 80)
    print(f"✓ Ausspeich.Rückverstr. row 366: {ausspeich_sum:,.2f}")
    print("=" * 80)

if __name__ == "__main__":
    calculate_ausspeich_rueckverstr()
