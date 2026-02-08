"""
WS 365 Days Service
====================
Backend service for 365-day energy simulation with Goal Seek.
Provides real-time recalculation when inputs change.
"""

from .models import VerbrauchData, RenewableData
from .ws_models import WSData


# Constants
GRID_LOSS_RATE = 0.092
ELECTROLYSIS_EFFICIENCY = 0.65
RUECKVERSTROEMUNG_EFFICIENCY = 0.585
FIXED_82_TARGET = 12000.0


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


def calculate_365_days(solar_value, ws_data, fixed_values):
    """
    Calculate all columns for 365 days given a Solar value.
    
    Args:
        solar_value: The solar generation value in GWh
        ws_data: Dictionary with promille arrays (from get_ws_base_data)
        fixed_values: Dictionary with fixed values (from get_fixed_values)
    
    Returns:
        Dictionary with all results and daily data
    """
    solar_promille = ws_data['solar_promille']
    wind_promille = ws_data['wind_promille']
    heizung_abwaerm_promille = ws_data['heizung_abwaerm_promille']
    verbrauch_promille = ws_data['verbrauch_promille']
    
    ziel_911 = fixed_values['ziel_911']
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


def _get_sector_totals():
    """
    Read the live sector totals used by the active pages:
    - Demand: Verbrauch 2.10 (Gebäudewärme), 3.7 (Prozesswärme)
    - Supply: Renewable 10.4 (Gebäudewärme), 10.5 (Prozesswärme)
    """
    v210 = VerbrauchData.objects.get(code='2.10')
    v37 = VerbrauchData.objects.get(code='3.7')
    r104 = RenewableData.objects.get(code='10.4')
    r105 = RenewableData.objects.get(code='10.5')

    gw_demand = float(v210.ziel or 0)
    pw_demand = float(v37.ziel or 0)
    gw_supply = float(r104.target_value or 0)
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


