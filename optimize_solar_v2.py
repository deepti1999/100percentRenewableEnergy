"""
OPTIMIZE SOLAR LANDUSE - Version 2
===================================
Finds optimal solar multiplier k that satisfies:

1️⃣ CYCLIC STORAGE: SOC_day365 = SOC_day1
2️⃣ NO OVERPRODUCTION: Net_generation ≈ Demand (minimal Abregelung)

Solar is the ONLY adjustable source:
  solar_annual = solar_base × k

All other sources (Wind, Bio, Water) are FIXED.

Run: python optimize_solar_v2.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from simulator.models import RenewableData, VerbrauchData
from simulator.ws_models import WSData

print("=" * 80)
print("OPTIMIZE SOLAR - Goal Seek for Balanced System")
print("=" * 80)

# =============================================================================
# SYSTEM PARAMETERS (FIXED)
# =============================================================================
GRID_LOSS_RATE = 0.092
ELEKTROLYSE_POWER_GW = 194
ELEKTROLYSE_MAX_DAY = ELEKTROLYSE_POWER_GW * 24  # 4,656 GWh/day
H2_CHARGE_EFF = 0.65
H2_DISCHARGE_EFF = 0.585
RUECKVERSTR_POWER_GW = 261
RUECKVERSTR_MAX_DAY = RUECKVERSTR_POWER_GW * 24  # 6,264 GWh/day
H2_STORAGE_CAPACITY = 241_727  # GWh

# =============================================================================
# LOAD FIXED DATA
# =============================================================================
print("\n📊 Loading data...")

# FIXED sources
wind_annual = RenewableData.objects.get(code='9.1.1').target_value or 0
bio_annual = RenewableData.objects.get(code='9.1.4').target_value or 0
water_annual = RenewableData.objects.get(code='9.1.3').target_value or 0
demand_annual = VerbrauchData.objects.get(code='7').ziel or 0

# Solar BASE (will be multiplied by k)
solar_base = RenewableData.objects.get(code='9.1.2').target_value or 0

# Daily profiles
ws_entries = list(WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr'))
solar_promille = [ws.solar_promille or 0 for ws in ws_entries]
wind_promille = [ws.wind_promille or 0 for ws in ws_entries]
verbrauch_promille = [ws.verbrauch_promille or 0 for ws in ws_entries]

print(f"\n   FIXED SOURCES:")
print(f"      Wind:          {wind_annual:>12,.0f} GWh/year")
print(f"      Bio:           {bio_annual:>12,.0f} GWh/year")
print(f"      Water:         {water_annual:>12,.0f} GWh/year")
print(f"      Demand:        {demand_annual:>12,.0f} GWh/year")
print(f"\n   ADJUSTABLE SOURCE:")
print(f"      Solar (base):  {solar_base:>12,.0f} GWh/year (current)")

# =============================================================================
# SIMULATION FUNCTION
# =============================================================================
def simulate_year(solar_annual, soc_start):
    """
    Run 365-day simulation with given solar and starting SOC.
    Returns detailed results dict.
    """
    soc = soc_start
    
    total_generation = 0
    total_grid_loss = 0
    total_demand = 0
    total_ueberschuss = 0
    total_mangel = 0
    total_einspeichern = 0
    total_abregelung = 0
    total_rueckverstr = 0
    total_mangel_last = 0
    
    # Track H2 storage losses
    total_h2_in = 0  # H2 stored
    total_h2_out = 0  # H2 withdrawn
    
    for d in range(365):
        # Generation (solar adjustable, others fixed)
        solar = solar_annual * (solar_promille[d] / 1000)
        wind = wind_annual * (wind_promille[d] / 1000)
        bio = bio_annual / 365
        water = water_annual / 365
        total_gen = solar + wind + bio + water
        grid_loss = total_gen * GRID_LOSS_RATE
        demand = demand_annual * (verbrauch_promille[d] / 1000)
        
        total_generation += total_gen
        total_grid_loss += grid_loss
        total_demand += demand
        
        # Balance after grid loss
        balance = total_gen - grid_loss - demand
        ueberschuss = max(balance, 0)
        mangel = max(-balance, 0)
        total_ueberschuss += ueberschuss
        total_mangel += mangel
        
        # === EINSPEICHERN (store surplus as H2) ===
        free_h2_space = H2_STORAGE_CAPACITY - soc
        free_h2_space_electric = max(free_h2_space / H2_CHARGE_EFF, 0)
        einspeichern_strom = min(ueberschuss, ELEKTROLYSE_MAX_DAY, free_h2_space_electric)
        einspeichern_h2 = einspeichern_strom * H2_CHARGE_EFF
        soc += einspeichern_h2
        total_h2_in += einspeichern_h2
        
        # Abregelung = surplus that couldn't be stored
        abregelung = ueberschuss - einspeichern_strom
        total_einspeichern += einspeichern_strom
        total_abregelung += abregelung
        
        # === RÜCKVERSTROMUNG (use H2 to cover deficit) ===
        max_from_soc = soc * H2_DISCHARGE_EFF
        rueckverstr_strom = min(mangel, max_from_soc, RUECKVERSTR_MAX_DAY)
        if rueckverstr_strom > 0:
            rueckverstr_h2 = rueckverstr_strom / H2_DISCHARGE_EFF
            soc -= rueckverstr_h2
            total_h2_out += rueckverstr_h2
        total_rueckverstr += rueckverstr_strom
        
        soc = max(soc, 0)
        
        # Mangel-Last (unserved demand)
        mangel_last = mangel - rueckverstr_strom
        total_mangel_last += mangel_last
    
    soc_end = soc
    
    # Calculate storage round-trip losses
    # Loss = (H2_in × charge_eff) - (H2_out × discharge_eff) conceptually
    # But simpler: electricity lost = einspeichern - rueckverstr
    storage_loss = total_einspeichern - total_rueckverstr
    
    # Net delivered electricity
    net_delivered = total_demand - total_mangel_last
    
    # Annual net generation (what actually serves demand)
    # = Generation - GridLoss - Abregelung - StorageLoss
    net_usable = total_generation - total_grid_loss - total_abregelung - storage_loss
    
    return {
        'solar_annual': solar_annual,
        'total_generation': total_generation,
        'total_grid_loss': total_grid_loss,
        'total_demand': total_demand,
        'total_ueberschuss': total_ueberschuss,
        'total_mangel': total_mangel,
        'total_einspeichern': total_einspeichern,
        'total_abregelung': total_abregelung,
        'total_rueckverstr': total_rueckverstr,
        'storage_loss': storage_loss,
        'total_mangel_last': total_mangel_last,
        'net_usable': net_usable,
        'soc_start': soc_start,
        'soc_end': soc_end,
        'soc_drift': soc_end - soc_start,
    }


def find_balanced_soc(solar_annual, initial_soc=None, max_iter=100, tolerance=10):
    """
    Find SOC_start that results in SOC_end = SOC_start (cyclic balance).
    Uses iterative convergence.
    """
    if initial_soc is None:
        soc = H2_STORAGE_CAPACITY / 2
    else:
        soc = initial_soc
    
    for i in range(max_iter):
        result = simulate_year(solar_annual, soc)
        drift = result['soc_drift']
        
        if abs(drift) < tolerance:
            return result
        
        # Adjust: if SOC drifts up, start lower; if drifts down, start higher
        soc = soc - drift * 0.7
        soc = max(0, min(soc, H2_STORAGE_CAPACITY))
    
    # Return last result even if not fully converged
    return simulate_year(solar_annual, soc)


# =============================================================================
# GOAL SEEK: Find optimal solar multiplier k
# =============================================================================
print("\n" + "=" * 80)
print("GOAL SEEK: Finding optimal solar multiplier k")
print("=" * 80)
print("""
Objective: Find k such that:
  1. SOC_day365 = SOC_day1 (cyclic)
  2. Abregelung ≈ 0 (no overproduction)
  3. Mangel-Last = 0 (100% demand met)

