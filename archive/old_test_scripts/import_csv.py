import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse

def clean_numeric_value(value):
    """Convert value to float, handling '-' and other non-numeric strings"""
    if pd.isna(value) or str(value).strip() in ['-', '']:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def find_parent_code(code):
    """Find parent code based on hierarchical structure"""
    if '.' not in code:
        return None  # Root level
    
    # For codes like "2.2.1", parent would be "2.2"
    # For codes like "1.1", parent would be "1"
    parts = code.split('.')
    if len(parts) > 1:
        return '.'.join(parts[:-1])
    return None

def run():
    # Clear existing data
    LandUse.objects.all().delete()
    
    # Load CSV
    df = pd.read_csv("Flaechen_Daten_Hierarchie.csv")
    
    print(f"Loading {len(df)} rows from CSV...")
    
    # Create all objects with exact CSV values
    created_objects = {}
    for _, row in df.iterrows():
        code = str(row["Code"])
        landuse = LandUse.objects.create(
            code=code,
            name=row["Flächenart / Energetische Nutzung"],
            status_ha=clean_numeric_value(row["Status (ha)"]),
            status_percent=clean_numeric_value(row["Status (% v.HS)"]),
            target_ha=clean_numeric_value(row["Ziel (ha)"]),
            target_percent=clean_numeric_value(row["Ziel (% v.HS)"]),
            change_ratio=clean_numeric_value(row["Änderung Ziel/Status"]),
            quelle=row["Quelle"]
        )
        created_objects[code] = landuse
    
    print(f"Successfully imported {LandUse.objects.count()} records with exact CSV data!")
    
    # Show some sample data
    print("\nSample records from CSV:")
    for landuse in LandUse.objects.all()[:5]:
        status_pct = f"{landuse.status_percent}%" if landuse.status_percent else "-"
        target_pct = f"{landuse.target_percent}%" if landuse.target_percent else "-"
        print(f"  {landuse.code} - Status: {status_pct}, Target: {target_pct}")
    
    print(f"Successfully imported {LandUse.objects.count()} records!")
    
    # Show some sample data
    print("\nSample records:")
    for landuse in LandUse.objects.all()[:5]:
        print(f"  {landuse.code} - {landuse.name}")

if __name__ == "__main__":
    run()
