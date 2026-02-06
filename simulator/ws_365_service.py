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


def apply_balanced_landuse():
    """
    Run Goal Seek, calculate required LandUse, and update LU_2.1 in database.
    
    This function uses ONLY ws_365_service calculations (no WSData database):
    1. Runs Goal Seek to find optimal Solar (balanced storage for 365 days)
    2. Calculates required LU_2.1 to achieve that Solar
    3. Updates LU_2.1 in database
    4. Recalculates ONLY the renewable chain (LU_2.1 -> 1.2.1.2 -> 9.1.2)
    5. Updates 9.3.1 and 9.3.4 from WS 365 calculation
    
    NO WSData recalculation - all balance logic comes from ws_365_service.
    
    Returns:
        dict with all results
    """
    from .models import LandUse, RenewableData
    from django.db import transaction
    
    # Step 1: Run Goal Seek (using ws_365_service ONLY)
    print("🔍 Running Goal Seek...")
    ws_data = get_ws_base_data()
    fixed_values = get_fixed_values()
    goal_seek_result = goal_seek_optimal_solar(ws_data, fixed_values)
    
    optimal_solar = goal_seek_result['optimal_solar']
    print(f"   ✅ Found optimal Solar: {optimal_solar:,.0f} GWh")
    print(f"   ✅ Storage drift at optimal: {goal_seek_result['result']['storage_drift']:.2f} GWh")
    
    # Step 2: Calculate required LandUse
    landuse_result = calculate_required_landuse(optimal_solar)
    required_landuse = landuse_result['required_landuse']
    old_landuse = landuse_result['current_landuse']
    print(f"   📐 Required LU_2.1: {required_landuse:,.0f} ha (change: {required_landuse - old_landuse:+,.0f} ha)")
    
    with transaction.atomic():
        # Step 3: Update LU_2.1 in database (skip cascade - we'll handle it)
        lu_21 = LandUse.objects.get(code='LU_2.1')
        lu_21.target_ha = required_landuse
        lu_21._skip_cascade = True
        lu_21.save(update_fields=['target_ha'])
        print(f"✅ Updated LU_2.1 target_ha: {old_landuse:.2f} → {required_landuse:.2f} ha")
        
        # Step 4: Recalculate ONLY the renewable chain affected by LU_2.1
        # The chain is: LU_2.1 -> 1.2.1.2 -> 1.2.1 -> 9.1.2 -> 9.1 -> 9.2 -> etc.
        print("🔄 Recalculating renewable chain...")
        
        # 1.2.1.2 = LU_2.1 * 1.2.1.1 / 1000
        r_1211 = RenewableData.objects.get(code='1.2.1.1')
        r_1212 = RenewableData.objects.get(code='1.2.1.2')
        new_1212 = required_landuse * (r_1211.target_value or 0) / 1000
        r_1212.target_value = new_1212
        r_1212.save(skip_cascade=True)
        print(f"   ✅ 1.2.1.2 = {new_1212:,.0f} GWh")
        
        # 9.1.2 = 1.1.2.1.2 + 1.2.1.2
        r_11212 = RenewableData.objects.get(code='1.1.2.1.2')
        r_912 = RenewableData.objects.get(code='9.1.2')
        new_912 = (r_11212.target_value or 0) + new_1212
        r_912.target_value = new_912
        r_912.save(skip_cascade=True)
        print(f"   ✅ 9.1.2 = {new_912:,.0f} GWh")
        
        # Step 5: Calculate WS 365 days with new Solar and update 9.3.1, 9.3.4
        print("📊 Calculating WS 365 days with new Solar...")
        ws_data = get_ws_base_data()
        fixed_values = get_fixed_values()  # This now has the new 9.1.2 value
        final_result = calculate_365_days(fixed_values['ziel_912'], ws_data, fixed_values)
        
        # Update 9.3.1 and 9.3.4 from WS 365 calculation
        einspeich_sum = final_result.get('einspeich_sum', 0)
        abregelung_sum = final_result.get('abregelung_sum', 0)
        
        value_931 = einspeich_sum / ELECTROLYSIS_EFFICIENCY if einspeich_sum > 0 else 0
        value_934 = abregelung_sum
        
        r931 = RenewableData.objects.get(code='9.3.1')
        r931.target_value = value_931
        r931.save(skip_cascade=True)
        print(f"   ✅ 9.3.1 = {value_931:,.0f} GWh (from einspeich)")
        
        r934 = RenewableData.objects.get(code='9.3.4')
        r934.target_value = value_934
        r934.save(skip_cascade=True)
        print(f"   ✅ 9.3.4 = {value_934:,.0f} GWh (from abregelung)")
        
        # Step 5b: Update 9.4.1 ziel with annual_electricity (final electricity production)
        # We also set is_fixed=True and clear the formula so recalculation won't overwrite it
        annual_electricity = final_result.get('annual_electricity', 0)
        r941 = RenewableData.objects.get(code='9.4.1')
        r941.target_value = annual_electricity
        r941.is_fixed = True  # Mark as fixed so formula won't overwrite
        r941.formula = None   # Clear the formula
        r941.save(skip_cascade=True)
        print(f"   ✅ 9.4.1 = {annual_electricity:,.0f} GWh (annual electricity from diagram, fixed)")
    
    # Step 6: Final verification
    final_drift = final_result['storage_drift']
    annual_electricity = final_result.get('annual_electricity', 0)
    print(f"\n✅ BALANCE COMPLETE")
    print(f"   Storage Drift: {final_drift:.2f} GWh (target: 0)")
    print(f"   Annual Electricity (9.4.1): {annual_electricity:,.0f} GWh")
    
    return {
        'success': True,
        'old_landuse': old_landuse,
        'new_landuse': required_landuse,
        'landuse_change': required_landuse - old_landuse,
        'optimal_solar': optimal_solar,
        'new_solar': fixed_values['ziel_912'],
        'storage_drift': final_drift,
        'annual_electricity': annual_electricity,
        'iterations': goal_seek_result['iterations'],
    }
