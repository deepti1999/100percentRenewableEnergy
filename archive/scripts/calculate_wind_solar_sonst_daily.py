import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("CALCULATING WINDSTROM, SOLARSTROM, SONST_KRAFT_KONSTANT FOR DAYS 1-365")
print("="*80)

# Get row 366 reference values
try:
    row_366 = WSData.objects.get(tag_im_jahr=366)
    windstrom_366 = row_366.windstrom
    solarstrom_366 = row_366.solarstrom
    sonst_kraft_366 = row_366.sonst_kraft_konstant
    
    print(f"\n📊 Reference Values from Row 366:")
    print(f"   Windstrom:            {windstrom_366:,.2f}")
    print(f"   Solarstrom:           {solarstrom_366:,.2f}")
    print(f"   Sonst.Kraft(konstant): {sonst_kraft_366:,.2f}")
    
    if windstrom_366 is None or solarstrom_366 is None or sonst_kraft_366 is None:
        print("\n❌ Error: Row 366 values are None!")
        exit(1)
    
    # Get all days 1-365
    daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr')
    
    print(f"\n📊 Processing {daily_rows.count()} days...")
    print(f"\nFormulas:")
    print(f"  windstrom(day)            = wind_promille(day) × {windstrom_366:,.2f} / 1000")
    print(f"  solarstrom(day)           = solar_promille(day) × {solarstrom_366:,.2f} / 1000")
    print(f"  sonst_kraft_konstant(day) = {sonst_kraft_366:,.2f} / 365")
    
    updated_count = 0
    windstrom_sum = 0
    solarstrom_sum = 0
    sonst_kraft_sum = 0
    
    # Constant value for sonst_kraft_konstant (same for all days)
    sonst_kraft_daily = sonst_kraft_366 / 365
    
    print("\n" + "="*80)
    print("CALCULATING VALUES")
    print("="*80)
    
    for row in daily_rows:
        if row.wind_promille is not None and row.solar_promille is not None:
            # windstrom = wind_promille × windstrom_366 / 1000
            windstrom_value = row.wind_promille * windstrom_366 / 1000
            
            # solarstrom = solar_promille × solarstrom_366 / 1000
            solarstrom_value = row.solar_promille * solarstrom_366 / 1000
            
            # sonst_kraft_konstant = sonst_kraft_366 / 365 (constant for all days)
            sonst_kraft_value = sonst_kraft_daily
            
            row.windstrom = windstrom_value
            row.solarstrom = solarstrom_value
            row.sonst_kraft_konstant = sonst_kraft_value
            row.save()
            
            windstrom_sum += windstrom_value
            solarstrom_sum += solarstrom_value
            sonst_kraft_sum += sonst_kraft_value
            updated_count += 1
            
            # Show first 3 and last 3 calculations
            if updated_count <= 3 or updated_count > daily_rows.count() - 3:
                print(f"Day {row.tag_im_jahr:3d}:")
                print(f"  Wind:  {row.wind_promille:.6f} × {windstrom_366:,.2f} / 1000 = {windstrom_value:,.2f}")
                print(f"  Solar: {row.solar_promille:.6f} × {solarstrom_366:,.2f} / 1000 = {solarstrom_value:,.2f}")
                print(f"  Sonst: {sonst_kraft_366:,.2f} / 365 = {sonst_kraft_value:,.2f}")
            elif updated_count == 4:
                print("...")
        else:
            missing = []
            if row.wind_promille is None:
                missing.append("wind_promille")
            if row.solar_promille is None:
                missing.append("solar_promille")
            print(f"⚠️  Day {row.tag_im_jahr}: {', '.join(missing)} is None, skipping")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Updated {updated_count} days")
    print(f"\n   Windstrom:")
    print(f"      Sum of daily values: {windstrom_sum:>15,.2f}")
    print(f"      Reference (Row 366): {windstrom_366:>15,.2f}")
    print(f"      Match: {'✅ YES' if abs(windstrom_sum - windstrom_366) < 1 else '❌ NO'}")
    
    print(f"\n   Solarstrom:")
    print(f"      Sum of daily values: {solarstrom_sum:>15,.2f}")
    print(f"      Reference (Row 366): {solarstrom_366:>15,.2f}")
    print(f"      Match: {'✅ YES' if abs(solarstrom_sum - solarstrom_366) < 1 else '❌ NO'}")
    
    print(f"\n   Sonst.Kraft(konstant):")
    print(f"      Sum of daily values: {sonst_kraft_sum:>15,.2f}")
    print(f"      Reference (Row 366): {sonst_kraft_366:>15,.2f}")
    print(f"      Match: {'✅ YES' if abs(sonst_kraft_sum - sonst_kraft_366) < 1 else '❌ NO'}")
    
except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
