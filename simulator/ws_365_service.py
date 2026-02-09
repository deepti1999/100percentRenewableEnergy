"""
WS 365 Days Service
====================
Backend service for 365-day energy simulation with Goal Seek.
Provides real-time recalculation when inputs change.
"""

import math
import os
import time

from .models import VerbrauchData, RenewableData
from .ws_models import WSData
from typing import Optional


# Constants
GRID_LOSS_RATE = 0.092
ELECTROLYSIS_EFFICIENCY = 0.65
RUECKVERSTROEMUNG_EFFICIENCY = 0.585
FIXED_82_TARGET = 12000.0


def _validate_required_landuse(required_landuse: float, parent_target_ha: Optional[float], code: str) -> float:
    """
    Guard against corrupted/overflow land-use targets.
    """
    value = float(required_landuse or 0.0)
    if not math.isfinite(value):
        raise ValueError(f"{code} required landuse is not finite: {required_landuse}")
    if value < 0:
        raise ValueError(f"{code} required landuse is negative: {value}")
    if parent_target_ha and parent_target_ha > 0:
        # Hard safety cap: anything above 100x parent area is almost certainly invalid input propagation.
        max_allowed = float(parent_target_ha) * 100.0
        if value > max_allowed:
            raise ValueError(
                f"{code} required landuse too large ({value:,.2f} ha), max allowed {max_allowed:,.2f} ha"
            )
    return value


