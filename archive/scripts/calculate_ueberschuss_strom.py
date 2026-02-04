import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("CALCULATING ueberschuss_strom FOR DAYS 1-365")
print("="*80)

# Get all days 1-365
daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr')

print(f"\n📊 Processing {daily_rows.count()} days...")
print(f"\nFormula: ueberschuss_strom = IF(direktverbr_strom == stromverbr_raumwaerm_korr,")
print(f"                                   wind_solar_konstant - stromverbr_raumwaerm_korr,")
print(f"                                   0)")

updated_count = 0
total_sum = 0

print("\n" + "="*80)
print("CALCULATING VALUES")
print("="*80)

for row in daily_rows:
    if (row.direktverbr_strom is not None and 
        row.stromverbr_raumwaerm_korr is not None and 
        row.wind_solar_konstant is not None):
        
        # ueberschuss_strom = IF(direktverbr == stromverbr, wind_solar_konstant - stromverbr, 0)
        # This means: if direktverbr equals stromverbr, calculate surplus; otherwise 0
        if abs(row.direktverbr_strom - row.stromverbr_raumwaerm_korr) < 0.01:  # Equal (with small tolerance)
            calculated_value = row.wind_solar_konstant - row.stromverbr_raumwaerm_korr
            condition = "direktverbr == stromverbr (has surplus)"
        else:
            calculated_value = 0
            condition = "direktverbr != stromverbr (no surplus)"
        
        row.ueberschuss_strom = calculated_value
        row.save()
        
        total_sum += calculated_value
        updated_count += 1
        
        # Show first 5 and last 5 calculations
        if updated_count <= 5 or updated_count > daily_rows.count() - 5:
            print(f"Day {row.tag_im_jahr:3d}: direktverbr={row.direktverbr_strom:,.2f}, stromverbr={row.stromverbr_raumwaerm_korr:,.2f}")
            print(f"         wind_solar={row.wind_solar_konstant:,.2f}")
            print(f"         → {condition} → ueberschuss = {calculated_value:,.2f}")
        elif updated_count == 6:
            print("...")
    else:
        missing = []
        if row.direktverbr_strom is None:
            missing.append("direktverbr_strom")
        if row.stromverbr_raumwaerm_korr is None:
            missing.append("stromverbr_raumwaerm_korr")
        if row.wind_solar_konstant is None:
            missing.append("wind_solar_konstant")
        print(f"⚠️  Day {row.tag_im_jahr}: {', '.join(missing)} is None, skipping")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✅ Updated {updated_count} days")
print(f"   Total sum of ueberschuss_strom: {total_sum:,.2f}")

# Update row 366 with sum
row_366 = WSData.objects.get(tag_im_jahr=366)
row_366.ueberschuss_strom = total_sum
row_366.save()

print(f"\n✅ Updated Row 366:")
print(f"   ueberschuss_strom = {total_sum:,.2f} (sum of daily values)")

print("\n" + "="*80)