def _balance_heat_sectors_after_ws():
    """
    After electricity/WS balancing, align heat-sector totals:
    - Gebäudewärme: 10.4 (supply) to 2.10 (demand) via Verbrauch 2.8 ziel
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

    def settle_totals(trigger_prefix: str, max_rounds: int = 3, tolerance: float = 1.0):
        """
        Recalculate until heat-sector gaps stabilize.
        This avoids optimizing 2.8 against transient intermediate states.
        """
        prev = None
        current = None
        for idx in range(max_rounds):
            recalc_all_verbrauch(trigger_code=f"{trigger_prefix}_{idx + 1}")
            recalc_all_renewables_full(exclude_ws_dependent=False)
            current = _get_sector_totals()
            if prev is not None:
                gw_delta = abs(current['gebaeudewaerme']['gap'] - prev['gebaeudewaerme']['gap'])
                pw_delta = abs(current['prozesswaerme']['gap'] - prev['prozesswaerme']['gap'])
                if gw_delta <= tolerance and pw_delta <= tolerance:
                    break
            prev = current
        return current or _get_sector_totals()

    # Ensure consumption + renewable totals are stable before calculating gaps.
    before = settle_totals("ws_heat_balance_start")

    # --- Gebäudewärme knob: Verbrauch 2.8 ziel (%) ---
    v28 = VerbrauchData.objects.get(code='2.8')
    old_28 = float(v28.ziel or 0)
    old_gap = float(before['gebaeudewaerme']['gap'])
    best_28 = old_28
    best_gap = abs(old_gap)
    tried_points = [(old_28, old_gap)]

    def _clamp_28(value_28: float) -> float:
        return max(0.0, min(100.0, float(value_28)))

    def apply_28_and_get_gap(value_28: float, settle_rounds: int = 3):
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

        settled = settle_totals("ws_heat_balance_2_8", max_rounds=max(1, settle_rounds))
        gap_now = float(settled['gebaeudewaerme']['gap'])
        return value_28, gap_now, settled

    def _remember_candidate(x_val: float, gap_val: float):
        nonlocal best_28, best_gap
        tried_points.append((x_val, gap_val))
        if abs(gap_val) < best_gap:
            best_gap = abs(gap_val)
            best_28 = x_val

    def _evaluate_28_gap(value_28: float, settle_rounds: int = 3):
        """
        Evaluate a real committed state for 2.8 and return the resulting gap.
        """
        x_eval, g_eval, _ = apply_28_and_get_gap(value_28, settle_rounds=settle_rounds)
        _remember_candidate(x_eval, g_eval)
        return x_eval, g_eval

    gw_gap_tolerance = 100.0

    if abs(old_gap) > gw_gap_tolerance:
        x_curr = old_28
        g_curr = old_gap
        probe_step = 0.5

        for _ in range(6):
            if abs(g_curr) <= gw_gap_tolerance:
                break

            direction = -1.0 if g_curr > 0 else 1.0
            x_probe = _clamp_28(x_curr + (direction * probe_step))
            if abs(x_probe - x_curr) < 1e-9:
                break

            x_probe, g_probe = _evaluate_28_gap(x_probe, settle_rounds=3)

            slope = None
            if abs(x_probe - x_curr) > 1e-9:
                slope = (g_probe - g_curr) / (x_probe - x_curr)

            x_next = None
            g_next = None
            if slope is not None and abs(slope) > 1e-9:
                x_guess = _clamp_28(x_curr - (g_curr / slope))
                max_jump = max(1.0, probe_step * 4.0)
                x_guess = max(x_curr - max_jump, min(x_curr + max_jump, x_guess))
                if abs(x_guess - x_probe) > 1e-9 and abs(x_guess - x_curr) > 1e-9:
                    x_next, g_next = _evaluate_28_gap(x_guess, settle_rounds=3)

            candidates = [(x_curr, g_curr), (x_probe, g_probe)]
            if x_next is not None:
                candidates.append((x_next, g_next))

            target_x, _ = min(candidates, key=lambda item: abs(item[1]))
            current_state_x = candidates[-1][0]

            if abs(target_x - current_state_x) > 1e-9:
                target_x, target_gap, _ = apply_28_and_get_gap(target_x, settle_rounds=3)
                _remember_candidate(target_x, target_gap)
            else:
                target_gap = candidates[-1][1]

            improved = abs(target_gap) < abs(g_curr)
            x_curr, g_curr = target_x, target_gap

            if improved:
                probe_step = min(2.0, probe_step * 1.3)
            else:
                probe_step = max(0.1, probe_step * 0.5)
                if probe_step <= 0.11:
                    break

    # Set final best 2.8 and keep that state with full settling.
    v28.refresh_from_db(fields=['ziel', 'user_percent'])
    final_28, final_gw_gap, totals_after_28 = apply_28_and_get_gap(best_28, settle_rounds=3)

    # --- Prozesswärme knob: Renewable 5.4.1 (%) driving 5.4.1.1 -> 10.5 ---
    r54 = RenewableData.objects.get(code='5.4')
    r541 = RenewableData.objects.get(code='5.4.1')
    base_54 = float(r54.target_value or 0)
    old_541 = float(r541.target_value or 0)
    pw_gap = totals_after_28['prozesswaerme']['gap']

    process_adjustment = {
        'base_5_4': base_54,
        'old_5_4_1_percent': old_541,
        'new_5_4_1_percent': old_541,
        'delta_percent': 0.0,
        'applied': False,
        'reason': '',
    }

    if base_54 > 0:
        delta_pct = (pw_gap * 100.0) / base_54
        new_541 = max(0.0, min(100.0, old_541 + delta_pct))
        if abs(new_541 - old_541) > 1e-9:
            r541.target_value = new_541
            r541.save(skip_cascade=True, update_fields=['target_value'])
        process_adjustment.update({
            'new_5_4_1_percent': new_541,
            'delta_percent': new_541 - old_541,
            'applied': abs(new_541 - old_541) > 1e-9,
            'reason': '' if abs(new_541 - old_541) > 1e-9 else 'No change needed',
        })
    else:
        process_adjustment['reason'] = 'Cannot adjust 5.4.1 because 5.4 target is 0'

    # Recalculate until stable after both knob updates.
    after = settle_totals("ws_heat_balance_final")

    return {
        'before': before,
        'after': after,
        'adjustments': {
            'verbrauch_2_8': {
                'old_ziel_percent': old_28,
                'new_ziel_percent': final_28,
                'delta_percent': final_28 - old_28,
                'final_gap': after['gebaeudewaerme']['gap'],
                'applied': abs(final_28 - old_28) > 1e-9,
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


def apply_balanced_landuse():
    """
    Run Goal Seek, calculate required LandUse, and update LU_2.1 in database.
    
    This function uses ONLY ws_365_service calculations (no WSData database):
    1. Runs Goal Seek to find optimal Solar (balanced storage for 365 days)
    2. Calculates required LU_2.1 to achieve that Solar
    3. Updates LU_2.1 in database
    4. Recalculates ONLY the renewable chain (LU_2.1 -> 1.2.1.2 -> 9.1.2)
    5. Updates 9.3.1 and 9.3.4 from WS 365 calculation
    6. Balances heat sectors (10.4↔2.10 and 10.5↔3.7) using active live formulas
    
    NO WSData recalculation - all balance logic comes from ws_365_service.
    
    Returns:
        dict with all results
    """
    from .models import LandUse, RenewableData
    from django.db import transaction
    
    max_convergence_cycles = 3
    ws_drift_tolerance = 0.1
    heat_gap_tolerance = 100.0

    old_landuse = None
    required_landuse = None
    goal_seek_result = None
    heat_balance = None
    final_result = None
    new_912 = None
    completed_cycles = 0

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
            lu_21.target_ha = required_landuse
            if lu_21.parent and lu_21.parent.target_ha and lu_21.parent.target_ha > 0:
                lu_21.user_percent = (required_landuse / lu_21.parent.target_ha) * 100.0
            lu_21._skip_cascade = True
            lu_21.save(update_fields=['target_ha', 'user_percent'])
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

            # Step 6: Heat balancing (existing logic)
            print("🔥 Balancing heat sectors (10.4↔2.10, 10.5↔3.7)...")
            heat_balance = _balance_heat_sectors_after_ws()
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
            )
            print(
                f"   🔎 Post-heat WS drift: {final_drift:.2f} GWh "
                f"(target ±{ws_drift_tolerance})"
            )
            if drift_ok and heat_ok:
                print("   ✅ Converged: WS + heat both balanced")
                break
    
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
    }