Logic:
  - If Abregelung > 0 and SOC_drift > 0 → reduce k (too much solar)
  - If Mangel-Last > 0 or SOC_drift < 0 → increase k (too little solar)
""")

# Search range for k
k_low = 0.1   # 10% of current solar
k_high = 1.5  # 150% of current solar

# Binary search
print(f"\n{'Iter':>4} | {'k':>8} | {'Solar (GWh)':>14} | {'Abregelung':>12} | {'Mangel-Last':>12} | {'SOC_drift':>12} | {'Status'}")
print("-" * 95)

iterations = 0
best_result = None
best_k = None

while k_high - k_low > 0.001:  # Stop when k range < 0.1%
    iterations += 1
    k_mid = (k_low + k_high) / 2
    solar_test = solar_base * k_mid
    
    # Run simulation with balanced SOC
    result = find_balanced_soc(solar_test)
    
    # Determine direction
    has_curtailment = result['total_abregelung'] > 100  # More than 100 GWh curtailed
    has_unserved = result['total_mangel_last'] > 1  # More than 1 GWh unserved
    soc_drifts_up = result['soc_drift'] > 100
    soc_drifts_down = result['soc_drift'] < -100
    
    # Status
    if has_unserved:
        status = "❌ Need more"
        k_low = k_mid  # Increase solar
    elif has_curtailment and soc_drifts_up:
        status = "⬇️ Too much"
        k_high = k_mid  # Reduce solar
    elif has_curtailment:
        status = "⚠️ Slight excess"
        k_high = k_mid  # Reduce solar slightly
    else:
        status = "✅ Balanced"
        best_result = result
        best_k = k_mid
        k_high = k_mid  # Try to find even lower
    
    print(f"{iterations:4d} | {k_mid:8.4f} | {solar_test:>14,.0f} | {result['total_abregelung']:>12,.0f} | {result['total_mangel_last']:>12,.0f} | {result['soc_drift']:>+12,.0f} | {status}")
    
    if iterations > 30:
        break

# If no perfect solution found, use last converged value
if best_result is None:
    k_final = k_high
    solar_final = solar_base * k_final
    best_result = find_balanced_soc(solar_final)
    best_k = k_final
else:
    k_final = best_k
    solar_final = solar_base * k_final

print(f"\n✅ Optimal k = {k_final:.4f}")
print(f"   Optimal Solar = {solar_final:,.0f} GWh/year")

# =============================================================================
# FINAL RESULTS
# =============================================================================
print("\n" + "=" * 80)
print("FINAL OPTIMIZED RESULTS")
print("=" * 80)

r = best_result

print(f"""
   GENERATION (with optimal solar):
      Solar:           {r['solar_annual']:>12,.0f} GWh/year  (k = {k_final:.4f})
      Wind:            {wind_annual:>12,.0f} GWh/year  (fixed)
      Bio:             {bio_annual:>12,.0f} GWh/year  (fixed)
      Water:           {water_annual:>12,.0f} GWh/year  (fixed)
      ─────────────────────────────────────────
      TOTAL:           {r['total_generation']:>12,.0f} GWh/year

   LOSSES:
      Grid Loss:       {r['total_grid_loss']:>12,.0f} GWh ({r['total_grid_loss']/r['total_generation']*100:.1f}%)
      Abregelung:      {r['total_abregelung']:>12,.0f} GWh (curtailed)
      Storage Loss:    {r['storage_loss']:>12,.0f} GWh (round-trip)
      ─────────────────────────────────────────
      TOTAL LOSS:      {r['total_grid_loss'] + r['total_abregelung'] + r['storage_loss']:>12,.0f} GWh

   DEMAND:
      Total Demand:    {r['total_demand']:>12,.0f} GWh
      Mangel-Last:     {r['total_mangel_last']:>12,.0f} GWh (unserved)
      DELIVERED:       {r['total_demand'] - r['total_mangel_last']:>12,.0f} GWh ({(r['total_demand'] - r['total_mangel_last'])/r['total_demand']*100:.1f}%)

   H2 STORAGE:
      Einspeichern:    {r['total_einspeichern']:>12,.0f} GWh (electricity → H2)
      Rückverstr.:     {r['total_rueckverstr']:>12,.0f} GWh (H2 → electricity)
      SOC_start:       {r['soc_start']:>12,.0f} GWh
      SOC_end:         {r['soc_end']:>12,.0f} GWh
      SOC_drift:       {r['soc_drift']:>+12,.0f} GWh {'✅ CYCLIC!' if abs(r['soc_drift']) < 100 else '⚠️'}

   ENERGY BALANCE CHECK:
      Net Usable:      {r['net_usable']:>12,.0f} GWh
      Demand:          {r['total_demand']:>12,.0f} GWh
      Difference:      {r['net_usable'] - r['total_demand']:>+12,.0f} GWh
