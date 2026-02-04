import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, RenewableData

print("="*80)
print("CALCULATING WINDSTROM AND SONST_KRAFT_KONSTANT FOR ROW 366")
print("="*80)

def get_renewable_target(code):
    """Helper function to get renewable TARGET value (Ziel) by code"""
    try:
        renewable = RenewableData.objects.get(code=code)
        return float(renewable.target_value) if renewable.target_value is not None else 0
    except RenewableData.DoesNotExist:
        return 0

# Get values from Annual Electricity diagram
pv_value = get_renewable_target('1.1.2.1.2') + get_renewable_target('1.2.1.2')
wind_value = get_renewable_target('2.1.1.2.2') + get_renewable_target('2.2.1.2')
hydro_value = get_renewable_target('3.1.1.2')
ely_power_to_gas = get_renewable_target('9.2.1.5.2')  # Elektrolyse Power to Gas

print(f"\n📊 Values from Annual Electricity Diagram:")
print(f"   PV:                          {pv_value:>15,.2f} MWh")
print(f"   Wind:                        {wind_value:>15,.2f} MWh")
print(f"   Hydro (Wasser):              {hydro_value:>15,.2f} MWh")
print(f"   ────────────────────────────────────────────")
print(f"   Total (PV + Wind + Hydro):   {pv_value + wind_value + hydro_value:>15,.2f} MWh")
print(f"   Elektrolyse Power to Gas:    {ely_power_to_gas:>15,.2f} MWh")

# Calculate: (PV + Wind + Hydro) - Elektrolyse
total_generation = pv_value + wind_value + hydro_value
remaining_after_ely = total_generation - ely_power_to_gas

print(f"   Remaining after Elektrolyse: {remaining_after_ely:>15,.2f} MWh")

# Calculate percentage
percentage = (remaining_after_ely / total_generation) * 100

print(f"\n📊 Percentage Calculation:")
print(f"   = (Total - Elektrolyse) / Total × 100")
print(f"   = {remaining_after_ely:,.2f} / {total_generation:,.2f} × 100")
print(f"   = {percentage:.6f}%")

# Calculate windstrom for row 366
windstrom_366 = wind_value * (percentage / 100)

print(f"\n📊 Windstrom Calculation:")
print(f"   = Wind × (percentage / 100)")
print(f"   = {wind_value:,.2f} × ({percentage:.6f} / 100)")
print(f"   = {windstrom_366:,.2f} MWh")

# Calculate sonst_kraft_konstant for row 366
sonst_kraft_konstant_366 = hydro_value * (percentage / 100)

print(f"\n📊 Sonst.Kraft(konstant) Calculation:")
print(f"   = Hydro × (percentage / 100)")
print(f"   = {hydro_value:,.2f} × ({percentage:.6f} / 100)")
print(f"   = {sonst_kraft_konstant_366:,.2f} MWh")

# Update row 366
try:
    row_366 = WSData.objects.get(tag_im_jahr=366)
    
    old_windstrom = row_366.windstrom
    old_sonst = row_366.sonst_kraft_konstant
    
    row_366.windstrom = windstrom_366
    row_366.sonst_kraft_konstant = sonst_kraft_konstant_366
    row_366.save()
    
    print(f"\n✅ Updated Row 366 - windstrom")
    print(f"   Old value: {old_windstrom}")
    print(f"   New value: {windstrom_366:,.2f}")
    
    print(f"\n✅ Updated Row 366 - sonst_kraft_konstant")
    print(f"   Old value: {old_sonst}")
    print(f"   New value: {sonst_kraft_konstant_366:,.2f}")
    
    # Show summary
    print(f"\n" + "="*80)
    print("SUMMARY - ROW 366 VALUES:")
    print("="*80)
    print(f"   Solarstrom:           {row_366.solarstrom:>15,.2f} MWh")
    print(f"   Windstrom:            {row_366.windstrom:>15,.2f} MWh")
    print(f"   Sonst.Kraft(konstant): {row_366.sonst_kraft_konstant:>15,.2f} MWh")
    print(f"   ────────────────────────────────────────────")
    print(f"   Total:                {row_366.solarstrom + row_366.windstrom + row_366.sonst_kraft_konstant:>15,.2f} MWh")
    
except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
