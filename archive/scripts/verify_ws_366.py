import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData

print("="*80)
print("VERIFICATION: WS ROW 366 VALUE")
print("="*80)

try:
    ws_row_366 = WSData.objects.get(tag_im_jahr=366)
    
    print(f"\n✅ WS Data Row 366 - {ws_row_366.datum_ref}")
    print(f"\n   Column J: stromverbr_raumwaerm_korr")
    print(f"   Current Value: {ws_row_366.stromverbr_raumwaerm_korr:,.2f}")
    print(f"\n   This value now comes from Annual Electricity calculation:")
    print(f"   Formula: Stromnetz zum Endverbrauch = T + O + S")
    print(f"   Where:")
    print(f"     T = Rückverstromung (Reconversion from gas storage)")
    print(f"     O = Direct renewable electricity to grid")
    print(f"     S = Biomass contribution")
    
    # Also show the sum of all daily stromverbr values
    daily_sum = sum([ws.stromverbr for ws in WSData.objects.filter(tag_im_jahr__lte=365) if ws.stromverbr is not None])
    print(f"\n   Sum of daily Stromverbr (days 1-365): {daily_sum:,.2f}")
    print(f"   Reference value (row 366): {ws_row_366.stromverbr_raumwaerm_korr:,.2f}")
    
    difference = ws_row_366.stromverbr_raumwaerm_korr - daily_sum
    percentage = (difference / daily_sum) * 100
    print(f"\n   Difference: {difference:,.2f} ({percentage:+.2f}%)")
    
except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
