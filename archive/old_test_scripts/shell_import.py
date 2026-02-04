import pandas as pd
from simulator.models import LandUse

# Clear existing data
LandUse.objects.all().delete()
print("Cleared existing data")

# Load CSV
df = pd.read_csv("Flaechen_Daten_Clean.csv")
print(f"Loading {len(df)} rows")

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
    print(f"Created: {code} - {landuse.name}")

# Second pass: Set parent relationships
print("Setting parent relationships:")
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
            print(f"{code} -> parent: {parent_code}")

print(f"Successfully imported {LandUse.objects.count()} records!")
