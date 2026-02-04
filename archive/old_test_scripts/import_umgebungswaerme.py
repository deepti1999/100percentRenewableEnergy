#!/usr/bin/env python3
"""
Import script for 7. Umgebungswärme (Wärmepumpe) data
This script imports environmental heat/heat pump data from umgebungswaerme_hierarchy.csv
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

def extract_code_from_parameter(parameter):
    """Extract the code (e.g., '7.1.1') from the parameter string"""
    if pd.isna(parameter) or parameter == '':
        return None
    
    # Split by space and take the first part which should be the code
    parts = str(parameter).split(' ')
    if len(parts) > 0:
        code_part = parts[0]
        # Check if it starts with a number (indicating it's a code)
        if code_part and (code_part[0].isdigit() or code_part.startswith('7')):
            return code_part
    return None

def extract_name_from_parameter(parameter):
    """Extract the name part from the parameter string"""
    if pd.isna(parameter) or parameter == '':
        return None
    
    # Split by space and take everything after the first part (the code)
    parts = str(parameter).split(' ', 1)
    if len(parts) > 1:
        return parts[1].strip()
    return str(parameter).strip()

def get_units_mapping():
    """Define units for each code based on the CSV data"""
    return {
        '7': None,  # Main category has no unit
        '7.1': 'GWh/a',
        '7.1.1': '%',
        '7.1.2': 'GWh/a', 
        '7.1.2.1': '',  # Dimensionless (Jahresarbeitszahl)
        '7.1.2.2': 'GWh/a',
        '7.1.2.3': 'GWh/a',
        '7.1.3': '%',
        '7.1.4': 'GWh/a',
        '7.1.4.1': '',  # Dimensionless (Jahresarbeitszahl) 
        '7.1.4.2': 'GWh/a',
        '7.1.4.3': 'GWh/a',
        '7.1.4.3.1': 'MWh/ha/a',
        '7.1.4.3.2': 'ha',
        '7.1.4.3.3': 'ha',
        '7.1.4.3.4': '%',
    }

def get_formulas_mapping():
    """Define calculation formulas for computed values"""
    return {
        '7.1.2': '7.1 * 7.1.1 / 100',  # WP-Luft Antriebsstromaufnahme = Gesamt * Anteil Luft
        '7.1.2.2': '7.1.2 * 7.1.2.1',  # Nutzwärme = Antriebsstrom * Jahresarbeitszahl
        '7.1.2.3': '7.1.2.2 - 7.1.2',  # Wärmegewinn = Nutzwärme - Antriebsstrom
        '7.1.4': '7.1 * 7.1.3 / 100',  # WP-Erdreich/Wasser Antriebsstrom = Gesamt * Anteil Erdreich
        '7.1.4.2': '7.1.4 * 7.1.4.1',  # Nutzwärme = Antriebsstrom * Jahresarbeitszahl
        '7.1.4.3': '7.1.4.2 - 7.1.4',  # Wärmegewinn = Nutzwärme - Antriebsstrom  
        '7.1.4.3.2': '7.1.4.3 / 7.1.4.3.1 * 1000',  # Entzugsfläche = Wärmgewinn / Wärmeertrag * 1000 (GWh→MWh conversion)
    }

def import_umgebungswaerme_data():
    """Import environmental heat/heat pump data from CSV"""
    
    print("🚀 Starting import of 7. Umgebungswärme (Wärmepumpe) data...")
    
    # Read the CSV file
    csv_file = '/Users/deeptimaheedharan/Desktop/check/umgebungswaerme_hierarchy.csv'
    
    try:
        df = pd.read_csv(csv_file)
        print(f"📊 Successfully loaded CSV with {len(df)} rows")
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        return False
    
    # Get mappings
    units_mapping = get_units_mapping()
    formulas_mapping = get_formulas_mapping()
    
    # Track statistics
    created_count = 0
    updated_count = 0
    
    # Process each row
    for index, row in df.iterrows():
        parameter = row['Parameter']
        unit = row['Unit'] if 'Unit' in row and pd.notna(row['Unit']) else None
        status = row['Status'] if 'Status' in row and pd.notna(row['Status']) else None 
        ziel = row['Ziel'] if 'Ziel' in row and pd.notna(row['Ziel']) else None
        
        # Extract code and name
        code = extract_code_from_parameter(parameter)
        name = extract_name_from_parameter(parameter)
        
        if not code:
            print(f"⚠️  Skipping row {index}: No valid code found in '{parameter}'")
            continue
            
        if not name:
            print(f"⚠️  Skipping row {index}: No name found in '{parameter}'")
            continue
        
        # Clean numeric values
        status_value = clean_numeric_value(status) if status else None
        target_value = clean_numeric_value(ziel) if ziel else None
        
        # Get unit from mapping or CSV
        final_unit = unit if unit else units_mapping.get(code)
        
        # Get formula if available
        formula = formulas_mapping.get(code)
        
        # Create or update the database entry
        try:
            renewable, created = RenewableData.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': 'Umgebungswärme',
                    'subcategory': 'Wärmepumpe',
                    'unit': final_unit,
                    'status_value': status_value,
                    'target_value': target_value,
                    'formula': formula,
                }
            )
            
            if created:
                created_count += 1
                print(f"✅ Created: {code} - {name}")
            else:
                # Update existing entry
                renewable.name = name
                renewable.category = 'Umgebungswärme'
                renewable.subcategory = 'Wärmepumpe'
                renewable.unit = final_unit
                renewable.status_value = status_value
                renewable.target_value = target_value
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
    sample_entries = RenewableData.objects.filter(category='Umgebungswärme').order_by('code')[:5]
    for entry in sample_entries:
        print(f"   {entry.code}: {entry.name} = {entry.status_value} {entry.unit}")
    
    return True

if __name__ == '__main__':
    success = import_umgebungswaerme_data()
    if success:
        print("\n🎉 Import completed successfully!")
    else:
        print("\n💥 Import failed!")
        sys.exit(1)