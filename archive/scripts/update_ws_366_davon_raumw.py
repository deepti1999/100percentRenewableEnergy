import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, VerbrauchData

print("="*80)
print("UPDATING WS ROW 366 - davon Raumw.korr. (Column H)")
print("="*80)

# Get values from VerbrauchData
try:
    verbrauch_292 = VerbrauchData.objects.get(code='2.9.2')
    verbrauch_24 = VerbrauchData.objects.get(code='2.4')
    
    print(f"\n📊 VerbrauchData 2.9.2:")
    print(f"   Category: {verbrauch_292.category}")
    print(f"   Status: {verbrauch_292.status}")
    print(f"   Ziel: {verbrauch_292.ziel}")
    
    print(f"\n📊 VerbrauchData 2.4:")
    print(f"   Category: {verbrauch_24.category}")
    print(f"   Status: {verbrauch_24.status}")
    print(f"   Ziel: {verbrauch_24.ziel}")
    
    # Calculate davon_raumw_korr = 2.9.2 Ziel × 2.4 Ziel (as percentage)
    davon_raumw_korr_value = verbrauch_292.ziel * (verbrauch_24.ziel / 100)
    
    print("\n" + "="*80)
    print("CALCULATION: davon Raumw.korr.")
    print("="*80)
    print(f"  Formula: 2.9.2 Ziel × 2.4 Ziel%")
    print(f"  = {verbrauch_292.ziel:,.2f} × ({verbrauch_24.ziel}% / 100)")
    print(f"  = {verbrauch_292.ziel:,.2f} × {verbrauch_24.ziel / 100:.3f}")
    print(f"  = {davon_raumw_korr_value:,.2f}")
    print("="*80)
    
    # Get row 366 and update it
    ws_row_366 = WSData.objects.get(tag_im_jahr=366)
    print(f"\n✅ Found WS Data Row: {ws_row_366.tag_im_jahr} - {ws_row_366.datum_ref}")
    
    # Set the value in davon Raumw.korr. column (Column H)
    old_value = ws_row_366.davon_raumw_korr
    ws_row_366.davon_raumw_korr = davon_raumw_korr_value
    ws_row_366.save()
    
    print(f"\n✅ Updated Row 366, Column H 'davon_raumw_korr'")
    print(f"   Old value: {old_value}")
    print(f"   New value: {davon_raumw_korr_value:,.2f}")
    print(f"   (Calculated from VerbrauchData: 2.9.2 Ziel × 2.4 Ziel)")
    
except VerbrauchData.DoesNotExist as e:
    print(f"\n❌ Error: VerbrauchData not found!")
    print(f"   {e}")
    
except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
print("NOTE: This creates a CALCULATION-BASED relationship:")
print("WS Row 366 Column H (davon Raumw.korr.) ← VerbrauchData 2.9.2 Ziel × 2.4 Ziel")
print("="*80)
