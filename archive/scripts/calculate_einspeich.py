#!/usr/bin/env python3
"""
Calculate Einspeich column for all 366 rows in WSData.

Formula from Excel: =WENN(O157/I157<=Abregelung;O157;I157*Abregelung)*EtaStromGas
Where:
- O = ueberschuss_strom
- I = stromverbr_raumwaerm_korr
- Abregelung (n2) = 100% = 1.0 (from WS1 Annual Electricity Diagram)
- EtaStromGas (n1) = 65% = 0.65 (from WS1 Annual Electricity Diagram)

Logic:
IF(ueberschuss_strom / stromverbr_raumwaerm_korr <= 1.0):
    einspeich = ueberschuss_strom * 0.65
ELSE:
    einspeich = stromverbr_raumwaerm_korr * 1.0 * 0.65
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.ws_models import WSData

# Constants from WS1 Annual Electricity Flow Diagram
ETA_STROM_GAS = 0.65  # n1: Power to Gas (H₂) efficiency
ABREGELUNG = 1.0      # n2: Base Rate (100%)

def calculate_einspeich():
    """Calculate Einspeich for all 366 rows"""
    
    print("=" * 80)
    print("CALCULATING EINSPEICH (Column Q) FOR ALL 366 ROWS")
    print("=" * 80)
    print(f"\nConstants from WS1 Annual Electricity Diagram:")
    print(f"  n1 (EtaStromGas): {ETA_STROM_GAS * 100}% = {ETA_STROM_GAS}")
    print(f"  n2 (Abregelung): {ABREGELUNG * 100}% = {ABREGELUNG}")
    print()
    
    # Get all 366 rows
    all_rows = WSData.objects.all().order_by('tag_im_jahr')
    
    updated_count = 0
    daily_sum = 0
    
    # Calculate for days 1-365
    daily_rows = all_rows.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    
    for row in daily_rows:
        # Get values
        ueberschuss = row.ueberschuss_strom if row.ueberschuss_strom is not None else 0
        stromverbr = row.stromverbr_raumwaerm_korr if row.stromverbr_raumwaerm_korr is not None else 0
        
        # Calculate einspeich
        if stromverbr == 0:
            # Avoid division by zero
            einspeich_value = 0
        else:
            ratio = ueberschuss / stromverbr
            if ratio <= ABREGELUNG:
                # Use ueberschuss if ratio is within limit
                einspeich_value = ueberschuss * ETA_STROM_GAS
            else:
                # Use stromverbr * abregelung if ratio exceeds limit
                einspeich_value = stromverbr * ABREGELUNG * ETA_STROM_GAS
        
        # Update the row
        row.einspeich = round(einspeich_value, 2)
        row.save()
        
        updated_count += 1
        daily_sum += einspeich_value
        
        # Show sample calculations for first 3 days
        if row.tag_im_jahr <= 3:
            ratio_str = f"{ratio:.4f}" if stromverbr != 0 else "N/A"
            condition = "ratio <= 1.0" if stromverbr != 0 and ratio <= ABREGELUNG else "ratio > 1.0"
            print(f"Row {row.tag_im_jahr:3d}: Überschuss={ueberschuss:12,.2f}, Stromverbr={stromverbr:12,.2f}")
            print(f"          Ratio={ratio_str:>10s}, {condition}")
            print(f"          Einspeich = {einspeich_value:,.2f}")
            print()
    
    # Row 366 = sum of rows 1-365
    try:
        row_366 = all_rows.get(tag_im_jahr=366)
        row_366.einspeich = round(daily_sum, 2)
        row_366.save()
        updated_count += 1
        
        print(f"Row 366: Sum of days 1-365")
        print(f"          Einspeich = {daily_sum:,.2f}")
        print()
    except WSData.DoesNotExist:
        pass
    
    print("=" * 80)
    print(f"✓ Successfully calculated Einspeich for {updated_count} rows")
    print(f"✓ Sum of Einspeich (rows 1-365): {daily_sum:,.2f}")
    print(f"✓ Row 366 Einspeich (sum): {round(daily_sum, 2):,.2f}")
    print("=" * 80)

if __name__ == "__main__":
    calculate_einspeich()
