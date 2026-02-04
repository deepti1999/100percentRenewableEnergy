#!/usr/bin/env python
"""
Import Stromwandlung / Stromspeicherung data (Section 9)
Power Conversion / Power Storage
"""

import os
import django
import csv

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def import_stromwandlung_data():
    csv_file = 'stromwandlung_hierarchy.csv'
    
    # Clear existing Stromwandlung data
    RenewableData.objects.filter(category='Stromwandlung').delete()
    print("Cleared existing Stromwandlung data")
    
    created_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            code = row['Code'].strip()
            name = row['Parameter'].strip()
            unit = row['Unit'].strip()
            type_info = row['Type'].strip()
            
            # Skip empty rows
            if not code or not name:
                continue
            
            # Determine if it's a fixed value or calculated
            is_fixed = type_info.lower() == 'fixed'
            
            # Create the renewable data entry
            renewable_data = RenewableData.objects.create(
                category='Stromwandlung',
                subcategory='Stromspeicherung' if 'speicher' in name.lower() else 'Stromwandlung',
                code=code,
                name=name,
                unit=unit if unit else '',
                is_fixed=is_fixed,
                source='stromwandlung_hierarchy.csv'
            )
            
            created_count += 1
            print(f"Created: {code} - {name} ({unit}) - Fixed: {is_fixed}")
    
    print(f"\n✅ Successfully imported {created_count} Stromwandlung entries")
    
    # Display summary
    print(f"\n📊 Stromwandlung Data Summary:")
    stromwandlung_entries = RenewableData.objects.filter(category='Stromwandlung').order_by('code')
    
    for entry in stromwandlung_entries:
        type_indicator = "📊 FIXED" if entry.is_fixed else "🔧 VARIABLE"
        print(f"  {entry.code}: {entry.name} [{entry.unit}] - {type_indicator}")

if __name__ == "__main__":
    import_stromwandlung_data()