"""
Bilanz (Balance Sheet) Calculation Engine

This module handles all calculations for the Bilanz diagram, which compares:
- Supply (Aktiva): Renewable + Fossil energy sources
- Demand (Passiva): Energy consumption by sector

All data comes dynamically from RenewableData and VerbrauchData models.
No hardcoded values.
"""

from django.apps import apps
from simulator.models import Formula
from simulator.formula_service import _safe_eval


# =============================================================================
# EXTENSIBILITY HELPERS: Auto-sum children by parent_code
# =============================================================================
# When you add a new energy source (e.g., 10.7 Tidal) via Django Admin,
# these functions automatically include it in parent totals - NO CODE CHANGES NEEDED!
# =============================================================================

def sum_renewable_children(parent_code: str, use_target: bool = True) -> float:
    """
    🔄 AUTO-SUM: Sum all RenewableData items that are children of the given parent_code.
    
    This makes the system EXTENSIBLE:
    - Add new RenewableData "10.3.5 Tidal" 
    - It's automatically included in 10.3 totals!
    - No code changes needed.
    
    Uses CODE PREFIX MATCHING to find children:
    - Parent "10.3" matches children "10.3.1", "10.3.2", "10.3.3", etc.
    - Only matches DIRECT children (one level deeper)
    
    Args:
        parent_code: The parent code to sum children of (e.g., '10.3')
        use_target: If True, sum target_value; if False, sum status_value
    
    Returns:
        float: Sum of all children's values
    
    Example:
        sum_renewable_children('10.3')  # Returns sum of 10.3.1, 10.3.2, 10.3.3, etc.
    """
    RenewableData = apps.get_model('simulator', 'RenewableData')
    
    # Calculate expected child code pattern
    # Parent "10.3" → children start with "10.3." and have one more level
    parent_depth = parent_code.count('.') + 1  # 10.3 has depth 2, children have depth 3
    
    # Find all items that start with parent_code followed by a dot
    prefix = f"{parent_code}."
    all_descendants = RenewableData.objects.filter(code__startswith=prefix)
    
    total = 0.0
    for item in all_descendants:
        # Only include DIRECT children (one level deeper)
        item_depth = item.code.count('.') + 1
        if item_depth == parent_depth + 1:
            if use_target:
                val = item.target_value
            else:
                val = item.status_value
            total += float(val or 0)
    
    return total


def sum_verbrauch_children(parent_code: str, use_ziel: bool = True) -> float:
    """
    🔄 AUTO-SUM: Sum all VerbrauchData items that are children of the given parent_code.
    
    This makes the system EXTENSIBLE for consumption data as well.
    Uses CODE PREFIX MATCHING to find children.
    
    Args:
        parent_code: The parent code to sum children of (e.g., '1.4')
        use_ziel: If True, sum ziel; if False, sum status
    
    Returns:
        float: Sum of all children's values
    """
    VerbrauchData = apps.get_model('simulator', 'VerbrauchData')
    
    # Calculate expected child code pattern
    parent_depth = parent_code.count('.') + 1
    
    # Find all items that start with parent_code followed by a dot
    prefix = f"{parent_code}."
    all_descendants = VerbrauchData.objects.filter(code__startswith=prefix)
    
    total = 0.0
    for item in all_descendants:
        # Only include DIRECT children (one level deeper)
        item_depth = item.code.count('.') + 1
        if item_depth == parent_depth + 1:
            if use_ziel:
                val = item.ziel
            else:
                val = item.status
            total += float(val or 0)
    
    return total


def get_all_sector_parents() -> dict:
    """
    🔄 AUTO-DISCOVER: Get all sector parent codes dynamically.
    
    Instead of hardcoding ['10.3', '10.4', '10.5', '10.6'], 
    this finds all unique parent codes under a given root.
    
    Future-proof: If you add 10.7, 10.8, etc., they're auto-discovered!
    """
    RenewableData = apps.get_model('simulator', 'RenewableData')
    
    # Find all items with parent_code starting with '10.'
    sector_items = RenewableData.objects.filter(
        code__startswith='10.',
        parent_code='10'
    ).values_list('code', flat=True)
    
    return list(sector_items)


