import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, RenewableData

print("="*80)
print("SETTING UP REFERENCE FROM ANNUAL ELECTRICITY FINAL VALUE")
print("="*80)

def get_renewable_target(code):
    """Helper function to get renewable TARGET value (Ziel) by code"""
    try:
        renewable = RenewableData.objects.get(code=code)
        return float(renewable.target_value) if renewable.target_value is not None else 0
    except RenewableData.DoesNotExist:
        return 0

# Calculate PV (K) = 1.1.2.1.2 Ziel + 1.2.1.2 Ziel
pv_value = get_renewable_target('1.1.2.1.2') + get_renewable_target('1.2.1.2')
print(f"\n📊 PV (K) = {pv_value}")

# Calculate Wind (J) = 2.1.1.2.2 Ziel + 2.2.1.2 Ziel
wind_value = get_renewable_target('2.1.1.2.2') + get_renewable_target('2.2.1.2')
print(f"📊 Wind (J) = {wind_value}")

# Biomass (S) = 4.4.1 Ziel
bio_value = get_renewable_target('4.4.1')
print(f"📊 Biomass (S) = {bio_value}")

# Hydro + Geothermal (L) = 3.1.1.2 Ziel
hydro_value = get_renewable_target('3.1.1.2')
print(f"📊 Hydro+Geothermal (L) = {hydro_value}")

# Calculate M total (PV + Wind + Hydro ONLY, Bio is separate)
m_total = pv_value + wind_value + hydro_value
print(f"\n🔄 M Total (PV+Wind+Hydro) = {m_total}")

# Get 9.2.1.5.2 value (Elektrolyse branch from M)
ely_branch_value = get_renewable_target('9.2.1.5.2')
print(f"🔄 Elektrolyse branch (9.2.1.5.2) = {ely_branch_value}")

# N node branches
n_input_branch = get_renewable_target('9.3.4')  # Value coming into N from above
n_output_branch = get_renewable_target('9.3.1')  # Value going down from N to Elektrolyse Stromspeicher
print(f"🔄 N input (9.3.4) = {n_input_branch}")
print(f"🔄 N output to Elektrolyse Stromspeicher (9.3.1) = {n_output_branch}")

# Gasspeicher Strom = Elektrolyse Stromspeicher * 65% (hydrogen production efficiency)
gas_storage = n_output_branch * 0.65
print(f"🔄 Gasspeicher Strom = {gas_storage}")

# T = Gasspeicher Strom - 160
t_value = gas_storage - 160
print(f"🔄 T (Reconversion) = {t_value}")

# Q (Abregelung) = value from 9.3.4
q_abregelung = n_input_branch

# N value = M - Elektrolyse Power to Gas (M remaining)
n_value = m_total - ely_branch_value

# O value = N - Q - Elektrolyse Stromspeicher
n_to_right = n_value - q_abregelung - n_output_branch
print(f"🔄 O (Direct to grid) = {n_to_right}")

# Final Stromnetz zum Endverbrauch = T + O + S(Bio)
final_stromnetz = t_value + n_to_right + bio_value

print("\n" + "="*80)
print("CALCULATION: Stromnetz zum Endverbrauch (T + O + S)")
print("="*80)
print(f"  T (Reconversion)     = {t_value:,.2f}")
print(f"  O (Direct to grid)   = {n_to_right:,.2f}")
print(f"  S (Biomass)          = {bio_value:,.2f}")
print(f"  ─────────────────────────────────")
print(f"  TOTAL                = {final_stromnetz:,.2f}")
print("="*80)

# Get row 366 and update it
try:
    ws_row_366 = WSData.objects.get(tag_im_jahr=366)
    print(f"\n✅ Found WS Data Row: {ws_row_366.tag_im_jahr} - {ws_row_366.datum_ref}")
    
    # Set the value in Stromverbr. Raumwärm.Korr. column (Column J)
    old_value = ws_row_366.stromverbr_raumwaerm_korr
    ws_row_366.stromverbr_raumwaerm_korr = final_stromnetz
    ws_row_366.save()
    
    print(f"\n✅ Updated Row 366, Column J 'stromverbr_raumwaerm_korr'")
    print(f"   Old value: {old_value}")
    print(f"   New value: {final_stromnetz}")
    print(f"   (Calculated from Annual Electricity: T + O + S)")
    
except WSData.DoesNotExist:
    print(f"\n❌ Error: WS Data row 366 not found!")

print("\n" + "="*80)
print("NOTE: This creates a CALCULATION-BASED relationship:")
print("WS Row 366 Column J (Stromverbr. Raumwärm.Korr.) ← Annual Electricity Final Value")
print("Formula: Stromnetz zum Endverbrauch = T + O + S")
print("  where T = Rückverstromung (Reconversion)")
print("        O = Direct renewable to grid")
print("        S = Biomass contribution")
print("="*80)
