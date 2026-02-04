#!/usr/bin/env python3

import os
import sys
import django
import pandas as pd

# Add the project directory to Python path
sys.path.append('/Users/deeptimaheedharan/Desktop/check')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def import_renewable_data():
    """Import solar energy data from CSV into RenewableData model"""
    
    # Path to the CSV file
    csv_path = "/Users/deeptimaheedharan/Desktop/check/solarenergie.csv"
    
    print(f"📁 Reading CSV file: {csv_path}")
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Successfully loaded {len(df)} rows")
        print("📊 Columns:", list(df.columns))
        
        # Clear existing renewable data
        RenewableData.objects.all().delete()
        print("🗑️ Cleared existing renewable data")
        
        created_count = 0
        
        for index, row in df.iterrows():
            try:
                # Determine category and subcategory
                name = str(row['Name']).strip()
                code = str(row['Code']).strip() if pd.notna(row['Code']) else None
                parent_code = str(row['Parent']).strip() if pd.notna(row['Parent']) else None
                
                # Skip empty rows
                if not name or name.lower() in ['nan', '']:
                    continue
                
                # Determine category based on hierarchy
                if parent_code == "0" or parent_code == "5":
                    category = "Solar"
                    subcategory = None
                elif "Dachflächen" in name:
                    category = "Solar"
                    subcategory = "Dachflächen"
                elif "Freiflächen" in name:
                    category = "Solar" 
                    subcategory = "Freiflächen"
                elif "Solarthermie" in name or "Thermie" in name:
                    category = "Solar"
                    subcategory = "Solarthermie"
                elif "Solarstrom" in name or "Strom" in name:
                    category = "Solar"
                    subcategory = "Solarstrom"
                else:
                    category = "Solar"
                    subcategory = "Other"
                
                # Extract values
                unit = str(row['Unit']).strip() if pd.notna(row['Unit']) else ""
                status_value = float(row['Status_Value']) if pd.notna(row['Status_Value']) else None
                target_value = float(row['Target_Value']) if pd.notna(row['Target_Value']) else None
                source = str(row['Source']).strip() if pd.notna(row['Source']) else ""
                is_calculated = str(row['Is_Calculated']).strip().lower() == 'true' if pd.notna(row['Is_Calculated']) else False
                
                # Extract formula if it's a calculated field
                formula = None
                if is_calculated and 'Formula:' in source:
                    formula = source.replace('Formula:', '').strip()
                elif is_calculated and 'Formula:' in name:
                    formula = name.split('Formula:')[1].strip() if 'Formula:' in name else None
                
                # Clean source (remove Formula: part)
                if 'Formula:' in source:
                    source = source.split('Formula:')[0].strip()
                
                # Create RenewableData entry
                renewable_data = RenewableData.objects.create(
                    category=category,
                    subcategory=subcategory,
                    code=code,
                    name=name,
                    unit=unit,
                    status_value=status_value,
                    target_value=target_value,
                    formula=formula,
                    source=source,
                    notes=f"Calculated: {is_calculated}, Parent: {parent_code}"
                )
                
                created_count += 1
                print(f"✅ Created: {category} - {subcategory} - {name}")
                
            except Exception as e:
                print(f"❌ Error processing row {index}: {e}")
                print(f"   Row data: {row.to_dict()}")
        
        print(f"\n🎉 Import completed!")
        print(f"📊 Total records created: {created_count}")
        
        # Show summary by category
        print("\n📈 Summary by category:")
        for category in RenewableData.objects.values_list('category', flat=True).distinct():
            count = RenewableData.objects.filter(category=category).count()
            print(f"   {category}: {count} records")
        
        # Show summary by subcategory
        print("\n📋 Summary by subcategory:")
        for subcat in RenewableData.objects.exclude(subcategory__isnull=True).values_list('subcategory', flat=True).distinct():
            count = RenewableData.objects.filter(subcategory=subcat).count()
            print(f"   {subcat}: {count} records")
            
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting renewable energy data import...")
    success = import_renewable_data()
    
    if success:
        print("✅ Import successful!")
    else:
        print("❌ Import failed!")