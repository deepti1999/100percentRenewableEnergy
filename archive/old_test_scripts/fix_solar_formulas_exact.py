#!/usr/bin/env python
"""
Fix solar energy formulas to match Excel exactly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, LandUse

def fix_solar_formulas():
    """Fix all solar formulas to match Excel"""
    
    print("="*80)
    print("FIXING SOLAR ENERGY FORMULAS TO MATCH EXCEL")
    print("="*80)
    
    # Fix 1.1.1.1.2 - Gebäudewärme (Solarthermie)
    # Excel: [6] [8] [9] = LandUse_1.1 * 1.1.1.1% * 1.1.1.1.1 / 1000
    entry = RenewableData.objects.get(code='1.1.1.1.2')
    landuse_1_1_s = LandUse.objects.get(code='1.1').status_ha
    landuse_1_1_t = LandUse.objects.get(code='1.1').target_ha
    anteil_s = RenewableData.objects.get(code='1.1.1.1').status_value
    anteil_t = RenewableData.objects.get(code='1.1.1.1').target_value
    ertrag_s = RenewableData.objects.get(code='1.1.1.1.1').status_value
    ertrag_t = RenewableData.objects.get(code='1.1.1.1.1').target_value
    
    entry.status_value = landuse_1_1_s * anteil_s / 100 * ertrag_s / 1000
    entry.target_value = landuse_1_1_t * anteil_t / 100 * ertrag_t / 1000
    entry.formula = 'LandUse_1.1 * 1.1.1.1 / 100 * 1.1.1.1.1 / 1000'
    entry.save()
    print(f"✓ 1.1.1.1.2 Gebäudewärme: Status={entry.status_value:.2f}, Target={entry.target_value:.2f}")
    
    # Fix 1.1.2.1.2 - Bruttostromerzeugung (Solarstrom Dach)
    # Excel: [6] [13] [14] = LandUse_1.1 * 1.1.2.1% * 1.1.2.1.1 / 1000
    entry = RenewableData.objects.get(code='1.1.2.1.2')
    anteil_strom_s = RenewableData.objects.get(code='1.1.2.1').status_value
    anteil_strom_t = RenewableData.objects.get(code='1.1.2.1').target_value
    ertrag_strom_s = RenewableData.objects.get(code='1.1.2.1.1').status_value
    ertrag_strom_t = RenewableData.objects.get(code='1.1.2.1.1').target_value
    
    entry.status_value = landuse_1_1_s * anteil_strom_s / 100 * ertrag_strom_s / 1000
    entry.target_value = landuse_1_1_t * anteil_strom_t / 100 * ertrag_strom_t / 1000
    entry.formula = 'LandUse_1.1 * 1.1.2.1 / 100 * 1.1.2.1.1 / 1000'
    entry.save()
    print(f"✓ 1.1.2.1.2 Bruttostromerzeugung Dach: Status={entry.status_value:.2f}, Target={entry.target_value:.2f}")
    
    # Fix 1.1.2.1.2.2 - Installierte Leistung (Solarstrom Dach)
    # Excel: [15] [16] = Bruttostromerzeugung / Vollbetriebstunden * 1000
    entry = RenewableData.objects.get(code='1.1.2.1.2.2')
    brutto_s = RenewableData.objects.get(code='1.1.2.1.2').status_value
    brutto_t = RenewableData.objects.get(code='1.1.2.1.2').target_value
    vollbetrieb = RenewableData.objects.get(code='1.1.2.1.2.1').status_value
    
    entry.status_value = brutto_s / vollbetrieb * 1000
    entry.target_value = brutto_t / vollbetrieb * 1000
    entry.formula = '1.1.2.1.2 / 1.1.2.1.2.1 * 1000'
    entry.save()
    print(f"✓ 1.1.2.1.2.2 Installierte Leistung Dach: Status={entry.status_value:.2f}, Target={entry.target_value:.2f}")
    
    # Fix 1.2 - Solar genutzte Freiflächen (comes from LandUse 2.1)
    entry = RenewableData.objects.get(code='1.2')
    landuse_2_1_s = LandUse.objects.get(code='2.1').status_ha
    landuse_2_1_t = LandUse.objects.get(code='2.1').target_ha
    entry.status_value = landuse_2_1_s
    entry.target_value = landuse_2_1_t
    entry.save()
    print(f"✓ 1.2 Solar Freiflächen: Status={entry.status_value:.2f}, Target={entry.target_value:.2f}")
    
    # Fix 1.2.1.2 - Bruttostromerzeugung (Solarstrom Freifläche)
    # Excel: [19] [21] = LandUse_2.1 * 1.2.1.1 / 1000
    entry = RenewableData.objects.get(code='1.2.1.2')
    ertrag_frei_s = RenewableData.objects.get(code='1.2.1.1').status_value
    ertrag_frei_t = RenewableData.objects.get(code='1.2.1.1').target_value
    
    entry.status_value = landuse_2_1_s * ertrag_frei_s / 1000
    entry.target_value = landuse_2_1_t * ertrag_frei_t / 1000
    entry.formula = 'LandUse_2.1 * 1.2.1.1 / 1000'
    entry.save()
    print(f"✓ 1.2.1.2 Bruttostromerzeugung Frei: Status={entry.status_value:.2f}, Target={entry.target_value:.2f}")
    
    # Fix 1.2.1.2.2 - Installierte Leistung (Solarstrom Freifläche)
    # Excel: [22] [23] = Bruttostromerzeugung / Vollbetriebstunden * 1000
    entry = RenewableData.objects.get(code='1.2.1.2.2')
    brutto_frei_s = RenewableData.objects.get(code='1.2.1.2').status_value
    brutto_frei_t = RenewableData.objects.get(code='1.2.1.2').target_value
    vollbetrieb_frei = RenewableData.objects.get(code='1.2.1.2.1').status_value
    
    entry.status_value = brutto_frei_s / vollbetrieb_frei * 1000
    entry.target_value = brutto_frei_t / vollbetrieb_frei * 1000
    entry.formula = '1.2.1.2 / 1.2.1.2.1 * 1000'
    entry.save()
    print(f"✓ 1.2.1.2.2 Installierte Leistung Frei: Status={entry.status_value:.2f}, Target={entry.target_value:.2f}")
    
    print("\n" + "="*80)
    print("VERIFICATION - COMPARING WITH EXCEL")
    print("="*80)
    
    # Verify against Excel values
    excel_values = {
        '1.1.1.1.2': {'status': 8449, 'target': 11515},
        '1.1.2.1.2': {'status': 44340, 'target': 365421},
        '1.1.2.1.2.2': {'status': 47857, 'target': 394410},
        '1.2': {'status': 19628, 'target': 676910},
        '1.2.1.2': {'status': 18095, 'target': 836209},
        '1.2.1.2.2': {'status': 19530, 'target': 902546},
    }
    
    all_match = True
    for code, excel_vals in excel_values.items():
        entry = RenewableData.objects.get(code=code)
        status_diff = abs(entry.status_value - excel_vals['status'])
        target_diff = abs(entry.target_value - excel_vals['target'])
        
        status_match = status_diff < 1
        target_match = target_diff < 1
        
        status_icon = '✓' if status_match else f'✗ (diff: {status_diff:.2f})'
        target_icon = '✓' if target_match else f'✗ (diff: {target_diff:.2f})'
        
        print(f"{code:15} Status: {status_icon:20} Target: {target_icon}")
        
        if not status_match or not target_match:
            all_match = False
    
    print("\n" + "="*80)
    if all_match:
        print("✅ ALL SOLAR VALUES NOW MATCH EXCEL PERFECTLY!")
    else:
        print("⚠️  Some values still don't match - may need rounding adjustment")
    print("="*80)

if __name__ == "__main__":
    fix_solar_formulas()
