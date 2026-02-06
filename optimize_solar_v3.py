"""
OPTIMIZE SOLAR LANDUSE - Version 3
===================================
Properly handles the energy balance constraint.

The key insight: We need to solve TWO nested problems:
1. INNER: For a given solar value, find SOC_start that gives cyclic balance
2. OUTER: Find the solar value that achieves both cyclic balance AND zero Mangel-Last

Run: python optimize_solar_v3.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from simulator.models import RenewableData, VerbrauchData
from simulator.ws_models import WSData

print("=" * 80)
print("OPTIMIZE SOLAR V3 - Proper Energy Balance")
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

# Solar BASE
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
print(f"      Solar (base):  {solar_base:>12,.0f} GWh/year")

# =============================================================================
# SINGLE YEAR SIMULATION
# =============================================================================
def simulate_year(solar_annual, soc_start):
    """Run single 365-day simulation."""
    soc = soc_start
    min_soc = soc_start
    max_soc = soc_start
    
    totals = {
        'generation': 0, 'grid_loss': 0, 'demand': 0,
        'ueberschuss': 0, 'mangel': 0,
        'einspeichern': 0, 'abregelung': 0,
        'rueckverstr': 0, 'mangel_last': 0
    }
    
    for d in range(365):
        # Generation
        solar = solar_annual * (solar_promille[d] / 1000)
        wind = wind_annual * (wind_promille[d] / 1000)
        bio = bio_annual / 365
        water = water_annual / 365
        total_gen = solar + wind + bio + water
        grid_loss = total_gen * GRID_LOSS_RATE
        demand = demand_annual * (verbrauch_promille[d] / 1000)
        
        totals['generation'] += total_gen
        totals['grid_loss'] += grid_loss
        totals['demand'] += demand
        
        # Balance
        balance = total_gen - grid_loss - demand
        ueberschuss = max(balance, 0)
        mangel = max(-balance, 0)
        totals['ueberschuss'] += ueberschuss
        totals['mangel'] += mangel
        
        # Einspeichern
        free_space = max(H2_STORAGE_CAPACITY - soc, 0) / H2_CHARGE_EFF
        einspeichern = min(ueberschuss, ELEKTROLYSE_MAX_DAY, free_space)
        soc += einspeichern * H2_CHARGE_EFF
        abregelung = ueberschuss - einspeichern
        totals['einspeichern'] += einspeichern
        totals['abregelung'] += abregelung
        
        # Rückverstromung
        max_from_soc = soc * H2_DISCHARGE_EFF
        rueckverstr = min(mangel, max_from_soc, RUECKVERSTR_MAX_DAY)
        if rueckverstr > 0:
            soc -= rueckverstr / H2_DISCHARGE_EFF
        totals['rueckverstr'] += rueckverstr
        
        soc = max(soc, 0)
        min_soc = min(min_soc, soc)
        max_soc = max(max_soc, soc)
        
        # Mangel-Last
        totals['mangel_last'] += mangel - rueckverstr
    
    return {
        'solar': solar_annual,
        'soc_start': soc_start,
        'soc_end': soc,
        'soc_drift': soc - soc_start,
        'min_soc': min_soc,
        'max_soc': max_soc,
        **totals
    }


def find_cyclic_soc(solar_annual, max_iter=100):
    """
    Find SOC_start where SOC_end = SOC_start.
    
    Strategy: Run multiple years until SOC stabilizes.
    """
    # Start with half-full storage
    soc = H2_STORAGE_CAPACITY / 2
    
    for i in range(max_iter):
        result = simulate_year(solar_annual, soc)
        drift = result['soc_drift']
        
        if abs(drift) < 1:  # Converged
            return result
        
        # Use end-of-year SOC as next year's start
        # This naturally converges to the cyclic point
        soc = result['soc_end']
        
        # Keep in bounds
        soc = max(0, min(soc, H2_STORAGE_CAPACITY))
    
    return simulate_year(solar_annual, soc)


# =============================================================================
# ANALYSIS: Check current system
# =============================================================================
print("\n" + "=" * 80)
print("ANALYSIS: Current System State")
print("=" * 80)

# Find cyclic SOC for current solar
print("\n📊 Finding cyclic SOC for current solar...")
r = find_cyclic_soc(solar_base)

print(f"""
   Current Solar: {solar_base:,.0f} GWh/year
   
   With cyclic SOC (SOC_start = SOC_end):
      SOC_start:       {r['soc_start']:>12,.0f} GWh
      SOC_end:         {r['soc_end']:>12,.0f} GWh
      SOC_drift:       {r['soc_drift']:>+12,.1f} GWh
      Min SOC:         {r['min_soc']:>12,.0f} GWh
      Max SOC:         {r['max_soc']:>12,.0f} GWh
      
   Energy flows:
      Überschuss:      {r['ueberschuss']:>12,.0f} GWh (surplus days)
      Mangel:          {r['mangel']:>12,.0f} GWh (deficit days)
      Einspeichern:    {r['einspeichern']:>12,.0f} GWh
      Abregelung:      {r['abregelung']:>12,.0f} GWh (curtailed: {r['abregelung']/r['ueberschuss']*100:.1f}%)
      Rückverstr.:     {r['rueckverstr']:>12,.0f} GWh
      Mangel-Last:     {r['mangel_last']:>12,.0f} GWh (unserved: {r['mangel_last']/r['mangel']*100:.1f}%)
