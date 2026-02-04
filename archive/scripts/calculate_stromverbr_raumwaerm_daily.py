import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("CALCULATING stromverbr_raumwaerm_korr FOR DAYS 1-365")
print("="*80)

# Get row 366 reference value
try:
    row_366 = WSData.objects.get(tag_im_jahr=366)
    stromverbr_raumwaerm_korr_366 = row_366.stromverbr_raumwaerm_korr
    
    print(f"\n📊 Reference Value from Row 366:")
    print(f"   stromverbr_raumwaerm_korr = {stromverbr_raumwaerm_korr_366:,.2f}")
    
    if stromverbr_raumwaerm_korr_366 is None:
        print("\n❌ Error: Row 366 stromverbr_raumwaerm_korr is None!")
        exit(1)
    
    # Get all days 1-365
    daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr')
    
    print(f"\n📊 Processing {daily_rows.count()} days...")
    print(f"\nFormula: stromverbr_raumwaerm_korr(day) = stromverbr_raumwaerm_korr(366) × verbrauch_promille(day) / 1000 + davon_raumw_korr(day)")
    print(f"         = {stromverbr_raumwaerm_korr_366:,.2f} × verbrauch_promille(day) / 1000 + davon_raumw_korr(day)")
    
    updated_count = 0
    total_sum = 0
    
    print("\n" + "="*80)
    print("CALCULATING VALUES")
    print("="*80)
    
    for row in daily_rows:
        if row.verbrauch_promille is not None and row.davon_raumw_korr is not None:
            # Formula: stromverbr_raumwaerm_korr = (stromverbr_raumwaerm_korr_366 × verbrauch_promille / 1000) + davon_raumw_korr
            part1 = stromverbr_raumwaerm_korr_366 * row.verbrauch_promille / 1000
            part2 = row.davon_raumw_korr
            calculated_value = part1 + part2
            
            row.stromverbr_raumwaerm_korr = calculated_value
            row.save()
            
            total_sum += calculated_value
            updated_count += 1
            
            # Show first 5 and last 5 calculations
            if updated_count <= 5 or updated_count > daily_rows.count() - 5:
                print(f"Day {row.tag_im_jahr:3d}: ({stromverbr_raumwaerm_korr_366:,.2f} × {row.verbrauch_promille:.6f} / 1000) + {part2:.2f} = {calculated_value:,.2f}")
            elif updated_count == 6:
                print("...")
        else:
            missing = []
            if row.verbrauch_promille is None:
                missing.append("verbrauch_promille")
            if row.davon_raumw_korr is None:
                missing.append("davon_raumw_korr")
            print(f"⚠️  Day {row.tag_im_jahr}: {', '.join(missing)} is None, skipping")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Updated {updated_count} days")
    print(f"   Total sum of daily values: {total_sum:,.2f}")
    print(f"   Reference value (Row 366): {stromverbr_raumwaerm_korr_366:,.2f}")
    
except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
