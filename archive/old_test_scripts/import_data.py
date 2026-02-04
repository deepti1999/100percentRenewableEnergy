#!/usr/bin/env python3
import os
import sys
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse

def import_csv():
    print("🚀 Starting CSV import...")
    
    # Clear existing data
    count_before = LandUse.objects.count()
    LandUse.objects.all().delete()
    print(f"🗑️  Cleared {count_before} existing records")
    
    # Load the new CSV file
    csv_file = "Flaechen_Daten_Clean.csv"
    df = pd.read_csv(csv_file)
    print(f"📊 Loading {len(df)} rows from {csv_file}")
    
    # First pass: Create all objects
    created_objects = {}
    for index, row in df.iterrows():
        code = str(row["Code"])
        
        landuse = LandUse.objects.create(
            code=code,
            name=row["Name"],
            status_ha=float(row["Status_ha"]) if pd.notna(row["Status_ha"]) else None,
            target_ha=float(row["Target_ha"]) if pd.notna(row["Target_ha"]) else None,
            quelle=row["Quelle"]
        )
        created_objects[code] = landuse
        print(f"  ✅ {code}: {landuse.name}")
    
    # Second pass: Set parent relationships
    print("\n🔗 Setting parent relationships:")
    for index, row in df.iterrows():
        code = str(row["Code"])
        parent_code_raw = row["Parent_Code"]
        
        if pd.notna(parent_code_raw):
            parent_code = str(int(parent_code_raw)) if isinstance(parent_code_raw, float) else str(parent_code_raw)
            if parent_code in created_objects:
                child = created_objects[code]
                parent = created_objects[parent_code]
                child.parent = parent
                child.save()
                print(f"    🔗 {code} -> parent: {parent_code}")
    
    print(f"\n🎉 Successfully imported {LandUse.objects.count()} records!")
    
    # Show some sample data
    print("\n📋 Sample imported data:")
    for landuse in LandUse.objects.all()[:5]:
        print(f"  {landuse.code}: {landuse.name} ({landuse.status_ha} ha)")

if __name__ == "__main__":
    import_csv()