"""
TEST 365 DAYS - Excel-Style Power Limits
=========================================
Matches Excel logic exactly:
- Elektrolyse power = 194 GW → max 4,656 GWh/day
- Einspeichern = min(Überschuss, Elektrolyse_max_day)
- Abregelung = Überschuss - Einspeichern

NO α factors. NO goal seek. Just capacity limits.

Run: python3 test_365days.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from simulator.models import RenewableData, VerbrauchData
from simulator.ws_models import WSData

print("=" * 70)
print("TEST 365 DAYS - Excel-Style with Power Limits")
print("=" * 70)

# =============================================================================
# STEP 1: Read Data
# =============================================================================
print("\n📊 STEP 1: Reading Data from Database")
print("-" * 60)

solar_annual = RenewableData.objects.get(code='9.1.2').target_value or 0
wind_annual = RenewableData.objects.get(code='9.1.1').target_value or 0
bio_annual = RenewableData.objects.get(code='9.1.4').target_value or 0
water_annual = RenewableData.objects.get(code='9.1.3').target_value or 0
demand_annual = VerbrauchData.objects.get(code='7').ziel or 0

print(f"   Solar:  {solar_annual:>12,.0f} GWh/year")
print(f"   Wind:   {wind_annual:>12,.0f} GWh/year")
print(f"   Bio:    {bio_annual:>12,.0f} GWh/year")
print(f"   Water:  {water_annual:>12,.0f} GWh/year")
print(f"   Demand: {demand_annual:>12,.0f} GWh/year")

ws_entries = list(WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr'))
solar_promille = [ws.solar_promille or 0 for ws in ws_entries]
wind_promille = [ws.wind_promille or 0 for ws in ws_entries]
verbrauch_promille = [ws.verbrauch_promille or 0 for ws in ws_entries]

# =============================================================================
# STEP 2: System Parameters (Excel-style)
# =============================================================================
print("\n📊 STEP 2: System Parameters")
print("-" * 60)

GRID_LOSS_RATE = 0.092  # 9.2%

# Electrolysis capacity (from Excel)
ELEKTROLYSE_POWER_GW = 194  # GW
ELEKTROLYSE_MAX_DAY = ELEKTROLYSE_POWER_GW * 24  # GWh/day = 4,656 GWh/day

# H2 storage efficiency
H2_CHARGE_EFF = 0.65   # Electrolysis
H2_DISCHARGE_EFF = 0.585  # Fuel cell

# Rückverstromung capacity (from Excel - different from electrolysis!)
RUECKVERSTR_POWER_GW = 261  # GW
RUECKVERSTR_MAX_DAY = RUECKVERSTR_POWER_GW * 24  # ≈ 6,264 GWh/day

# H2 STORAGE CAPACITY (from WS.xlsm - this was missing!)
H2_STORAGE_CAPACITY = 241_727  # GWh max H2 energy

print(f"   Elektrolyse:     {ELEKTROLYSE_POWER_GW} GW → {ELEKTROLYSE_MAX_DAY:,.0f} GWh/day max")
print(f"   Rückverstromung: {RUECKVERSTR_POWER_GW} GW → {RUECKVERSTR_MAX_DAY:,.0f} GWh/day max")
print(f"   H2 Storage Cap:  {H2_STORAGE_CAPACITY:,} GWh")
print(f"   H2 Charge eff:   {H2_CHARGE_EFF*100:.0f}%")
print(f"   H2 Discharge eff: {H2_DISCHARGE_EFF*100:.1f}%")
print(f"   Grid Loss:       {GRID_LOSS_RATE*100:.1f}%")

# =============================================================================
# STEP 3: Run 365-Day Simulation
# =============================================================================
print("\n📊 STEP 3: Running 365-Day Simulation")
print("-" * 60)

# Initialize with pre-filled H2 storage (Excel steady-state level)
H2_SOC_START = 219_322  # GWh - matches Excel steady state
soc = H2_SOC_START

# Daily arrays
results = {k: [] for k in [
    'solar', 'wind', 'total_gen', 'grid_loss', 'demand',
    'balance', 'ueberschuss', 'mangel',
    'einspeichern_strom', 'einspeichern_h2', 'abregelung',
    'rueckverstr_strom', 'rueckverstr_h2', 'soc', 'mangel_last'
]}

for d in range(365):
    # Generation
    solar = solar_annual * (solar_promille[d] / 1000)
    wind = wind_annual * (wind_promille[d] / 1000)
    bio = bio_annual / 365
    water = water_annual / 365
    total_gen = solar + wind + bio + water
    grid_loss = total_gen * GRID_LOSS_RATE
    demand = demand_annual * (verbrauch_promille[d] / 1000)
    
    # Balance
    balance = total_gen - grid_loss - demand
    ueberschuss = max(balance, 0)
    mangel = max(-balance, 0)
    
    # === EINSPEICHERN (Excel logic with 3 limits) ===
    # Limit 1: Electrolysis power capacity
    # Limit 2: Available surplus
    # Limit 3: Free H2 storage space (THIS WAS MISSING!)
    free_h2_space = H2_STORAGE_CAPACITY - soc
    free_h2_space_electric = max(free_h2_space / H2_CHARGE_EFF, 0)
    
    einspeichern_strom = min(
        ueberschuss,
        ELEKTROLYSE_MAX_DAY,
        free_h2_space_electric  # NEW: storage capacity limit
    )
    einspeichern_h2 = einspeichern_strom * H2_CHARGE_EFF
    soc += einspeichern_h2
    
    # Abregelung = surplus that couldn't be stored
    abregelung = ueberschuss - einspeichern_strom
    
    # === RÜCKVERSTROMUNG (Excel logic) ===
    # Limited by: 1) mangel, 2) SOC, 3) power capacity
    max_from_soc = soc * H2_DISCHARGE_EFF
    rueckverstr_strom = min(mangel, max_from_soc, RUECKVERSTR_MAX_DAY)
    
    if rueckverstr_strom > 0:
        rueckverstr_h2 = rueckverstr_strom / H2_DISCHARGE_EFF
        soc -= rueckverstr_h2
    else:
        rueckverstr_h2 = 0
    
    soc = max(soc, 0)
    
    # Unserved demand
    mangel_last = mangel - rueckverstr_strom
    
    # Store results
    for key, val in [
        ('solar', solar), ('wind', wind), ('total_gen', total_gen),
        ('grid_loss', grid_loss), ('demand', demand), ('balance', balance),
        ('ueberschuss', ueberschuss), ('mangel', mangel),
        ('einspeichern_strom', einspeichern_strom), ('einspeichern_h2', einspeichern_h2),
        ('abregelung', abregelung), ('rueckverstr_strom', rueckverstr_strom),
        ('rueckverstr_h2', rueckverstr_h2), ('soc', soc), ('mangel_last', mangel_last)
    ]:
        results[key].append(val)

print(f"   ✅ Simulation complete")

# =============================================================================
# STEP 4: Display First 15 Days
# =============================================================================
print("\n📊 STEP 4: Daily Values - First 15 Days")
print("-" * 140)
print(f"{'Day':>3} | {'TotGen':>8} | {'Demand':>8} | {'Balance':>8} | {'Ueber':>8} | {'Einspch':>8} | {'Abregel':>8} | {'SOC':>10} | {'RueckStr':>8} | {'MangLast':>8}")
print("-" * 140)

for d in range(15):
    print(f"{d+1:3d} | {results['total_gen'][d]:8,.0f} | {results['demand'][d]:8,.0f} | {results['balance'][d]:+8,.0f} | {results['ueberschuss'][d]:8,.0f} | {results['einspeichern_strom'][d]:8,.0f} | {results['abregelung'][d]:8,.0f} | {results['soc'][d]:10,.0f} | {results['rueckverstr_strom'][d]:8,.0f} | {results['mangel_last'][d]:8,.0f}")

# =============================================================================
# STEP 5: Summary Statistics
# =============================================================================
print("\n📊 STEP 5: Annual Summary")
print("-" * 60)

total_gen = sum(results['total_gen'])
total_grid_loss = sum(results['grid_loss'])
total_demand = sum(results['demand'])
total_ueberschuss = sum(results['ueberschuss'])
total_mangel = sum(results['mangel'])
total_einspeichern = sum(results['einspeichern_strom'])
total_abregelung = sum(results['abregelung'])
total_rueckverstr = sum(results['rueckverstr_strom'])
total_mangel_last = sum(results['mangel_last'])
soc_end = results['soc'][-1]

print(f"   GENERATION:")
print(f"      Total:         {total_gen:>12,.0f} GWh")
print(f"      Grid Loss:     {total_grid_loss:>12,.0f} GWh")
print(f"      Net:           {total_gen - total_grid_loss:>12,.0f} GWh")
print()
print(f"   DEMAND:")
print(f"      Total:         {total_demand:>12,.0f} GWh")
print()
print(f"   DAILY BALANCE:")
print(f"      Überschuss:    {total_ueberschuss:>12,.0f} GWh (surplus days)")
print(f"      Mangel:        {total_mangel:>12,.0f} GWh (deficit days)")
print()
print(f"   H2 STORAGE:")
print(f"      Einspeichern:  {total_einspeichern:>12,.0f} GWh (→ electrolysis)")
print(f"      Abregelung:    {total_abregelung:>12,.0f} GWh (curtailed)")
print(f"      Rückverstr.:   {total_rueckverstr:>12,.0f} GWh (← fuel cell)")
print(f"      SOC_end:       {soc_end:>12,.0f} GWh")
print()
print(f"   RESULT:")
delivered = total_demand - total_mangel_last
print(f"      Demand:        {total_demand:>12,.0f} GWh")
print(f"      Mangel-Last:   {total_mangel_last:>12,.0f} GWh (unserved)")
print(f"      DELIVERED:     {delivered:>12,.0f} GWh ({delivered/total_demand*100:.1f}%)")

# =============================================================================
# FINAL
# =============================================================================
print("\n" + "=" * 70)
print("FINAL RESULT")
print("=" * 70)
print(f"\n   Elektrolyse capacity: {ELEKTROLYSE_POWER_GW} GW")
print(f"   Max daily storage: {ELEKTROLYSE_MAX_DAY:,.0f} GWh/day")
print()
print(f"   Total Einspeichern: {total_einspeichern:,.0f} GWh")
print(f"   Total Abregelung:   {total_abregelung:,.0f} GWh ({total_abregelung/total_ueberschuss*100:.1f}% of surplus)")
print(f"   Total Rückverstr.:  {total_rueckverstr:,.0f} GWh")
print(f"   Total Mangel-Last:  {total_mangel_last:,.0f} GWh ({total_mangel_last/total_mangel*100:.1f}% of deficit)")
print()
print(f"   SOC_start: {H2_SOC_START:,.0f} → SOC_end: {soc_end:,.0f} GWh")
soc_drift = soc_end - H2_SOC_START
if abs(soc_drift) < 1000:
    print(f"   ✅ SOC is CYCLIC! (drift = {soc_drift:,.0f} GWh)")
else:
    print(f"   ⚠️ SOC drift = {soc_drift:,.0f} GWh")
print()
print("=" * 70)

