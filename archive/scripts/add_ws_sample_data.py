import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

# Clear existing data
print("Clearing existing WS Data entries...")
WSData.objects.all().delete()

# Create 375 empty rows with proper date sequence
print("Creating 375 empty WS Data entries...")

start_date = datetime(2023, 1, 1)

for day in range(1, 376):
    current_date = start_date + timedelta(days=day-1)
    datum_ref = current_date.strftime('%d.%m.%y')
    
    entry = WSData.objects.create(
        tag_im_jahr=day,
        datum_ref=datum_ref,
        # All other fields are empty (null) - ready for you to fill
    )
    
    if day % 50 == 0:
        print(f"Created {day} entries...")

print(f"\n✅ Successfully created 375 empty entries!")
print(f"Total WS Data entries in database: {WSData.objects.count()}")
print("\n📋 All 52+ columns are ready with empty spaces for each of the 375 days")
print("🔄 Refresh your admin page to see the table!")
print("\nYou can now:")
print("  1. Click 'ADD WS DATA ENTRY' to add more rows")
print("  2. Click on any row to edit and fill in the data")
print("  3. Edit multiple rows at once in the list view")