def get_renewable_with_children_sum(code: str, use_target: bool = True, include_children: bool = True) -> float:
    """
    🔄 HYBRID: Get a renewable value, optionally including sum of children.
    
    This combines:
    1. The parent's own value (if any)
    2. The sum of all children (if include_children=True)
    
    Useful for parent codes like '10.3' that might have:
    - Their own stored value (summary)
    - OR should be calculated from children (10.3.1 + 10.3.2 + ...)
    
    Args:
        code: The code to get value for
        use_target: If True, use target_value; if False, use status_value
        include_children: If True, also sum children
    
    Returns:
        float: The value (parent + children if include_children=True)
    """
    RenewableData = apps.get_model('simulator', 'RenewableData')
    
    try:
        item = RenewableData.objects.get(code=code)
        own_value = (item.target_value if use_target else item.status_value) or 0
    except RenewableData.DoesNotExist:
        own_value = 0
    
    if include_children:
        children_sum = sum_renewable_children(code, use_target)
        # If parent has a value AND children exist, use children sum (more accurate)
        # This handles cases where parent is a calculated summary
        if children_sum > 0:
            return children_sum
        return float(own_value)
    
    return float(own_value)


def _get_constant(name: str) -> float:
    """
    Load bilanz constants from database (category='bilanz_constant').
    No hardcoded fallbacks: a missing constant raises to enforce DB completeness.
    """
    try:
        obj = Formula.objects.get(key=name, category="bilanz_constant", is_active=True)
        return float(obj.expression)
    except Formula.DoesNotExist as exc:
        raise ValueError(f"Bilanz constant '{name}' missing in database (category bilanz_constant)") from exc


def get_renewable_value(code, use_target=True, fail_fast=True):
    """
    Get renewable energy value from RenewableData model.
    
    FAIL-FAST MODE (default):
    - Raises ValueError if code not found
    - Raises ValueError if calculated value is None
    - NO silent fallbacks to 0
    
    Args:
        code: RenewableData code (e.g., '10.2' for renewable electricity)
        use_target: If True, returns target_value; if False, returns status_value
        fail_fast: If True (default), raises on missing data instead of returning 0
        
    Returns:
        float: The value
        
    Raises:
        ValueError: If code not found or value is None (when fail_fast=True)
    """
    try:
        RenewableData = apps.get_model('simulator', 'RenewableData')
        renewable = RenewableData.objects.get(code=code)
    except RenewableData.DoesNotExist:
        if fail_fast:
            raise ValueError(f"RenewableData code '{code}' not found in database")
        return 0
    
    # Always recalculate for non-fixed values
    if not renewable.is_fixed:
        try:
            status, target = renewable.get_calculated_values()
            value = target if use_target else status
            
            if value is None and fail_fast:
                raise ValueError(
                    f"Calculated value for RenewableData '{code}' is None. "
                    f"Check formula and FormulaVariables in database."
                )
            return value if value is not None else 0
        except Exception as e:
            if fail_fast:
                raise ValueError(f"Error calculating RenewableData '{code}': {e}") from e
            return 0
    
    # Fixed values
    value = renewable.target_value if use_target else renewable.status_value
    if value is None and fail_fast:
        raise ValueError(f"RenewableData '{code}' has no stored value (is_fixed=True but value is None)")
    return value if value is not None else 0


def get_renewable_raw(code, field="target"):
    """
    Get raw stored renewable value (status_value/target_value) without recalculation.
    """
    try:
        RenewableData = apps.get_model('simulator', 'RenewableData')
        renewable = RenewableData.objects.get(code=code)
        if field == "target":
            return renewable.target_value or 0
        return renewable.status_value or 0
    except Exception as e:
        print(f"Warning: Could not get raw renewable value for code {code}: {e}")
        return 0


