#!/usr/bin/env python

import os
import sys
import django
import csv

# Add the project root to sys.path
project_root = '/Users/deeptimaheedharan/Desktop/check'
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def parse_fixed_values(fixed_values_str):
    """Parse fixed values string like '17.8 / 14.2' or '99.1% / 100.0%'"""
    if not fixed_values_str or fixed_values_str.strip() == '':
        return None, None
    
    # Split by '/' and clean up
    parts = fixed_values_str.split('/')
    if len(parts) != 2:
        return None, None
    
    try:
        # Remove % signs and convert to float
        status = float(parts[0].strip().replace('%', ''))
        target = float(parts[1].strip().replace('%', ''))
        return status, target
    except ValueError:
        return None, None

def import_biogene_brennstoffe_fluessig():
    """Import biogene brennstoffe (flüssig) data from CSV"""
    
    csv_file = '/Users/deeptimaheedharan/Desktop/check/biogene_brennstoffe_fluessig_hierarchy.csv'
    
    print("🚀 Starting Biogene Brennstoffe (flüssig) import...")
    
    # First, let's delete existing entries with code starting with '6.'
    existing = RenewableData.objects.filter(code__startswith='6.')
    count_deleted = existing.count()
    existing.delete()
    print(f"🗑️  Deleted {count_deleted} existing biogene brennstoffe (flüssig) entries")
    
    imported_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            code = row['Code'].strip()
            parameter = row['Parameter'].strip()
            entry_type = row['Type'].strip()
            fixed_values = row['Fixed Values (Status/Target)'].strip()
            
            # Skip empty rows
            if not code or not parameter:
                continue
                
            print(f"Processing: {code} - {parameter}")
            
            # Parse fixed values
            status_value, target_value = parse_fixed_values(fixed_values)
            
            # Determine category and subcategory
            category = "Biogene Brennstoffe (flüssig)"
            
            # Set subcategory based on code structure
            if code.count('.') == 0:  # 6
                subcategory = "Main"
            elif code.count('.') == 1:  # 6.1, 6.2
                subcategory = "Biodiesel" if "6.1" in code else "Bioethanol"
            elif code.count('.') == 2:  # 6.1.1, 6.2.1
                if "6.1" in code:
                    subcategory = "Biodiesel Anbau"
                else:
                    subcategory = "Bioethanol Anbau"
            else:  # deeper levels
                if "6.1" in code:
                    subcategory = "Biodiesel Details"
                else:
                    subcategory = "Bioethanol Details"
            
            # Create the renewable data entry
            renewable_entry = RenewableData.objects.create(
                code=code,
                name=parameter,
                category=category,
                subcategory=subcategory,
                unit="TJ/a",  # Default unit, can be adjusted later
                status_value=status_value,
                target_value=target_value,
                formula=None  # Will be set later for calculated entries
            )
            
            print(f"✅ Created: {code} - {parameter} (subcategory: {subcategory})")
            imported_count += 1
    
    print(f"\n🎉 Import completed! Imported {imported_count} biogene brennstoffe (flüssig) entries")
    
    # Print summary
    total_entries = RenewableData.objects.filter(code__startswith='6.').count()
    print(f"📊 Total biogene brennstoffe (flüssig) entries in database: {total_entries}")

if __name__ == '__main__':
    import_biogene_brennstoffe_fluessig()