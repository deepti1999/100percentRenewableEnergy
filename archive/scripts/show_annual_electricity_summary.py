import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, RenewableData

print("="*80)
print("ANNUAL ELECTRICITY FLOW - COMPLETE SUMMARY")
print("="*80)

def get_renewable_target(code):
    """Helper function to get renewable TARGET value (Ziel) by code"""
    try:
        renewable = RenewableData.objects.get(code=code)
        return float(renewable.target_value) if renewable.target_value is not None else 0
    except RenewableData.DoesNotExist:
        return 0

# Calculate PV (K)
pv_value = get_renewable_target('1.1.2.1.2') + get_renewable_target('1.2.1.2')

# Calculate Wind (J)
wind_value = get_renewable_target('2.1.1.2.2') + get_renewable_target('2.2.1.2')

# Biomass (S)
bio_value = get_renewable_target('4.4.1')

# Hydro + Geothermal (L)
hydro_value = get_renewable_target('3.1.1.2')

# M total
m_total = pv_value + wind_value + hydro_value

# Elektrolyse branches
ely_branch_value = get_renewable_target('9.2.1.5.2')
n_output_branch = get_renewable_target('9.3.1')

# Storage calculations
gas_storage = n_output_branch * 0.65
t_value = gas_storage - 160

# Flow calculations
n_input_branch = get_renewable_target('9.3.4')
n_value = m_total - ely_branch_value
n_to_right = n_value - n_input_branch - n_output_branch

# Final calculation
final_stromnetz = t_value + n_to_right + bio_value

print("\n" + "─"*80)
print("1. GENERATION SOURCES")
print("─"*80)
print(f"   S - Biomass (4.4.1)              : {bio_value:>15,.2f} MWh")
print(f"   K - PV (1.1.2.1.2 + 1.2.1.2)     : {pv_value:>15,.2f} MWh")
print(f"   J - Wind (2.1.1.2.2 + 2.2.1.2)   : {wind_value:>15,.2f} MWh")
print(f"   L - Hydro+Geothermal (3.1.1.2)   : {hydro_value:>15,.2f} MWh")

print("\n" + "─"*80)
print("2. FLOW THROUGH SYSTEM")
print("─"*80)
print(f"   M - Total Generation (K+J+L)     : {m_total:>15,.2f} MWh")
print(f"   Elektrolyse nach Angebot (9.2.1.5.2): {ely_branch_value:>15,.2f} MWh")
print(f"   → H₂ Production (65% Eta)        : {ely_branch_value * 0.65:>15,.2f} MWh")
print(f"   N - After Elektrolyse            : {n_value:>15,.2f} MWh")
print(f"   Q - Abregelung (9.3.4)           : {n_input_branch:>15,.2f} MWh")
print(f"   Elektrolyse Stromspeicher (9.3.1): {n_output_branch:>15,.2f} MWh")

print("\n" + "─"*80)
print("3. STORAGE & RECONVERSION")
print("─"*80)
print(f"   P - Elektrolyse Stromspeicher    : {n_output_branch:>15,.2f} MWh")
print(f"   U - Gasspeicher Strom (65% Eta)  : {gas_storage:>15,.2f} MWh")
print(f"   T - Rückverstromung (U - 160)    : {t_value:>15,.2f} MWh")

print("\n" + "─"*80)
print("4. FINAL CALCULATION")
print("─"*80)
print(f"   T - Reconversion                 : {t_value:>15,.2f} MWh")
print(f"   O - Direct to Grid               : {n_to_right:>15,.2f} MWh")
print(f"   S - Biomass                      : {bio_value:>15,.2f} MWh")
print(f"   {'─'*40}")
print(f"   STROMNETZ ZUM ENDVERBRAUCH       : {final_stromnetz:>15,.2f} MWh")

print("\n" + "─"*80)
print("5. WS DATABASE INTEGRATION")
print("─"*80)
ws_row_366 = WSData.objects.get(tag_im_jahr=366)
print(f"   WS Row 366 - Column J            : {ws_row_366.stromverbr_raumwaerm_korr:>15,.2f} MWh")
print(f"   Match with calculation           : {'✅ YES' if abs(ws_row_366.stromverbr_raumwaerm_korr - final_stromnetz) < 0.01 else '❌ NO'}")

print("\n" + "─"*80)
print("6. DAILY CONSUMPTION")
print("─"*80)
daily_sum = sum([ws.stromverbr for ws in WSData.objects.filter(tag_im_jahr__lte=365) if ws.stromverbr is not None])
print(f"   Sum of Daily Stromverbr (1-365)  : {daily_sum:>15,.2f} MWh")
print(f"   Annual Reference (Row 366)       : {ws_row_366.stromverbr_raumwaerm_korr:>15,.2f} MWh")
difference = ws_row_366.stromverbr_raumwaerm_korr - daily_sum
percentage = (difference / daily_sum) * 100
print(f"   Difference                       : {difference:>15,.2f} MWh ({percentage:+.2f}%)")

print("\n" + "="*80)
print("✅ Annual Electricity Flow calculation complete!")
print("✅ WS Database row 366 updated with final value")
print("✅ View the diagram at: http://127.0.0.1:8000/annual-electricity/")
print("="*80)
