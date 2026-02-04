#!/usr/bin/env python3

import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def import_new_solar_data():
    """Import the new solar_energy.csv file and replace existing renewable data"""
    
    # Clear existing renewable data
    print("🗑️  Clearing existing renewable energy data...")
    deleted_count = RenewableData.objects.count()
    RenewableData.objects.all().delete()
    print(f"   Deleted {deleted_count} existing records")
    
    # Read the new CSV
    print("📁 Reading solar_energy.csv...")
    df = pd.read_csv('solar_energy.csv')
    
    print(f"   Found {len(df)} records in new solar data")
    
    # Process and create new records
    created_records = []
    
    for index, row in df.iterrows():
        code = str(row['Code']).strip()
        name = str(row['Name']).strip()
        unit = str(row['Unit']).strip() if pd.notna(row['Unit']) and row['Unit'] != '-' else ''
        fixed_value = row['Fixed Value'] if pd.notna(row['Fixed Value']) else None
        formula = str(row['Formula']).strip() if pd.notna(row['Formula']) else None
        
        # Determine category and subcategory based on hierarchy level
        code_parts = code.split('.')
        level = len(code_parts)
        
        if level == 1:
            category = name  # "Solarenergie"
            subcategory = None
        elif level == 2:
            category = "Solar"
            subcategory = name  # "Solare Dachflächen", etc.
        elif level == 3:
            category = "Solar" 
            subcategory = name  # "Solarthermie", "Solarstrom", etc.
        else:
            category = "Solar"
            subcategory = "Parameters"  # For deeper levels
        
        # Create the record - using fixed_value as status_value
        record = RenewableData.objects.create(
            code=code,
            name=name,
            category=category,
            subcategory=subcategory,
            unit=unit,
            status_value=fixed_value,  # Using Fixed Value as current status
            target_value=None,        # New CSV doesn't have targets
            formula=formula,
            source="solar_energy.csv (new)"
        )
        
        created_records.append(record)
        
        value_info = f" (Value: {fixed_value})" if fixed_value else ""
        formula_info = f" [Formula: {formula}]" if formula else ""
        print(f"   ✅ Created: {code} - {name}{value_info}{formula_info}")
    
    print(f"\n=== IMPORT SUMMARY ===")
    print(f"✅ Successfully imported {len(created_records)} new records")
    print(f"📊 Previous records: {deleted_count}")
    print(f"📊 New records: {len(created_records)}")
    
    # Show breakdown by category/subcategory
    categories = {}
    formulas_count = 0
    values_count = 0
    
    for record in created_records:
        key = f"{record.category}"
        if record.subcategory:
            key += f" - {record.subcategory}"
        categories[key] = categories.get(key, 0) + 1
        
        if record.formula:
            formulas_count += 1
        if record.status_value:
            values_count += 1
    
    print(f"\n=== DATA BREAKDOWN ===")
    for category, count in categories.items():
        print(f"   📂 {category}: {count} records")
    
    print(f"\n=== DATA FEATURES ===")
    print(f"   🧮 Records with formulas: {formulas_count}")
    print(f"   📊 Records with values: {values_count}")
    print(f"   🏗️  Hierarchy levels: {max([len(r.code.split('.')) for r in created_records])}")
    
    return len(created_records)

if __name__ == '__main__':
    try:
        count = import_new_solar_data()
        print(f"\n🎉 SUCCESS! Imported {count} new renewable energy records!")
        print("\n📍 Next steps:")
        print("   1. Visit http://127.0.0.1:8000/admin/simulator/renewabledata/ to see admin")
        print("   2. Visit http://127.0.0.1:8000/renewable/ to see web interface")
        print("   3. All changes are immediately reflected in both!")
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        raise