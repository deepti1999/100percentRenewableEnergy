#!/usr/bin/env python3

import os
import sys
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse

def main():
    print("🚀 Starting fresh import of clean CSV data...")
    
    # Clear all existing data
    count_before = LandUse.objects.count()
    LandUse.objects.all().delete()
    print(f"🗑️  Cleared {count_before} existing records")
    
    # Load the new CSV file
    csv_file = "Flaechen_Daten_Clean.csv"
    print(f"📁 Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"📊 Found {len(df)} rows in CSV")
    
    # First pass: Create all objects without parent relationships
    created_objects = {}
    print("\n🏗️  Creating land use records:")
    
    for index, row in df.iterrows():
        code = str(row["Code"])
        name = row["Name"]
        status_ha = float(row["Status_ha"]) if pd.notna(row["Status_ha"]) else None
        target_ha = float(row["Target_ha"]) if pd.notna(row["Target_ha"]) else None
        quelle = row["Quelle"]
        
        landuse = LandUse.objects.create(
            code=code,
            name=name,
            status_ha=status_ha,
            target_ha=target_ha,
            quelle=quelle
        )
        created_objects[code] = landuse
        print(f"  ✅ {code}: {name}")
    
    # Second pass: Set parent relationships
    print("\n🔗 Setting up parent-child relationships:")
    
    for index, row in df.iterrows():
        code = str(row["Code"])
        parent_code_raw = row["Parent_Code"]
        
        if pd.notna(parent_code_raw):
            # Handle both string and float parent codes
            if isinstance(parent_code_raw, float):
                parent_code = str(int(parent_code_raw))
            else:
                parent_code = str(parent_code_raw)
            
            if parent_code in created_objects:
                child = created_objects[code]
                parent = created_objects[parent_code]
                child.parent = parent
                child.save()
                print(f"  🔗 {code} ({child.name}) -> Parent: {parent_code} ({parent.name})")
    
    # Final summary
    total_count = LandUse.objects.count()
    print(f"\n🎉 Successfully imported {total_count} land use records!")
    
    # Show some sample data
    print("\n📋 Sample of imported data:")
    for landuse in LandUse.objects.filter(parent=None)[:5]:  # Top level items
        print(f"  • {landuse.code}: {landuse.name}")
        children = landuse.children.all()[:3]
        for child in children:
            print(f"    - {child.code}: {child.name}")
    
    print("\n✅ Database is ready! You can now access:")
    print("   🌐 Main site: http://127.0.0.1:8000/")
    print("   ⚙️  Admin: http://127.0.0.1:8000/admin/ (admin/admin123)")

if __name__ == "__main__":
    main()