import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.ws_models import WSData

# Get all rows from day 1 to 365
rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)

# Calculate sum
total_sum = sum(row.stromverbr for row in rows if row.stromverbr is not None)

print("=" * 80)
print("STROMVERBR. COLUMN SUM (Days 1-365)")
print("=" * 80)
print(f"\n📊 Total Sum: {total_sum:,.2f}")
print(f"📊 Total Sum (exact): {total_sum}")
print(f"\n✅ Summed {rows.count()} rows")
print("=" * 80)
