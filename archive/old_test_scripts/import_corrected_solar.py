#!/usr/bin/env python3

import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def import_corrected_solar_data():
    """Import the corrected solar energy data with proper hierarchy"""
    
    # Clear existing renewable data
    print("Clearing existing renewable energy data...")
    RenewableData.objects.all().delete()
    
    # Read the corrected CSV
    print("Reading solarenergie_corrected.csv...")
    df = pd.read_csv('solarenergie_corrected.csv')
    
    print(f"Found {len(df)} records in corrected solar data")
    
    # Store records by code for parent lookup
    records_by_code = {}
    created_records = []
    
    # First pass: Create all records without parent relationships
    for index, row in df.iterrows():
        code = str(row['Code']).strip()
        parameter = str(row['Parameter']).strip()
        unit = row['Unit'] if pd.notna(row['Unit']) else ''
        status_value = row['Status Value'] if pd.notna(row['Status Value']) else None
        target_value = row['Target Value'] if pd.notna(row['Target Value']) else None
        formula = row['Formula'] if pd.notna(row['Formula']) else None
        
        # Determine category and subcategory based on hierarchy level
        code_parts = code.split('.')
        level = len(code_parts)
        
        if level == 1:
            category = parameter  # "Solarenergie"
            subcategory = None
        elif level == 2:
            category = "Solar"
            subcategory = parameter  # "Solare Dachflächen", etc.
        elif level == 3:
            category = "Solar" 
            subcategory = parameter  # "Solarthermie", "Solarstrom", etc.
        else:
            category = "Solar"
            subcategory = "Details"  # For deeper levels
        
        # Create the record
        record = RenewableData.objects.create(
            code=code,
            name=parameter,
            category=category,
            subcategory=subcategory,
            unit=unit,
            status_value=status_value,
            target_value=target_value,
            formula=formula,
            source="solarenergie_corrected.csv"
        )
        
        records_by_code[code] = record
        created_records.append(record)
        
        print(f"Created: {code} - {parameter}")
    
    # Second pass: Establish parent relationships (if needed for future use)
    print("\nEstablishing relationships (for reference)...")
    relationship_count = 0
    
    for index, row in df.iterrows():
        code = str(row['Code']).strip()
        parent_code = str(row['Parent']).strip() if pd.notna(row['Parent']) else None
        
        if parent_code and parent_code in records_by_code:
            # Note: RenewableData doesn't have parent field, but we track it for info
            print(f"  {code} -> parent: {parent_code}")
            relationship_count += 1
    
    print(f"\n=== IMPORT SUMMARY ===")
    print(f"Total records created: {len(created_records)}")
    print(f"Hierarchical relationships noted: {relationship_count}")
    
    # Show breakdown by category/subcategory
    categories = {}
    for record in created_records:
        key = f"{record.category}"
        if record.subcategory:
            key += f" - {record.subcategory}"
        categories[key] = categories.get(key, 0) + 1
    
    print("\n=== BREAKDOWN BY CATEGORY ===")
    for category, count in categories.items():
        print(f"  {category}: {count} records")
    
    # Show records with formulas
    formula_records = [r for r in created_records if r.formula]
    print(f"\n=== CALCULATED FIELDS ===")
    print(f"Records with formulas: {len(formula_records)}")
    for record in formula_records:
        print(f"  {record.code}: {record.name} = {record.formula}")
    
    return len(created_records)

if __name__ == '__main__':
    try:
        count = import_corrected_solar_data()
        print(f"\n✅ Successfully imported {count} corrected solar energy records!")
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        raise