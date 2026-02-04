import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("CALCULATING direktverbr_strom FOR DAYS 1-365")
print("="*80)

# Get all days 1-365
daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr')

print(f"\n📊 Processing {daily_rows.count()} days...")
print(f"\nFormula: direktverbr_strom = IF(wind_solar_konstant <= stromverbr_raumwaerm_korr,")
print(f"                                   wind_solar_konstant,")
print(f"                                   stromverbr_raumwaerm_korr)")

updated_count = 0
total_sum = 0

print("\n" + "="*80)
print("CALCULATING VALUES")
print("="*80)

for row in daily_rows:
    if row.wind_solar_konstant is not None and row.stromverbr_raumwaerm_korr is not None:
        # direktverbr_strom = MIN(wind_solar_konstant, stromverbr_raumwaerm_korr)
        # If wind_solar_konstant <= stromverbr_raumwaerm_korr, use wind_solar_konstant
        # Otherwise, use stromverbr_raumwaerm_korr
        if row.wind_solar_konstant <= row.stromverbr_raumwaerm_korr:
            calculated_value = row.wind_solar_konstant
            condition = "wind_solar <= stromverbr"
        else:
            calculated_value = row.stromverbr_raumwaerm_korr
            condition = "wind_solar > stromverbr"
        
        row.direktverbr_strom = calculated_value
        row.save()
        
        total_sum += calculated_value
        updated_count += 1
        
        # Show first 3 and last 3 calculations
        if updated_count <= 3 or updated_count > daily_rows.count() - 3:
            print(f"Day {row.tag_im_jahr:3d}: wind_solar={row.wind_solar_konstant:,.2f}, stromverbr={row.stromverbr_raumwaerm_korr:,.2f}")
            print(f"         → {condition} → direktverbr_strom = {calculated_value:,.2f}")
        elif updated_count == 4:
            print("...")
    else:
        missing = []
        if row.wind_solar_konstant is None:
            missing.append("wind_solar_konstant")
        if row.stromverbr_raumwaerm_korr is None:
            missing.append("stromverbr_raumwaerm_korr")
        print(f"⚠️  Day {row.tag_im_jahr}: {', '.join(missing)} is None, skipping")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✅ Updated {updated_count} days")
print(f"   Total sum of direktverbr_strom: {total_sum:,.2f}")

# Also update row 366
try:
    row_366 = WSData.objects.get(tag_im_jahr=366)
    if row_366.wind_solar_konstant and row_366.stromverbr_raumwaerm_korr:
        if row_366.wind_solar_konstant <= row_366.stromverbr_raumwaerm_korr:
            direktverbr_366 = row_366.wind_solar_konstant
        else:
            direktverbr_366 = row_366.stromverbr_raumwaerm_korr
        
        row_366.direktverbr_strom = direktverbr_366
        row_366.save()
        print(f"\n✅ Updated Row 366:")
        print(f"   wind_solar_konstant: {row_366.wind_solar_konstant:,.2f}")
        print(f"   stromverbr_raumwaerm_korr: {row_366.stromverbr_raumwaerm_korr:,.2f}")
        print(f"   direktverbr_strom = {direktverbr_366:,.2f}")
except WSData.DoesNotExist:
    print(f"\n⚠️  Row 366 not found")

print("\n" + "="*80)
