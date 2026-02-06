"""
OPTIMIZE SOLAR LANDUSE
======================
Finds the optimal solar landuse value that:
1. Meets 100% demand (Mangel-Last = 0)
2. Minimizes curtailment (Abregelung)  
3. Ensures SOC balance (SOC_day1 ≈ SOC_day365)

Uses binary search to find the minimum solar that still meets demand.

Run: python optimize_solar.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from simulator.models import RenewableData, VerbrauchData
from simulator.ws_models import WSData

print("=" * 70)
print("OPTIMIZE SOLAR LANDUSE - Find Minimum Solar for 100% Demand")
print("=" * 70)

# =============================================================================
# SYSTEM PARAMETERS
# =============================================================================
GRID_LOSS_RATE = 0.092
ELEKTROLYSE_POWER_GW = 194
ELEKTROLYSE_MAX_DAY = ELEKTROLYSE_POWER_GW * 24
H2_CHARGE_EFF = 0.65
H2_DISCHARGE_EFF = 0.585
RUECKVERSTR_POWER_GW = 261
RUECKVERSTR_MAX_DAY = RUECKVERSTR_POWER_GW * 24
H2_STORAGE_CAPACITY = 241_727

# =============================================================================
# LOAD DATA
# =============================================================================
print("\n📊 Loading data...")

wind_annual = RenewableData.objects.get(code='9.1.1').target_value or 0
bio_annual = RenewableData.objects.get(code='9.1.4').target_value or 0
water_annual = RenewableData.objects.get(code='9.1.3').target_value or 0
demand_annual = VerbrauchData.objects.get(code='7').ziel or 0
current_solar = RenewableData.objects.get(code='9.1.2').target_value or 0

ws_entries = list(WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr'))
solar_promille = [ws.solar_promille or 0 for ws in ws_entries]
wind_promille = [ws.wind_promille or 0 for ws in ws_entries]
verbrauch_promille = [ws.verbrauch_promille or 0 for ws in ws_entries]

print(f"   Current Solar: {current_solar:,.0f} GWh/year")
print(f"   Wind: {wind_annual:,.0f} GWh/year")
print(f"   Demand: {demand_annual:,.0f} GWh/year")

# =============================================================================
# SIMULATION FUNCTION
# =============================================================================
def simulate_year(solar_annual, soc_start, find_balanced_soc=False):
    """
    Run 365-day simulation with given solar value.
    
    If find_balanced_soc=True, iterates to find SOC_start where SOC_end = SOC_start.
    
    Returns dict with results.
    """
    soc_init = soc_start
    
    # If we need to find balanced SOC, iterate
    max_iterations = 50 if find_balanced_soc else 1
    
    for iteration in range(max_iterations):
        soc = soc_init
        
        total_ueberschuss = 0
        total_mangel = 0
        total_einspeichern = 0
        total_abregelung = 0
        total_rueckverstr = 0
        total_mangel_last = 0
        total_demand = 0
        
        for d in range(365):
            # Generation
            solar = solar_annual * (solar_promille[d] / 1000)
            wind = wind_annual * (wind_promille[d] / 1000)
            bio = bio_annual / 365
            water = water_annual / 365
            total_gen = solar + wind + bio + water
            grid_loss = total_gen * GRID_LOSS_RATE
            demand = demand_annual * (verbrauch_promille[d] / 1000)
            total_demand += demand
            
            # Balance
            balance = total_gen - grid_loss - demand
            ueberschuss = max(balance, 0)
            mangel = max(-balance, 0)
            total_ueberschuss += ueberschuss
            total_mangel += mangel
            
            # Einspeichern
            free_h2_space = H2_STORAGE_CAPACITY - soc
            free_h2_space_electric = max(free_h2_space / H2_CHARGE_EFF, 0)
            einspeichern_strom = min(ueberschuss, ELEKTROLYSE_MAX_DAY, free_h2_space_electric)
            einspeichern_h2 = einspeichern_strom * H2_CHARGE_EFF
            soc += einspeichern_h2
            
            # Abregelung
            abregelung = ueberschuss - einspeichern_strom
            total_einspeichern += einspeichern_strom
            total_abregelung += abregelung
            
            # Rückverstromung
            max_from_soc = soc * H2_DISCHARGE_EFF
            rueckverstr_strom = min(mangel, max_from_soc, RUECKVERSTR_MAX_DAY)
            if rueckverstr_strom > 0:
                rueckverstr_h2 = rueckverstr_strom / H2_DISCHARGE_EFF
                soc -= rueckverstr_h2
            total_rueckverstr += rueckverstr_strom
            
            soc = max(soc, 0)
            
            # Mangel-Last
            mangel_last = mangel - rueckverstr_strom
            total_mangel_last += mangel_last
        
        soc_end = soc
        soc_drift = soc_end - soc_init
        
        if not find_balanced_soc:
            break
            
        # Update soc_init for next iteration to achieve balance
        if abs(soc_drift) < 10:  # Close enough (< 10 GWh drift)
            break
        # Adjust: if SOC drifts up, start lower. If drifts down, start higher.
        soc_init = soc_init - soc_drift * 0.7
        soc_init = max(0, min(soc_init, H2_STORAGE_CAPACITY))
    
    return {
        'solar_annual': solar_annual,
        'total_demand': total_demand,
        'total_ueberschuss': total_ueberschuss,
        'total_mangel': total_mangel,
        'total_einspeichern': total_einspeichern,
        'total_abregelung': total_abregelung,
        'total_rueckverstr': total_rueckverstr,
        'total_mangel_last': total_mangel_last,
        'soc_start': soc_init,
        'soc_end': soc_end,
        'soc_drift': soc_end - soc_init,
        'meets_demand': total_mangel_last < 1,  # < 1 GWh is essentially 0
        'soc_balanced': abs(soc_end - soc_init) < 100,  # SOC is balanced
    }

# =============================================================================
# BINARY SEARCH FOR OPTIMAL SOLAR (with SOC balance)
# =============================================================================
print("\n📊 Finding optimal solar value using binary search...")
print("   (Each iteration finds balanced SOC where SOC_start = SOC_end)")
print("-" * 70)

# Start with a range
solar_low = 100_000   # 100 TWh - definitely too low
solar_high = current_solar  # Current value - definitely works (but may be too high)

# First check if current solar actually meets demand with balanced SOC
result = simulate_year(current_solar, H2_STORAGE_CAPACITY / 2, find_balanced_soc=True)
if not result['meets_demand']:
    print(f"   ⚠️ Current solar ({current_solar:,.0f} GWh) doesn't meet 100% demand!")
    print(f"   Mangel-Last = {result['total_mangel_last']:,.0f} GWh")
    print("   Cannot optimize - need MORE solar, not less.")
    sys.exit(1)

print(f"   Current solar meets demand. Searching for minimum...")
print(f"   Range: {solar_low:,.0f} - {solar_high:,.0f} GWh\n")

# Binary search
iterations = 0
while solar_high - solar_low > 1000:  # Stop when range is < 1000 GWh
    iterations += 1
    solar_mid = (solar_low + solar_high) / 2
    
    # Run simulation with SOC balancing
    result = simulate_year(solar_mid, H2_STORAGE_CAPACITY / 2, find_balanced_soc=True)
    
    status = "✅" if result['meets_demand'] else "❌"
    print(f"   Iter {iterations:2d}: Solar = {solar_mid:>12,.0f} GWh | "
          f"Mangel-Last = {result['total_mangel_last']:>10,.0f} GWh | "
          f"Abregelung = {result['total_abregelung']:>10,.0f} GWh | "
          f"SOC_drift = {result['soc_drift']:>+8,.0f} | {status}")
    
    if result['meets_demand']:
        solar_high = solar_mid  # Can reduce solar further
    else:
        solar_low = solar_mid   # Need more solar
    
    if iterations > 30:  # Safety limit
        break

# Final result
optimal_solar = solar_high  # Use the higher value to ensure 100% demand
print(f"\n   ✅ Optimal solar found: {optimal_solar:,.0f} GWh")

# =============================================================================
# RUN FINAL SIMULATION WITH OPTIMAL SOLAR
# =============================================================================
print("\n" + "=" * 70)
print("FINAL RESULTS WITH OPTIMAL SOLAR")
print("=" * 70)

# Find balanced SOC
print("\n📊 Finding balanced SOC (SOC_start = SOC_end)...")
result = simulate_year(optimal_solar, H2_STORAGE_CAPACITY / 2, find_balanced_soc=True)

print(f"\n   GENERATION:")
print(f"      Solar:         {optimal_solar:>12,.0f} GWh/year")
print(f"      Wind:          {wind_annual:>12,.0f} GWh/year")
print(f"      Bio + Water:   {bio_annual + water_annual:>12,.0f} GWh/year")
print(f"      TOTAL:         {optimal_solar + wind_annual + bio_annual + water_annual:>12,.0f} GWh/year")
print()
print(f"   DEMAND:")
print(f"      Total:         {result['total_demand']:>12,.0f} GWh")
print()
print(f"   BALANCE:")
print(f"      Überschuss:    {result['total_ueberschuss']:>12,.0f} GWh")
print(f"      Mangel:        {result['total_mangel']:>12,.0f} GWh")
print()
print(f"   H2 STORAGE:")
print(f"      Einspeichern:  {result['total_einspeichern']:>12,.0f} GWh")
print(f"      Abregelung:    {result['total_abregelung']:>12,.0f} GWh ({result['total_abregelung']/max(result['total_ueberschuss'],1)*100:.1f}%)")
print(f"      Rückverstr.:   {result['total_rueckverstr']:>12,.0f} GWh")
print()
print(f"   SOC:")
print(f"      SOC_start:     {result['soc_start']:>12,.0f} GWh")
print(f"      SOC_end:       {result['soc_end']:>12,.0f} GWh")
print(f"      SOC_drift:     {result['soc_drift']:>+12,.0f} GWh")
if abs(result['soc_drift']) < 100:
    print(f"      ✅ SOC is BALANCED!")
print()
print(f"   RESULT:")
print(f"      Mangel-Last:   {result['total_mangel_last']:>12,.0f} GWh")
print(f"      Delivered:     {result['total_demand'] - result['total_mangel_last']:>12,.0f} GWh ({(result['total_demand'] - result['total_mangel_last'])/result['total_demand']*100:.1f}%)")

# =============================================================================
# COMPARISON
# =============================================================================
print("\n" + "=" * 70)
print("COMPARISON: Current vs Optimal Solar")
print("=" * 70)

# Current
result_current = simulate_year(current_solar, 219_322)

print(f"\n{'Metric':<25} | {'Current':>15} | {'Optimal':>15} | {'Diff':>15}")
print("-" * 75)
print(f"{'Solar (GWh)':<25} | {current_solar:>15,.0f} | {optimal_solar:>15,.0f} | {optimal_solar - current_solar:>+15,.0f}")
print(f"{'Abregelung (GWh)':<25} | {result_current['total_abregelung']:>15,.0f} | {result['total_abregelung']:>15,.0f} | {result['total_abregelung'] - result_current['total_abregelung']:>+15,.0f}")
print(f"{'Einspeichern (GWh)':<25} | {result_current['total_einspeichern']:>15,.0f} | {result['total_einspeichern']:>15,.0f} | {result['total_einspeichern'] - result_current['total_einspeichern']:>+15,.0f}")
print(f"{'Rückverstr. (GWh)':<25} | {result_current['total_rueckverstr']:>15,.0f} | {result['total_rueckverstr']:>15,.0f} | {result['total_rueckverstr'] - result_current['total_rueckverstr']:>+15,.0f}")
print(f"{'SOC drift (GWh)':<25} | {result_current['soc_drift']:>+15,.0f} | {result['soc_drift']:>+15,.0f} | {'':>15}")
print(f"{'Mangel-Last (GWh)':<25} | {result_current['total_mangel_last']:>15,.0f} | {result['total_mangel_last']:>15,.0f} | {result['total_mangel_last'] - result_current['total_mangel_last']:>+15,.0f}")

# =============================================================================
# CALCULATE REQUIRED LANDUSE
# =============================================================================
print("\n" + "=" * 70)
print("LANDUSE CALCULATION")
print("=" * 70)

# Get current solar landuse from database
solar_data = RenewableData.objects.get(code='9.1.2')
current_landuse = solar_data.landnutzung or 0  # km²

# Calculate the ratio
if current_solar > 0:
    solar_per_km2 = current_solar / current_landuse if current_landuse > 0 else 0
    optimal_landuse = optimal_solar / solar_per_km2 if solar_per_km2 > 0 else 0
    
    print(f"\n   Current Landuse:  {current_landuse:>12,.2f} km²")
    print(f"   Current Solar:    {current_solar:>12,.0f} GWh → {solar_per_km2:,.2f} GWh/km²")
    print(f"\n   Optimal Solar:    {optimal_solar:>12,.0f} GWh")
    print(f"   Optimal Landuse:  {optimal_landuse:>12,.2f} km² (reduction of {current_landuse - optimal_landuse:,.2f} km²)")
    print(f"   Reduction:        {(current_landuse - optimal_landuse) / current_landuse * 100:.1f}%")

print("\n" + "=" * 70)
print("✅ Optimization complete!")
print("=" * 70)
