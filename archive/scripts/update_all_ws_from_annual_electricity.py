import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, RenewableData, VerbrauchData

print("="*80)
print("COMPREHENSIVE WS DATABASE UPDATE")
print("Recalculating all columns based on Annual Electricity & Verbrauch data")
print("="*80)

def get_renewable_target(code):
    """Helper function to get renewable TARGET value (Ziel) by code"""
    try:
        renewable = RenewableData.objects.get(code=code)
        return float(renewable.target_value) if renewable.target_value is not None else 0
    except RenewableData.DoesNotExist:
        return 0

# ============================================================================
# STEP 1: Calculate Row 366 Reference Values
# ============================================================================
print("\n" + "="*80)
print("STEP 1: CALCULATING ROW 366 REFERENCE VALUES")
print("="*80)

# 1a. davon_raumw_korr_366 from Verbrauch data
verbrauch_292 = VerbrauchData.objects.get(code='2.9.2')
verbrauch_24 = VerbrauchData.objects.get(code='2.4')
davon_raumw_korr_366 = verbrauch_292.ziel * (verbrauch_24.ziel / 100)
print(f"\n1a. davon_raumw_korr (366) = 2.9.2 Ziel × 2.4 Ziel%")
print(f"    = {verbrauch_292.ziel:,.2f} × {verbrauch_24.ziel}% = {davon_raumw_korr_366:,.2f}")

# 1b. stromverbr_raumwaerm_korr_366 from Annual Electricity
pv_value = get_renewable_target('1.1.2.1.2') + get_renewable_target('1.2.1.2')
wind_value = get_renewable_target('2.1.1.2.2') + get_renewable_target('2.2.1.2')
hydro_value = get_renewable_target('3.1.1.2')
bio_value = get_renewable_target('4.4.1')
ely_power_to_gas = get_renewable_target('9.2.1.5.2')
n_output_branch = get_renewable_target('9.3.1')
n_input_branch = get_renewable_target('9.3.4')

total_generation = pv_value + wind_value + hydro_value
remaining_after_ely = total_generation - ely_power_to_gas
gas_storage = n_output_branch * 0.65
t_value = gas_storage - 160
m_total = pv_value + wind_value + hydro_value
n_value = m_total - ely_power_to_gas
n_to_right = n_value - n_input_branch - n_output_branch
# Apply 58.5% efficiency to T (reconversion efficiency)
stromverbr_raumwaerm_korr_366 = (t_value * 0.585) + n_to_right + bio_value

print(f"\n1b. stromverbr_raumwaerm_korr (366) = (T × 58.5%) + O + S")
print(f"    = ({t_value:,.2f} × 0.585) + {n_to_right:,.2f} + {bio_value:,.2f}")
print(f"    = {t_value * 0.585:,.2f} + {n_to_right:,.2f} + {bio_value:,.2f} = {stromverbr_raumwaerm_korr_366:,.2f}")

# 1c. Calculate percentage for renewable distribution
percentage = (remaining_after_ely / total_generation) * 100
solarstrom_366 = pv_value * (percentage / 100)
windstrom_366 = wind_value * (percentage / 100)
sonst_kraft_konstant_366 = hydro_value * (percentage / 100)

print(f"\n1c. Renewable distribution (percentage = {percentage:.6f}%)")
print(f"    solarstrom (366) = {solarstrom_366:,.2f}")
print(f"    windstrom (366) = {windstrom_366:,.2f}")
print(f"    sonst_kraft_konstant (366) = {sonst_kraft_konstant_366:,.2f}")

# Update row 366
row_366 = WSData.objects.get(tag_im_jahr=366)
row_366.davon_raumw_korr = davon_raumw_korr_366
row_366.stromverbr_raumwaerm_korr = stromverbr_raumwaerm_korr_366
row_366.solarstrom = solarstrom_366
row_366.windstrom = windstrom_366
row_366.sonst_kraft_konstant = sonst_kraft_konstant_366
row_366.save()

print(f"\n✅ Row 366 updated with reference values")

# ============================================================================
# STEP 2: Calculate Daily Values (Days 1-365)
# ============================================================================
print("\n" + "="*80)
print("STEP 2: CALCULATING DAILY VALUES (Days 1-365)")
print("="*80)

daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr')
updated_count = 0

