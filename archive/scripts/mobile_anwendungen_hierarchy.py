#!/usr/bin/env python3
"""
Mobile Anwendungen (MA) Hierarchy Structure for VerbrauchData

Based on Excel data structure, creating complete 4.x code hierarchy:
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

# Complete Mobile Anwendungen hierarchy structure
MA_HIERARCHY = [
    # Main Mobile Anwendungen
    {
        'code': '4.0', 
        'category': 'Mobile Anwendungen (MA)', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # MA am Boden
    {
        'code': '4.1', 
        'category': 'MA am Boden (Straße, Schiene, Schifffahrt, Maschinen)', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # Base demand (static)
    {
        'code': '4.1.0', 
        'category': 'Bedarfsniveau (statisch)', 
        'unit': 'GWh/a', 
        'status': 639.193, 
        'ziel': 639.193, 
        'is_calculated': False
    },
    
    # ===== PERSONENVERKEHR (PVk) SECTION =====
    
    # PVk percentage
    {
        'code': '4.1.1', 
        'category': 'davon Personenverkehr (PVk)', 
        'unit': '%', 
        'status': 67.4, 
        'ziel': 67.4, 
        'is_calculated': False
    },
    
    # PVk influence factor
    {
        'code': '4.1.1.1', 
        'category': 'Zieleinfluss Pers.-Verkehrsleist./Pers.', 
        'unit': '%', 
        'status': 100, 
        'ziel': 100.0, 
        'is_calculated': False
    },
    
    # PVk demand level (after development)
    {
        'code': '4.1.1.2', 
        'category': 'Bedarfsniveau PVk (nach Entwicklung)', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # PVk traction efficiency
    {
        'code': '4.1.1.3', 
        'category': 'Nutzungsgrad Traktionsmix', 
        'unit': '%', 
        'status': 27.1, 
        'ziel': 62.7, 
        'is_calculated': False
    },
    
    # PVk total useful energy
    {
        'code': '4.1.1.4', 
        'category': 'Nutzenergie (NE) gesamt PVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # === PVk Elektrotraktion ===
    {
        'code': '4.1.1.5', 
        'category': 'Anteil Elektrotraktion an PvK-Leistung', 
        'unit': '%', 
        'status': 8.6, 
        'ziel': 86.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.1.6', 
        'category': 'Anteil Elektrotraktion an Endverbr. PVk', 
        'unit': '%', 
        'status': 3.0, 
        'ziel': 69.1, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.1.7', 
        'category': 'Nutzungsgrad Elektrotraktion (NG e)', 
        'unit': '%', 
        'status': 78.0, 
        'ziel': 78.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.1.8', 
        'category': 'Anteil NE Elektrotrakt.an Endverbr. PVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.1.9', 
        'category': 'Anteil NE Elektrotrakt.an NE ges.PVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.1.10', 
        'category': 'Stromverbrauch PVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # === PVk Verbrennungsmotor ===
    {
        'code': '4.1.1.11', 
        'category': 'Anteil Verbrenn.Trakt.an Endverbr.PVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.1.12', 
        'category': 'Nutzungsgrad Verbrenn.Traktion (NG k)', 
        'unit': '%', 
        'status': 25.5, 
        'ziel': 28.4, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.1.13', 
        'category': 'Anteil NE Verbrenn.Trakt.an Endverbr.PVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.1.14', 
        'category': 'Anteil NE Verbrenn.Trakt.an NE ges.PVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.1.15', 
        'category': 'Kohlenwasserstoff-Verbr.(gasf.) PVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # === PVk FC-Traktion ===
    {
        'code': '4.1.1.16', 
        'category': 'Anteil FC-Trakt.an Endverbr.PVk', 
        'unit': '%', 
        'status': 0.0, 
        'ziel': 0.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.1.17', 
        'category': 'Nutzungsgrad FC-Traktion (NG FC)', 
        'unit': '%', 
        'status': 35.0, 
        'ziel': 35.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.1.18', 
        'category': 'Anteil NE FC-Trakt.an Endverbr.PVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.1.19', 
        'category': 'Anteil NE FC-Trakt.an NE ges.PVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.1.20', 
        'category': 'Wasserstoffverbrauch PVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # ===== GÜTERVERKEHR (GVk) SECTION =====
    
    # GVk percentage
    {
        'code': '4.1.2', 
        'category': 'davon Güterverkehr u. a. (GVk)', 
        'unit': '%', 
        'status': 32.6, 
        'ziel': 32.6, 
        'is_calculated': False
    },
    
    # GVk influence factor
    {
        'code': '4.1.2.1', 
        'category': 'Zieleinfluss Güterverk.-Leistung/Pers.', 
        'unit': '%', 
        'status': 100, 
        'ziel': 100.0, 
        'is_calculated': False
    },
    
    # GVk demand level (after development)
    {
        'code': '4.1.2.2', 
        'category': 'Bedarfsniveau GVk (nach Entwicklung)', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # GVk traction efficiency
    {
        'code': '4.1.2.3', 
        'category': 'Nutzungsgrad Traktionsmix', 
        'unit': '%', 
        'status': 30.7, 
        'ziel': 62.1, 
        'is_calculated': False
    },
    
    # GVk total useful energy
    {
        'code': '4.1.2.4', 
        'category': 'Nutzenergie (NE) gesamt GVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # === GVk Elektrotraktion ===
    {
        'code': '4.1.2.5', 
        'category': 'Anteil Elektrotraktion an GVk-Leistung', 
        'unit': '%', 
        'status': 18.6, 
        'ziel': 84.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.2.6', 
        'category': 'Anteil Elektrotraktion an Endverbr. GVk', 
        'unit': '%', 
        'status': 7.3, 
        'ziel': 66.9, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.2.7', 
        'category': 'Nutzungsgrad Elektrotraktion (NG e)', 
        'unit': '%', 
        'status': 78.0, 
        'ziel': 78.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.2.8', 
        'category': 'Anteil NE Elektrotrakt.an Endverbr. GVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.2.9', 
        'category': 'Anteil NE Elektrotrakt.an NE ges.GVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.2.10', 
        'category': 'Stromverbrauch GVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # === GVk Verbrennungsmotor ===
    {
        'code': '4.1.2.11', 
        'category': 'Anteil Verbrenn.-Trakt.an Endverbr.GVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.2.12', 
        'category': 'Nutzungsgrad Verbrenn.-Traktion (NG k)', 
        'unit': '%', 
        'status': 27.0, 
        'ziel': 30.1, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.2.13', 
        'category': 'Anteil NE Verbrenn-Trakt.an Endverbr.GVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.2.14', 
        'category': 'Anteil NE Verbrenn.Trakt.an NE ges.GVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.2.15', 
        'category': 'Kohlenwasserstoff-Verbr.(gasf.) GVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    # === GVk FC-Traktion ===
    {
        'code': '4.1.2.16', 
        'category': 'Anteil FC-Trakt.an Endverbr.GVk', 
        'unit': '%', 
        'status': 0.0, 
        'ziel': 0.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.2.17', 
        'category': 'Nutzungsgrad FC-Traktion (NG FC)', 
        'unit': '%', 
        'status': 35.0, 
        'ziel': 35.0, 
        'is_calculated': False
    },
    
    {
        'code': '4.1.2.18', 
        'category': 'Anteil NE FC-Trakt.an Endverbr.GVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.2.19', 
        'category': 'Anteil NE FC-Trakt.an NE ges.GVk', 
        'unit': '%', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    },
    
    {
        'code': '4.1.2.20', 
        'category': 'Wasserstoffverbrauch GVk', 
        'unit': 'GWh/a', 
        'status': None, 
        'ziel': None, 
        'is_calculated': True
    }
]

def create_ma_entries():
    """Create all Mobile Anwendungen entries"""
    created_count = 0
    
    for entry_data in MA_HIERARCHY:
        entry, created = VerbrauchData.objects.get_or_create(
            code=entry_data['code'],
            defaults=entry_data
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {entry_data['code']} - {entry_data['category']}")
        else:
            print(f"- Exists: {entry_data['code']} - {entry_data['category']}")
    
    print(f"\n✓ Created {created_count} new MA entries")
    return created_count

if __name__ == "__main__":
    print("=== CREATING MOBILE ANWENDUNGEN HIERARCHY ===")
    create_ma_entries()