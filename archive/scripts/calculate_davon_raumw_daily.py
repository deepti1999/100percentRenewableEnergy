import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("CALCULATING davon_raumw_korr FOR DAYS 1-365")
print("="*80)

# Get row 366 reference value
try:
    row_366 = WSData.objects.get(tag_im_jahr=366)
    davon_raumw_korr_366 = row_366.davon_raumw_korr
    
    print(f"\n📊 Reference Value from Row 366:")
    print(f"   davon_raumw_korr = {davon_raumw_korr_366:,.2f}")
    
    if davon_raumw_korr_366 is None:
        print("\n❌ Error: Row 366 davon_raumw_korr is None!")
        print("   Please run update_ws_366_davon_raumw.py first")
        exit(1)
    
    # Get all days 1-365
    daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr')
    
    print(f"\n📊 Processing {daily_rows.count()} days...")
    print(f"\nFormula: davon_raumw_korr(day) = davon_raumw_korr(366) × heizung_abwaerm_promille(day) / 365")
    print(f"         davon_raumw_korr(day) = {davon_raumw_korr_366:,.2f} × heizung_abwaerm_promille(day) / 365")
    
    updated_count = 0
    total_sum = 0
    
    print("\n" + "="*80)
    print("CALCULATING VALUES")
    print("="*80)
    
    for row in daily_rows:
        if row.heizung_abwaerm_promille is not None:
            # Formula: davon_raumw_korr = davon_raumw_korr_366 × heizung_abwaerm_promille / 365
            calculated_value = davon_raumw_korr_366 * row.heizung_abwaerm_promille / 365
            
            row.davon_raumw_korr = calculated_value
            row.save()
            
            total_sum += calculated_value
            updated_count += 1
            
            # Show first 5 and last 5 calculations
            if updated_count <= 5 or updated_count > daily_rows.count() - 5:
                print(f"Day {row.tag_im_jahr:3d}: {davon_raumw_korr_366:,.2f} × {row.heizung_abwaerm_promille:.6f} / 365 = {calculated_value:,.2f}")
            elif updated_count == 6:
                print("...")
        else:
            print(f"⚠️  Day {row.tag_im_jahr}: heizung_abwaerm_promille is None, skipping")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Updated {updated_count} days")
    print(f"   Total sum of daily values: {total_sum:,.2f}")
    print(f"   Reference value (Row 366): {davon_raumw_korr_366:,.2f}")
    print(f"   Difference: {total_sum - davon_raumw_korr_366:,.2f}")
    print(f"   Match: {'✅ YES' if abs(total_sum - davon_raumw_korr_366) < 1 else '❌ NO'}")
    
except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
