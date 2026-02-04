import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, RenewableData

print("="*80)
print("⚠️  DEPRECATED SCRIPT - USE link_ws_to_annual_electricity.py INSTEAD")
print("="*80)
print("\nThis script previously set WS Row 366 from RenewableData 9.4.3")
print("However, Row 366 should now use the Annual Electricity calculation (T+O+S)")
print("\nPlease run: python3 link_ws_to_annual_electricity.py")
print("="*80)
print("\nContinuing with old method for reference...")
print("="*80)
print("SETTING UP REFERENCE FROM RENEWABLE ENERGY 9.4.3 (OLD METHOD)")
print("="*80)

# Get the value from RenewableData code 9.4.3
try:
    renewable = RenewableData.objects.get(code='9.4.3')
    print(f"\n✅ Found RenewableData: {renewable.code} - {renewable.name}")
    print(f"   Status Value: {renewable.status_value}")
    print(f"   Target Value: {renewable.target_value}")
    
    # Get row 366
    ws_row_366 = WSData.objects.get(tag_im_jahr=366)
    print(f"\n✅ Found WS Data Row: {ws_row_366.tag_im_jahr} - {ws_row_366.datum_ref}")
    
    # Set the value in Stromverbr. Raumwärm.Korr. column (Column J)
    ws_row_366.stromverbr_raumwaerm_korr = renewable.status_value
    ws_row_366.save()
    
    print(f"\n✅ Updated Row 366, Column J 'stromverbr_raumwaerm_korr'")
    print(f"   Value set to: {renewable.status_value}")
    print(f"   (Referenced from RenewableData 9.4.3)")
    
except RenewableData.DoesNotExist:
    print(f"\n❌ Error: RenewableData with code '9.4.3' not found!")
    print("   Available codes starting with 9.4:")
    codes = RenewableData.objects.filter(code__startswith='9.4').values_list('code', 'name')
    for code, name in codes:
        print(f"   - {code}: {name}")

except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
print("NOTE: This creates a REFERENCE relationship:")
print("WS Row 366 Column J (Stromverbr. Raumwärm.Korr.) → RenewableData 9.4.3")
print("(Stromangebot aus Erneuerbaren E. (gesamt))")
print("="*80)
