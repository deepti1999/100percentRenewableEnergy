import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("CALCULATING STROMVERBR. FOR ALL 365 DAYS")
print("="*80)

# Get the reference value from row 366
row_366 = WSData.objects.get(tag_im_jahr=366)
reference_value = row_366.stromverbr_raumwaerm_korr

print(f"\n📌 Reference Value (Row 366, Column J):")
print(f"   Stromverbr.Raumw.korr. = {reference_value}")

if reference_value is None:
    print("\n❌ Error: Row 366 Stromverbr.Raumw.korr. is NULL!")
    print("   Cannot calculate without reference value.")
    exit(1)

print(f"\n📐 Formula: Stromverbr = {reference_value} × Verbrauch Promille / 1000")
print(f"\n🔄 Calculating for days 1-365...")

# Calculate for all 365 days
updated_count = 0
error_count = 0

for day in range(1, 366):
    try:
        row = WSData.objects.get(tag_im_jahr=day)
        
        if row.verbrauch_promille is not None:
            # Formula: Stromverbr = Row366_Value × Verbrauch_Promille / 1000
            row.stromverbr = reference_value * row.verbrauch_promille / 1000
            row.save()
            updated_count += 1
            
            if day <= 5:  # Show first 5 as examples
                print(f"   Day {day}: {reference_value} × {row.verbrauch_promille} / 1000 = {row.stromverbr}")
        else:
            error_count += 1
            if error_count <= 3:
                print(f"   ⚠️  Day {day}: Verbrauch Promille is NULL, skipping")
    
    except WSData.DoesNotExist:
        print(f"   ❌ Day {row} not found")
        error_count += 1

    if day % 50 == 0:
        print(f"   ... Processed {day} days ...")

print("\n" + "="*80)
print(f"✅ CALCULATION COMPLETE")
print("="*80)
print(f"Successfully calculated: {updated_count} rows")
print(f"Errors/Skipped: {error_count} rows")
print(f"\n🔄 Refresh admin: http://127.0.0.1:8000/admin/simulator/wsdata/")
print(f"   Column G (Stromverbr.) is now filled for days 1-365")
