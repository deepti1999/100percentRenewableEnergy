"""
TEST 365 DAYS - New Implementation with Goal Seek
==================================================
Clean implementation with new data and formulas.
Includes Goal Seek to balance Solar for storage equilibrium.

Run: python3 test_365days.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from simulator.models import VerbrauchData, RenewableData
from simulator.ws_models import WSData

# =============================================================================
# STEP 1: Read WS Data for 365 Days
# =============================================================================
print("=" * 70)
print("LOADING BASE DATA")
print("=" * 70)

ws_entries = list(WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr'))

# Create columns for 365 days
solar_promille = [ws.solar_promille or 0 for ws in ws_entries]
wind_promille = [ws.wind_promille or 0 for ws in ws_entries]
heizung_abwaerm_promille = [ws.heizung_abwaerm_promille or 0 for ws in ws_entries]
verbrauch_promille = [ws.verbrauch_promille or 0 for ws in ws_entries]

print(f"   Loaded {len(ws_entries)} days of WS data")

# =============================================================================
# STEP 2: Get Fixed Values from Database
# =============================================================================
# Verbrauch values
verbrauch_7 = VerbrauchData.objects.get(code='7')
verbrauch_7_ziel = verbrauch_7.ziel or 0
verbrauch_292 = VerbrauchData.objects.get(code='2.9.2')
verbrauch_24 = VerbrauchData.objects.get(code='2.4')
verbrauch_292_ziel = verbrauch_292.ziel or 0
verbrauch_24_ziel = verbrauch_24.ziel or 0

# Renewable values
r_911 = RenewableData.objects.get(code='9.1.1')
r_912 = RenewableData.objects.get(code='9.1.2')
r_913 = RenewableData.objects.get(code='9.1.3')
r_914 = RenewableData.objects.get(code='9.1.4')
r_92152 = RenewableData.objects.get(code='9.2.1.5.2')

ziel_911 = r_911.target_value or 0  # Wind (fixed)
ziel_912_original = r_912.target_value or 0  # Solar (variable)
ziel_913 = r_913.target_value or 0  # Sonst.
ziel_914 = r_914.target_value or 0  # Bio
ziel_92152 = r_92152.target_value or 0  # Subtraction

# Constants
GRID_LOSS_RATE = 0.092
annual_demand = verbrauch_7_ziel / (1 - GRID_LOSS_RATE)
raumw_korr_annual = verbrauch_292_ziel * (verbrauch_24_ziel / 100)

# Pre-calculate fixed daily values
stromverbrauch = [annual_demand * verbrauch_promille[d] / 1000 for d in range(365)]
davon_raumw_korr = [raumw_korr_annual * heizung_abwaerm_promille[d] / 365 for d in range(365)]
stromverbr_raumw_korr = [stromverbrauch[d] + davon_raumw_korr[d] for d in range(365)]

print(f"   Annual Demand: {annual_demand:,.0f} GWh")
print(f"   Original Solar (9.1.2): {ziel_912_original:,.0f} GWh")

# =============================================================================
# FUNCTION: Calculate all 365 days given a Solar value
# =============================================================================
def calculate_365_days(solar_value):
    """
    Calculate all columns for 365 days given a Solar value.
    Returns: (ladezust_brutto_day1, ladezust_brutto_day365, annual_electricity, results_dict)
    """
    ziel_912 = solar_value
    
    # Renewable percentage
    sum_renewable = ziel_911 + ziel_912 + ziel_913
    value = sum_renewable - ziel_92152
    pct = (value / sum_renewable) if sum_renewable > 0 else 0
    
    # Daily generation
    solar_strom = [ziel_912 * pct * solar_promille[d] / 1000 for d in range(365)]
    wind_strom = [ziel_911 * pct * wind_promille[d] / 1000 for d in range(365)]
    sonst_kraftw_daily = ziel_913 * pct / 365
    sonst_kraftw = [sonst_kraftw_daily for _ in range(365)]
    
    # Wind+Solar+konstant
    wind_solar_konstant = [solar_strom[d] + wind_strom[d] + sonst_kraftw[d] for d in range(365)]
    
    # Direktverbr. Strom
    direktverbr_strom = [min(wind_solar_konstant[d], stromverbr_raumw_korr[d]) for d in range(365)]
    
    # Überschuss Strom
    ueberschuss_strom = []
    for d in range(365):
        if direktverbr_strom[d] == stromverbr_raumw_korr[d]:
            ueberschuss_strom.append(wind_solar_konstant[d] - stromverbr_raumw_korr[d])
        else:
            ueberschuss_strom.append(0)
    
    # Einspeich.
    einspeich = []
    for d in range(365):
        if stromverbr_raumw_korr[d] > 0:
            ratio = ueberschuss_strom[d] / stromverbr_raumw_korr[d]
        else:
            ratio = 0
        if ratio <= 1:
            einspeich.append(ueberschuss_strom[d] * 0.65)
        else:
            einspeich.append(stromverbr_raumw_korr[d] * 1 * 0.65)
    
    # Abregelung
    abregelung = []
    for d in range(365):
        if stromverbr_raumw_korr[d] > 0:
            ratio = ueberschuss_strom[d] / stromverbr_raumw_korr[d]
        else:
            ratio = 0
        if ratio <= 1:
            abregelung.append(0)
        else:
            abregelung.append(ueberschuss_strom[d] - einspeich[d] / 0.65)
    
    # Mangel-Last
    mangel_last = [stromverbr_raumw_korr[d] - direktverbr_strom[d] for d in range(365)]
    
    # Brennstoff-Ausgleichs-Strom
    mangel_last_min_value = sum(stromverbr_raumw_korr) - sum(direktverbr_strom)
    if mangel_last_min_value > 0:
        brennstoff_factor = ziel_914 / mangel_last_min_value
    else:
        brennstoff_factor = 0
    brennstoff_ausgleich = [brennstoff_factor * mangel_last[d] for d in range(365)]
    
    # Speicher-Ausgl.-Strom
    speicher_ausgl_strom = [mangel_last[d] - brennstoff_ausgleich[d] for d in range(365)]
    
    # Ausspeich. Rückverstr.
    ausspeich_rueckverstr = [speicher_ausgl_strom[d] / 0.585 for d in range(365)]
    
    # Ausspeich. Gas (constant 0)
    ausspeich_gas = [0 for _ in range(365)]
    
    # Ladezust. Brutto
    ladezust_brutto = []
    for d in range(365):
        if d == 0:
            prev = 0
        else:
            prev = ladezust_brutto[d - 1]
        ladezust_brutto.append(prev + einspeich[d] - ausspeich_rueckverstr[d] - ausspeich_gas[d])
    
    # Annual Electricity
    base_electricity = ziel_911 + ziel_912 + ziel_913 - ziel_92152
    einspeich_adjustment = sum(einspeich) / 0.65
    abregelung_total = sum(abregelung)
    ausspeich_rueckverstr_adjustment = sum(ausspeich_rueckverstr) * 0.585
    annual_electricity = base_electricity - einspeich_adjustment - abregelung_total + ziel_914 + ausspeich_rueckverstr_adjustment
    
    return {
        'ladezust_day1': ladezust_brutto[0],
        'ladezust_day365': ladezust_brutto[364],
        'annual_electricity': annual_electricity,
        'storage_drift': ladezust_brutto[364] - ladezust_brutto[0],
        'einspeich_sum': sum(einspeich),
        'ausspeich_sum': sum(ausspeich_rueckverstr),
        'abregelung_sum': sum(abregelung),
        'solar_strom_sum': sum(solar_strom),
        'wind_strom_sum': sum(wind_strom),
        'ladezust_brutto': ladezust_brutto,
        'renewable_pct': pct * 100
    }

# =============================================================================
# STEP 3: Goal Seek - Find optimal Solar value
# =============================================================================
print("\n" + "=" * 70)
print("GOAL SEEK: Finding optimal Solar value")
print("=" * 70)

# Binary search to find Solar value where storage_drift ≈ 0
solar_low = ziel_912_original * 0.5   # Start with 50% of original
solar_high = ziel_912_original * 1.5  # Up to 150% of original
tolerance = 0.1  # GWh tolerance for storage drift
max_iterations = 50

print(f"\n   Target: Ladezust.Brutto Day365 = Day1 (storage drift ≈ 0)")
print(f"   Search range: {solar_low:,.0f} - {solar_high:,.0f} GWh")
print(f"   Tolerance: {tolerance} GWh")
print("-" * 60)

# First check the current value
current_result = calculate_365_days(ziel_912_original)
print(f"\n   Original Solar: {ziel_912_original:,.0f} GWh")
print(f"   Storage Drift: {current_result['storage_drift']:,.2f} GWh")

# Binary search
for iteration in range(max_iterations):
    solar_mid = (solar_low + solar_high) / 2
    result = calculate_365_days(solar_mid)
    drift = result['storage_drift']
    
    if abs(drift) < tolerance:
        print(f"\n   ✅ FOUND! Iteration {iteration + 1}")
        break
    
    # If drift > 0 (accumulating), decrease Solar
    # If drift < 0 (depleting), increase Solar
    if drift > 0:
        solar_high = solar_mid
    else:
        solar_low = solar_mid
    
    if iteration % 10 == 0:
        print(f"   Iteration {iteration + 1}: Solar = {solar_mid:,.0f}, Drift = {drift:,.2f}")

optimal_solar = solar_mid
optimal_result = calculate_365_days(optimal_solar)

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

print(f"\n   Original Solar (9.1.2):    {ziel_912_original:>14,.0f} GWh")
print(f"   Optimal Solar:             {optimal_solar:>14,.0f} GWh")
print(f"   Change:                    {optimal_solar - ziel_912_original:>+14,.0f} GWh ({((optimal_solar/ziel_912_original)-1)*100:+.2f}%)")

print(f"\n   Storage Balance:")
print(f"   Ladezust. Brutto Day 1:    {optimal_result['ladezust_day1']:>14,.2f} GWh")
print(f"   Ladezust. Brutto Day 365:  {optimal_result['ladezust_day365']:>14,.2f} GWh")
print(f"   Storage Drift:             {optimal_result['storage_drift']:>14,.2f} GWh")

print(f"\n   Annual Values:")
print(f"   Annual Electricity:        {optimal_result['annual_electricity']:>14,.0f} GWh")
print(f"   Annual Demand:             {annual_demand:>14,.0f} GWh")
print(f"   Difference:                {optimal_result['annual_electricity'] - annual_demand:>14,.0f} GWh")

print(f"\n   Generation (with optimal Solar):")
print(f"   Solar Strom Sum:           {optimal_result['solar_strom_sum']:>14,.0f} GWh")
print(f"   Wind Strom Sum:            {optimal_result['wind_strom_sum']:>14,.0f} GWh")
print(f"   Renewable Percentage:      {optimal_result['renewable_pct']:>14.2f} %")

print(f"\n   Storage Flows:")
print(f"   Einspeich. Sum:            {optimal_result['einspeich_sum']:>14,.0f} GWh")
print(f"   Ausspeich.Rück Sum:        {optimal_result['ausspeich_sum']:>14,.0f} GWh")
print(f"   Abregelung Sum:            {optimal_result['abregelung_sum']:>14,.0f} GWh")

print("\n" + "=" * 70)
print("✅ Goal Seek Complete!")
print("=" * 70)
