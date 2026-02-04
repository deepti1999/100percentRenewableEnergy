#!/usr/bin/env python3

import os
import sys
import django
import pandas as pd

# Add the project directory to Python path
sys.path.append('/Users/deeptimaheedharan/Desktop/check')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse

def main():
    print("🚀 Starting clean CSV import...")
    
    # Clear existing data
    count_before = LandUse.objects.count()
    LandUse.objects.all().delete()
    print(f"🗑️  Cleared {count_before} existing records")
    
    # Load CSV
    csv_path = "/Users/deeptimaheedharan/Desktop/check/Flaechen_Daten_Clean.csv"
    df = pd.read_csv(csv_path)
    print(f"📁 Loading {len(df)} rows from clean CSV...")
    
    # First pass: Create all objects
    created_objects = {}
    for _, row in df.iterrows():
        code = str(row["Code"])
        landuse = LandUse.objects.create(
            code=code,
            name=row["Name"],
            status_ha=float(row["Status_ha"]) if pd.notna(row["Status_ha"]) else None,
            target_ha=float(row["Target_ha"]) if pd.notna(row["Target_ha"]) else None,
            quelle=row["Quelle"]
        )
        created_objects[code] = landuse
        print(f"  ✅ Created: {code} - {landuse.name}")
    
    # Second pass: Set parent relationships
    print("\n🔗 Setting up parent relationships:")
    for _, row in df.iterrows():
        code = str(row["Code"])
        parent_code_raw = row["Parent_Code"]
        
        if pd.notna(parent_code_raw):
            parent_code = str(int(parent_code_raw)) if isinstance(parent_code_raw, float) else str(parent_code_raw)
            if parent_code in created_objects:
                child = created_objects[code]
                parent = created_objects[parent_code]
                child.parent = parent
                child.save()
                print(f"  🔗 {code} -> parent: {parent_code}")
    
    print(f"\n🎉 Successfully imported {LandUse.objects.count()} records!")
    
    # Test some calculations
    print("\n📊 Testing calculations:")
    test_codes = ['1', '1.1', '2', '2.1']
    for code in test_codes:
        try:
            lu = LandUse.objects.get(code=code)
            status_pct = f'{lu.status_percent}%' if lu.status_percent else '-'
            target_pct = f'{lu.target_percent}%' if lu.target_percent else '-'
            change = f'{lu.change_ratio}' if lu.change_ratio else '-'
            print(f"  {lu.code:4} - {lu.name:30} | Status: {status_pct:6} | Target: {target_pct:6} | Change: {change}")
        except LandUse.DoesNotExist:
            print(f"  {code} - Not found")
    
    print("\n✅ Database is ready for web admin!")

if __name__ == "__main__":
    main()