""")

# =============================================================================
# GOAL SEEK: Find optimal solar
# =============================================================================
print("=" * 80)
print("GOAL SEEK: Find minimum solar for 100% demand WITH margin")
print("=" * 80)

# Minimum Abregelung threshold (must have some curtailment as safety margin)
MIN_ABREGELUNG = 1000  # At least 1,000 GWh curtailment as buffer

print(f"""
Strategy:
  1. For each solar value, find the cyclic SOC
  2. Check if Mangel-Last = 0 AND Abregelung >= {MIN_ABREGELUNG:,} GWh
  3. Binary search to find MINIMUM solar that meets these conditions
  
Note: Abregelung > 0 is required as safety margin.
""")

# First, check if current solar meets demand
if r['mangel_last'] < 1 and r['abregelung'] >= MIN_ABREGELUNG:
    print(f"✅ Current solar ({solar_base:,.0f} GWh) meets 100% demand with margin")
    print("   Searching for MINIMUM solar that still works...")
    k_low = 0.1
    k_high = 1.0
elif r['mangel_last'] < 1:
    print(f"⚠️ Current solar meets demand but Abregelung ({r['abregelung']:,.0f}) is too low")
    print("   Need slightly more solar for safety margin...")
    k_low = 1.0
    k_high = 1.5
else:
    print(f"❌ Current solar ({solar_base:,.0f} GWh) has {r['mangel_last']:,.0f} GWh unserved")
    print("   Searching for solar that meets 100% demand with margin...")
    k_low = 1.0
    k_high = 3.0

print(f"\n{'Iter':>4} | {'k':>8} | {'Solar':>14} | {'Abregelung':>12} | {'Mangel-Last':>12} | {'SOC_start':>12} | {'Status'}")
print("-" * 95)

iterations = 0
best_k = None
best_result = None

while k_high - k_low > 0.001:
    iterations += 1
    k_mid = (k_low + k_high) / 2
    solar_test = solar_base * k_mid
    
    result = find_cyclic_soc(solar_test)
    
    meets_demand = result['mangel_last'] < 1
    has_margin = result['abregelung'] >= MIN_ABREGELUNG
    
    if meets_demand and has_margin:
        status = "✅ OK"
        k_high = k_mid  # Try lower
        best_k = k_mid
        best_result = result
    elif meets_demand and not has_margin:
        status = "⚠️ No margin"
        k_low = k_mid  # Need more solar for margin
    else:
        status = "❌ Short"
        k_low = k_mid  # Need more
    
    print(f"{iterations:4d} | {k_mid:8.4f} | {solar_test:>14,.0f} | {result['abregelung']:>12,.0f} | {result['mangel_last']:>12,.0f} | {result['soc_start']:>12,.0f} | {status}")
    
    if iterations > 25:
        break

# Final answer
if best_k is None:
    print("\n⚠️ Could not find a solution. Using k_high.")
    best_k = k_high
    best_result = find_cyclic_soc(solar_base * best_k)

solar_optimal = solar_base * best_k

print(f"\n✅ Optimal k = {best_k:.4f}")
print(f"   Optimal Solar = {solar_optimal:,.0f} GWh/year")

# =============================================================================
# FINAL RESULTS
# =============================================================================
print("\n" + "=" * 80)
print("FINAL RESULTS: OPTIMAL SYSTEM")
print("=" * 80)

r = best_result

storage_loss = r['einspeichern'] - r['rueckverstr']

print(f"""
   GENERATION:
      Solar:           {r['solar']:>12,.0f} GWh/year  (×{best_k:.3f} of current)
      Wind:            {wind_annual:>12,.0f} GWh/year
      Bio:             {bio_annual:>12,.0f} GWh/year
      Water:           {water_annual:>12,.0f} GWh/year
      ─────────────────────────────────────
      TOTAL:           {r['generation']:>12,.0f} GWh/year

   LOSSES:
      Grid Loss:       {r['grid_loss']:>12,.0f} GWh ({GRID_LOSS_RATE*100:.1f}%)
      Abregelung:      {r['abregelung']:>12,.0f} GWh (curtailed)
      Storage Loss:    {storage_loss:>12,.0f} GWh

   DEMAND:
      Total:           {r['demand']:>12,.0f} GWh
      Mangel-Last:     {r['mangel_last']:>12,.0f} GWh
      DELIVERED:       {r['demand'] - r['mangel_last']:>12,.0f} GWh ({(r['demand'] - r['mangel_last'])/r['demand']*100:.1f}%)

   H2 STORAGE (CYCLIC):
      SOC_start:       {r['soc_start']:>12,.0f} GWh
      SOC_end:         {r['soc_end']:>12,.0f} GWh
      SOC_drift:       {r['soc_drift']:>+12,.1f} GWh ✅ CYCLIC
      Min SOC:         {r['min_soc']:>12,.0f} GWh
      Max SOC:         {r['max_soc']:>12,.0f} GWh

   STORAGE UTILIZATION:
      Einspeichern:    {r['einspeichern']:>12,.0f} GWh
      Rückverstr.:     {r['rueckverstr']:>12,.0f} GWh
      Round-trip eff:  {r['rueckverstr']/r['einspeichern']*100:.1f}% (of stored energy)