for row in daily_rows:
    if (row.verbrauch_promille is not None and 
        row.heizung_abwaerm_promille is not None and
        row.wind_promille is not None and
        row.solar_promille is not None):
        
        # Column G: stromverbr
        row.stromverbr = stromverbr_raumwaerm_korr_366 * row.verbrauch_promille / 1000
        
        # Column H: davon_raumw_korr
        row.davon_raumw_korr = davon_raumw_korr_366 * row.heizung_abwaerm_promille / 365
        
        # Column J: stromverbr_raumwaerm_korr
        row.stromverbr_raumwaerm_korr = (stromverbr_raumwaerm_korr_366 * row.verbrauch_promille / 1000) + row.davon_raumw_korr
        
        # Column K: windstrom
        row.windstrom = row.wind_promille * windstrom_366 / 1000
        
        # Column L: solarstrom
        row.solarstrom = row.solar_promille * solarstrom_366 / 1000
        
        # Column M: sonst_kraft_konstant
        row.sonst_kraft_konstant = sonst_kraft_konstant_366 / 365
        
        # Column N: wind_solar_konstant
        row.wind_solar_konstant = row.windstrom + row.solarstrom + row.sonst_kraft_konstant
        
        # Column O: direktverbr_strom
        if row.wind_solar_konstant <= row.stromverbr_raumwaerm_korr:
            row.direktverbr_strom = row.wind_solar_konstant
        else:
            row.direktverbr_strom = row.stromverbr_raumwaerm_korr
        
        # Column P: ueberschuss_strom
        if abs(row.direktverbr_strom - row.stromverbr_raumwaerm_korr) < 0.01:
            row.ueberschuss_strom = row.wind_solar_konstant - row.stromverbr_raumwaerm_korr
        else:
            row.ueberschuss_strom = 0
        
        row.save()
        updated_count += 1

print(f"\n✅ Updated {updated_count} daily rows")

# ============================================================================
# STEP 3: Update Row 366 with Sums
# ============================================================================
print("\n" + "="*80)
print("STEP 3: UPDATING ROW 366 WITH SUMS")
print("="*80)

daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)

sum_stromverbr = sum([r.stromverbr for r in daily_rows if r.stromverbr])
sum_davon_raumw = sum([r.davon_raumw_korr for r in daily_rows if r.davon_raumw_korr])
sum_stromverbr_raumwaerm = sum([r.stromverbr_raumwaerm_korr for r in daily_rows if r.stromverbr_raumwaerm_korr])
sum_windstrom = sum([r.windstrom for r in daily_rows if r.windstrom])
sum_solarstrom = sum([r.solarstrom for r in daily_rows if r.solarstrom])
sum_sonst_kraft = sum([r.sonst_kraft_konstant for r in daily_rows if r.sonst_kraft_konstant])
sum_wind_solar_konstant = sum([r.wind_solar_konstant for r in daily_rows if r.wind_solar_konstant])
sum_direktverbr = sum([r.direktverbr_strom for r in daily_rows if r.direktverbr_strom])
sum_ueberschuss = sum([r.ueberschuss_strom for r in daily_rows if r.ueberschuss_strom])

row_366.wind_solar_konstant = sum_wind_solar_konstant
row_366.direktverbr_strom = sum_direktverbr
row_366.ueberschuss_strom = sum_ueberschuss
row_366.save()

print(f"\nRow 366 Summary:")
print(f"  stromverbr:                {sum_stromverbr:>15,.2f} (should match row 366: {row_366.stromverbr_raumwaerm_korr:,.2f})")
print(f"  windstrom:                 {sum_windstrom:>15,.2f} (should match row 366: {row_366.windstrom:,.2f})")
print(f"  solarstrom:                {sum_solarstrom:>15,.2f} (should match row 366: {row_366.solarstrom:,.2f})")
print(f"  sonst_kraft_konstant:      {sum_sonst_kraft:>15,.2f} (should match row 366: {row_366.sonst_kraft_konstant:,.2f})")
print(f"  wind_solar_konstant:       {sum_wind_solar_konstant:>15,.2f}")
print(f"  direktverbr_strom:         {sum_direktverbr:>15,.2f}")
print(f"  ueberschuss_strom:         {sum_ueberschuss:>15,.2f}")

print("\n" + "="*80)
print("✅ COMPLETE! All WS columns updated from Annual Electricity data")
print("="*80)
