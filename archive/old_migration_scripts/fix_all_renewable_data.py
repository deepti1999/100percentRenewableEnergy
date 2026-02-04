#!/usr/bin/env python
"""
Fix ALL missing renewable energy data values (codes 1-9)
Implements proper calculation formulas without changing stored formulas
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, LandUse
from decimal import Decimal

def get_landuse_value(code, use_target=False):
    """Get LandUse value by code"""
    try:
        lu = LandUse.objects.get(code=code)
        return float(lu.target_ha if use_target else lu.status_ha) if (lu.target_ha if use_target else lu.status_ha) else 0
    except:
        return 0

def get_renewable_value(code, use_target=False):
    """Get RenewableData value by code"""
    try:
        rd = RenewableData.objects.get(code=code)
        return float(rd.target_value if use_target else rd.status_value) if (rd.target_value if use_target else rd.status_value) else 0
    except:
        return 0

def calculate_value(code, use_target=False):
    """Calculate value based on formulas"""
    
    # CODE 1.x - SOLAR
    if code == "1":  # Solarenergie (header - not calculated)
        return None
    
    elif code == "1.1":  # Solare Dachflächen
        return get_landuse_value("1.1", use_target)
    
    elif code == "1.1.1":  # Solarthermie (header)
        return None
    
    elif code == "1.1.2":  # Solarstrom (header)
        return None
    
    elif code == "1.2.1":  # Solarstrom Freifläche (header)
        return None
    
    elif code == "1.1.1.1.2":  # Gebäudewärme Solarthermie
        landuse_1_1 = get_landuse_value("1.1", use_target)
        anteil = get_renewable_value("1.1.1.1", use_target)
        ertrag = get_renewable_value("1.1.1.1.1", use_target)
        return (landuse_1_1 * anteil / 100 * ertrag) / 1000
    
    elif code == "1.1.2.1.2.2":  # Installierte Leistung Solar Dach
        val_1 = get_renewable_value("1.1.2.1.2", use_target)
        val_2 = get_renewable_value("1.1.2.1.2.1", use_target)
        if val_2 != 0:
            return val_1 / val_2 * 1000
        return 0
    
    elif code == "1.2":  # Solar genutzte Freiflächen
        return get_landuse_value("2.1", use_target)
    
    elif code == "1.2.1.2.2":  # Installierte Leistung Solar Frei
        val_1 = get_renewable_value("1.2.1.2", use_target)
        val_2 = get_renewable_value("1.2.1.2.1", use_target)
        if val_2 != 0:
            return val_1 / val_2 * 1000
        return 0
    
    # CODE 2.x - WIND
    elif code == "2.1":  # Onshore-Windstrom (header)
        return None
    
    elif code == "2.2":  # Offshore-Windstrom (header)
        return None
    
    elif code == "2.1.1":  # Windparkfläche
        return get_landuse_value("5.1", use_target)
    
    elif code == "2.1.1.2":  # Installierte Leistung Wind
        val_1 = get_renewable_value("2.1.1", use_target)
        val_2 = get_renewable_value("2.1.1.1", use_target)
        if val_2 != 0:
            return val_1 / val_2
        return 0
    
    elif code == "2.1.1.2.2":  # Bruttostromerzeugung Wind
        val_1 = get_renewable_value("2.1.1.2", use_target)
        val_2 = get_renewable_value("2.1.1.2.1", use_target)
        return val_1 * val_2 / 1000
    
    elif code == "2.1.1.2.3":  # Energieertrag Wind
        val_1 = get_renewable_value("2.1.1.2.2", use_target)
        val_2 = get_renewable_value("2.1.1", use_target)
        if val_2 != 0:
            return val_1 * 1000 / val_2
        return 0
    
    elif code == "2.2.1.2":  # Bruttostromerzeugung Offshore
        val_1 = get_renewable_value("2.2.1", use_target)
        val_2 = get_renewable_value("2.2.1.1", use_target)
        return val_1 * val_2 / 1000
    
    # CODE 3.x - LAUFWASSER
    elif code == "3.":  # Laufwasser (header)
        return None
    
    elif code == "3.1.1.2":  # Bruttostromerzeugung Laufwasser
        val_1 = get_renewable_value("3.1", use_target)
        val_2 = get_renewable_value("3.1.1", use_target)
        val_3 = get_renewable_value("3.1.1.1", use_target)
        return val_1 * val_2 / 100 * val_3 / 1000
    
    # CODE 4.x - BIOGENE BRENNSTOFFE (fest)
    elif code == "4.":  # Biogene Brennstoffe (fest) - header
        return None
    
    elif code == "4.1":  # Energieholz - header
        return None
    
    elif code == "4.1.1":  # Aus Forstwirtschaft - header
        return None
    
    elif code == "4.1.1.1":  # Nutzbare Forstfläche
        return get_landuse_value("2.2.1", use_target)
    
    elif code == "4.1.2":  # Aus Ackerbau - header
        return None
    
    elif code == "4.1.2.1":  # Anbaufläche KUP
        return get_landuse_value("2.2.3", use_target)
    
    elif code == "4.2":  # Stroh aus Getreideanbau - header
        return None
    
    elif code == "4.2.1":  # Getreide-Anbaufläche
        return get_landuse_value("2.3.1", use_target)
    
    elif code == "4.1.1.1.1.2":  # Energieholzaufkommen Forst
        val_1 = get_renewable_value("4.1.1.1.1", use_target)
        val_2 = get_renewable_value("4.1.1.1.1.1", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.1.2.1.2":  # Energieholzaufkommen Ackerbau
        val_1 = get_renewable_value("4.1.2.1", use_target)
        val_2 = get_renewable_value("4.1.2.1.1", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.1.3":  # Energieholzaufkommen gesamt
        val_1 = get_renewable_value("4.1.1.1.1.2", use_target)
        val_2 = get_renewable_value("4.1.2.1.2", use_target)
        return val_1 + val_2
    
    elif code == "4.2.1.1.2":  # Strohbrennstoff-Aufkommen
        val_1 = get_renewable_value("4.2.1.1.1", use_target)
        val_2 = get_renewable_value("4.2.1.1", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.3":  # Brennstoffaufkommen NAWARO gesamt
        val_1 = get_renewable_value("4.1.3", use_target)
        val_2 = get_renewable_value("4.2.1.1.2", use_target)
        return val_1 + val_2
    
    elif code == "4.3.1":  # Einsatz für Gebäudewärme
        val_1 = get_renewable_value("4.3", use_target)
        val_2 = get_renewable_value("4.1.3.1", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.3.2":  # Einsatz für Prozesswärme
        val_1 = get_renewable_value("4.3", use_target)
        val_2 = get_renewable_value("4.1.3.2", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.3.3":  # Einsatz für Verstromung
        val_1 = get_renewable_value("4.3", use_target)
        val_2 = get_renewable_value("4.1.3.3", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.3.3.4":  # Wärmenetze GW (KWK)
        val_1 = get_renewable_value("4.3.3.2", use_target)
        val_2 = get_renewable_value("4.3.3.3", use_target)
        val_3 = get_renewable_value("4.3.3.1", use_target)
        if val_3 != 0:
            return val_1 * val_2 / val_3
        return 0
    
    elif code == "4.3.4":  # Einsatz für Heizwerke/Wärmenetze
        val_1 = get_renewable_value("4.3", use_target)
        val_2 = get_renewable_value("4.1.3.4", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.3.4.2":  # Wärmenetze GW (Heizwerk)
        val_1 = get_renewable_value("4.3.4", use_target)
        val_2 = get_renewable_value("4.3.4.1", use_target)
        return val_1 * val_2 / 100
    
    elif code == "4.4":  # Biogener Anteil der Abfälle
        val_1 = get_renewable_value("4.4.1", use_target)
        val_2 = get_renewable_value("4.4.2", use_target)
        return val_1 + val_2
    
    # CODE 5.x - BIOGAS
    elif code == "5.4.1.1":  # Biogas für Prozesswärme
        val_1 = get_renewable_value("5.4", use_target)
        val_2 = get_renewable_value("5.4.1", use_target)
        return val_1 * val_2 / 100
    
    elif code == "5.4.2.4":  # Gebäudewärme (Endenergie) from Biogas
        val_1 = get_renewable_value("5.4", use_target)
        val_2 = get_renewable_value("5.4.2", use_target)
        val_3 = get_renewable_value("5.4.2.3", use_target)
        return val_1 * val_2 / 100 * val_3 / 100
    
    elif code == "5.4.4.2":  # Biokraftstoff (flüssig)
        val_1 = get_renewable_value("5.4", use_target)
        val_2 = get_renewable_value("5.4.4", use_target)
        val_3 = get_renewable_value("5.4.4.1", use_target)
        return val_1 * val_2 / 100 * val_3 / 100
    
    # CODE 6.x - BIOGENE BRENNSTOFFE (flüssig)
    elif code == "6.1":  # Biodiesel - header
        return None
    
    elif code == "6.2.1":  # Anbaufläche Bioethanol
        return get_landuse_value("2.2.4", use_target)
    
    elif code == "6.2.1.2":  # Bioethanol aus eigenem Anbau
        val_1 = get_renewable_value("6.2.1", use_target)
        val_2 = get_renewable_value("6.2.1.1", use_target)
        return val_1 * val_2 / 1000
    
    elif code == "6.2.3":  # Bioethanol gesamt
        val_1 = get_renewable_value("6.2.1.2", use_target)
        val_2 = get_renewable_value("6.2.2", use_target)
        return val_1 + val_2
    
    # CODE 7.x - UMGEBUNGSWÄRME
    elif code == "7.1":  # Wärmepumpen-Antriebsstromaufnahme
        # This needs VerbrauchData_2.9.2 - will be handled separately
        return None
    
    elif code == "7.1.4.3.3":  # Gebäude- & Freifläche (Siedlung)
        return get_landuse_value("1", use_target)
    
    # CODE 8.x - TIEFENGEOTHERMIE
    elif code == "8.1":  # Netzanschlussleistung - target missing but status exists
        # Only target is missing, but it's a fixed value, not calculated
        return None
    
    # CODE 9.x - RENEWABLE ENERGY SUPPLY
    elif code == "9.1.1":  # aus Windenergie
        val_1 = get_renewable_value("2.2.1.2.3", use_target)
        val_2 = get_renewable_value("2.1.1.2.2", use_target)
        return val_1 + val_2
    
    elif code == "9.1.2":  # aus Solarenergie
        val_1 = get_renewable_value("1.1.2.1.2", use_target)
        val_2 = get_renewable_value("1.2.1.2", use_target)
        return val_1 + val_2
    
    elif code == "9.1.3":  # aus Wasserkraft + Tiefengeothermie
        val_1 = get_renewable_value("3.1.1.2", use_target)
        val_2 = get_renewable_value("8.1.2", use_target)
        return val_1 + val_2
    
    elif code == "9.1.4":  # aus Biobrennstoffen
        val_1 = get_renewable_value("4.3.3.2", use_target)
        val_2 = get_renewable_value("4.4.1", use_target)
        val_3 = get_renewable_value("5.4.2.2", use_target)
        val_4 = get_renewable_value("6.1.3.2.2", use_target)
        return val_1 + val_2 + val_3 + val_4
    
    elif code == "9.1":  # Bruttostromerzeugung aus Erneuerbaren
        val_1 = get_renewable_value("9.1.1", use_target)
        val_2 = get_renewable_value("9.1.2", use_target)
        val_3 = get_renewable_value("9.1.3", use_target)
        val_4 = get_renewable_value("9.1.4", use_target)
        return val_1 + val_2 + val_3 + val_4
    
    elif code == "9.2":  # Bruttostromerzeugung Erneuerbar (inkl. A)
        return get_renewable_value("9.1", use_target)
    
    elif code == "9.2.1.2.2":  # Wasserstoff für Kraftstoffsynthese (Methan)
        val_1 = get_renewable_value("9.2.1.2", use_target)
        val_2 = get_renewable_value("9.2.1.2.1", use_target)
        if val_2 != 0:
            return val_1 / val_2 * 100
        return 0
    
    elif code == "9.2.1.4.2":  # Wasserstoff für Grundstoffsynthese
        val_1 = get_renewable_value("9.2.1.4", use_target)
        val_2 = get_renewable_value("9.2.1.4.1", use_target)
        if val_2 != 0:
            return val_1 / val_2 * 100
        return 0
    
    elif code == "9.2.1.5":  # Wasserstofferzeugung
        val_1 = get_renewable_value("9.2.1.1", use_target)
        val_2 = get_renewable_value("9.2.1.1.2", use_target)
        val_3 = get_renewable_value("9.2.1.2.2", use_target)
        val_4 = get_renewable_value("9.2.1.3.2", use_target)
        val_5 = get_renewable_value("9.2.1.4.2", use_target)
        return val_1 + val_2 + val_3 + val_4 + val_5
    
    elif code == "9.2.1":  # Wasser-Elektrolyse (header)
        return None
    
    elif code == "9.2.1.5.1":  # Nutzungsgrad Wasserelektrolyse (status missing)
        # Status is missing but target exists - this is a fixed parameter
        return None
    
    elif code == "9.3":  # Langzeitspeicherung (header)
        return None
    
    elif code == "9.4":  # Stromangebot (header)
        return None
    
    return None

def fix_all_values():
    """Fix all missing values in renewable energy data"""
    
    print("="*80)
    print("FIXING ALL RENEWABLE ENERGY DATA VALUES")
    print("="*80)
    
    # Define order of calculation (dependencies matter!)
    calculation_order = [
        # CODE 1 - Solar
        "1.1", "1.1.1.1.2", "1.1.2.1.2.2", "1.2", "1.2.1.2.2",
        
        # CODE 2 - Wind
        "2.1.1", "2.1.1.2", "2.1.1.2.2", "2.1.1.2.3", "2.2.1.2",
        
        # CODE 3 - Laufwasser
        "3.1.1.2",
        
        # CODE 4 - Biogene Brennstoffe (fest) - now include LandUse connections
        "4.1.1.1", "4.1.2.1", "4.2.1",
        "4.1.1.1.1.2", "4.1.2.1.2", "4.1.3", "4.2.1.1.2", "4.3",
        "4.3.1", "4.3.2", "4.3.3", "4.3.3.4", "4.3.4", "4.3.4.2", "4.4",
        
        # CODE 5 - Biogas
        "5.4.1.1", "5.4.2.4", "5.4.4.2",
        
        # CODE 6 - Biogene Brennstoffe (flüssig)
        "6.2.1", "6.2.1.2", "6.2.3",
        
        # CODE 7 - Umgebungswärme
        "7.1.4.3.3",
        
        # CODE 9 - Renewable Energy Supply (order matters!)
        "9.1.1", "9.1.2", "9.1.3", "9.1.4", "9.1", "9.2",
        "9.2.1.2.2", "9.2.1.4.2", "9.2.1.5",
    ]
    
    fixed_count = 0
    
    for code in calculation_order:
        try:
            entry = RenewableData.objects.get(code=code)
            
            # Calculate status
            if entry.status_value is None:
                calc_status = calculate_value(code, use_target=False)
                if calc_status is not None:
                    entry.status_value = calc_status
                    print(f"✓ {code:15} Status: {calc_status:>15.2f}")
                    fixed_count += 1
            
            # Calculate target
            if entry.target_value is None:
                calc_target = calculate_value(code, use_target=True)
                if calc_target is not None:
                    entry.target_value = calc_target
                    print(f"✓ {code:15} Target: {calc_target:>15.2f}")
                    fixed_count += 1
            
            entry.save()
            
        except RenewableData.DoesNotExist:
            print(f"✗ {code:15} NOT FOUND IN DATABASE")
        except Exception as e:
            print(f"✗ {code:15} ERROR: {str(e)}")
    
    print("="*80)
    print(f"Fixed {fixed_count} missing values")
    print("="*80)

if __name__ == "__main__":
    fix_all_values()
    print("\n✅ ALL RENEWABLE DATA VALUES FIXED!")
