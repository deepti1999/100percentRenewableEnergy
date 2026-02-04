import pandas as pd

# Load existing CSV
df = pd.read_csv("solar_energy.csv")

print("Original CSV structure:")
print(df.head())
print(f"Columns: {list(df.columns)}")

# Add new columns if not exist
if "Target" not in df.columns:
    df["Target"] = None
if "Fixed?" not in df.columns:
    df["Fixed?"] = "YES"   # default
if "Formula" not in df.columns:
    df["Formula"] = None
if "Parent" not in df.columns:
    df["Parent"] = None

# Set specific values based on your requirements
mapping = {
    "1": {"Target": None, "Fixed?": None, "Formula": None, "Parent": None},
    "1.1": {"Target": 199398, "Fixed?": "NO", "Formula": "comes from LandUse", "Parent": "1"},
    "1.1.1": {"Target": None, "Fixed?": None, "Formula": None, "Parent": None},
    "1.1.1.1": {"Target": "1.1", "Fixed?": "YES", "Formula": None, "Parent": "1.1.1"},
    "1.1.1.1.1": {"Target": 5250, "Fixed?": "YES", "Formula": None, "Parent": "1.1.1.1"},
    "1.1.1.1.2": {"Target": 11515, "Fixed?": "NO", "Formula": "(ha * AnteilThermie * ErtragThermie)/1000", "Parent": "1.1.1.1"},
    "1.1.2": {"Target": None, "Fixed?": None, "Formula": None, "Parent": None},
    "1.1.2.1": {"Target": 98.9, "Fixed?": "NO", "Formula": "100 - AnteilThermie", "Parent": "1.1.2"},
    "1.1.2.1.1": {"Target": 1853, "Fixed?": "YES", "Formula": None, "Parent": "1.1.2.1"},
    "1.1.2.1.2": {"Target": 365421, "Fixed?": "NO", "Formula": "(ha * AnteilStrom * ErtragStrom)/1000", "Parent": "1.1.2.1"},
    "1.1.2.1.2.1": {"Target": 927, "Fixed?": "YES", "Formula": None, "Parent": "1.1.2.1.2"},
    "1.1.2.1.2.2": {"Target": 394410, "Fixed?": "NO", "Formula": "Bruttostromerzeugung/Vollbetriebsstunden", "Parent": "1.1.2.1.2"},
    "1.2": {"Target": 676910, "Fixed?": "NO", "Formula": "comes from LandUse", "Parent": "1"},
    "1.2.1": {"Target": None, "Fixed?": None, "Formula": None, "Parent": None},
    "1.2.1.1": {"Target": 1235, "Fixed?": "YES", "Formula": None, "Parent": "1.2.1"},
    "1.2.1.2": {"Target": 836209, "Fixed?": "NO", "Formula": "(ha * Ertrag)/1000", "Parent": "1.2.1"},
    "1.2.1.2.1": {"Target": 927, "Fixed?": "YES", "Formula": None, "Parent": "1.2.1.2"},
    "1.2.1.2.2": {"Target": 902546, "Fixed?": "NO", "Formula": "Bruttostromerzeugung/Vollbetriebsstunden", "Parent": "1.2.1.2"}
}

# Apply the mapping
for index, row in df.iterrows():
    code = str(row['Code'])
    if code in mapping:
        for column, value in mapping[code].items():
            df.at[index, column] = value

# Reorder columns to match the desired structure
column_order = ['Code', 'Name', 'Unit', 'Fixed Value', 'Target', 'Fixed?', 'Formula', 'Parent']
df = df[column_order]

print("\nUpdated CSV structure:")
print(df.head(10))
print(f"Columns: {list(df.columns)}")

# Save the updated CSV
df.to_csv("solar_energy_updated.csv", index=False)
print("\nSaved as solar_energy_updated.csv")

# Also replace the original file
df.to_csv("solar_energy.csv", index=False)
print("Updated original solar_energy.csv")