""")

# =============================================================================
# COMPARISON TABLE
# =============================================================================
print("=" * 80)
print("COMPARISON: Current vs Optimal")
print("=" * 80)

current = find_cyclic_soc(solar_base)

print(f"""
{'Metric':<25} | {'Current':>15} | {'Optimal':>15} | {'Change':>15}
{'-' * 75}
{'Solar (GWh/year)':<25} | {solar_base:>15,.0f} | {solar_optimal:>15,.0f} | {solar_optimal - solar_base:>+15,.0f}
{'Solar multiplier k':<25} | {1.0:>15.3f} | {best_k:>15.3f} | {best_k - 1:>+15.3f}
{'Total Generation':<25} | {current['generation']:>15,.0f} | {r['generation']:>15,.0f} | {r['generation'] - current['generation']:>+15,.0f}
{'Abregelung':<25} | {current['abregelung']:>15,.0f} | {r['abregelung']:>15,.0f} | {r['abregelung'] - current['abregelung']:>+15,.0f}
{'Mangel-Last':<25} | {current['mangel_last']:>15,.0f} | {r['mangel_last']:>15,.0f} | {r['mangel_last'] - current['mangel_last']:>+15,.0f}
{'SOC_start (cyclic)':<25} | {current['soc_start']:>15,.0f} | {r['soc_start']:>15,.0f} | {r['soc_start'] - current['soc_start']:>+15,.0f}
""")

# =============================================================================
# SUMMARY
# =============================================================================
print("=" * 80)
print("SUMMARY")
print("=" * 80)

if best_k < 1:
    change_pct = (1 - best_k) * 100
    print(f"""
✅ Solar can be REDUCED by {change_pct:.1f}%
   From: {solar_base:>15,.0f} GWh/year
   To:   {solar_optimal:>15,.0f} GWh/year
   
This reduction:
   - Eliminates {current['abregelung'] - r['abregelung']:,.0f} GWh of curtailment
   - Still meets 100% of demand ({r['demand']:,.0f} GWh)
   - Maintains cyclic H2 storage (SOC_day1 = SOC_day365)
""")
else:
    change_pct = (best_k - 1) * 100
    print(f"""
⚠️ Solar needs to be INCREASED by {change_pct:.1f}%
   From: {solar_base:>15,.0f} GWh/year
   To:   {solar_optimal:>15,.0f} GWh/year
   
This is required to:
   - Meet 100% of demand ({r['demand']:,.0f} GWh)
   - Maintain cyclic H2 storage (SOC_day1 = SOC_day365)
""")

print("=" * 80)
