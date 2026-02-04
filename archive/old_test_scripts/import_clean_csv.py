import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse

def clean_numeric_value(value):
    """Convert value to float, handling empty strings and None"""
    if pd.isna(value) or str(value).strip() == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def run():
    # Clear existing data
    LandUse.objects.all().delete()
    
    # Load the clean CSV
    df = pd.read_csv("Flaechen_Daten_Clean.csv")
    
    print(f"Loading {len(df)} rows from clean CSV...")
    
    # First pass: Create all objects without parent relationships
    created_objects = {}
    for _, row in df.iterrows():
        code = str(row["Code"])
        landuse = LandUse.objects.create(
            code=code,
            name=row["Name"],
            status_ha=clean_numeric_value(row["Status_ha"]),
            target_ha=clean_numeric_value(row["Target_ha"]),
            quelle=row["Quelle"]
        )
        created_objects[code] = landuse
        print(f"  Created: {code} - {landuse.name}")
    
    # Second pass: Set up parent relationships using Parent_Code column
    print("\nSetting up parent relationships:")
    for _, row in df.iterrows():
        code = str(row["Code"])
        parent_code_raw = row["Parent_Code"]
        
        # Handle parent code - could be int or string, might be NaN
        if pd.notna(parent_code_raw):
            parent_code = str(int(parent_code_raw)) if isinstance(parent_code_raw, float) else str(parent_code_raw)
            
            if parent_code in created_objects:
                child = created_objects[code]
                parent = created_objects[parent_code]
                child.parent = parent
                child.save()
                print(f"  {code} -> parent: {parent_code}")
            else:
                print(f"  Warning: Parent {parent_code} not found for {code}")
        else:
            print(f"  {code} -> root level (no parent)")
    
    print(f"\n✅ Successfully imported {LandUse.objects.count()} records!")
    
    # Show hierarchy with calculated percentages
    print("\n📊 Sample calculations:")
    for code in ['1', '1.1', '2', '2.1']:
        try:
            landuse = LandUse.objects.get(code=code)
            status_pct = f"{landuse.status_percent}%" if landuse.status_percent else "-"
            target_pct = f"{landuse.target_percent}%" if landuse.target_percent else "-"
            change = f"{landuse.change_ratio}" if landuse.change_ratio else "-"
            print(f"  {landuse.code} - Status: {status_pct}, Target: {target_pct}, Change: {change}")
        except LandUse.DoesNotExist:
            pass

if __name__ == "__main__":
    run()
