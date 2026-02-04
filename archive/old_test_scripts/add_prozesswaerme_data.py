#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def add_prozesswaerme_data():
    print("=== ADDING PROZESSWÄRME (PW) DATA TO DATABASE ===\n")
    
    # Prozesswärme data structure based on Excel rows 93-120
    pw_data = [
        # Row 93 - Main category
        {'code': '3.0', 'category': 'Prozesswärme (PW)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 94 - Bedarfsniveau (statisch)
        {'code': '3.1', 'category': 'Bedarfsniveau (statisch)', 'unit': 'GWh/a', 'status': 555.395, 'ziel': 555.395, 'is_calculated': False},
        
        # Row 95 - davon Haushalte
        {'code': '3.1.1', 'category': '* davon Haushalte', 'unit': '%', 'status': 8.7, 'ziel': 8.7, 'is_calculated': False},
        
        # Row 96 - Haushalte calculated value
        {'code': '3.1.1.0', 'category': '= Haushalte Endenergieverbrauch', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 97 - Zieleinfluss Endanwendungs-Effizienz Haushalte
        {'code': '3.1.1.1', 'category': '* Zieleinfluss Endanwendungs-Effizienz', 'unit': '%', 'status': 100, 'ziel': 95.0, 'is_calculated': False},
        
        # Row 98 - Haushalte final calculated value
        {'code': '3.1.1.2', 'category': '= Haushalte Endenergieverbrauch (nach Effizienz)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 100 - davon Industrie + Gewerbeant.GHD
        {'code': '3.1.2', 'category': '* davon Industrie + Gewerbeant.GHD', 'unit': '%', 'status': 91.3, 'ziel': 91.3, 'is_calculated': False},
        
        # Row 101 - Industrie/GHD calculated value
        {'code': '3.1.2.0', 'category': '= Industrie/GHD Endenergieverbrauch', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 102 - Zieleinfluss Materialdurchsatz/Pers.
        {'code': '3.1.2.1', 'category': '* Zieleinfluss Materialdurchsatz/Pers.', 'unit': '%', 'status': 100, 'ziel': 100.0, 'is_calculated': False},
        
        # Row 103 - Materialdurchsatz calculated value
        {'code': '3.1.2.2', 'category': '= Industrie/GHD (nach Materialdurchsatz)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 104 - Zieleinfluss Prozess-Effizienz
        {'code': '3.1.2.3', 'category': '* Zieleinfluss Prozess-Effizienz', 'unit': '%', 'status': 100, 'ziel': 89.0, 'is_calculated': False},
        
        # Row 105 - Final Industrie/GHD calculated value
        {'code': '3.1.2.4', 'category': '= Industrie/GHD (nach Prozess-Effizienz)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 107 - Bedarfsniveau (Prod.-Vol., Proz.-Effiz.)
        {'code': '3.2', 'category': 'Bedarfsniveau (Prod.-Vol., Proz.-Effiz.)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 108 - davon Brennstoffe
        {'code': '3.2.1', 'category': '* davon Brennstoffe', 'unit': '% v. [107]', 'status': 60.3, 'ziel': 26.7, 'is_calculated': False},
        
        # Row 109 - Brennstoffe Endenergieverbrauch
        {'code': '3.2.1.0', 'category': '= Endenergieverbrauch Brennstoffe', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 110 - Nutzungsgrad Endanwendung
        {'code': '3.2.1.1', 'category': '> Nutzungsgrad Endanwendung', 'unit': '%', 'status': 86.0, 'ziel': 88.0, 'is_calculated': False},
        
        # Row 111 - Wandlungsverluste Endanwendung
        {'code': '3.2.1.2', 'category': '> Wandlungsverluste Endanwendung', 'unit': '% v. [107]', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 112 - Einsparung gegenüber Status (relativ)
        {'code': '3.2.1.3', 'category': '= Einsparung gegenüber Status (relativ)', 'unit': '% v. [107]', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 113 - Einsparung gegenüber Status (absolut)
        {'code': '3.2.1.4', 'category': '= Einsparung gegenüber Status (absolut)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 115 - davon Wärme (>100°C,verlustarm nutzbar)
        {'code': '3.2.2', 'category': '* davon Wärme (>100°C,verlustarm nutzbar)', 'unit': '% v. [107]', 'status': 25.9, 'ziel': 0.0, 'is_calculated': False},
        
        # Row 116 - Wärme Endenergieverbrauch
        {'code': '3.2.2.0', 'category': '= Endenergieverbrauch Wärme', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 117 - davon Strom (verlustarm nutzbar)
        {'code': '3.2.3', 'category': '* davon Strom (verlustarm nutzbar)', 'unit': '% v. [107]', 'status': 13.8, 'ziel': 71.9, 'is_calculated': False},
        
        # Row 118 - Strom Endenergieverbrauch
        {'code': '3.2.3.0', 'category': '= Endenergieverbrauch Strom', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Row 120 - Endenergieverbrauch PW gesamt
        {'code': '3.3', 'category': 'Endenergieverbrauch PW gesamt', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
    ]
    
    print("Adding Prozesswärme entries to database:")
    
    for entry in pw_data:
        # Check if entry already exists
        existing = VerbrauchData.objects.filter(code=entry['code']).first()
        
        if existing:
            print(f"  {entry['code']}: Already exists - updating")
            # Update existing entry
            existing.category = entry['category']
            existing.unit = entry['unit']
            existing.status = entry['status']
            existing.ziel = entry['ziel']
            existing.is_calculated = entry['is_calculated']
            existing.save()
        else:
            print(f"  {entry['code']}: Creating new entry")
            # Create new entry
            VerbrauchData.objects.create(
                code=entry['code'],
                category=entry['category'],
                unit=entry['unit'],
                status=entry['status'],
                ziel=entry['ziel'],
                is_calculated=entry['is_calculated']
            )
    
    print(f"\n✅ Successfully added {len(pw_data)} Prozesswärme entries to database")
    
    # Verify the data
    print(f"\n=== VERIFICATION ===")
    pw_entries = VerbrauchData.objects.filter(code__startswith='3.').order_by('code')
    print(f"Total Prozesswärme entries in database: {pw_entries.count()}")
    
    for entry in pw_entries:
        calc_status = "CALCULATED" if entry.is_calculated else "FIXED"
        print(f"  {entry.code}: {entry.category[:50]}... [{calc_status}]")

if __name__ == "__main__":
    add_prozesswaerme_data()