def get_verbrauch_value(code, use_ziel=True, fail_fast=True):
    """
    Get consumption value from VerbrauchData model.
    
    FAIL-FAST MODE (default):
    - Raises ValueError if code not found
    - Raises ValueError if calculated value is None
    - NO silent fallbacks to 0
    
    Args:
        code: VerbrauchData code (e.g., '1.4' for KLIK electricity)
        use_ziel: If True, returns ziel; if False, returns status
        fail_fast: If True (default), raises on missing data instead of returning 0
        
    Returns:
        float: The value
        
    Raises:
        ValueError: If code not found or value is None (when fail_fast=True)
    """
    try:
        VerbrauchData = apps.get_model('simulator', 'VerbrauchData')
        verbrauch = VerbrauchData.objects.get(code=code)
    except VerbrauchData.DoesNotExist:
        if fail_fast:
            raise ValueError(f"VerbrauchData code '{code}' not found in database")
        return 0
    
    # Recalculate if marked as calculated
    if verbrauch.is_calculated or (use_ziel and verbrauch.ziel_calculated) or (not use_ziel and verbrauch.status_calculated):
        try:
            if use_ziel:
                value = verbrauch.calculate_ziel_value()
            else:
                value = verbrauch.calculate_value()
            
            if value is None and fail_fast:
                raise ValueError(
                    f"Calculated value for VerbrauchData '{code}' is None. "
                    f"Check formula in database."
                )
            return value if value is not None else 0
        except Exception as e:
            if fail_fast:
                raise ValueError(f"Error calculating VerbrauchData '{code}': {e}") from e
            return 0
    
    # Fixed values
    value = verbrauch.ziel if use_ziel else verbrauch.status
    if value is None and fail_fast:
        raise ValueError(f"VerbrauchData '{code}' has no stored value")
    return value if value is not None else 0


