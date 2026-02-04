import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

# Read the CSV file
csv_file = '/Users/deeptimaheedharan/Downloads/ws_data_2023.csv'
df = pd.read_csv(csv_file)

print(f"Reading CSV file: {csv_file}")
print(f"Found {len(df)} rows in CSV")
print(f"\nColumns: {df.columns.tolist()}")

# Clear existing data
print("\nClearing existing WS Data entries...")
WSData.objects.all().delete()

# Import data
print("\nImporting data into database...")
success_count = 0
error_count = 0

for index, row in df.iterrows():
    try:
        # Parse date
        datum_ref = pd.to_datetime(row['Datum Ref.']).strftime('%d.%m.%y')
        
        # Create entry
        WSData.objects.create(
            tag_im_jahr=index + 1,
            datum_ref=datum_ref,
            wind_promille=float(row['Wind\nPromille']),
            solar_promille=float(row['Solar \nPromille']),
            heizung_abwaerm_promille=float(row['Heizung Abweich.\nPromille']),
            verbrauch_promille=float(row['Verbrauch Promille'])
        )
        success_count += 1
        
        if (index + 1) % 50 == 0:
            print(f"Imported {index + 1} rows...")
            
    except Exception as e:
        print(f"Error on row {index + 1}: {e}")
        error_count += 1

print(f"\n{'='*80}")
print(f"✅ Import Complete!")
print(f"{'='*80}")
print(f"Successfully imported: {success_count} rows")
print(f"Errors: {error_count}")
print(f"Total entries in database: {WSData.objects.count()}")
print(f"\n📊 First 4 columns filled:")
print(f"  - Column C: Wind Promille")
print(f"  - Column D: Solar Promille")
print(f"  - Column E: Heizung Abwärm. Promille")
print(f"  - Column F: Verbrauch Promille")
print(f"\n🔄 Refresh admin page: http://127.0.0.1:8000/admin/simulator/wsdata/")
