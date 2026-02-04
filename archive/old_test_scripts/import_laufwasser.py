#!/usr/bin/env python3

import os
import sys
import django
import csv
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/Users/deeptimaheedharan/Desktop/check')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def parse_german_number(value_str):
    """Convert German number format (comma as decimal separator) to float"""
    if not value_str or value_str.strip() == '':
        return None
    
    # Replace comma with dot for decimal separator
    cleaned = value_str.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        print(f"Warning: Could not parse number '{value_str}'")
        return None

def extract_code_from_hierarchy(hierarchy_text):
    """Extract the code (e.g., '3.1.1') from hierarchy text"""
    if not hierarchy_text:
        return None
    
    # Split by space and take the first part
    parts = hierarchy_text.split()
    if parts:
        return parts[0]
    return None

def extract_description_from_hierarchy(hierarchy_text):
    """Extract the description part from hierarchy text"""
    if not hierarchy_text:
        return ""
    
    # Split by space and take everything after the first part
    parts = hierarchy_text.split(' ', 1)
    if len(parts) > 1:
        return parts[1]
    return parts[0] if parts else ""

def determine_subcategory(code):
    """Determine subcategory based on code structure"""
    if not code:
        return "Laufwasser"
    
    if code.startswith("3."):
        return "Laufwasser"
    
    return "Laufwasser"

def import_laufwasser_data():
    """Import Laufwasser (Water) data from CSV file"""
    
    csv_file = '/Users/deeptimaheedharan/Desktop/check/laufwasser_full_hierarchy.csv'
    
    print("Starting Laufwasser data import...")
    print("=" * 50)
    
    # Clear existing water data (codes starting with 3.)
    existing_count = RenewableData.objects.filter(code__startswith='3.').count()
    if existing_count > 0:
        print(f"Removing {existing_count} existing Laufwasser entries...")
        RenewableData.objects.filter(code__startswith='3.').delete()
    
    imported_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, 1):
            hierarchy = row['Hierarchy'].strip()
            unit = row['Unit'].strip()
            status_str = row['Status'].strip()
            target_str = row['Ziel'].strip()  # German for "Target"
            notes = row['Notes'].strip()
            
            # Skip empty rows or header rows
            if not hierarchy:
                continue
            
            # Extract code and description
            code = extract_code_from_hierarchy(hierarchy)
            description = extract_description_from_hierarchy(hierarchy)
            
            if not code:
                print(f"Skipping row {row_num}: No valid code found in '{hierarchy}'")
                continue
            
            # Parse numeric values
            status_value = parse_german_number(status_str)
            target_value = parse_german_number(target_str)
            
            # Determine if this entry should be calculated or fixed
            is_fixed = status_value is not None or target_value is not None
            formula = None
            
            # For calculated entries (those without values), we'll add formulas later
            if not is_fixed:
                formula = None  # Will be added when implementing calculations
            
            # Determine subcategory
            subcategory = determine_subcategory(code)
            
            # Create the database entry
            renewable_entry = RenewableData.objects.create(
                category='Solar',  # Keep same category as Solar/Wind for unified display
                subcategory=subcategory,
                code=code,
                name=description,  # Set name field for template display
                description=description,  # Also set description field
                unit=unit,
                status_value=status_value,
                target_value=target_value,
                is_fixed=is_fixed,
                formula=formula,
                notes=notes
            )
            
            print(f"✅ Imported {code}: {description}")
            print(f"   Unit: {unit}")
            print(f"   Status: {status_value}, Target: {target_value}")
            print(f"   Fixed: {is_fixed}, Formula: {formula}")
            print()
            
            imported_count += 1
    
    print("=" * 50)
    print(f"✅ Import completed! Imported {imported_count} Laufwasser entries")
    
    # Show summary
    total_renewable = RenewableData.objects.count()
    solar_count = RenewableData.objects.filter(code__startswith='1.').count()
    wind_count = RenewableData.objects.filter(code__startswith='2.').count()
    water_count = RenewableData.objects.filter(code__startswith='3.').count()
    
    print(f"\nDatabase summary:")
    print(f"Total renewable entries: {total_renewable}")
    print(f"Solar (1.x): {solar_count}")
    print(f"Wind (2.x): {wind_count}")
    print(f"Water (3.x): {water_count}")

if __name__ == '__main__':
    import_laufwasser_data()