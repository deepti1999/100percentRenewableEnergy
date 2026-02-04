import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("CALCULATING wind_solar_konstant FOR DAYS 1-365")
print("="*80)

# Get all days 1-365
daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr')

print(f"\n📊 Processing {daily_rows.count()} days...")
print(f"\nFormula: wind_solar_konstant = windstrom + solarstrom + sonst_kraft_konstant")

updated_count = 0
total_sum = 0

print("\n" + "="*80)
print("CALCULATING VALUES")
print("="*80)

for row in daily_rows:
    if row.windstrom is not None and row.solarstrom is not None and row.sonst_kraft_konstant is not None:
        # wind_solar_konstant = windstrom + solarstrom + sonst_kraft_konstant
        calculated_value = row.windstrom + row.solarstrom + row.sonst_kraft_konstant
        
        row.wind_solar_konstant = calculated_value
        row.save()
        
        total_sum += calculated_value
        updated_count += 1
        
        # Show first 3 and last 3 calculations
        if updated_count <= 3 or updated_count > daily_rows.count() - 3:
            print(f"Day {row.tag_im_jahr:3d}: {row.windstrom:,.2f} + {row.solarstrom:,.2f} + {row.sonst_kraft_konstant:,.2f} = {calculated_value:,.2f}")
        elif updated_count == 4:
            print("...")
    else:
        missing = []
        if row.windstrom is None:
            missing.append("windstrom")
        if row.solarstrom is None:
            missing.append("solarstrom")
        if row.sonst_kraft_konstant is None:
            missing.append("sonst_kraft_konstant")
        print(f"⚠️  Day {row.tag_im_jahr}: {', '.join(missing)} is None, skipping")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✅ Updated {updated_count} days")
print(f"   Total sum of wind_solar_konstant: {total_sum:,.2f}")

# Also update row 366
try:
    row_366 = WSData.objects.get(tag_im_jahr=366)
    if row_366.windstrom and row_366.solarstrom and row_366.sonst_kraft_konstant:
        wind_solar_konstant_366 = row_366.windstrom + row_366.solarstrom + row_366.sonst_kraft_konstant
        row_366.wind_solar_konstant = wind_solar_konstant_366
        row_366.save()
        print(f"\n✅ Updated Row 366:")
        print(f"   wind_solar_konstant = {wind_solar_konstant_366:,.2f}")
        print(f"\n   Match with daily sum: {'✅ YES' if abs(total_sum - wind_solar_konstant_366) < 1 else '❌ NO'}")
except WSData.DoesNotExist:
    print(f"\n⚠️  Row 366 not found")

print("\n" + "="*80)
