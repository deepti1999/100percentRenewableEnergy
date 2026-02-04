"""
Export WSData promille values to CSV files for PyPSA.

Run this from Django shell or as a management command:
    python manage.py shell < pypsa_solver/export_data.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from simulator.ws_models import WSData
from pathlib import Path
import csv

def export_promille_data():
    """Export wind, solar, and verbrauch promille from WSData to CSV files."""
    
    # Get all WSData entries ordered by day
    ws_data = WSData.objects.filter(tag_im_jahr__lte=365).order_by('tag_im_jahr')
    
    # Output directory
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Extract data
    wind_values = []
    solar_values = []
    verbrauch_values = []
    
    for entry in ws_data:
        wind_values.append(entry.wind_promille or 0)
        solar_values.append(entry.solar_promille or 0)
        verbrauch_values.append(entry.verbrauch_promille or 0)
    
    # Write solar_promile.csv
    with open(data_dir / "solar_promile.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["solar_promile"])
        for val in solar_values:
            writer.writerow([val])
    
    # Write wind_promile.csv
    with open(data_dir / "wind_promile.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["wind_promile"])
        for val in wind_values:
            writer.writerow([val])
    
    # Write verbrauch_promile.csv
    with open(data_dir / "verbrauch_promile.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["verbrauch_promile"])
        for val in verbrauch_values:
            writer.writerow([val])
    
    print(f"✓ Exported {len(wind_values)} rows to CSV files:")
    print(f"  - solar_promile.csv")
    print(f"  - wind_promile.csv") 
    print(f"  - verbrauch_promile.csv")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Wind total: {sum(wind_values):.1f} promille")
    print(f"  Solar total: {sum(solar_values):.1f} promille")
    print(f"  Verbrauch total: {sum(verbrauch_values):.1f} promille")


if __name__ == "__main__":
    export_promille_data()
