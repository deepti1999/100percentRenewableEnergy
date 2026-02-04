import pandas as pd

# Load the CSV file
df = pd.read_csv("Flaechen_Daten_Hierarchie.csv")

# Show first rows
print("First 5 rows:")
print(df.head())

# Show column names
print("\nColumns in CSV:")
print(df.columns.tolist())

# Show number of rows
print(f"\nTotal rows: {len(df)}")