def get_ws_base_data():
    """Load WS data for 365 days."""
    ws_entries = list(WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr'))
    
    return {
        'solar_promille': [ws.solar_promille or 0 for ws in ws_entries],
        'wind_promille': [ws.wind_promille or 0 for ws in ws_entries],
        'heizung_abwaerm_promille': [ws.heizung_abwaerm_promille or 0 for ws in ws_entries],
        'verbrauch_promille': [ws.verbrauch_promille or 0 for ws in ws_entries],
    }


def get_fixed_values():
    """Get fixed values from database."""
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
    
    return {
        'verbrauch_7_ziel': verbrauch_7_ziel,
        'verbrauch_292_ziel': verbrauch_292_ziel,
        'verbrauch_24_ziel': verbrauch_24_ziel,
        'ziel_911': r_911.target_value or 0,  # Wind (fixed)
        'ziel_912': r_912.target_value or 0,  # Solar (variable)
        'ziel_913': r_913.target_value or 0,  # Sonst.
        'ziel_914': r_914.target_value or 0,  # Bio
        'ziel_92152': r_92152.target_value or 0,  # Subtraction
    }


def calculate_365_days(solar_value, ws_data, fixed_values, wind_value=None):
    """
    Calculate all columns for 365 days given a Solar value.
    
    Args:
        solar_value: The solar generation value in GWh
        ws_data: Dictionary with promille arrays (from get_ws_base_data)
        fixed_values: Dictionary with fixed values (from get_fixed_values)
        wind_value: Optional wind override in GWh (defaults to fixed ziel_911)
    
    Returns:
        Dictionary with all results and daily data
    """
    solar_promille = ws_data['solar_promille']
    wind_promille = ws_data['wind_promille']
    heizung_abwaerm_promille = ws_data['heizung_abwaerm_promille']
    verbrauch_promille = ws_data['verbrauch_promille']
    
    ziel_911 = wind_value if wind_value is not None else fixed_values['ziel_911']
    ziel_912 = solar_value
    ziel_913 = fixed_values['ziel_913']
    ziel_914 = fixed_values['ziel_914']
    ziel_92152 = fixed_values['ziel_92152']
    
    annual_demand = fixed_values['verbrauch_7_ziel'] / (1 - GRID_LOSS_RATE)
    raumw_korr_annual = fixed_values['verbrauch_292_ziel'] * (fixed_values['verbrauch_24_ziel'] / 100)
    
    # Pre-calculate fixed daily values
    stromverbrauch = [annual_demand * verbrauch_promille[d] / 1000 for d in range(365)]
    davon_raumw_korr = [raumw_korr_annual * heizung_abwaerm_promille[d] / 365 for d in range(365)]
    stromverbr_raumw_korr = [stromverbrauch[d] + davon_raumw_korr[d] for d in range(365)]
    
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
            einspeich.append(ueberschuss_strom[d] * ELECTROLYSIS_EFFICIENCY)
        else:
            einspeich.append(stromverbr_raumw_korr[d] * 1 * ELECTROLYSIS_EFFICIENCY)
    
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
            abregelung.append(ueberschuss_strom[d] - einspeich[d] / ELECTROLYSIS_EFFICIENCY)
    
    # Mangel-Last
    mangel_last = [stromverbr_raumw_korr[d] - direktverbr_strom[d] for d in range(365)]
    
    # Brennstoff-Ausgleichs-Strom
    mangel_last_total = sum(stromverbr_raumw_korr) - sum(direktverbr_strom)
    if mangel_last_total > 0:
        brennstoff_factor = ziel_914 / mangel_last_total
    else:
        brennstoff_factor = 0
    brennstoff_ausgleich = [brennstoff_factor * mangel_last[d] for d in range(365)]
    
    # Speicher-Ausgl.-Strom
    speicher_ausgl_strom = [mangel_last[d] - brennstoff_ausgleich[d] for d in range(365)]
    
    # Ausspeich. Rückverstr.
    ausspeich_rueckverstr = [speicher_ausgl_strom[d] / RUECKVERSTROEMUNG_EFFICIENCY for d in range(365)]
    
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
    einspeich_adjustment = sum(einspeich) / ELECTROLYSIS_EFFICIENCY
    abregelung_total = sum(abregelung)
    ausspeich_rueckverstr_adjustment = sum(ausspeich_rueckverstr) * RUECKVERSTROEMUNG_EFFICIENCY
    annual_electricity = base_electricity - einspeich_adjustment - abregelung_total + ziel_914 + ausspeich_rueckverstr_adjustment
    
    # Build daily data for frontend
    daily_data = []
    for d in range(365):
        daily_data.append({
            'day': d + 1,
            'solar_promille': solar_promille[d],
            'wind_promille': wind_promille[d],
            'heizung_abwaerm_promille': heizung_abwaerm_promille[d],
            'verbrauch_promille': verbrauch_promille[d],
            'stromverbrauch': round(stromverbrauch[d], 2),
            'davon_raumw_korr': round(davon_raumw_korr[d], 2),
            'stromverbr_raumw_korr': round(stromverbr_raumw_korr[d], 2),
            'solar_strom': round(solar_strom[d], 2),
            'wind_strom': round(wind_strom[d], 2),
            'sonst_kraftw': round(sonst_kraftw[d], 2),
            'wind_solar_konstant': round(wind_solar_konstant[d], 2),
            'direktverbr_strom': round(direktverbr_strom[d], 2),
            'ueberschuss_strom': round(ueberschuss_strom[d], 2),
            'einspeich': round(einspeich[d], 2),
            'abregelung': round(abregelung[d], 2),
            'mangel_last': round(mangel_last[d], 2),
            'brennstoff_ausgleich': round(brennstoff_ausgleich[d], 2),
            'speicher_ausgl_strom': round(speicher_ausgl_strom[d], 2),
            'ausspeich_rueckverstr': round(ausspeich_rueckverstr[d], 2),
            'ausspeich_gas': round(ausspeich_gas[d], 2),
            'ladezust_brutto': round(ladezust_brutto[d], 2),
        })
    
    return {
        'ladezust_day1': ladezust_brutto[0],
        'ladezust_day365': ladezust_brutto[364],
        'annual_electricity': annual_electricity,
        'annual_demand': annual_demand,
        'storage_drift': ladezust_brutto[364] - ladezust_brutto[0],
        'einspeich_sum': sum(einspeich),
        'ausspeich_sum': sum(ausspeich_rueckverstr),
        'abregelung_sum': sum(abregelung),
        'ueberschuss_sum': sum(ueberschuss_strom),
        'solar_strom_sum': sum(solar_strom),
        'wind_strom_sum': sum(wind_strom),
        'renewable_pct': pct * 100,
        'daily_data': daily_data,
    }


def goal_seek_optimal_solar(ws_data, fixed_values, tolerance=0.1, max_iterations=50):
    """
    Find optimal Solar value where storage_drift ≈ 0 (Day 365 = Day 1).
    
    Args:
        ws_data: Dictionary with promille arrays
        fixed_values: Dictionary with fixed values
        tolerance: Acceptable storage drift in GWh
        max_iterations: Maximum binary search iterations
    
    Returns:
        Dictionary with optimal solar value and results
    """
    original_solar = fixed_values['ziel_912']
    solar_low = original_solar * 0.5
    solar_high = original_solar * 1.5
    
    for iteration in range(max_iterations):
        solar_mid = (solar_low + solar_high) / 2
        result = calculate_365_days(solar_mid, ws_data, fixed_values)
        drift = result['storage_drift']
        
        if abs(drift) < tolerance:
            break
        
        # If drift > 0 (accumulating), decrease Solar
        # If drift < 0 (depleting), increase Solar
        if drift > 0:
            solar_high = solar_mid
        else:
            solar_low = solar_mid
    
    optimal_result = calculate_365_days(solar_mid, ws_data, fixed_values)
    
    return {
        'original_solar': original_solar,
        'optimal_solar': solar_mid,
        'solar_change': solar_mid - original_solar,
        'solar_change_pct': ((solar_mid / original_solar) - 1) * 100 if original_solar > 0 else 0,
        'iterations': iteration + 1,
        'result': optimal_result,
    }


def goal_seek_optimal_wind(ws_data, fixed_values, tolerance=0.1, max_iterations=50):
    """
    Find optimal Wind value where storage_drift ≈ 0 (Day 365 = Day 1),
    keeping Solar fixed.
    """
    original_wind = max(0.0, float(fixed_values.get('ziel_911') or 0.0))

    def _evaluate(wind_candidate):
        result = calculate_365_days(
            fixed_values['ziel_912'],
            ws_data,
            fixed_values,
            wind_value=wind_candidate
        )
        return float(result['storage_drift']), result

    # Robust bracket search: expand bounds until drift sign changes.
    base_wind = max(original_wind, 1.0)
    wind_low = max(0.0, base_wind * 0.5)
    wind_high = max(base_wind * 1.5, wind_low + 1.0)

    drift_low, result_low = _evaluate(wind_low)
    drift_high, result_high = _evaluate(wind_high)

    expansion_steps = 0
    max_expansion_steps = 12
    while drift_low * drift_high > 0 and expansion_steps < max_expansion_steps:
        expansion_steps += 1

        if drift_low < 0 and drift_high < 0:
            # Need more Wind to move drift upward through zero.
            wind_low, drift_low, result_low = wind_high, drift_high, result_high
            wind_high = max(wind_high * 1.7, wind_high + 1.0)
            drift_high, result_high = _evaluate(wind_high)
        elif drift_low > 0 and drift_high > 0:
            # Need less Wind to move drift downward through zero.
            wind_high, drift_high, result_high = wind_low, drift_low, result_low
            if wind_low <= 0:
                break
            wind_low = max(0.0, wind_low * 0.3)
            drift_low, result_low = _evaluate(wind_low)
        else:
            break

    # If no sign change exists in feasible range, return best endpoint.
    if drift_low * drift_high > 0:
        if abs(drift_low) <= abs(drift_high):
            optimal_wind, optimal_result = wind_low, result_low
        else:
            optimal_wind, optimal_result = wind_high, result_high
        return {
            'original_wind': original_wind,
            'optimal_wind': optimal_wind,
            'wind_change': optimal_wind - original_wind,
            'wind_change_pct': ((optimal_wind / original_wind) - 1) * 100 if original_wind > 0 else 0,
            'iterations': expansion_steps + 1,
            'result': optimal_result,
        }

    # Standard bisection within sign-changing bracket.
    wind_mid = (wind_low + wind_high) / 2.0
    optimal_result = result_low
    bisection_iterations = 0

    for iteration in range(max_iterations):
        bisection_iterations = iteration + 1
        wind_mid = (wind_low + wind_high) / 2.0
        drift_mid, result_mid = _evaluate(wind_mid)
        optimal_result = result_mid

        if abs(drift_mid) < tolerance:
            break

        if drift_low * drift_mid <= 0:
            wind_high = wind_mid
            drift_high = drift_mid
        else:
            wind_low = wind_mid
            drift_low = drift_mid

    return {
        'original_wind': original_wind,
        'optimal_wind': wind_mid,
        'wind_change': wind_mid - original_wind,
        'wind_change_pct': ((wind_mid / original_wind) - 1) * 100 if original_wind > 0 else 0,
        'iterations': expansion_steps + bisection_iterations,
        'result': optimal_result,
    }


def get_ws_365_data(run_goal_seek=False):
    """
    Main function to get all WS 365-day data.
    
    Args:
        run_goal_seek: If True, also run Goal Seek to find optimal solar
    
    Returns:
        Dictionary with all data for frontend display
    """
    ws_data = get_ws_base_data()
    fixed_values = get_fixed_values()
    
    # Calculate with current Solar value
    current_result = calculate_365_days(fixed_values['ziel_912'], ws_data, fixed_values)
    
    # ==================================================================================
    # ALWAYS UPDATE DATABASE VALUES FOR 9.3.1 AND 9.3.4
    # This ensures all dependent formulas (9.3.1.2, etc.) get correct values
    # ==================================================================================
    update_renewable_from_ws365(current_result)
    # ==================================================================================
    
    response = {
        'current': {
            'solar': fixed_values['ziel_912'],
            'wind': fixed_values['ziel_911'],
            'sonst': fixed_values['ziel_913'],
            'bio': fixed_values['ziel_914'],
            'annual_demand': current_result['annual_demand'],
            'annual_electricity': current_result['annual_electricity'],
            'storage_drift': current_result['storage_drift'],
            'ladezust_day1': current_result['ladezust_day1'],
            'ladezust_day365': current_result['ladezust_day365'],
            'einspeich_sum': current_result['einspeich_sum'],
            'ausspeich_sum': current_result['ausspeich_sum'],
            'abregelung_sum': current_result['abregelung_sum'],
            'ueberschuss_sum': current_result['ueberschuss_sum'],
            'solar_strom_sum': current_result['solar_strom_sum'],
            'wind_strom_sum': current_result['wind_strom_sum'],
            'renewable_pct': current_result['renewable_pct'],
        },
        'daily_data': current_result['daily_data'],
    }
    
    if run_goal_seek:
        goal_seek_result = goal_seek_optimal_solar(ws_data, fixed_values)
        response['goal_seek'] = {
            'original_solar': goal_seek_result['original_solar'],
            'optimal_solar': goal_seek_result['optimal_solar'],
            'solar_change': goal_seek_result['solar_change'],
            'solar_change_pct': goal_seek_result['solar_change_pct'],
            'iterations': goal_seek_result['iterations'],
            'storage_drift': goal_seek_result['result']['storage_drift'],
            'annual_electricity': goal_seek_result['result']['annual_electricity'],
            'ladezust_day1': goal_seek_result['result']['ladezust_day1'],
            'ladezust_day365': goal_seek_result['result']['ladezust_day365'],
        }
        response['optimal_daily_data'] = goal_seek_result['result']['daily_data']
    
    return response


def update_renewable_from_ws365(ws_result):
    """
    Update RenewableData 9.3.1 and 9.3.4 target values from WS 365 calculation.
    
    This ensures all dependent formulas (9.3.1.2, 9.3.1.3, etc.) will use 
    the correct WS 365 values when they are calculated.
    
    Args:
        ws_result: Result dictionary from calculate_365_days()
    """
    # 9.3.1 ziel = einspeich_sum / 0.65
    einspeich_sum = ws_result.get('einspeich_sum', 0)
    value_931 = einspeich_sum / ELECTROLYSIS_EFFICIENCY if einspeich_sum > 0 else 0
    
    # 9.3.4 ziel = abregelung_sum
    value_934 = ws_result.get('abregelung_sum', 0)
    
    # Update database - SKIP CASCADE to avoid infinite loop!
    # The cascade will be triggered by unified_recalc_all after all updates are done.
    try:
        r931 = RenewableData.objects.get(code='9.3.1')
        if r931.target_value != value_931:
            r931.target_value = value_931
            r931.save(skip_cascade=True, update_fields=['target_value'])
            print(f"✅ Updated 9.3.1 ziel to {value_931:.2f} GWh")
    except RenewableData.DoesNotExist:
        print("⚠️ RenewableData 9.3.1 not found")
    
    try:
        r934 = RenewableData.objects.get(code='9.3.4')
        if r934.target_value != value_934:
            r934.target_value = value_934
            r934.save(skip_cascade=True, update_fields=['target_value'])
            print(f"✅ Updated 9.3.4 ziel to {value_934:.2f} GWh")
    except RenewableData.DoesNotExist:
        print("⚠️ RenewableData 9.3.4 not found")


def calculate_required_landuse(optimal_solar):
    """
    Reverse-engineer the LandUse (LU_2.1) needed to achieve the optimal Solar value.
    
    The formula chain is:
    - 9.1.2 = 1.1.2.1.2 + 1.2.1.2
    - 1.2.1.2 = LU_2.1 * 1.2.1.1 / 1000
    
    So: LU_2.1 = (optimal_solar - 1.1.2.1.2) * 1000 / 1.2.1.1
    
    Args:
        optimal_solar: The optimal Solar (9.1.2) value in GWh
    
    Returns:
        dict with required_landuse (ha) and other info
    """
    from .models import LandUse
    
    # Get current values
    r_11212 = RenewableData.objects.get(code='1.1.2.1.2')
    r_1211 = RenewableData.objects.get(code='1.2.1.1')
    lu_21 = LandUse.objects.get(code='LU_2.1')
    
    fixed_solar = r_11212.target_value or 0  # 1.1.2.1.2 (Rooftop PV - not from LU_2.1)
    yield_factor = r_1211.target_value or 1  # 1.2.1.1 (yield per ha)
    current_landuse = lu_21.target_ha or 0
    
    # Calculate required LandUse
    # 1.2.1.2 = LU_2.1 * 1.2.1.1 / 1000
    # So: LU_2.1 = 1.2.1.2 * 1000 / 1.2.1.1
    # And: 1.2.1.2 = optimal_solar - 1.1.2.1.2
    required_1212 = optimal_solar - fixed_solar
    required_landuse = required_1212 * 1000 / yield_factor if yield_factor > 0 else 0
    
    return {
        'optimal_solar': optimal_solar,
        'fixed_solar': fixed_solar,
        'required_1212': required_1212,
        'yield_factor': yield_factor,
        'required_landuse': required_landuse,
        'current_landuse': current_landuse,
        'landuse_change': required_landuse - current_landuse,
    }


def calculate_required_landuse_wind(optimal_wind):
    """
    Reverse-engineer LandUse (LU_6) needed to achieve optimal Wind (9.1.1).

    Chain:
    - 9.1.1 = 2.2.1.2.3 + 2.1.1.2.2
    - 2.1.1.2.2 = (2.1.1 / 2.1.1.1) * 2.1.1.2.1 / 1000
    - 2.1.1 = LU_6
    """
    from .models import LandUse

    r_22123 = RenewableData.objects.get(code='2.2.1.2.3')
    r_21111 = RenewableData.objects.get(code='2.1.1.1')
    r_211121 = RenewableData.objects.get(code='2.1.1.2.1')
    lu_6 = LandUse.objects.get(code='LU_6')

    fixed_wind = r_22123.target_value or 0  # non-LU_6 wind component
    factor_21111 = r_21111.target_value or 0
    factor_211121 = r_211121.target_value or 0
    current_landuse = lu_6.target_ha or 0

    required_211122 = optimal_wind - fixed_wind
    if factor_211121 > 0:
        required_landuse = required_211122 * 1000 * factor_21111 / factor_211121
    else:
        required_landuse = 0

    return {
        'optimal_wind': optimal_wind,
        'fixed_wind': fixed_wind,
        'required_211122': required_211122,
        'factor_21111': factor_21111,
        'factor_211121': factor_211121,
        'required_landuse': required_landuse,
        'current_landuse': current_landuse,
        'landuse_change': required_landuse - current_landuse,
    }


def _get_sector_totals():
    """
    Read the live sector totals used by the active pages:
    - Demand: Verbrauch 2.8.0 (Gebäudewärme), 3.7 (Prozesswärme)
    - Supply: Renewable 10.4.2 (Gebäudewärme), 10.5 (Prozesswärme)
    """
    v280 = VerbrauchData.objects.get(code='2.8.0')
    v37 = VerbrauchData.objects.get(code='3.7')
    r1042 = RenewableData.objects.get(code='10.4.2')
    r105 = RenewableData.objects.get(code='10.5')

    gw_demand = float(v280.ziel or 0)
    pw_demand = float(v37.ziel or 0)
    gw_supply = float(r1042.target_value or 0)
    pw_supply = float(r105.target_value or 0)

    return {
        'gebaeudewaerme': {
            'demand': gw_demand,
            'supply': gw_supply,
            'gap': gw_demand - gw_supply,
        },
        'prozesswaerme': {
            'demand': pw_demand,
            'supply': pw_supply,
            'gap': pw_demand - pw_supply,
        },
    }


def _balance_heat_sectors_after_ws(mode="quick"):
    """
    After electricity/WS balancing, align heat-sector totals:
    - Gebäudewärme: 10.4.2 (supply) to 2.8.0 (demand) via Verbrauch 2.8 ziel
    - Prozesswärme: 10.5 (supply) to 3.7 (demand) via 5.4.1 target percentage

    Returns detailed before/after values for API/UI visibility.
    """
    from simulator.recalc_service import recalc_all_renewables_full
    from simulator.verbrauch_recalculator import recalc_all_verbrauch

    # Keep 8.2 fixed to the required baseline value.
    r82_fixed = RenewableData.objects.get(code='8.2')
    old_82_target = float(r82_fixed.target_value or 0)
    if abs(old_82_target - FIXED_82_TARGET) > 1e-9:
        r82_fixed.target_value = FIXED_82_TARGET
        r82_fixed.is_fixed = True
        r82_fixed.save(skip_cascade=True, update_fields=['target_value', 'is_fixed'])
    new_82_target = float(r82_fixed.target_value or 0)

    profile = (mode or "quick").strip().lower()
    if profile not in {"quick", "full"}:
        profile = "quick"

    if profile == "full":
        # Full profile still needs bounded runtime for async job guarantees.
        max_seconds = float(os.environ.get("WS_HEAT_BALANCE_FULL_MAX_SECONDS", "60"))
        settle_rounds_default = 3
        eval_settle_rounds = 2
        coordinate_passes = 3
        solver_iterations = 8
        renewable_max_passes = 3
    else:
        # Timeout-safe profile for sync request paths.
        max_seconds = float(os.environ.get("WS_HEAT_BALANCE_MAX_SECONDS", "20"))
        settle_rounds_default = 2
        eval_settle_rounds = 1
        coordinate_passes = 1
        solver_iterations = 4
        renewable_max_passes = 2

    deadline = time.monotonic() + max(5.0, max_seconds)

    def _deadline_exceeded() -> bool:
        return time.monotonic() >= deadline

    def settle_totals(trigger_prefix: str, max_rounds: int = None, tolerance: float = 1.0):
        """
        Recalculate until heat-sector gaps stabilize.
        This avoids optimizing 2.8 against transient intermediate states.
        """
        rounds = max_rounds if max_rounds is not None else settle_rounds_default
        prev = None
        current = None
        for idx in range(rounds):
            if _deadline_exceeded():
                break
            # Use the fast dependency path even in full mode; we run more rounds
            # and deterministic scalar solving below to regain accuracy.
            recalc_all_verbrauch(
                trigger_code=f"{trigger_prefix}_{idx + 1}",
                propagate_renewables=False,
            )
            recalc_all_renewables_full(
                exclude_ws_dependent=False,
                max_passes=renewable_max_passes,
                change_tolerance=1e-6,
            )
            current = _get_sector_totals()
            if prev is not None:
                gw_delta = abs(current['gebaeudewaerme']['gap'] - prev['gebaeudewaerme']['gap'])
                pw_delta = abs(current['prozesswaerme']['gap'] - prev['prozesswaerme']['gap'])
                if gw_delta <= tolerance and pw_delta <= tolerance:
                    break
            prev = current
        return current or _get_sector_totals()

    def _bounded_scalar_solve(
        current_value: float,
        lower: float,
        upper: float,
        tolerance: float,
        evaluator,
        seed_values=None,
        max_iterations=None,
    ):
        """
        Deterministic bounded scalar solver:
        - always stays inside [lower, upper]
        - uses sign bracketing when available
        - falls back to secant/newton-like refinement
        """
        seeds = list(seed_values or [])
        cache = {}

        def _clamp(value: float) -> float:
            return max(lower, min(upper, float(value)))

        def _evaluate(value: float):
            x = _clamp(value)
            key = round(x, 8)
            if key in cache:
                return cache[key]
            solved_x, solved_gap, solved_totals = evaluator(x, settle_rounds=eval_settle_rounds)
            result = (float(solved_x), float(solved_gap), solved_totals)
            cache[key] = result
            return result

        _evaluate(current_value)
        _evaluate(lower)
        _evaluate(upper)
        for seed in seeds:
            if _deadline_exceeded():
                break
            _evaluate(seed)

        def _best_point():
            return min(cache.values(), key=lambda item: abs(item[1]))

        iteration_limit = solver_iterations if max_iterations is None else max(1, int(max_iterations))
        for iteration in range(iteration_limit):
            if _deadline_exceeded():
                break
            best_x, best_gap, _ = _best_point()
            if abs(best_gap) <= tolerance:
                break

            points = sorted(cache.values(), key=lambda item: item[0])
            bracket = None
            for left, right in zip(points, points[1:]):
                g_left = left[1]
                g_right = right[1]
                if g_left == 0.0 or g_right == 0.0 or (g_left * g_right) < 0.0:
                    if bracket is None:
                        bracket = (left, right)
                        continue
                    old_span = abs(bracket[1][0] - bracket[0][0])
                    new_span = abs(right[0] - left[0])
                    if new_span < old_span:
                        bracket = (left, right)

            if bracket is not None:
                candidate = (bracket[0][0] + bracket[1][0]) / 2.0
            else:
                ranked = sorted(cache.values(), key=lambda item: abs(item[1]))
                candidate = best_x
                if len(ranked) >= 2:
                    x1, g1, _ = ranked[0]
                    x2, g2, _ = ranked[1]
                    if abs(g2 - g1) > 1e-9 and abs(x2 - x1) > 1e-9:
                        candidate = x2 - (g2 * (x2 - x1) / (g2 - g1))
                if abs(candidate - best_x) < 1e-9:
                    span = (upper - lower) * (0.5 ** (iteration + 2))
                    candidate = best_x + (span if best_gap < 0 else -span)

            candidate = _clamp(candidate)
            key = round(candidate, 8)
            if key in cache:
                base_step = max((upper - lower) / 200.0, 0.05)
                found_alt = False
                for mul in (1.0, -1.0, 2.0, -2.0, 4.0, -4.0):
                    alt = _clamp(candidate + (base_step * mul))
                    if round(alt, 8) not in cache:
                        candidate = alt
                        found_alt = True
                        break
                if not found_alt:
                    break

            _evaluate(candidate)

        best_x, _, _ = _best_point()
        # Finalize on best candidate with full settle rounds for accurate residual.
        return evaluator(best_x, settle_rounds=settle_rounds_default)

    # Ensure consumption + renewable totals are stable before calculating gaps.
    before = settle_totals("ws_heat_balance_start")

    # --- Gebäudewärme knob: Verbrauch 2.8 ziel (%) ---
    v28 = VerbrauchData.objects.get(code='2.8')
    old_28 = float(v28.ziel or 0)

    def _clamp_28(value_28: float) -> float:
        return max(0.0, min(100.0, float(value_28)))

    def apply_28_and_get_gap(value_28: float, settle_rounds: int = None):
        value_28 = _clamp_28(value_28)
        v28.ziel = value_28
        if v28.user_editable:
            v28.user_percent = value_28
            v28.save(
                skip_cascade=True,
                skip_rebalance=True,
                update_fields=['ziel', 'user_percent']
            )
        else:
            v28.save(
                skip_cascade=True,
                skip_rebalance=True,
                update_fields=['ziel']
            )

        rounds = settle_rounds if settle_rounds is not None else settle_rounds_default
        settled = settle_totals("ws_heat_balance_2_8", max_rounds=max(1, rounds))
        gap_now = float(settled['gebaeudewaerme']['gap'])
        return value_28, gap_now, settled

    gw_gap_tolerance = float(os.environ.get("WS_HEAT_GW_GAP_TOLERANCE", "1.0"))
    pw_gap_tolerance = 100.0

    # --- Prozesswärme knob: Renewable 5.4.1 (%) driving 5.4.1.1 -> 10.5 ---
    r54 = RenewableData.objects.get(code='5.4')
    r541 = RenewableData.objects.get(code='5.4.1')
    base_54 = float(r54.target_value or 0)
    old_541 = float(r541.target_value or 0)

    process_adjustment = {
        'base_5_4': base_54,
        'old_5_4_1_percent': old_541,
        'new_5_4_1_percent': old_541,
        'delta_percent': 0.0,
        'applied': False,
        'reason': '',
    }
    gw_solver_meta = {'iterations': 0, 'applied': False}
    pw_solver_meta = {'iterations': 0, 'applied': False}
    final_28 = old_28
    final_541 = old_541
    after = before

    def apply_541_and_get_gap(value_541: float, settle_rounds: int = None):
        value_541 = max(0.0, min(100.0, float(value_541)))
        r541.target_value = value_541
        r541.save(skip_cascade=True, update_fields=['target_value'])
        rounds = settle_rounds if settle_rounds is not None else settle_rounds_default
        settled = settle_totals("ws_heat_balance_5_4_1", max_rounds=max(1, rounds))
        gap_now = float(settled['prozesswaerme']['gap'])
        return value_541, gap_now, settled

    # Alternate both controls in coordinate steps to absorb coupling effects.
    for coord_idx in range(coordinate_passes):
        if _deadline_exceeded():
            break

        gw_gap_now = float(after['gebaeudewaerme']['gap'])
        pw_gap_now = float(after['prozesswaerme']['gap'])
        if abs(gw_gap_now) <= gw_gap_tolerance and abs(pw_gap_now) <= pw_gap_tolerance:
            break

        if abs(gw_gap_now) > gw_gap_tolerance:
            gw_demand = float(after['gebaeudewaerme']['demand'] or 0.0)
            gw_supply = float(after['gebaeudewaerme']['supply'] or 0.0)
            gw_seeds = []
            if gw_demand > 0 and final_28 > 0:
                gw_seeds.append(final_28 * (gw_supply / gw_demand))
            # Closed-form seed from the direct chain: 2.8.0 = 2.6 * 2.8 / 100.
            v26_base = float(VerbrauchData.objects.get(code='2.6').ziel or 0.0)
            if v26_base > 0:
                gw_seeds.append(_clamp_28((gw_supply * 100.0) / v26_base))
            solved_28, solved_gw_gap, solved_totals = _bounded_scalar_solve(
                current_value=final_28,
                lower=0.0,
                upper=100.0,
                tolerance=gw_gap_tolerance,
                evaluator=apply_28_and_get_gap,
                seed_values=gw_seeds,
                max_iterations=3,
            )
            final_28 = solved_28
            after = solved_totals
            gw_solver_meta['iterations'] = coord_idx + 1
            gw_solver_meta['applied'] = abs(final_28 - old_28) > 1e-9
            if abs(solved_gw_gap) <= gw_gap_tolerance and abs(after['prozesswaerme']['gap']) <= pw_gap_tolerance:
                break

        if _deadline_exceeded():
            break

        if base_54 > 0:
            pw_gap_now = float(after['prozesswaerme']['gap'])
            if abs(pw_gap_now) > pw_gap_tolerance:
                linear_guess = final_541 + ((pw_gap_now * 100.0) / base_54)
                solved_541, solved_pw_gap, solved_totals = _bounded_scalar_solve(
                    current_value=final_541,
                    lower=0.0,
                    upper=100.0,
                    tolerance=pw_gap_tolerance,
                    evaluator=apply_541_and_get_gap,
                    seed_values=[linear_guess],
                )
                final_541 = solved_541
                after = solved_totals
                pw_solver_meta['iterations'] = coord_idx + 1
                pw_solver_meta['applied'] = abs(final_541 - old_541) > 1e-9
                if abs(solved_pw_gap) <= pw_gap_tolerance and abs(after['gebaeudewaerme']['gap']) <= gw_gap_tolerance:
                    break
        else:
            process_adjustment['reason'] = 'Cannot adjust 5.4.1 because 5.4 target is 0'
            break

    # Final settle after the chosen control values.
    after = settle_totals("ws_heat_balance_final", max_rounds=settle_rounds_default)
    final_gw_gap = float(after['gebaeudewaerme']['gap'])
    final_pw_gap = float(after['prozesswaerme']['gap'])

    # Apply one closed-form fine-tune step for 2.8 so 2.8.0 aligns with 10.4.2:
    # 2.8.0 = 2.6 * 2.8 / 100  =>  2.8 = 10.4.2 * 100 / 2.6
    exact_28_adjustment = {
        'applied': False,
        'old_ziel_percent': final_28,
        'new_ziel_percent': final_28,
        'delta_percent': 0.0,
        'reason': '',
    }
    if not _deadline_exceeded():
        v26_exact = float(VerbrauchData.objects.get(code='2.6').ziel or 0.0)
        if v26_exact > 0 and abs(final_gw_gap) > 1e-6:
            gw_supply_now = float(after['gebaeudewaerme']['supply'] or 0.0)
            exact_28 = _clamp_28((gw_supply_now * 100.0) / v26_exact)
            if abs(exact_28 - final_28) > 1e-9:
                old_28_exact = final_28
                old_gap_exact = final_gw_gap
                solved_28, solved_gap, solved_totals = apply_28_and_get_gap(exact_28, settle_rounds=1)
                if abs(solved_gap) <= abs(old_gap_exact) + 1e-6:
                    final_28 = solved_28
                    after = solved_totals
                    final_gw_gap = float(after['gebaeudewaerme']['gap'])
                    final_pw_gap = float(after['prozesswaerme']['gap'])
                    exact_28_adjustment.update({
                        'applied': True,
                        'old_ziel_percent': old_28_exact,
                        'new_ziel_percent': final_28,
                        'delta_percent': final_28 - old_28_exact,
                    })
                else:
                    # Guardrail: keep the previous best candidate if exact step worsens the gap.
                    reverted_28, _, reverted_totals = apply_28_and_get_gap(old_28_exact, settle_rounds=1)
                    final_28 = reverted_28
                    after = reverted_totals
                    final_gw_gap = float(after['gebaeudewaerme']['gap'])
                    final_pw_gap = float(after['prozesswaerme']['gap'])
                    exact_28_adjustment['reason'] = 'Skipped exact step (would worsen GW gap)'
        elif v26_exact <= 0:
            exact_28_adjustment['reason'] = 'Skipped exact step (2.6 ziel <= 0)'

    process_adjustment.update({
        'new_5_4_1_percent': final_541,
        'delta_percent': final_541 - old_541,
        'applied': abs(final_541 - old_541) > 1e-9,
        'reason': process_adjustment.get('reason') or (
            'No change needed' if abs(final_541 - old_541) <= 1e-9 else ''
        ),
        'final_gap': final_pw_gap,
        'solver_iterations': pw_solver_meta['iterations'],
    })

    return {
        'before': before,
        'after': after,
        'adjustments': {
            'verbrauch_2_8': {
                'old_ziel_percent': old_28,
                'new_ziel_percent': final_28,
                'delta_percent': final_28 - old_28,
                'final_gap': final_gw_gap,
                'applied': abs(final_28 - old_28) > 1e-9,
                'solver_iterations': gw_solver_meta['iterations'],
                'equation': '2.8.0 = 2.6 * 2.8 / 100',
                'exact_math_adjustment': exact_28_adjustment,
            },
            'renewable_8_2_fixed': {
                'old_target': old_82_target,
                'new_target': new_82_target,
                'fixed_target': FIXED_82_TARGET,
                'applied': abs(old_82_target - new_82_target) > 1e-9,
            },
            'renewable_5_4_1': process_adjustment,
        },
    }


def apply_balanced_landuse(enable_heat_balance=None, max_convergence_cycles=None, heat_profile="quick"):
    """
    Run Goal Seek, calculate required LandUse, and update LU_2.1 in database.
    
    This function uses ONLY ws_365_service calculations (no WSData database):
    1. Runs Goal Seek to find optimal Solar (balanced storage for 365 days)
    2. Calculates required LU_2.1 to achieve that Solar
    3. Updates LU_2.1 in database
    4. Recalculates ONLY the renewable chain (LU_2.1 -> 1.2.1.2 -> 9.1.2)
    5. Updates 9.3.1 and 9.3.4 from WS 365 calculation
    6. Balances heat sectors (10.4.2↔2.8.0 and 10.5↔3.7) using active live formulas
    
    NO WSData recalculation - all balance logic comes from ws_365_service.
    
    Returns:
        dict with all results
    """
    from .models import LandUse, RenewableData
    from django.db import transaction
    
    if max_convergence_cycles is None:
        # Keep sync HTTP request under Heroku's router timeout by default.
        max_convergence_cycles = 1
    ws_drift_tolerance = float(os.environ.get("WS_BALANCE_DRIFT_TOLERANCE", "0.5"))
    heat_gap_tolerance = 100.0
    if enable_heat_balance is None:
        enable_heat_balance = os.environ.get("WS_ENABLE_HEAT_BALANCE", "false").lower() == "true"
    heat_profile = (heat_profile or "quick").strip().lower()
    if heat_profile not in {"quick", "full"}:
        heat_profile = "quick"
    intermediate_heat_profile = os.environ.get("WS_BALANCE_INTERMEDIATE_HEAT_PROFILE", "quick").strip().lower()
    if intermediate_heat_profile not in {"quick", "full"}:
        intermediate_heat_profile = "quick"
    intermediate_heat_gap_threshold = float(
        os.environ.get("WS_BALANCE_INTERMEDIATE_HEAT_GAP_THRESHOLD", "5000")
    )

    old_landuse = None
    required_landuse = None
    goal_seek_result = None
    heat_balance = None
    final_result = None
    new_912 = None
    completed_cycles = 0
    landuse_code = 'LU_2.1'
    landuse_name = 'LU_2.1'
    old_landuse_percent = None
    new_landuse_percent = None
    converged = False
    gw_after = {'gap': 0.0, 'demand': 0.0, 'supply': 0.0}
    pw_after = {'gap': 0.0, 'demand': 0.0, 'supply': 0.0}
    final_drift = float('inf')
    force_full_heat_validation = False

    with transaction.atomic():
        for cycle_index in range(max_convergence_cycles):
            cycle_no = cycle_index + 1
            completed_cycles = cycle_no
            print(f"🔁 Convergence cycle {cycle_no}/{max_convergence_cycles}")

            # Step 1: Goal Seek on current WS inputs
            print("🔍 Running Goal Seek...")
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            goal_seek_result = goal_seek_optimal_solar(
                ws_data,
                fixed_values,
                tolerance=ws_drift_tolerance
            )

            optimal_solar = goal_seek_result['optimal_solar']
            print(f"   ✅ Found optimal Solar: {optimal_solar:,.0f} GWh")
            print(f"   ✅ Storage drift at optimal: {goal_seek_result['result']['storage_drift']:.2f} GWh")

            # Step 2: Calculate required LU_2.1 from optimal solar
            landuse_result = calculate_required_landuse(optimal_solar)
            required_landuse = landuse_result['required_landuse']
            if old_landuse is None:
                old_landuse = landuse_result['current_landuse']
            print(
                f"   📐 Required LU_2.1: {required_landuse:,.0f} ha "
                f"(change: {required_landuse - (landuse_result['current_landuse'] or 0):+,.0f} ha)"
            )

            # Step 3: Update LU_2.1 in DB
            lu_21 = LandUse.objects.select_related('parent').get(code='LU_2.1')
            landuse_name = lu_21.name or landuse_name
            if old_landuse_percent is None:
                if lu_21.user_percent is not None:
                    old_landuse_percent = float(lu_21.user_percent)
                elif lu_21.parent and lu_21.parent.target_ha and lu_21.parent.target_ha > 0 and old_landuse is not None:
                    old_landuse_percent = (float(old_landuse) / float(lu_21.parent.target_ha)) * 100.0
            required_landuse = _validate_required_landuse(
                required_landuse,
                lu_21.parent.target_ha if lu_21.parent else None,
                'LU_2.1'
            )
            lu_21.target_ha = required_landuse
            if lu_21.parent and lu_21.parent.target_ha and lu_21.parent.target_ha > 0:
                lu_21.user_percent = (required_landuse / lu_21.parent.target_ha) * 100.0
            lu_21._skip_cascade = True
            lu_21.save(update_fields=['target_ha', 'user_percent'])
            if lu_21.user_percent is not None:
                new_landuse_percent = float(lu_21.user_percent)
            elif lu_21.parent and lu_21.parent.target_ha and lu_21.parent.target_ha > 0:
                new_landuse_percent = (float(required_landuse) / float(lu_21.parent.target_ha)) * 100.0
            print(f"✅ Updated LU_2.1 target_ha to {required_landuse:.2f} ha")

            # Step 4: Recalculate local renewable chain LU_2.1 -> 1.2.1.2 -> 9.1.2
            print("🔄 Recalculating renewable chain...")
            r_1211 = RenewableData.objects.get(code='1.2.1.1')
            r_1212 = RenewableData.objects.get(code='1.2.1.2')
            new_1212 = required_landuse * (r_1211.target_value or 0) / 1000
            r_1212.target_value = new_1212
            r_1212.save(skip_cascade=True)
            print(f"   ✅ 1.2.1.2 = {new_1212:,.0f} GWh")

            r_11212 = RenewableData.objects.get(code='1.1.2.1.2')
            r_912 = RenewableData.objects.get(code='9.1.2')
            new_912 = (r_11212.target_value or 0) + new_1212
            r_912.target_value = new_912
            r_912.save(skip_cascade=True)
            print(f"   ✅ 9.1.2 = {new_912:,.0f} GWh")

            # Step 5: WS calculation and sync 9.3.1 / 9.3.4 / 9.4.1
            print("📊 Calculating WS 365 days with new Solar...")
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            final_result = calculate_365_days(fixed_values['ziel_912'], ws_data, fixed_values)
            update_renewable_from_ws365(final_result)

            annual_electricity = final_result.get('annual_electricity', 0)
            r941 = RenewableData.objects.get(code='9.4.1')
            r941.target_value = annual_electricity
            r941.is_fixed = True
            r941.formula = None
            r941.save(skip_cascade=True)
            print(f"   ✅ 9.4.1 = {annual_electricity:,.0f} GWh (annual electricity from diagram, fixed)")

            # Step 6: Heat balancing (optional; can exceed Heroku request timeout in production).
            if enable_heat_balance:
                cycle_heat_profile = heat_profile
                if (
                    heat_profile == "full"
                    and cycle_no < max_convergence_cycles
                    and not force_full_heat_validation
                ):
                    pre_heat_totals = _get_sector_totals()
                    pre_gw_gap = abs(float(pre_heat_totals['gebaeudewaerme']['gap']))
                    pre_pw_gap = abs(float(pre_heat_totals['prozesswaerme']['gap']))
                    is_close_enough_for_quick = (
                        pre_gw_gap <= intermediate_heat_gap_threshold and
                        pre_pw_gap <= intermediate_heat_gap_threshold
                    )
                    if is_close_enough_for_quick:
                        cycle_heat_profile = intermediate_heat_profile
                    print(
                        f"   ℹ️ Pre-heat gaps: GW={pre_gw_gap:.2f}, PW={pre_pw_gap:.2f}, "
                        f"quick_threshold={intermediate_heat_gap_threshold:.2f}"
                    )
                if cycle_heat_profile == "quick":
                    print("   ⚡ Using quick intermediate heat solve")
                else:
                    print("   🎯 Using full-precision heat solve")
                print(
                    "🔥 Balancing heat sectors (10.4.2↔2.8.0, 10.5↔3.7)"
                    f" [{cycle_heat_profile}]..."
                )
                heat_balance = _balance_heat_sectors_after_ws(mode=cycle_heat_profile)
                gw_after = heat_balance['after']['gebaeudewaerme']
                pw_after = heat_balance['after']['prozesswaerme']
                print(
                    f"   ✅ Gebäudewärme gap: {gw_after['gap']:.2f} GWh "
                    f"(demand {gw_after['demand']:,.0f} / supply {gw_after['supply']:,.0f})"
                )
                print(
                    f"   ✅ Prozesswärme gap: {pw_after['gap']:.2f} GWh "
                    f"(demand {pw_after['demand']:,.0f} / supply {pw_after['supply']:,.0f})"
                )
            else:
                after_totals = _get_sector_totals()
                heat_balance = {
                    'before': after_totals,
                    'after': after_totals,
                    'adjustments': {
                        'skipped': True,
                        'reason': 'WS_ENABLE_HEAT_BALANCE=false (timeout-safe mode)',
                    },
                }
                gw_after = heat_balance['after']['gebaeudewaerme']
                pw_after = heat_balance['after']['prozesswaerme']
                print("⚠️ Skipping heat-sector balancing for timeout-safe request handling.")

            # Step 7: Re-check WS drift AFTER heat (because 2.8 changes WS demand inputs)
            ws_data_post_heat = get_ws_base_data()
            fixed_values_post_heat = get_fixed_values()
            final_result = calculate_365_days(
                fixed_values_post_heat['ziel_912'],
                ws_data_post_heat,
                fixed_values_post_heat
            )
            update_renewable_from_ws365(final_result)

            annual_electricity = final_result.get('annual_electricity', 0)
            r941.target_value = annual_electricity
            r941.save(skip_cascade=True, update_fields=['target_value'])

            final_drift = final_result['storage_drift']
            drift_ok = abs(final_drift) <= ws_drift_tolerance
            heat_ok = (
                abs(gw_after['gap']) <= heat_gap_tolerance and
                abs(pw_after['gap']) <= heat_gap_tolerance
            ) if enable_heat_balance else True
            print(
                f"   🔎 Post-heat WS drift: {final_drift:.2f} GWh "
                f"(target ±{ws_drift_tolerance})"
            )
            if drift_ok and heat_ok:
                if (
                    enable_heat_balance
                    and heat_profile == "full"
                    and cycle_heat_profile == "quick"
                    and cycle_no < max_convergence_cycles
                ):
                    force_full_heat_validation = True
                    print("   ⏭️ Quick heat pass converged; running one full-precision validation cycle.")
                    continue
                print("   ✅ Converged: WS + heat both balanced")
                converged = True
                break

            if (
                enable_heat_balance
                and heat_profile == "full"
                and cycle_heat_profile == "quick"
                and cycle_no < max_convergence_cycles
                and not force_full_heat_validation
            ):
                force_full_heat_validation = True
                print("   ⚠️ Quick heat pass did not converge; forcing full-precision heat solve next cycle.")

        if not converged:
            raise RuntimeError(
                "WS balance did not converge within limits "
                f"(cycles={completed_cycles}, drift={final_drift:.2f}, "
                f"gw_gap={gw_after['gap']:.2f}, pw_gap={pw_after['gap']:.2f})"
            )
    
    # Final verification
    final_drift = final_result['storage_drift'] if final_result else 0
    annual_electricity = final_result.get('annual_electricity', 0) if final_result else 0
    print(f"\n✅ BALANCE COMPLETE")
    print(f"   Storage Drift: {final_drift:.2f} GWh (target: 0)")
    print(f"   Annual Electricity (9.4.1): {annual_electricity:,.0f} GWh")
    
    return {
        'success': True,
        'old_landuse': old_landuse,
        'new_landuse': required_landuse,
        'landuse_change': required_landuse - old_landuse,
        'optimal_solar': optimal_solar,
        'new_solar': new_912,
        'storage_drift': final_drift,
        'annual_electricity': annual_electricity,
        'iterations': goal_seek_result['iterations'] if goal_seek_result else 0,
        'convergence_cycles': completed_cycles,
        'heat_balance': heat_balance,
        'landuse_code': landuse_code,
        'landuse_name': landuse_name,
        'old_landuse_percent': old_landuse_percent,
        'new_landuse_percent': new_landuse_percent,
    }


def apply_balanced_wind_landuse(enable_heat_balance=None, max_convergence_cycles=None, heat_profile="quick"):
    """
    Run Goal Seek with Wind as variable, calculate required LU_6, and update database.

    Flow mirrors apply_balanced_landuse(), but driver is Wind (9.1.1/LU_6)
    instead of Solar (9.1.2/LU_2.1). Heat balancing remains identical.
    """
    from .models import LandUse, RenewableData
    from django.db import transaction

    if max_convergence_cycles is None:
        # Keep sync HTTP request under Heroku's router timeout by default.
        max_convergence_cycles = 1
    # Use tighter tolerance so Day1/Day365 also match in UI precision.
    ws_drift_tolerance = 0.005
    heat_gap_tolerance = 100.0
    if enable_heat_balance is None:
        enable_heat_balance = os.environ.get("WS_ENABLE_HEAT_BALANCE", "false").lower() == "true"
    heat_profile = (heat_profile or "quick").strip().lower()
    if heat_profile not in {"quick", "full"}:
        heat_profile = "quick"
    intermediate_heat_profile = os.environ.get("WS_BALANCE_INTERMEDIATE_HEAT_PROFILE", "quick").strip().lower()
    if intermediate_heat_profile not in {"quick", "full"}:
        intermediate_heat_profile = "quick"
    intermediate_heat_gap_threshold = float(
        os.environ.get("WS_BALANCE_INTERMEDIATE_HEAT_GAP_THRESHOLD", "5000")
    )

    old_landuse = None
    required_landuse = None
    goal_seek_result = None
    heat_balance = None
    final_result = None
    new_911 = None
    completed_cycles = 0
    optimal_wind = None
    landuse_code = 'LU_6'
    landuse_name = 'LU_6'
    old_landuse_percent = None
    new_landuse_percent = None
    converged = False
    gw_after = {'gap': 0.0, 'demand': 0.0, 'supply': 0.0}
    pw_after = {'gap': 0.0, 'demand': 0.0, 'supply': 0.0}
    final_drift = float('inf')
    force_full_heat_validation = False

    # Wind mode must not alter Solar/LU_2.1.
    r912_guard = RenewableData.objects.get(code='9.1.2')
    fixed_solar_912 = float(r912_guard.target_value or 0)
    lu21_guard = LandUse.objects.get(code='LU_2.1')
    fixed_lu21_target = float(lu21_guard.target_ha or 0)
    fixed_lu21_percent = lu21_guard.user_percent

    def _restore_frozen_solar_if_needed():
        r912_now = RenewableData.objects.get(code='9.1.2')
        if abs(float(r912_now.target_value or 0) - fixed_solar_912) > 1e-9:
            r912_now.target_value = fixed_solar_912
            r912_now.save(skip_cascade=True, update_fields=['target_value'])

    with transaction.atomic():
        for cycle_index in range(max_convergence_cycles):
            cycle_no = cycle_index + 1
            completed_cycles = cycle_no
            print(f"🔁 Wind convergence cycle {cycle_no}/{max_convergence_cycles}")

            # Step 1: Goal Seek on current WS inputs (Wind variable)
            print("🔍 Running Wind Goal Seek...")
            _restore_frozen_solar_if_needed()
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            fixed_values['ziel_912'] = fixed_solar_912
            goal_seek_result = goal_seek_optimal_wind(
                ws_data,
                fixed_values,
                tolerance=ws_drift_tolerance
            )

            optimal_wind = goal_seek_result['optimal_wind']
            print(f"   ✅ Found optimal Wind: {optimal_wind:,.0f} GWh")
            print(f"   ✅ Storage drift at optimal: {goal_seek_result['result']['storage_drift']:.2f} GWh")

            # Step 2: Calculate required LU_6 from optimal wind
            landuse_result = calculate_required_landuse_wind(optimal_wind)
            required_landuse = landuse_result['required_landuse']
            if old_landuse is None:
                old_landuse = landuse_result['current_landuse']
            print(
                f"   📐 Required LU_6: {required_landuse:,.0f} ha "
                f"(change: {required_landuse - (landuse_result['current_landuse'] or 0):+,.0f} ha)"
            )

            # Step 3: Update LU_6 in DB
            lu_6 = LandUse.objects.select_related('parent').get(code='LU_6')
            landuse_name = lu_6.name or landuse_name
            if old_landuse_percent is None:
                if lu_6.user_percent is not None:
                    old_landuse_percent = float(lu_6.user_percent)
                elif lu_6.parent and lu_6.parent.target_ha and lu_6.parent.target_ha > 0 and old_landuse is not None:
                    old_landuse_percent = (float(old_landuse) / float(lu_6.parent.target_ha)) * 100.0
            required_landuse = _validate_required_landuse(
                required_landuse,
                lu_6.parent.target_ha if lu_6.parent else None,
                'LU_6'
            )
            lu_6.target_ha = required_landuse
            if lu_6.parent and lu_6.parent.target_ha and lu_6.parent.target_ha > 0:
                lu_6.user_percent = (required_landuse / lu_6.parent.target_ha) * 100.0
            lu_6._skip_cascade = True
            lu_6.save(update_fields=['target_ha', 'user_percent'])
            if lu_6.user_percent is not None:
                new_landuse_percent = float(lu_6.user_percent)
            elif lu_6.parent and lu_6.parent.target_ha and lu_6.parent.target_ha > 0:
                new_landuse_percent = (float(required_landuse) / float(lu_6.parent.target_ha)) * 100.0
            print(f"✅ Updated LU_6 target_ha to {required_landuse:.2f} ha")

            # Step 4: Recalculate local renewable chain LU_6 -> 2.1.1 -> 2.1.1.2.2 -> 9.1.1
            print("🔄 Recalculating wind renewable chain...")
            r_211 = RenewableData.objects.get(code='2.1.1')
            r_211.target_value = required_landuse
            r_211.save(skip_cascade=True)
            print(f"   ✅ 2.1.1 = {required_landuse:,.0f} ha")

            r_21111 = RenewableData.objects.get(code='2.1.1.1')
            r_21112 = RenewableData.objects.get(code='2.1.1.2')
            divisor_21111 = float(r_21111.target_value or 0)
            new_21112 = (required_landuse / divisor_21111) if divisor_21111 > 0 else 0
            r_21112.target_value = new_21112
            r_21112.save(skip_cascade=True)
            print(f"   ✅ 2.1.1.2 = {new_21112:,.0f}")

            r_211121 = RenewableData.objects.get(code='2.1.1.2.1')
            r_211122 = RenewableData.objects.get(code='2.1.1.2.2')
            new_211122 = new_21112 * (r_211121.target_value or 0) / 1000
            r_211122.target_value = new_211122
            r_211122.save(skip_cascade=True)
            print(f"   ✅ 2.1.1.2.2 = {new_211122:,.0f} GWh")

            r_22123 = RenewableData.objects.get(code='2.2.1.2.3')
            r_911 = RenewableData.objects.get(code='9.1.1')
            new_911 = (r_22123.target_value or 0) + new_211122
            r_911.target_value = new_911
            r_911.save(skip_cascade=True)
            print(f"   ✅ 9.1.1 = {new_911:,.0f} GWh")

            # Step 5: WS calculation and sync 9.3.1 / 9.3.4 / 9.4.1
            print("📊 Calculating WS 365 days with new Wind...")
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            fixed_values['ziel_912'] = fixed_solar_912
            final_result = calculate_365_days(fixed_solar_912, ws_data, fixed_values)
            update_renewable_from_ws365(final_result)

            annual_electricity = final_result.get('annual_electricity', 0)
            r941 = RenewableData.objects.get(code='9.4.1')
            r941.target_value = annual_electricity
            r941.is_fixed = True
            r941.formula = None
            r941.save(skip_cascade=True)
            print(f"   ✅ 9.4.1 = {annual_electricity:,.0f} GWh (annual electricity from diagram, fixed)")

            # Step 6: Heat balancing (optional; can exceed Heroku request timeout in production).
            if enable_heat_balance:
                cycle_heat_profile = heat_profile
                if (
                    heat_profile == "full"
                    and cycle_no < max_convergence_cycles
                    and not force_full_heat_validation
                ):
                    pre_heat_totals = _get_sector_totals()
                    pre_gw_gap = abs(float(pre_heat_totals['gebaeudewaerme']['gap']))
                    pre_pw_gap = abs(float(pre_heat_totals['prozesswaerme']['gap']))
                    is_close_enough_for_quick = (
                        pre_gw_gap <= intermediate_heat_gap_threshold and
                        pre_pw_gap <= intermediate_heat_gap_threshold
                    )
                    if is_close_enough_for_quick:
                        cycle_heat_profile = intermediate_heat_profile
                    print(
                        f"   ℹ️ Pre-heat gaps: GW={pre_gw_gap:.2f}, PW={pre_pw_gap:.2f}, "
                        f"quick_threshold={intermediate_heat_gap_threshold:.2f}"
                    )
                if cycle_heat_profile == "quick":
                    print("   ⚡ Using quick intermediate heat solve")
                else:
                    print("   🎯 Using full-precision heat solve")
                print(
                    "🔥 Balancing heat sectors (10.4.2↔2.8.0, 10.5↔3.7)"
                    f" [{cycle_heat_profile}]..."
                )
                heat_balance = _balance_heat_sectors_after_ws(mode=cycle_heat_profile)
                gw_after = heat_balance['after']['gebaeudewaerme']
                pw_after = heat_balance['after']['prozesswaerme']
                print(
                    f"   ✅ Gebäudewärme gap: {gw_after['gap']:.2f} GWh "
                    f"(demand {gw_after['demand']:,.0f} / supply {gw_after['supply']:,.0f})"
                )
                print(
                    f"   ✅ Prozesswärme gap: {pw_after['gap']:.2f} GWh "
                    f"(demand {pw_after['demand']:,.0f} / supply {pw_after['supply']:,.0f})"
                )
            else:
                after_totals = _get_sector_totals()
                heat_balance = {
                    'before': after_totals,
                    'after': after_totals,
                    'adjustments': {
                        'skipped': True,
                        'reason': 'WS_ENABLE_HEAT_BALANCE=false (timeout-safe mode)',
                    },
                }
                gw_after = heat_balance['after']['gebaeudewaerme']
                pw_after = heat_balance['after']['prozesswaerme']
                print("⚠️ Skipping heat-sector balancing for timeout-safe request handling.")

            # Step 7: Re-check WS drift AFTER heat
            ws_data_post_heat = get_ws_base_data()
            fixed_values_post_heat = get_fixed_values()
            fixed_values_post_heat['ziel_912'] = fixed_solar_912
            _restore_frozen_solar_if_needed()
            final_result = calculate_365_days(
                fixed_solar_912,
                ws_data_post_heat,
                fixed_values_post_heat
            )
            update_renewable_from_ws365(final_result)

            annual_electricity = final_result.get('annual_electricity', 0)
            r941.target_value = annual_electricity
            r941.save(skip_cascade=True, update_fields=['target_value'])

            final_drift = final_result['storage_drift']
            drift_ok = abs(final_drift) <= ws_drift_tolerance
            heat_ok = (
                abs(gw_after['gap']) <= heat_gap_tolerance and
                abs(pw_after['gap']) <= heat_gap_tolerance
            ) if enable_heat_balance else True
            print(
                f"   🔎 Post-heat WS drift: {final_drift:.2f} GWh "
                f"(target ±{ws_drift_tolerance})"
            )
            if drift_ok and heat_ok:
                if (
                    enable_heat_balance
                    and heat_profile == "full"
                    and cycle_heat_profile == "quick"
                    and cycle_no < max_convergence_cycles
                ):
                    force_full_heat_validation = True
                    print("   ⏭️ Quick heat pass converged; running one full-precision validation cycle.")
                    continue
                print("   ✅ Converged: WS + heat both balanced")
                converged = True
                break

            if (
                enable_heat_balance
                and heat_profile == "full"
                and cycle_heat_profile == "quick"
                and cycle_no < max_convergence_cycles
                and not force_full_heat_validation
            ):
                force_full_heat_validation = True
                print("   ⚠️ Quick heat pass did not converge; forcing full-precision heat solve next cycle.")

        if not converged:
            raise RuntimeError(
                "WS wind balance did not converge within limits "
                f"(cycles={completed_cycles}, drift={final_drift:.2f}, "
                f"gw_gap={gw_after['gap']:.2f}, pw_gap={pw_after['gap']:.2f})"
            )

        # Guard-restore: keep Solar/LU_2.1 untouched in wind mode.
        r912_now = RenewableData.objects.get(code='9.1.2')
        if abs(float(r912_now.target_value or 0) - fixed_solar_912) > 1e-9:
            r912_now.target_value = fixed_solar_912
            r912_now.save(skip_cascade=True, update_fields=['target_value'])

        lu21_now = LandUse.objects.get(code='LU_2.1')
        lu21_changed = (
            abs(float(lu21_now.target_ha or 0) - fixed_lu21_target) > 1e-9 or
            lu21_now.user_percent != fixed_lu21_percent
        )
        if lu21_changed:
            lu21_now.target_ha = fixed_lu21_target
            lu21_now.user_percent = fixed_lu21_percent
            lu21_now._skip_cascade = True
            lu21_now.save(update_fields=['target_ha', 'user_percent'])

        # Final WS recompute after any guard restore so day1/day365 and drift reflect DB truth.
        ws_data_final = get_ws_base_data()
        fixed_values_final = get_fixed_values()
        fixed_values_final['ziel_912'] = fixed_solar_912
        _restore_frozen_solar_if_needed()
        final_result = calculate_365_days(
            fixed_solar_912,
            ws_data_final,
            fixed_values_final
        )
        update_renewable_from_ws365(final_result)

        annual_electricity = final_result.get('annual_electricity', 0)
        r941 = RenewableData.objects.get(code='9.4.1')
        r941.target_value = annual_electricity
        r941.save(skip_cascade=True, update_fields=['target_value'])

    final_drift = final_result['storage_drift'] if final_result else 0
    annual_electricity = final_result.get('annual_electricity', 0) if final_result else 0
    print(f"\n✅ WIND BALANCE COMPLETE")
    print(f"   Storage Drift: {final_drift:.2f} GWh (target: 0)")
    print(f"   Annual Electricity (9.4.1): {annual_electricity:,.0f} GWh")

    return {
        'success': True,
        'old_landuse': old_landuse,
        'new_landuse': required_landuse,
        'landuse_change': required_landuse - old_landuse,
        'optimal_wind': optimal_wind,
        'new_wind': new_911,
        'storage_drift': final_drift,
        'annual_electricity': annual_electricity,
        'iterations': goal_seek_result['iterations'] if goal_seek_result else 0,
        'convergence_cycles': completed_cycles,
        'heat_balance': heat_balance,
        'landuse_code': landuse_code,
        'landuse_name': landuse_name,
        'old_landuse_percent': old_landuse_percent,
        'new_landuse_percent': new_landuse_percent,
    }
