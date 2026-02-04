#!/usr/bin/env python3
"""
Import script for 8. Tiefengeothermie (Deep Geothermal Energy) data
This script imports deep geothermal energy data from tiefengeothermie_hierarchy.csv
"""

import os
import sys
import django
import pandas as pd
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/Users/deeptimaheedharan/Desktop/check')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def clean_numeric_value(value_str):
    """Clean and convert numeric values from German format"""
    if pd.isna(value_str) or value_str == '' or value_str is None:
        return None
    
    # Convert to string and handle German decimal notation
    value_str = str(value_str).strip()
    if value_str == '':
        return None
        
    # Replace German decimal comma with dot and remove thousands separators
    value_str = value_str.replace('.', '').replace(',', '.')
    
    try:
        return float(value_str)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert '{value_str}' to number")
        return None

def extract_code_from_hierarchy(hierarchy):
    """Extract the code (e.g., '8.1.1') from the hierarchy string"""
    if pd.isna(hierarchy) or hierarchy == '':
        return None
    
    # Split by space and take the first part which should be the code
    parts = str(hierarchy).split(' ')
    if len(parts) > 0:
        code_part = parts[0]
        # Check if it starts with a number (indicating it's a code)
        if code_part and (code_part[0].isdigit() or code_part.startswith('8')):
            return code_part
    return None

def extract_name_from_hierarchy(hierarchy):
    """Extract the name part from the hierarchy string"""
    if pd.isna(hierarchy) or hierarchy == '':
        return None
    
    # Split by space and take everything after the first part (the code)
    parts = str(hierarchy).split(' ', 1)
    if len(parts) > 1:
        return parts[1].strip()
    return str(hierarchy).strip()

def get_formulas_mapping():
    """Define calculation formulas for computed values"""
    return {
        '8.1.2': '8.1 * 8.1.1 / 1000',  # Bruttostromerzeugung = Netzanschlussleistung * Vollbetriebsstunden / 1000
    }

def import_tiefengeothermie_data():
    """Import deep geothermal energy data from CSV"""
    
    print("🚀 Starting import of 8. Tiefengeothermie data...")
    
    # Read the CSV file
    csv_file = '/Users/deeptimaheedharan/Desktop/check/tiefengeothermie_hierarchy.csv'
    
    try:
        df = pd.read_csv(csv_file)
        print(f"📊 Successfully loaded CSV with {len(df)} rows")
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        return False
    
    # Get formulas mapping
    formulas_mapping = get_formulas_mapping()
    
    # Track statistics
    created_count = 0
    updated_count = 0
    
    # Process each row
    for index, row in df.iterrows():
        hierarchy = row['Hierarchy']
        unit = row['Unit'] if 'Unit' in row and pd.notna(row['Unit']) else None
        fixed_value = row['Fixed Value'] if 'Fixed Value' in row and pd.notna(row['Fixed Value']) else None
        
        # Extract code and name
        code = extract_code_from_hierarchy(hierarchy)
        name = extract_name_from_hierarchy(hierarchy)
        
        if not code:
            print(f"⚠️  Skipping row {index}: No valid code found in '{hierarchy}'")
            continue
            
        if not name:
            print(f"⚠️  Skipping row {index}: No name found in '{hierarchy}'")
            continue
        
        # Clean numeric values
        status_value = clean_numeric_value(fixed_value) if fixed_value else None
        
        # Get formula if available
        formula = formulas_mapping.get(code)
        
        # Create or update the database entry
        try:
            renewable, created = RenewableData.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': 'Tiefengeothermie',
                    'subcategory': 'Geothermie',
                    'unit': unit or '',
                    'status_value': status_value,
                    'target_value': None,  # No target values in this CSV
                    'formula': formula,
                }
            )
            
            if created:
                created_count += 1
                print(f"✅ Created: {code} - {name}")
            else:
                # Update existing entry
                renewable.name = name
                renewable.category = 'Tiefengeothermie'
                renewable.subcategory = 'Geothermie'
                renewable.unit = unit or ''
                renewable.status_value = status_value
                renewable.target_value = None
                renewable.formula = formula
                renewable.save()
                updated_count += 1
                print(f"🔄 Updated: {code} - {name}")
                
        except Exception as e:
            print(f"❌ Error processing {code}: {e}")
            continue
    
    print(f"\n📈 Import Summary:")
    print(f"   ✅ Created: {created_count} entries")  
    print(f"   🔄 Updated: {updated_count} entries")
    print(f"   📊 Total processed: {created_count + updated_count} entries")
    
    # Display some imported data for verification
    print(f"\n🔍 Sample imported data:")
    sample_entries = RenewableData.objects.filter(category='Tiefengeothermie').order_by('code')
    for entry in sample_entries:
        status_display = entry.status_value if entry.status_value is not None else "None"
        formula_display = f" (Formula: {entry.formula})" if entry.formula else ""
        print(f"   {entry.code}: {entry.name} = {status_display} {entry.unit}{formula_display}")
    
    return True

if __name__ == '__main__':
    success = import_tiefengeothermie_data()
    if success:
        print("\n🎉 Import completed successfully!")
    else:
        print("\n💥 Import failed!")
        sys.exit(1)