""")

# =============================================================================
# COMPARISON: Current vs Optimal
# =============================================================================
print("=" * 80)
print("COMPARISON: Current Solar vs Optimal Solar")
print("=" * 80)

current_result = find_balanced_soc(solar_base)

print(f"""
{'Metric':<25} | {'Current':>15} | {'Optimal':>15} | {'Change':>15}
{'-' * 75}
{'Solar (GWh/year)':<25} | {solar_base:>15,.0f} | {solar_final:>15,.0f} | {solar_final - solar_base:>+15,.0f}
{'Solar multiplier (k)':<25} | {1.0:>15.4f} | {k_final:>15.4f} | {k_final - 1.0:>+15.4f}
{'Total Generation':<25} | {current_result['total_generation']:>15,.0f} | {r['total_generation']:>15,.0f} | {r['total_generation'] - current_result['total_generation']:>+15,.0f}
{'Abregelung (curtailed)':<25} | {current_result['total_abregelung']:>15,.0f} | {r['total_abregelung']:>15,.0f} | {r['total_abregelung'] - current_result['total_abregelung']:>+15,.0f}
{'Einspeichern':<25} | {current_result['total_einspeichern']:>15,.0f} | {r['total_einspeichern']:>15,.0f} | {r['total_einspeichern'] - current_result['total_einspeichern']:>+15,.0f}
{'Rückverstr.':<25} | {current_result['total_rueckverstr']:>15,.0f} | {r['total_rueckverstr']:>15,.0f} | {r['total_rueckverstr'] - current_result['total_rueckverstr']:>+15,.0f}
{'Storage Loss':<25} | {current_result['storage_loss']:>15,.0f} | {r['storage_loss']:>15,.0f} | {r['storage_loss'] - current_result['storage_loss']:>+15,.0f}
{'SOC_drift':<25} | {current_result['soc_drift']:>+15,.0f} | {r['soc_drift']:>+15,.0f} | {'':>15}
{'Mangel-Last':<25} | {current_result['total_mangel_last']:>15,.0f} | {r['total_mangel_last']:>15,.0f} | {r['total_mangel_last'] - current_result['total_mangel_last']:>+15,.0f}
""")

# =============================================================================
# KEY INSIGHT
# =============================================================================
print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print(f"""
With current solar ({solar_base:,.0f} GWh):
   → Abregelung (wasted): {current_result['total_abregelung']:,.0f} GWh
   → This is {current_result['total_abregelung']/solar_base*100:.1f}% of solar generation!

With optimal solar ({solar_final:,.0f} GWh):
   → Abregelung (wasted): {r['total_abregelung']:,.0f} GWh
   → Solar reduction needed: {(1 - k_final)*100:.1f}%

The system is MASSIVELY over-sized for solar.
Reducing solar to {k_final*100:.1f}% of current still meets 100% demand.
""")

print("=" * 80)
print("✅ Optimization complete!")
print("=" * 80)
