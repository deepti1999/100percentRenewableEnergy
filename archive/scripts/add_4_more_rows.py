import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

# Get the last entry to continue from there
last_entry = WSData.objects.order_by('-tag_im_jahr').first()

if last_entry:
    last_day = last_entry.tag_im_jahr
    last_date = datetime.strptime(last_entry.datum_ref, '%d.%m.%y')
else:
    last_day = 0
    last_date = datetime(2023, 1, 1)

print(f"Current total rows: {WSData.objects.count()}")
print(f"Last entry: Day {last_day}, Date: {last_date.strftime('%d.%m.%y')}")

# Add 4 more rows
print("\nAdding 4 more rows...")

for i in range(1, 5):
    day_number = last_day + i
    new_date = last_date + timedelta(days=i)
    datum_ref = new_date.strftime('%d.%m.%y')
    
    WSData.objects.create(
        tag_im_jahr=day_number,
        datum_ref=datum_ref
        # All other fields are NULL/empty
    )
    print(f"Created: Day {day_number}, Date: {datum_ref}")

print(f"\n✅ Total rows now: {WSData.objects.count()}")
print(f"Expected: 369 rows (365 + 4)")
print(f"\n🔄 Refresh admin: http://127.0.0.1:8000/admin/simulator/wsdata/")