def calculate_bilanz_data(fail_fast=False):
    """
    Calculate all bilanz (balance sheet) data dynamically from RenewableData and VerbrauchData.
    
    Args:
        fail_fast: If True, raises on missing formulas. If False (default for backward compat), returns 0.
    
    Returns:
        dict: Complete bilanz data structure with all categories
    """
    # Pre-build lookup with Verbrauch_*, Renewable_* prefixes ONCE
    names = {}
    VerbrauchData = apps.get_model('simulator', 'VerbrauchData')
    RenewableData = apps.get_model('simulator', 'RenewableData')
    
    # Use .values() for faster performance
    for v in VerbrauchData.objects.values('code', 'status', 'ziel'):
        code_clean = v['code'].replace('.', '_')
        names[f"Verbrauch_{code_clean}"] = float(v['status'] or 0)
        names[f"Verbrauch_{code_clean}_T"] = float(v['ziel'] or 0)
    for r in RenewableData.objects.values('code', 'status_value', 'target_value'):
        code_clean = r['code'].replace('.', '_')
        names[f"Renewable_{code_clean}"] = float(r['status_value'] or 0)
        names[f"Renewable_{code_clean}_T"] = float(r['target_value'] or 0)

    # Resolve all bilanz formulas via DB (category='bilanz')
    def eval_bilanz(key):
        try:
            f = Formula.objects.get(key=key, category='bilanz', is_active=True)
        except Formula.DoesNotExist:
            if fail_fast:
                raise ValueError(f"Bilanz formula '{key}' not found in database (category=bilanz)")
            return 0.0
        
        # Include previously computed bilanz values to allow chaining
        names.update(computed)
        val = _safe_eval(f.expression, names, use_target=True)
        
        if val is None and fail_fast:
            raise ValueError(f"Bilanz formula '{key}' evaluated to None. Expression: {f.expression}")
        return float(val or 0)

    computed = {}
    # Electricity totals
    computed['BILANZ_VERB_STROM_STATUS'] = eval_bilanz('BILANZ_VERB_STROM_STATUS')
    computed['BILANZ_VERB_STROM_ZIEL'] = eval_bilanz('BILANZ_VERB_STROM_ZIEL')
    computed['BILANZ_REN_STROM_STATUS'] = eval_bilanz('BILANZ_REN_STROM_STATUS')
    computed['BILANZ_REN_STROM_ZIEL'] = eval_bilanz('BILANZ_REN_STROM_ZIEL')
    computed['BILANZ_REN_STROM_FOSSIL_STATUS'] = eval_bilanz('BILANZ_REN_STROM_FOSSIL_STATUS')
    computed['BILANZ_REN_STROM_FOSSIL_ZIEL'] = eval_bilanz('BILANZ_REN_STROM_FOSSIL_ZIEL')
    # Fuels
    computed['BILANZ_VERB_FUELS_STATUS'] = eval_bilanz('BILANZ_VERB_FUELS_STATUS')
    computed['BILANZ_VERB_FUELS_ZIEL'] = eval_bilanz('BILANZ_VERB_FUELS_ZIEL')
    computed['BILANZ_REN_FUELS_STATUS'] = eval_bilanz('BILANZ_REN_FUELS_STATUS')
    computed['BILANZ_REN_FUELS_ZIEL'] = eval_bilanz('BILANZ_REN_FUELS_ZIEL')
    computed['BILANZ_REN_FUELS_FOSSIL_STATUS'] = eval_bilanz('BILANZ_REN_FUELS_FOSSIL_STATUS')
    computed['BILANZ_REN_FUELS_FOSSIL_ZIEL'] = eval_bilanz('BILANZ_REN_FUELS_FOSSIL_ZIEL')
    # Heat
    computed['BILANZ_VERB_HEAT_STATUS'] = eval_bilanz('BILANZ_VERB_HEAT_STATUS')
    computed['BILANZ_VERB_HEAT_ZIEL'] = eval_bilanz('BILANZ_VERB_HEAT_ZIEL')
    computed['BILANZ_REN_HEAT_STATUS'] = eval_bilanz('BILANZ_REN_HEAT_STATUS')
    computed['BILANZ_REN_HEAT_ZIEL'] = eval_bilanz('BILANZ_REN_HEAT_ZIEL')
    computed['BILANZ_REN_HEAT_FOSSIL_STATUS'] = eval_bilanz('BILANZ_REN_HEAT_FOSSIL_STATUS')
    computed['BILANZ_REN_HEAT_FOSSIL_ZIEL'] = eval_bilanz('BILANZ_REN_HEAT_FOSSIL_ZIEL')
    # Totals
    computed['BILANZ_VERB_TOTAL_STATUS'] = eval_bilanz('BILANZ_VERB_TOTAL_STATUS')
    computed['BILANZ_VERB_TOTAL_ZIEL'] = eval_bilanz('BILANZ_VERB_TOTAL_ZIEL')
    
    # ============================================================================
    # SECTION 4: VERBRAUCH GESAMT (Total Consumption)
    # ============================================================================
    
    # Use direct total codes from VerbrauchData - use same code for both status and ziel
    # The code is the same, but we pull from different columns (status vs ziel)
    
    # KLIK: Code 1.4 - status column for Status, ziel column for Ziel
    klik_total_s = get_verbrauch_value('1.4', use_ziel=False)    # Status column
    klik_total_t = get_verbrauch_value('1.4', use_ziel=True)     # Ziel column
    
    # Gebäudewärme: Code 2.10 - status column for Status, ziel column for Ziel
    gw_total_s = get_verbrauch_value('2.10', use_ziel=False)     # Status column: 798,867
    gw_total_t = get_verbrauch_value('2.10', use_ziel=True)      # Ziel column: 663,397
    
    # Prozesswärme: Code 3.3 - status column for Status, ziel column for Ziel
    pw_total_s = get_verbrauch_value('3.7', use_ziel=False)      # Prozesswärme gesamt status
    pw_total_t = get_verbrauch_value('3.7', use_ziel=True)       # Prozesswärme gesamt ziel
    
    # Mobile: Code 6.0 (was 4.3.1) - status column for Status, ziel column for Ziel
    mobile_total_s = get_verbrauch_value('6.0', use_ziel=False)  # Status column: 753,713
    mobile_total_t = get_verbrauch_value('6.0', use_ziel=True)   # Ziel column: 388,761
    
    # Total consumption by sector (using direct codes from same row, different columns)
    verbrauch_gesamt = {
        'status': {
            'kraft_licht': klik_total_s,
            'gebaeudewaerme': gw_total_s,
            'prozesswaerme': pw_total_s,
            'mobile': mobile_total_s,
            'gesamt': klik_total_s + gw_total_s + pw_total_s + mobile_total_s,
        },
        'ziel': {
            'kraft_licht': klik_total_t,
            'gebaeudewaerme': gw_total_t,
            'prozesswaerme': pw_total_t,
            'mobile': mobile_total_t,
            'gesamt': klik_total_t + gw_total_t + pw_total_t + mobile_total_t,
        }
    }

    # ============================================================================
    # SECTION 5: RENEWABLE BY SECTOR (direct RenewableData codes 10.3–10.6)
    # ============================================================================
    def safe_get_renewable(code: str, use_target: bool):
        try:
            return get_renewable_value(code, use_target=use_target)
        except Exception:
            return 0

    renewable_by_sector = {
        'status': {
            'kraft_licht': safe_get_renewable('10.3.1', use_target=False),
            'gebaeudewaerme': safe_get_renewable('10.4.3', use_target=False),
            'prozesswaerme': safe_get_renewable('10.5.3', use_target=False),
            'mobile': safe_get_renewable('10.6.2', use_target=False),
        },
        'ziel': {
            'kraft_licht': safe_get_renewable('10.3.1', use_target=True),
            'gebaeudewaerme': safe_get_renewable('10.4.3', use_target=True),
            'prozesswaerme': safe_get_renewable('10.5.3', use_target=True),
            'mobile': safe_get_renewable('10.6.2', use_target=True),
        },
    }
    renewable_by_sector['status']['gesamt'] = sum(renewable_by_sector['status'].values())
    renewable_by_sector['ziel']['gesamt'] = sum(renewable_by_sector['ziel'].values())

    # ============================================================================
    # SECTION 6: VERBRAUCH GESAMT FOSSIL (remaining after renewable by sector)
    # ============================================================================
    def residual(total_dict, ren_dict):
        res = {
            'kraft_licht': max(0, (total_dict.get('kraft_licht') or 0) - (ren_dict.get('kraft_licht') or 0)),
            'gebaeudewaerme': max(0, (total_dict.get('gebaeudewaerme') or 0) - (ren_dict.get('gebaeudewaerme') or 0)),
            'prozesswaerme': max(0, (total_dict.get('prozesswaerme') or 0) - (ren_dict.get('prozesswaerme') or 0)),
            'mobile': max(0, (total_dict.get('mobile') or 0) - (ren_dict.get('mobile') or 0)),
        }
        res['gesamt'] = sum(res.values())
        return res

    # This will be refined later after helper functions are defined
    verbrauch_gesamt_fossil = {
        'status': residual(verbrauch_gesamt['status'], renewable_by_sector['status']),
        'ziel': residual(verbrauch_gesamt['ziel'], renewable_by_sector['ziel']),
    }

    # Fuels breakdown via DB formulas (gaseous/liquid/solid)
    fuels_breakdown = {
        'gaseous': {
            'status': eval_bilanz('BILANZ_FUELS_BREAKDOWN_GASEOUS_STATUS'),
            'ziel': eval_bilanz('BILANZ_FUELS_BREAKDOWN_GASEOUS_ZIEL'),
        },
        'liquid': {
            'status': eval_bilanz('BILANZ_FUELS_BREAKDOWN_LIQUID_STATUS'),
            'ziel': eval_bilanz('BILANZ_FUELS_BREAKDOWN_LIQUID_ZIEL'),
        },
        'solid': {
            'status': eval_bilanz('BILANZ_FUELS_BREAKDOWN_SOLID_STATUS'),
            'ziel': eval_bilanz('BILANZ_FUELS_BREAKDOWN_SOLID_ZIEL'),
        },
    }

    # Placeholder for Abwärme (no current data source)
    verbrauch_heat_abwaerme = {
        'status': {
            'kraft_licht': 0,
            'gebaeudewaerme': 0,
            'prozesswaerme': 0,
            'mobile': 0,
            'gesamt': 0,
        },
        'ziel': {
            'kraft_licht': 0,
            'gebaeudewaerme': 0,
            'prozesswaerme': 0,
            'mobile': 0,
            'gesamt': 0,
        }
    }

    # ============================================================================
    # RETURN COMPLETE DATA STRUCTURE
    # ============================================================================

    # Helper to create sector structure from a single total value
    def create_sector_dict(total_value):
        return {
            'kraft_licht': 0,
            'gebaeudewaerme': 0,
            'prozesswaerme': 0,
            'mobile': 0,
            'gesamt': total_value,
        }

    # Helper to get sector-based dictionary for a specific energy type
    def get_sector_data(codes, use_ziel):
        # codes map: {'kraft_licht': '1.4', 'gebaeudewaerme': '2.9', ...}
        data = {}
        total = 0
        for sector, code in codes.items():
            if code:
                val = get_verbrauch_value(code, use_ziel=use_ziel, fail_fast=False)
                data[sector] = val
                total += val
            else:
                data[sector] = 0
        data['gesamt'] = total
        return data

    # Helper to get sector-based dictionary for renewables
    # 🔄 EXTENSIBLE: Now uses auto-sum for parent codes!
    def get_sector_renewable_data(codes, use_target):
        """
        Get renewable values by sector, with AUTO-SUM for extensibility.
        
        When a parent code (like '10.3') is provided, this automatically
        sums all children (10.3.1, 10.3.2, 10.3.3, etc.).
        
        If you add 10.3.5 via Admin, it's automatically included!
        """
        data = {}
        total = 0
        for sector, code in codes.items():
            if code:
                # 🔄 Use get_renewable_with_children_sum for auto-inclusion of new sources
                val = get_renewable_with_children_sum(code, use_target=use_target, include_children=True)
                data[sector] = val
                total += val
            else:
                data[sector] = 0
        data['gesamt'] = total
        return data

    # Define code mappings for different energy types in VerbrauchData
    strom_codes = {
        'kraft_licht': '1.4',
        'gebaeudewaerme': '2.9.2',
        'prozesswaerme': '3.6.0',
        'mobile': '6.2'  # was 4.3.6
    }
    
    fuel_codes = {
        'kraft_licht': None, # Usually 0
        'gebaeudewaerme': '2.7.0',
        'prozesswaerme': '3.4.0',
        'mobile': '6.1'  # was 4.3.2
    }

    fuel_renewable_codes = {
        'kraft_licht': None,
        'gebaeudewaerme': '10.4.1',
        'prozesswaerme': '10.5.1',
        'mobile': '10.6.1'
    }
    
    heat_renewable_codes = {
        'kraft_licht': None,
        'gebaeudewaerme': '10.4.2',
        'prozesswaerme': '10.5.2',
        'mobile': None
    }
    
    # Helper for Abwärme Gebäudewärme - STATUS column (original formula)
    def get_abwaerme_gebaeudewaerme_status():
        codes = ['4.3.4.2', '4.4.1', '5.4.2.4', '6.1.3.2.4', '9.3.2.1']
        total_val = 0
        for c in codes:
            total_val += safe_get_renewable(c, use_target=False)
        return total_val
    
    # Helper for Abwärme Gebäudewärme - ZIEL column
    # Formula: 4.3.3.4 status + 4.4.2 status + 5.4.2.4 status + 6.1.3.2.4 status
    # Note: Uses STATUS values from RenewableData for Ziel display in Bilanz
    def get_abwaerme_gebaeudewaerme_ziel():
        codes = ['4.3.3.4', '4.4.2', '5.4.2.4', '6.1.3.2.4']
        total_val = 0
        for c in codes:
            total_val += safe_get_renewable(c, use_target=False)  # Use status values
        return total_val

    abwaerme_status_gw = get_abwaerme_gebaeudewaerme_status()
    abwaerme_ziel_gw = get_abwaerme_gebaeudewaerme_ziel()

    verbrauch_heat_abwaerme = {
        'status': {
            'kraft_licht': 0,
            'gebaeudewaerme': abwaerme_status_gw,
            'prozesswaerme': 0,
            'mobile': 0,
            'gesamt': abwaerme_status_gw,
        },
        'ziel': {
            'kraft_licht': 0,
            'gebaeudewaerme': abwaerme_ziel_gw,
            'prozesswaerme': 0,
            'mobile': 0,
            'gesamt': abwaerme_ziel_gw,
        }
    }

    # Helper for Heat Renewable with Abwärme extraction
    def get_heat_renewable_refined(use_target):
        data = get_sector_renewable_data(heat_renewable_codes, use_target)
        ab = abwaerme_ziel_gw if use_target else abwaerme_status_gw
        # For Gebäudewärme, user wants 10.4.2 - Abwärme
        data['gebaeudewaerme'] = max(0, data['gebaeudewaerme'] - ab)
        # Recalculate gesamt
        data['gesamt'] = (data.get('kraft_licht') or 0) + (data.get('gebaeudewaerme') or 0) + \
                        (data.get('prozesswaerme') or 0) + (data.get('mobile') or 0)
        return data

    # Heat residual: Total - Renewable - Abwärme
    def heat_residual(total_dict, ren_dict, ab_dict):
        res = {
            'kraft_licht': max(0, (total_dict.get('kraft_licht') or 0) - (ren_dict.get('kraft_licht') or 0) - (ab_dict.get('kraft_licht') or 0)),
            'gebaeudewaerme': max(0, (total_dict.get('gebaeudewaerme') or 0) - (ren_dict.get('gebaeudewaerme') or 0) - (ab_dict.get('gebaeudewaerme') or 0)),
            'prozesswaerme': max(0, (total_dict.get('prozesswaerme') or 0) - (ren_dict.get('prozesswaerme') or 0) - (ab_dict.get('prozesswaerme') or 0)),
            'mobile': max(0, (total_dict.get('mobile') or 0) - (ren_dict.get('mobile') or 0) - (ab_dict.get('mobile') or 0)),
        }
        res['gesamt'] = sum(res.values())
        return res

    v_heat_status_ren = get_heat_renewable_refined(False)
    v_heat_ziel_ren = get_heat_renewable_refined(True)

    # NOW CALCULATE TOTAL RENEWABLES AND RESIDUAL FOSSIL
    total_renewable_codes = {
        'kraft_licht': '10.3',
        'gebaeudewaerme': '10.4',
        'prozesswaerme': '10.5',
        'mobile': '10.6'
    }

    renewable_gesamt_by_sector = {
        'status': get_sector_renewable_data(total_renewable_codes, False),
        'ziel': get_sector_renewable_data(total_renewable_codes, True),
    }

    # RE-ESTABLISH verbrauch_gesamt_fossil using total renewables
    verbrauch_gesamt_fossil = {
        'status': residual(verbrauch_gesamt['status'], renewable_gesamt_by_sector['status']),
        'ziel': residual(verbrauch_gesamt['ziel'], renewable_gesamt_by_sector['ziel']),
    }

    heat_codes = {
        'kraft_licht': None,
        'gebaeudewaerme': '2.8.0',
        'prozesswaerme': '3.5.0',
        'mobile': None
    }

    # Final data structure assembly
    return {
        'verbrauch_strom': {
            'status': get_sector_data(strom_codes, False),
            'ziel': get_sector_data(strom_codes, True),
        },
        'verbrauch_strom_renewable': {
            'status': renewable_by_sector['status'],
            'ziel': renewable_by_sector['ziel'],
        },
        'verbrauch_strom_fossil': {
            'status': residual(get_sector_data(strom_codes, False), renewable_by_sector['status']),
            'ziel': residual(get_sector_data(strom_codes, True), renewable_by_sector['ziel']),
        },
        'verbrauch_fuels': {
            'status': get_sector_data(fuel_codes, False),
            'ziel': get_sector_data(fuel_codes, True),
        },
        'verbrauch_fuels_renewable': {
            'status': get_sector_renewable_data(fuel_renewable_codes, False),
            'ziel': get_sector_renewable_data(fuel_renewable_codes, True),
        },
        'verbrauch_fuels_fossil': {
            'status': residual(get_sector_data(fuel_codes, False), get_sector_renewable_data(fuel_renewable_codes, False)),
            'ziel': residual(get_sector_data(fuel_codes, True), get_sector_renewable_data(fuel_renewable_codes, True)),
        },
        'fuels_breakdown': fuels_breakdown,
        'verbrauch_heat': {
            'status': get_sector_data(heat_codes, False),
            'ziel': get_sector_data(heat_codes, True),
        },
        'verbrauch_heat_renewable': {
            'status': v_heat_status_ren,
            'ziel': v_heat_ziel_ren,
        },
        'verbrauch_heat_fossil': {
            'status': heat_residual(get_sector_data(heat_codes, False), v_heat_status_ren, verbrauch_heat_abwaerme['status']),
            'ziel': heat_residual(get_sector_data(heat_codes, True), v_heat_ziel_ren, verbrauch_heat_abwaerme['ziel']),
        },
        'verbrauch_heat_abwaerme': verbrauch_heat_abwaerme,
        'verbrauch_gesamt': verbrauch_gesamt,
        'verbrauch_gesamt_fossil': verbrauch_gesamt_fossil,
        'erneuerbar': renewable_by_sector,
        'renewable_by_sector': renewable_by_sector,
        'renewable_gesamt_by_sector': renewable_gesamt_by_sector,
    }
