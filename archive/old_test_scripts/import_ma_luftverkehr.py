#!/usr/bin/env python3
"""
Import MA Luftverkehr (Air Transport) data into the database
4.2.x series for Mobile Applications Air Transport
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def create_ma_luftverkehr_data():
    """Create MA Luftverkehr entries in the database"""
    
    # MA Luftverkehr data based on Excel structure
    luftverkehr_data = [
        {
            'code': '4.2.1',
            'category': 'MA Luftverkehr',
            'name': 'Bedarfsniveau (statisch)',
            'unit': 'GWh/a',
            'wert': 114.520,
            'ziel': 114.520,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Base air transport demand (static)'
        },
        {
            'code': '4.2.2', 
            'category': 'MA Luftverkehr',
            'name': 'Zieleinfluss Luftverk.-Leistung/Person',
            'unit': '%',
            'wert': 100.0,
            'ziel': 100.0,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Air transport person efficiency influence'
        },
        {
            'code': '4.2.3',
            'category': 'MA Luftverkehr', 
            'name': 'Bedarfsniv. Luftverk. (nach Entwicklung)',
            'unit': 'GWh/a',
            'wert': 114.520,
            'ziel': 114.520,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Air transport demand after development'
        },
        {
            'code': '4.2.4',
            'category': 'MA Luftverkehr',
            'name': 'Zieleinfluss Luftverkehrs-Effizienz', 
            'unit': '%',
            'wert': 100.0,
            'ziel': 87.0,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Air transport efficiency influence'
        },
        {
            'code': '4.2.5',
            'category': 'MA Luftverkehr',
            'name': 'Kraftstoffverbrauch (flüssig) Luftverkehr',
            'unit': 'GWh/a', 
            'wert': 114.520,
            'ziel': 99.632,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Liquid fuel consumption for air transport'
        },
        {
            'code': '4.2.6',
            'category': 'MA Luftverkehr',
            'name': 'Endenergieverbrauch MA gesamt',
            'unit': 'GWh/a',
            'wert': 753.713,
            'ziel': 388.749,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Total end energy consumption MA'
        },
        {
            'code': '4.2.7',
            'category': 'MA Luftverkehr',
            'name': 'davon Kraftstoffe',
            'unit': 'GWh/a',
            'wert': 725.561,
            'ziel': 191.199,
            'is_calculated': False, 
            'ziel_calculated': False,
            'description': 'Total fuel consumption'
        },
        {
            'code': '4.2.8',
            'category': 'MA Luftverkehr',
            'name': 'davon Wasserstoff (FC-Traktion)',
            'unit': 'GWh/a',
            'wert': 0.0,
            'ziel': 0.0,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Hydrogen fuel consumption (FC-Traction)'
        },
        {
            'code': '4.2.9',
            'category': 'MA Luftverkehr',
            'name': 'davon Kohlenwassserst.(gasförmig)',
            'unit': 'GWh/a',
            'wert': 611.042,
            'ziel': 91.567,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Gaseous hydrocarbon consumption'
        },
        {
            'code': '4.2.10',
            'category': 'MA Luftverkehr', 
            'name': 'dav.Kohlenwasserst. (flüssig, für Luftverk.)',
            'unit': 'GWh/a',
            'wert': 114.520,
            'ziel': 99.632,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Liquid hydrocarbons for air transport'
        },
        {
            'code': '4.2.11',
            'category': 'MA Luftverkehr',
            'name': 'davon Strom',
            'unit': 'GWh/a',
            'wert': 28.151,
            'ziel': 197.549,
            'is_calculated': False,
            'ziel_calculated': False,
            'description': 'Electricity consumption'
        }
    ]
    
    print("=== Importing MA Luftverkehr Data ===")
    created_count = 0
    updated_count = 0
    
    for item_data in luftverkehr_data:
        code = item_data['code']
        
        # Check if item already exists
        existing_item = VerbrauchData.objects.filter(code=code).first()
        
        if existing_item:
            # Update existing item
            for key, value in item_data.items():
                if key != 'code':  # Don't update the code itself
                    setattr(existing_item, key, value)
            existing_item.save()
            print(f"✅ Updated {code}: {item_data['name']}")
            updated_count += 1
        else:
            # Create new item
            new_item = VerbrauchData.objects.create(**item_data)
            print(f"✅ Created {code}: {item_data['name']}")
            created_count += 1
    
    print(f"\n=== Import Summary ===")
    print(f"Created: {created_count} items")
    print(f"Updated: {updated_count} items") 
    print(f"Total: {created_count + updated_count} MA Luftverkehr items")
    
    # Verify the import
    print(f"\n=== Verification ===")
    all_items = VerbrauchData.objects.filter(code__startswith='4.2.').order_by('code')
    for item in all_items:
        print(f"{item.code}: {item.name} | Status: {item.wert} | Ziel: {item.ziel} {item.unit}")

if __name__ == "__main__":
    create_ma_luftverkehr_data()