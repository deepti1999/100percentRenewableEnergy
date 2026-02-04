#!/usr/bin/env python3

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def delete_existing_prozesswaerme():
    """Delete all existing Prozesswärme entries"""
    deleted = VerbrauchData.objects.filter(code__startswith='3.').delete()
    print(f"Deleted {deleted[0]} existing Prozesswärme entries")

def create_properly_numbered_prozesswaerme():
    """Create Prozesswärme structure with PROPER SEQUENTIAL NUMBERING"""
    
    # Following exact Gebäudewärme numbering pattern
    prozesswaerme_data = [
        # Level 1: Main category (like 2.0)
        {'code': '3.0', 'category': 'Bedarfsniveau (statisch)', 'unit': 'GWh/a', 'status': 555.395, 'ziel': 555.395, 'is_calculated': False},
        
        # Level 2: Main divisions (like 2.1, 2.2)
        {'code': '3.1', 'category': 'davon Haushalte', 'unit': '%', 'status': 8.7, 'ziel': 8.7, 'is_calculated': False},
        {'code': '3.1.0', 'category': '=', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        {'code': '3.1.1', 'category': 'Zieleinfluss Endanwendungs-Effizienz', 'unit': '%', 'status': 100.0, 'ziel': 95.0, 'is_calculated': False},
        {'code': '3.1.2', 'category': '=', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        {'code': '3.2', 'category': 'dav.Industrie + Gewerbeant.GHD', 'unit': '%', 'status': 91.3, 'ziel': 91.3, 'is_calculated': False},
        {'code': '3.2.0', 'category': '=', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        {'code': '3.2.1', 'category': 'Zieleinfluss Materialdurchsatz/Pers.', 'unit': '%', 'status': 100.0, 'ziel': 100.0, 'is_calculated': False},
        {'code': '3.2.2', 'category': 'Zieleinfluss Prozess-Effizienz', 'unit': '%', 'status': 100.0, 'ziel': 89.0, 'is_calculated': False},
        {'code': '3.2.3', 'category': '=', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Level 3: Combined level (like 2.3)
        {'code': '3.3', 'category': 'Bedarfsniveau (Prod.-Vol., Proz.-Effiz.)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Level 4: Energy type breakdown (like 2.4, 2.5, 2.6, 2.7, 2.8, 2.9)
        {'code': '3.4', 'category': 'davon Brennstoffe', 'unit': '%', 'status': 60.3, 'ziel': 26.7, 'is_calculated': False},
        {'code': '3.4.0', 'category': '= Endenergieverbrauch', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        {'code': '3.4.1', 'category': '> Nutzungsgrad Endanwendung', 'unit': '%', 'status': 86.0, 'ziel': 88.0, 'is_calculated': False},
        {'code': '3.4.2', 'category': '> Wandlungsverluste Endanwendung', 'unit': '%', 'status': None, 'ziel': None, 'is_calculated': True},
        {'code': '3.4.3', 'category': '= Einsparung gegenüber Status (relativ)', 'unit': '%', 'status': None, 'ziel': None, 'is_calculated': True},
        {'code': '3.4.4', 'category': '= Einsparung gegenüber Status (absolut)', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        {'code': '3.5', 'category': 'davon Wärme (>100°C,verlustarm nutzbar)', 'unit': '%', 'status': 25.9, 'ziel': 0.0, 'is_calculated': False},
        {'code': '3.5.0', 'category': '= Endenergieverbrauch', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        {'code': '3.6', 'category': 'davon Strom (verlustarm nutzbar)', 'unit': '%', 'status': 13.8, 'ziel': 71.9, 'is_calculated': False},
        {'code': '3.6.0', 'category': '= Endenergieverbrauch', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
        
        # Final level (like 2.10)
        {'code': '3.7', 'category': 'Endenergieverbrauch PW gesamt', 'unit': 'GWh/a', 'status': None, 'ziel': None, 'is_calculated': True},
    ]
    
    # Create all entries
    for data in prozesswaerme_data:
        entry = VerbrauchData.objects.create(**data)
        print(f"Created: {entry.code} - {entry.category}")
    
    print(f"\nCreated {len(prozesswaerme_data)} properly numbered Prozesswärme entries")

if __name__ == "__main__":
    print("FIXING PROZESSWÄRME NUMBERING TO FOLLOW PROPER HIERARCHY")
    print("=" * 70)
    
    # Step 1: Delete existing incorrect structure
    delete_existing_prozesswaerme()
    
    # Step 2: Create properly numbered structure
    create_properly_numbered_prozesswaerme()
    
    print("\nPROZESSWÄRME NUMBERING FIXED!")