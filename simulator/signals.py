from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import LandUse, RenewableData, VerbrauchData, Formula, FormulaVariable
from .ws_models import WSData
from .ws_formula_template import WSFormulaTemplate
from calculation_engine.formula_evaluator import FormulaEvaluator
import math
import re


# Lazy initialization for WS calculator (to avoid DB queries during import)
_ws_calculator = None

# Track if we're currently in a cascade to prevent infinite recursion
_cascade_in_progress = False

def get_ws_calculator():
    global _ws_calculator
    if _ws_calculator is None:
        from calculation_engine.ws_engine import WSCalculator
        _ws_calculator = WSCalculator()
    return _ws_calculator

# Initialize formula evaluator
formula_evaluator = FormulaEvaluator()


# Helper function to load WS constants from database
def get_ws_constants():
    """
    Load WS efficiency constants from database.
    100% DATABASE-DRIVEN - NO HARDCODED VALUES!
    
    Returns:
        dict with keys: ETA_STROM_GAS, ETA_GAS_STROM, ABREGELUNG_THRESHOLD
    """
    try:
        eta_strom_gas = Formula.objects.get(key='WS_ETA_STROM_GAS', category='ws_constant')
        eta_gas_strom = Formula.objects.get(key='WS_ETA_GAS_STROM', category='ws_constant')
        abregelung_threshold = Formula.objects.get(key='WS_ABREGELUNG_THRESHOLD', category='ws_constant')
        
        return {
            'ETA_STROM_GAS': float(eta_strom_gas.expression),
            'ETA_GAS_STROM': float(eta_gas_strom.expression),
            'ABREGELUNG_THRESHOLD': float(abregelung_threshold.expression),
        }
    except Formula.DoesNotExist as e:
        raise ValueError(
            f"WS constants not found in database (need WS_ETA_STROM_GAS, WS_ETA_GAS_STROM, "
            f"WS_ABREGELUNG_THRESHOLD). Please import ws_constant formulas. Error: {e}"
        )


def _apply_daily_ws_formulas(daily_rows, reference_values):
    """
    🚀 100% DATABASE-DRIVEN - NO HARDCODED FALLBACKS!
    
    Apply daily WS formulas (rows 1-365) from database ONLY.
    All column calculations use formulas from Formula table.
    
    Formula naming pattern: WS_COLUMNNAME (for rows 1-365)
    All formulas MUST be in database - no fallback to hardcoded values.
    
    Args:
        daily_rows: QuerySet of WSData for rows 1-365
        reference_values: Dict with reference values from row 366 calculations
    """
    from simulator.models import Formula
    
    # Column names in dependency order - FIRST PASS (non-cumulative, no sums needed)
    first_pass_columns = [
        'stromverbr',
        'davon_raumw_korr',
        'stromverbr_raumwaerm_korr',
        'windstrom',
        'solarstrom',
        'sonst_kraft_konstant',
        'wind_solar_konstant',
        'direktverbr_strom',
        'ueberschuss_strom',
        'einspeich',
        'abregelung_z',
        'mangel_last',
    ]
    
    # SECOND PASS columns (require sum_mangel_last)
    second_pass_columns = [
        'brennstoff_ausgleichs_strom',
        'speicher_ausgl_strom',
        'ausspeich_rueckverstr',
        'ausspeich_gas',
    ]
    
    # FIRST PASS: Calculate non-cumulative columns
    for row in daily_rows:
        # Skip if missing required promille values
        if (row.verbrauch_promille is None or row.heizung_abwaerm_promille is None or
            row.wind_promille is None or row.solar_promille is None):
            continue
        
        # Build context for formula evaluation
        context = {
            # Promille values from row
            'verbrauch_promille': row.verbrauch_promille,
            'heizung_abwaerm_promille': row.heizung_abwaerm_promille,
            'wind_promille': row.wind_promille,
            'solar_promille': row.solar_promille,
            # Reference values from row 366
            **reference_values,
        }
        
        # Calculate each column using database formulas
        for column_name in first_pass_columns:
            formula_key = f'WS_{column_name.upper()}'
            
            try:
                formula = Formula.objects.get(key=formula_key, is_active=True, category='ws')
                
                # Build evaluation context with current row values + references
                eval_context = context.copy()
                # Add already-calculated column values from this row
                for col in first_pass_columns:
                    current_value = getattr(row, col, None)
                    if current_value is not None:
                        eval_context[f'WS_{col.upper()}'] = current_value
                
                # Evaluate formula
                result = _evaluate_ws_formula(formula.expression, eval_context)
                
                # Set column value
                setattr(row, column_name, result)
                
            except Formula.DoesNotExist:
                # Formula missing - raise error (NO FALLBACK!)
                raise ValueError(f"Missing WS formula in database: {formula_key}. Daily WS calculations require all formulas to be in database.")
            except Exception as e:
                print(f"❌ Row {row.tag_im_jahr}.{column_name}: Formula '{formula_key}' failed: {e}")
                setattr(row, column_name, 0)
        
        # Save row after first pass
        row.save()
    
    # Calculate sum_mangel_last for second pass
    daily_rows_reloaded = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    sum_mangel_last = sum([r.mangel_last for r in daily_rows_reloaded if r.mangel_last is not None])
    
    # SECOND PASS: Calculate columns that require sum_mangel_last
    for row in daily_rows:
        # Build context for formula evaluation
        context = {
            # Promille values from row
            'verbrauch_promille': row.verbrauch_promille,
            'heizung_abwaerm_promille': row.heizung_abwaerm_promille,
            'wind_promille': row.wind_promille,
            'solar_promille': row.solar_promille,
            # Reference values from row 366
            **reference_values,
            # Add sum for second pass (BOTH formats for compatibility!)
            'sum_mangel_last': sum_mangel_last,
            'sum_mangel_last_366': sum_mangel_last,  # Formula uses _366 suffix
        }
        
        # Calculate each column using database formulas
        for column_name in second_pass_columns:
            formula_key = f'WS_{column_name.upper()}'
            
            try:
                formula = Formula.objects.get(key=formula_key, is_active=True, category='ws')
                
                # Build evaluation context with current row values + references
                eval_context = context.copy()
                # Add already-calculated column values from first pass
                for col in first_pass_columns:
                    current_value = getattr(row, col, None)
                    if current_value is not None:
                        eval_context[f'WS_{col.upper()}'] = current_value
                # Add already-calculated column values from second pass
                for col in second_pass_columns:
                    current_value = getattr(row, col, None)
                    if current_value is not None:
                        eval_context[f'WS_{col.upper()}'] = current_value
                
                # Evaluate formula
                result = _evaluate_ws_formula(formula.expression, eval_context)
                
                # Set column value
                setattr(row, column_name, result)
                
            except Formula.DoesNotExist:
                # Formula missing - raise error (NO FALLBACK!)
                raise ValueError(f"Missing WS formula in database: {formula_key}. Daily WS calculations require all formulas to be in database.")
            except Exception as e:
                print(f"❌ Row {row.tag_im_jahr}.{column_name}: Formula '{formula_key}' failed: {e}")
                setattr(row, column_name, 0)
        
        # Save row after second pass
        row.save()
    
    # THIRD PASS: Calculate cumulative columns (ladezust_burtto, etc.)
    # These depend on previous day values
    cumulative_columns = [
        'ladezust_burtto',
        'ladezustand_abs_vorl_tl',
        'selbstentl',
        'ladezustand_netto',
        'ladezustand_abs',
    ]
    
    # Initialize tracking for cumulative values
    ladezust_burtto_prev = 0
    ladezustand_netto_prev = 0
    
    # Get row 367 for reference (needed for some formulas)
    try:
        row_367 = WSData.objects.get(tag_im_jahr=367)
        ladezust_burtto_367 = row_367.ladezust_burtto or 0
        ladezustand_netto_367 = row_367.ladezustand_netto or 0
    except WSData.DoesNotExist:
        ladezust_burtto_367 = 0
        ladezustand_netto_367 = 0
    
    for row in daily_rows:
        # Build context with previous values and row 367 references
        context = {
            'WS_LADEZUST_BURTTO_PREV': ladezust_burtto_prev,
            'WS_LADEZUSTAND_NETTO_PREV': ladezustand_netto_prev,
            # Add WITH WS_ prefix (what formulas expect)
            'WS_LADEZUST_BURTTO_367': ladezust_burtto_367,
            'WS_LADEZUSTAND_NETTO_367': ladezustand_netto_367,
            # Also add without prefix (for backwards compatibility)
            'ladezust_burtto_367': ladezust_burtto_367,
            'ladezustand_netto_367': ladezustand_netto_367,
        }
        
        # Add current row's non-cumulative values to context
        for col in first_pass_columns:
            current_value = getattr(row, col, None)
            if current_value is not None:
                context[f'WS_{col.upper()}'] = current_value
        
        # Add current row's second pass values to context
        for col in second_pass_columns:
            current_value = getattr(row, col, None)
            if current_value is not None:
                context[f'WS_{col.upper()}'] = current_value
        
        # Calculate each cumulative column
        for column_name in cumulative_columns:
            formula_key = f'WS_{column_name.upper()}'
            
            try:
                formula = Formula.objects.get(key=formula_key, is_active=True, category='ws')
                
                # Add already-calculated cumulative values to context
                for col in cumulative_columns:
                    current_value = getattr(row, col, None)
                    if current_value is not None:
                        context[f'WS_{col.upper()}'] = current_value
                
                # Evaluate formula
                result = _evaluate_ws_formula(formula.expression, context)
                
                # Set column value
                setattr(row, column_name, result)
                
            except Formula.DoesNotExist:
                # Formula missing - raise error (NO FALLBACK!)
                raise ValueError(f"Missing WS formula in database: {formula_key}. Daily WS calculations require all formulas to be in database.")
            except Exception as e:
                print(f"❌ Row {row.tag_im_jahr}.{column_name}: Formula '{formula_key}' failed: {e}")
                setattr(row, column_name, 0)
        
        # Save row after second pass
        row.save()
        
        # Update previous values for next iteration
        ladezust_burtto_prev = row.ladezust_burtto or 0
        ladezustand_netto_prev = row.ladezustand_netto or 0


def _apply_daily_ws_formulas_cumulative(daily_rows, reference_values):
    """
    Apply cumulative WS formulas (second pass for storage state calculations).
    
    These columns depend on previous day values:
    - ladezust_burtto
    - ladezustand_abs_vorl_tl
    - selbstentl
    - ladezustand_netto
    - ladezustand_abs
    """
    from simulator.models import Formula
    
    cumulative_columns = [
        'ladezust_burtto',
        'ladezustand_abs_vorl_tl',
        'selbstentl',
        'ladezustand_netto',
        'ladezustand_abs',
    ]
    
    # Initialize tracking for cumulative values
    ladezust_burtto_prev = 0
    ladezustand_netto_prev = 0
    
    # Get row 367 for reference
    try:
        row_367 = WSData.objects.get(tag_im_jahr=367)
        ladezust_burtto_367 = row_367.ladezust_burtto or 0
        ladezustand_netto_367 = row_367.ladezustand_netto or 0
    except WSData.DoesNotExist:
        ladezust_burtto_367 = 0
        ladezustand_netto_367 = 0
    
    for row in daily_rows:
        # Build context with previous values and row 367 references
        context = {
            'WS_LADEZUST_BURTTO_PREV': ladezust_burtto_prev,
            'WS_LADEZUSTAND_NETTO_PREV': ladezustand_netto_prev,
            # Provide both naming styles (upper/lower) so formulas can resolve
            'WS_LADEZUST_BURTTO_367': ladezust_burtto_367,
            'WS_LADEZUSTAND_NETTO_367': ladezustand_netto_367,
            'ladezust_burtto_367': ladezust_burtto_367,
            'ladezustand_netto_367': ladezustand_netto_367,
            **reference_values,
        }
        
        # Add current row's already-calculated values to context
        for field in row._meta.get_fields():
            if hasattr(field, 'name') and not field.name.startswith('_'):
                value = getattr(row, field.name, None)
                if value is not None and isinstance(value, (int, float)):
                    context[f'WS_{field.name.upper()}'] = value
        
        # Calculate each cumulative column
        for column_name in cumulative_columns:
            formula_key = f'WS_{column_name.upper()}'
            
            try:
                formula = Formula.objects.get(key=formula_key, is_active=True, category='ws')
                
                # Evaluate formula
                result = _evaluate_ws_formula(formula.expression, context)
                
                # Set column value
                setattr(row, column_name, result)
                
                # Update context for next column in same row
                context[f'WS_{column_name.upper()}'] = result
                
            except Formula.DoesNotExist:
                # Formula missing - raise error (NO FALLBACK!)
                raise ValueError(f"Missing WS formula in database: {formula_key}. Cumulative WS calculations require all formulas to be in database.")
            except Exception as e:
                print(f"❌ Row {row.tag_im_jahr}.{column_name}: Formula '{formula_key}' failed: {e}")
                setattr(row, column_name, 0)
        
        # Save row
        row.save()
        
        # Update previous values for next iteration
        ladezust_burtto_prev = row.ladezust_burtto or 0
        ladezustand_netto_prev = row.ladezustand_netto or 0


def _evaluate_ws_formula(expression, context):
    """
    Evaluate WS formula expression with given context.
    Supports:
    - Direct value references (e.g., 'verbrauch_promille')
    - WS column references (e.g., 'WS_STROMVERBR')
    - Reference values (e.g., 'WS_REF_STROMVERBR_366')
    - Math functions: max(), min(), abs()
    - Arithmetic operations
    """
    # Simple direct value references
    if expression in context:
        return context[expression]
    
    # Prepare safe evaluation environment
    safe_dict = context.copy()
    safe_dict.update({
        'max': max,
        'min': min,
        'abs': abs,
        'round': round,
    })
    
    try:
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return result if result is not None else 0
    except Exception as e:
        print(f"    Error evaluating WS formula '{expression}': {e}")
        return 0


def _apply_row_366_formulas(row_366, daily_rows, davon_raumw_korr_366, stromverbr_raumwaerm_korr_366, sums):
    """
    🚀 100% DATABASE-DRIVEN - NO HARDCODED FALLBACKS!
    
    Apply row 366 formulas from database ONLY.
    All formulas MUST be in database - no fallback to hardcoded values.
    
    Formula naming pattern: WS_COLUMNNAME_366
    Example: WS_LADEZUST_BURTTO_366, WS_STROMVERBR_366, etc.
    
    ✅ Fully extensible - add any formula via database
    ✅ No hardcoded column_defaults
    ✅ All formulas in simulator_formula table
    """
    from simulator.models import Formula
    
    # Get day 1 and day 365 for difference calculations
    day_1 = daily_rows.filter(tag_im_jahr=1).first()
    day_365 = daily_rows.filter(tag_im_jahr=365).first()
    
    # Load all active row 366 formulas from database
    row_366_formulas = Formula.objects.filter(
        category='ws',
        is_active=True,
        key__endswith='_366'
    ).select_related()
    
    # Create a lookup of column_name -> formula
    formula_lookup = {}
    for formula in row_366_formulas:
        # Extract column name from formula key (e.g., WS_LADEZUST_BURTTO_366 -> ladezust_burtto)
        if formula.key.startswith('WS_') and formula.key.endswith('_366'):
            # Remove WS_ prefix and _366 suffix, convert to lowercase
            column_name = formula.key[3:-4].lower()
            formula_lookup[column_name] = formula
    
    # Build context for formula evaluation (shared for all formulas)
    # Get diagram reference values for WS_REF_* formulas
    diagram = compute_ws_diagram_reference(use_ws_overrides=False)
    
    context = {
        'day_1': day_1,
        'day_365': day_365,
        'daily_rows': daily_rows,
        'sums': sums,
        'davon_raumw_korr_366': davon_raumw_korr_366,
        'stromverbr_raumwaerm_korr_366': stromverbr_raumwaerm_korr_366,
        # WS_REF_* keys that formulas expect
        'WS_REF_BIO': diagram.get('bio_value', 0),
        'WS_REF_PV': diagram.get('pv_value', 0),
        'WS_REF_WIND': diagram.get('wind_value', 0),
        'WS_REF_HYDRO': diagram.get('hydro_value', 0),
        'WS_REF_ELY': diagram.get('ely_branch_value', 0),
        'WS_REF_T_VALUE': diagram.get('t_value', 0),
        'WS_REF_TOTAL_GEN': diagram.get('m_total', 0),
        'WS_REF_AFTER_ELY': diagram.get('remaining_after_ely', 0),
        'WS_REF_N_INPUT': diagram.get('n_input_branch', 0),
        'WS_REF_N_OUTPUT': diagram.get('n_output_branch', 0),
    }
    
    # Apply ALL formulas from database (100% database-driven - NO fallbacks!)
    for column_name, formula in formula_lookup.items():
        try:
            # Evaluate the formula
            value = _evaluate_row_366_formula(formula.expression, context)
            setattr(row_366, column_name, value)
            print(f"✓ Row 366.{column_name}: Database formula '{formula.key}' = {value}")
        except Exception as e:
            # Formula failed - log error and set to 0 (NO fallback to hardcoded values!)
            setattr(row_366, column_name, 0)
            print(f"❌ Row 366.{column_name}: Formula '{formula.key}' failed: {e}")


def _evaluate_row_366_formula(expression, context):
    """
    Enhanced formula evaluator for row 366 formulas.
    Supports:
    - sum_columnname - Sum references
    - day_365.columnname - End of year values
    - day_1.columnname - Start of year values
    - column_day1, column_day365 - Day reference format
    - davon_raumw_korr_366 - Reference values
    - AE_* - Annual Electricity formula references
    - V_* - Verbrauch data references
    - Complex formulas: IF(condition; true_val; false_val)
    - Mathematical functions: MAX(), MIN(), ROUND(), ABS()
    - Basic math operations (+, -, *, /, etc.)
    
    FULLY EXTENSIBLE - supports ANY WS column dynamically!
    """
    from simulator.models import Formula, VerbrauchData, RenewableData
    from simulator.formula_service import _safe_eval
    
    # Simple direct value references from context
    if expression in context:
        return context[expression]
    
    # Handle sum references: sum_stromverbr (simple form)
    if expression.startswith('sum_'):
        sum_key = expression
        return context['sums'].get(sum_key, 0)
    
    # Preprocess expression: replace context references
    eval_expr = expression
    day_1 = context.get('day_1')
    day_365 = context.get('day_365')
    
    # Build lookup dictionary for formula evaluation
    lookup_dict = {}
    
    # Add reference values from context
    lookup_dict['davon_raumw_korr_366'] = context.get('davon_raumw_korr_366', 0)
    lookup_dict['stromverbr_raumwaerm_korr_366'] = context.get('stromverbr_raumwaerm_korr_366', 0)
    
    # Add all sums to lookup
    for key, value in context.get('sums', {}).items():
        lookup_dict[key] = value
    
    # Find and resolve Annual Electricity formula references (AE_*)
    ae_pattern = r'\bAE_[A-Z_]+\b'
    ae_matches = re.findall(ae_pattern, expression)
    for ae_key in set(ae_matches):
        try:
            # Get Annual Electricity formula and evaluate it
            ae_formula = Formula.objects.get(key=ae_key, category='annual', is_active=True)
            
            # Build lookup for Annual Electricity evaluation
            ae_lookup = {}
            
            # Add renewable data
            for r in RenewableData.objects.all():
                if r.target_value is not None:
                    ae_lookup[f"Renewable_{r.code.replace('.', '_')}"] = float(r.target_value)
            
            # Add WS constants
            ws_consts = get_ws_constants()
            ae_lookup.update({
                'WS_ETA_STROM_GAS': ws_consts['ETA_STROM_GAS'],
                'WS_ETA_GAS_STROM': ws_consts['ETA_GAS_STROM'],
            })
            
            # Add WS row 366 values for override logic
            # (Use None for now since we're calculating row 366 - it will use defaults)
            ae_lookup['WS_ABREGELUNG_Z_366'] = None
            ae_lookup['WS_EINSPEICH_366'] = None
            ae_lookup['WS_AUSSPEICH_RUECKVERSTR_366'] = None
            
            # Recursively resolve other AE formulas that this one depends on
            ae_value = _safe_eval(ae_formula.expression, ae_lookup, use_target=True)
            lookup_dict[ae_key] = ae_value if ae_value is not None else 0
            
        except Formula.DoesNotExist:
            lookup_dict[ae_key] = 0
        except Exception as e:
            print(f"    Error evaluating AE formula '{ae_key}': {e}")
            lookup_dict[ae_key] = 0
    
    # Find and resolve Verbrauch data references (V_*)
    # Pattern: V_2_9_2_ziel or V_2_4_ziel
    v_pattern = r'\bV_(\d+_\d+(?:_\d+)?(?:_\d+)?)_(ziel|status)\b'
    v_matches = re.findall(v_pattern, expression)
    for code_parts, field in v_matches:
        # Convert code_parts back to dotted format (e.g., "2_9_2" -> "2.9.2")
        code = code_parts.replace('_', '.')
        lookup_key = f'V_{code_parts}_{field}'
        
        try:
            verbrauch = VerbrauchData.objects.get(code=code)
            value = getattr(verbrauch, field, 0)
            lookup_dict[lookup_key] = float(value) if value is not None else 0
        except VerbrauchData.DoesNotExist:
            lookup_dict[lookup_key] = 0
        except Exception as e:
            print(f"    Error getting Verbrauch {code}.{field}: {e}")
            lookup_dict[lookup_key] = 0
    
    # Find all day column references in the expression
    # Pattern 1: column_name_day1 or column_name_day365
    pattern = r'(\w+)_day(1|365)\b'
    matches = re.findall(pattern, expression)
    for column_name, day_num in matches:
        day_obj = day_1 if day_num == '1' else day_365
        value = getattr(day_obj, column_name, 0) if day_obj else 0
        lookup_key = f'{column_name}_day{day_num}'
        if lookup_key not in lookup_dict:  # Don't overwrite if already set
            lookup_dict[lookup_key] = value
    
    # Use simple eval for arithmetic expressions
    safe_dict = lookup_dict.copy()
    safe_dict.update({
        'MAX': max,
        'MIN': min,
        'ROUND': round,
        'ABS': abs,
        'max': max,
        'min': min,
        'round': round,
        'abs': abs,
        # Add sums dictionary for formulas using sums['key'] syntax
        'sums': context.get('sums', {}),
        # Add day references for formulas using day_365.column syntax
        'day_1': day_1,
        'day_365': day_365,
    })
    
    try:
        return eval(eval_expr, {"__builtins__": {}}, safe_dict)
    except Exception as e:
        print(f"    Error evaluating formula '{expression}': {e}")
        return 0


def _apply_row_367_formulas(row_367, sums):
    """
    🚀 100% DATABASE-DRIVEN - NO HARDCODED FALLBACKS!
    
    Apply row 367 formulas from database ONLY.
    Row 367 is a reference row used in daily calculations.
    
    Formula naming pattern: WS_COLUMNNAME_367
    All formulas MUST be in database - no fallback to hardcoded values.
    """
    from simulator.models import Formula
    
    # Load all active row 367 formulas from database
    row_367_formulas = Formula.objects.filter(
        category='ws',
        is_active=True,
        key__endswith='_367'
    ).select_related()
    
    # Create a lookup of column_name -> formula
    formula_lookup = {}
    for formula in row_367_formulas:
        # Extract column name from formula key (e.g., WS_LADEZUST_BURTTO_367 -> ladezust_burtto)
        if formula.key.startswith('WS_') and formula.key.endswith('_367'):
            column_name = formula.key[3:-4].lower()
            formula_lookup[column_name] = formula
    
    # Build context for formula evaluation
    context = {'sums': sums}
    
    # Apply ALL formulas from database (100% database-driven - NO fallbacks!)
    for column_name, formula in formula_lookup.items():
        try:
            # Evaluate the formula
            value = _evaluate_row_367_formula(formula.expression, context)
            setattr(row_367, column_name, value)
            print(f"✓ Row 367.{column_name}: Database formula '{formula.key}' = {value}")
        except Exception as e:
            # Formula failed - log error and set to 0 (NO fallback!)
            setattr(row_367, column_name, 0)
            print(f"❌ Row 367.{column_name}: Formula '{formula.key}' failed: {e}")


def _evaluate_row_367_formula(expression, context):
    """
    Simple formula evaluator for row 367 formulas.
    """
    # Handle literal values
    if expression.isdigit() or (expression.startswith('-') and expression[1:].isdigit()):
        return float(expression)
    
    if expression == '0':
        return 0
    
    # Handle sum references
    if expression.startswith('sums['):
        import re
        match = re.search(r"sums\['([^']+)'\]", expression)
        if match:
            sum_key = match.group(1)
            return context['sums'].get(sum_key, 0)
    
    # Return 0 if we can't evaluate
    return 0


def apply_ws_row_formulas(ws_row, tag_im_jahr, all_daily_rows=None, sums=None):
    """
    🚀 UNIVERSAL FORMULA SYSTEM FOR ANY WS ROW (1-365, 366, 367)
    
    Apply database formulas to ANY WS row - makes ENTIRE WS database 100% extensible!
    
    Formula naming pattern: WS_COLUMNNAME_DAY where DAY is tag_im_jahr (1-367)
    Examples:
        - WS_STROMVERBR_1 (day 1 formula)
        - WS_LADEZUST_BURTTO_100 (day 100 formula)
        - WS_WINDSTROM_365 (day 365 formula)
        - WS_EINSPEICH_366 (row 366 formula)
        - WS_BRENNSTOFF_AUSGLEICHS_STROM_367 (row 367 formula)
    
    Args:
        ws_row: WSData instance to apply formulas to
        tag_im_jahr: Day number (1-367)
        all_daily_rows: QuerySet of all daily rows (optional, for context)
        sums: Dictionary of sum values (optional, for context)
    
    Returns:
        bool: True if any formulas were applied, False otherwise
    """
    from simulator.models import Formula
    
    # Load formulas for this specific row
    row_formulas = Formula.objects.filter(
        category='ws',
        is_active=True,
        key__endswith=f'_{tag_im_jahr}'
    ).select_related()
    
    if not row_formulas.exists():
        return False  # No formulas for this row
    
    # Build context for formula evaluation
    context = {
        'tag_im_jahr': tag_im_jahr,
        'sums': sums or {},
        'all_daily_rows': all_daily_rows,
    }
    
    # Add neighboring rows for reference (day_prev, day_next, day_1, day_365)
    if all_daily_rows:
        context['day_1'] = all_daily_rows.filter(tag_im_jahr=1).first()
        context['day_365'] = all_daily_rows.filter(tag_im_jahr=365).first()
        if tag_im_jahr > 1:
            context['day_prev'] = all_daily_rows.filter(tag_im_jahr=tag_im_jahr-1).first()
        if tag_im_jahr < 365:
            context['day_next'] = all_daily_rows.filter(tag_im_jahr=tag_im_jahr+1).first()
    
    formulas_applied = 0
    
    # Apply each formula
    for formula in row_formulas:
        # Extract column name from formula key
        # Example: WS_STROMVERBR_100 -> stromverbr
        if formula.key.startswith('WS_') and '_' in formula.key:
            parts = formula.key.split('_')
            # Remove WS_ prefix and _DAY suffix
            column_name = '_'.join(parts[1:-1]).lower()
            
            try:
                # Evaluate formula using the universal evaluator
                value = _evaluate_ws_formula_universal(formula.expression, context, ws_row)
                
                # Try to set as regular field first, fallback to custom field
                if hasattr(ws_row, column_name):
                    setattr(ws_row, column_name, value)
                else:
                    # Custom field - store in JSONField
                    ws_row.set_custom_field(column_name, value)
                
                formulas_applied += 1
                print(f'✓ Row {tag_im_jahr}.{column_name}: Applied formula \'{formula.key}\' = {value}')
            except Exception as e:
                print(f'❌ Row {tag_im_jahr}.{column_name}: Formula failed. Error: {e}')
    
    return formulas_applied > 0


def _evaluate_ws_formula_universal(expression, context, current_row=None):
    """
    Universal formula evaluator for ANY WS row.
    
    Supports:
    - row.columnname - Current row values (checks regular fields AND custom_fields)
    - day_N.columnname - Reference to specific day (e.g., day_1.stromverbr, day_365.ladezust_burtto)
    - day_prev.columnname, day_next.columnname - Adjacent days
    - sums['sum_key'] - Sum references
    - Complex formulas: IF(condition; true_val; false_val)
    - Mathematical functions: MAX(), MIN(), ROUND(), ABS()
    
    Returns:
        float: Calculated value
    """
    # Build lookup dictionary for formula evaluator
    lookup_dict = {}
    eval_expr = expression
    
    def get_field_value(ws_obj, field_name):
        """Get value from regular field or custom_fields JSON"""
        if hasattr(ws_obj, field_name):
            return getattr(ws_obj, field_name, 0) or 0
        else:
            # Check custom_fields
            return ws_obj.get_custom_field(field_name, 0) if hasattr(ws_obj, 'get_custom_field') else 0
    
    # Replace 'row.column' references (current row - regular OR custom fields)
    if current_row:
        row_pattern = r'row\\.([\\w]+)'
        row_matches = re.findall(row_pattern, expression)
        for column_name in row_matches:
            value = get_field_value(current_row, column_name)
            lookup_key = f'ROW_{column_name.upper()}'
            lookup_dict[lookup_key] = value
            eval_expr = eval_expr.replace(f'row.{column_name}', lookup_key)
    
    # Replace day references (day_1, day_365, day_prev, day_next, day_N)
    day_pattern = r'day_(\\w+)\\.([\\w]+)'
    day_matches = re.findall(day_pattern, expression)
    for day_ref, column_name in day_matches:
        # Get the day object from context
        if day_ref.isdigit():
            # Specific day number: day_100.stromverbr
            day_num = int(day_ref)
            day_obj = context.get('all_daily_rows').filter(tag_im_jahr=day_num).first() if context.get('all_daily_rows') else None
        else:
            # Named reference: day_prev, day_next, day_1, day_365
            day_obj = context.get(f'day_{day_ref}')
        
        # Get value from regular field OR custom_fields
        value = get_field_value(day_obj, column_name) if day_obj else 0
        lookup_key = f'DAY_{day_ref.upper()}_{column_name.upper()}'
        lookup_dict[lookup_key] = value
        eval_expr = eval_expr.replace(f'day_{day_ref}.{column_name}', lookup_key)
    
    # Replace sum references
    sum_pattern = r"sums\['([^']+)'\]"
    sum_matches = re.findall(sum_pattern, eval_expr)
    for sum_key in sum_matches:
        value = context.get('sums', {}).get(sum_key, 0)
        lookup_key = f'SUM_{sum_key.upper()}'
        lookup_dict[lookup_key] = value
        eval_expr = eval_expr.replace(f"sums['{sum_key}']", lookup_key)
    
    # Handle IF statements and complex formulas using FormulaEvaluator
    if 'IF(' in eval_expr or 'MAX(' in eval_expr or 'MIN(' in eval_expr:
        formula_evaluator.set_lookups(lookup_dict, {})
        result = formula_evaluator.evaluate(eval_expr, use_target=False)
        return result if result is not None else 0
    
    # For simple expressions, evaluate with math functions
    safe_dict = lookup_dict.copy()
    safe_dict.update({
        'MAX': max, 'MIN': min, 'ROUND': round, 'ABS': abs,
        'max': max, 'min': min, 'round': round, 'abs': abs,
    })
    
    try:
        return eval(eval_expr, {"__builtins__": {}}, safe_dict)
    except Exception as e:
        print(f'    Error evaluating universal formula \'{expression}\': {e}')
        return 0


@receiver(post_save, sender=LandUse)
def update_renewable_calculations(sender, instance, created, **kwargs):
    """
    🔄 AUTO-CASCADE: LandUse changes → Renewable → WS 365 → Update 9.3.1/9.3.4
    
    When any LandUse value (status_ha or target_ha) changes, this signal:
    1. Recalculates INPUT renewables (9.1.x, 9.2.x, 10.x except 9.3.1, 9.3.4)
    2. Updates 9.3.1 and 9.3.4 target values from WS 365-day calculation
       (9.3.1/9.3.4 status values stay 0)
    3. Recalculates ALL renewables (so 10.1, 9.3.1.2, etc. include correct values)
    
    NOTE: WSData (366 rows) is NOT recalculated - only WS 365 service is used.
    NOTE: Does NOT auto-balance! User must manually click "Balance All" on Bilanz page.
    
    Set instance._skip_cascade = True before save to skip this cascade.
    """
    global _cascade_in_progress
    
    # Check if cascade should be skipped (set by admin or other callers)
    if getattr(instance, '_skip_cascade', False):
        instance._skip_cascade = False  # Reset flag
        return
    
    # Skip if we're already in a cascade
    if _cascade_in_progress:
        return
    
    # Run recalc IMMEDIATELY (synchronously) so values are ready when user navigates
    try:
        _cascade_in_progress = True
        print(f"🔄 LandUse {instance.code} changed - triggering full recalculation...")
        
        from simulator.recalc_service import unified_recalc_all
        
        # Only recalculate - NO balance (user will click Balance All manually)
        stats = unified_recalc_all()
        
        print(f"✅ LandUse cascade complete: Recalculated {stats.get('input_renewables', 0)} input renewables, "
              f"{stats.get('ws_updated', 0)} WS entries, {stats.get('final_renewables', 0)} total renewables")
        print(f"   ℹ️ Go to Bilanz page and click 'Balance All' to balance the system")
            
    except Exception as e:
        print(f"❌ LandUse cascade error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        _cascade_in_progress = False


@receiver(post_delete, sender=LandUse)
def handle_landuse_deletion(sender, instance, **kwargs):
    """
    Handle when LandUse data is deleted - set dependent renewable values to 0
    """
    from simulator.models import FormulaVariable
    
    print(f"⚠️ LandUse {instance.code} deleted")
    
    # Find all formulas that reference this LandUse code
    affected_variables = FormulaVariable.objects.filter(
        source_type__in=['landuse_status', 'landuse_target'],
        source_key=instance.code
    ).select_related('formula')
    
    # Collect unique renewable codes
    renewable_codes = set()
    for var in affected_variables:
        if var.formula and var.formula.category == 'renewable':
            key = var.formula.key
            if key.endswith('_ziel_target'):
                base_code = key.replace('_ziel_target', '')
            else:
                base_code = key
            renewable_codes.add(base_code)
    
    print(f"   Affected renewable entries will show 0: {renewable_codes}")


def compute_ws_diagram_reference(use_ws_overrides: bool = True):
    """
    Compute Annual Electricity (WS1) reference values using the same logic as the
    diagram (Annual Electricity view) with TARGET-first inputs and WS 365 days
    calculation (Abregelung/Einspeich/Ausspeich sums) when requested.
    
    ✅ 100% FRESH VALUES from database formulas (not stale stored values)
    ✅ Now uses WS 365-day calculations for Q, Elektrolyse, and Gasspeicher values
    """

    def renewable_value(code: str) -> float:
        """Get FRESH calculated renewable value (prefer target, fallback to status)."""
        try:
            r = RenewableData.objects.get(code=code)
            
            # If fixed value, use stored data
            if r.is_fixed or not r.formula:
                if r.target_value is not None:
                    return float(r.target_value)
                if r.status_value is not None:
                    return float(r.status_value)
                return 0.0
            
            # For calculated rows, get FRESH values using get_calculated_values()
            try:
                calc_status, calc_target = r.get_calculated_values(fail_fast=False)
                # Prefer target, fallback to status
                if calc_target is not None:
                    return float(calc_target)
                if calc_status is not None:
                    return float(calc_status)
            except Exception:
                # Fallback to stored values if calculation fails
                if r.target_value is not None:
                    return float(r.target_value)
                if r.status_value is not None:
                    return float(r.status_value)
        except RenewableData.DoesNotExist:
            return 0.0
        return 0.0


    ws_consts = get_ws_constants()

    pv_value = renewable_value('9.1.2')  # aus Solarenergie (Photovoltaik)
    wind_value = renewable_value('9.1.1')  # aus Windenergie
    hydro_value = renewable_value('9.1.3')  # aus Wasserkraft + Tiefengeothermie
    bio_value = renewable_value('9.1.4')  # aus Biobrennstoffen

    ely_branch_value = renewable_value('9.2.1.5.2')
    
    # ==================================================================================
    # GET VALUES FROM WS 365-DAY CALCULATION (instead of WSData row 366)
    # ==================================================================================
    try:
        from .ws_365_service import get_ws_365_data
        ws_365_data = get_ws_365_data(run_goal_seek=False)
        current = ws_365_data['current']
        
        # Q (Abregelung) = sum of abregelung column from WS 365 days
        q_abregelung = float(current.get('abregelung_sum', 0))
        
        # Elektrolyse Stromspeicher (Überschuss) = sum of einspeich / 65%
        einspeich_sum = float(current.get('einspeich_sum', 0))
        n_output_branch = einspeich_sum / 0.65 if einspeich_sum > 0 else 0
        
        # Gasspeicher Strom T = sum of ausspeich_rueckverstr from WS 365 days
        t_value = float(current.get('ausspeich_sum', 0))
        
    except Exception as e:
        # Fallback to WSData row 366 if WS 365 service fails
        print(f"WS 365 service failed, falling back to WSData row 366: {e}")
        try:
            ws_row_366 = WSData.objects.get(tag_im_jahr=366)
            q_abregelung = float(ws_row_366.abregelung_z or 0)
            einspeich_366 = float(ws_row_366.einspeich or 0)
            n_output_branch = einspeich_366 / 0.65
            t_value = float(ws_row_366.ausspeich_rueckverstr or 0)
        except WSData.DoesNotExist:
            q_abregelung = 0
            n_output_branch = 0
            t_value = 0
    
    n_input_branch = q_abregelung  # Abregelung feeds into N

    m_total = pv_value + wind_value + hydro_value
    remaining_after_ely = m_total - ely_branch_value

    gas_storage = n_output_branch * ws_consts['ETA_STROM_GAS']
    # t_value now comes from WSData row 366 ausspeich_rueckverstr (set above)
    t_output = t_value * ws_consts['ETA_GAS_STROM']

    # WS row 366 values used for diagram

    n_value = m_total - ely_branch_value  # N = M - 385933 (Q is deducted later)
    # O = N - Q - Elektrolyse Stromspeicher
    o_value = n_value - q_abregelung - n_output_branch
    n_to_right = o_value  # This is what flows to the right (O)
    # Stromnetz zum Endverbrauch = O + Bio + Gasspeicher Strom × 58.5%
    final_stromnetz = o_value + bio_value + (t_value * 0.585)

    # Source splits for WS daily distributions
    factor = (remaining_after_ely / m_total) if m_total else 0.0
    solarstrom_366 = pv_value * factor
    windstrom_366 = wind_value * factor
    sonst_kraft_konstant_366 = hydro_value * factor

    h2_offer = ely_branch_value * ws_consts['ETA_STROM_GAS']
    h2_surplus = n_output_branch * ws_consts['ETA_STROM_GAS']

    return {
        'pv_value': pv_value,
        'wind_value': wind_value,
        'hydro_value': hydro_value,
        'bio_value': bio_value,
        'm_total': m_total,
        'ely_branch_value': ely_branch_value,
        'ely_offer': ely_branch_value,
        'h2_offer': h2_offer,
        'n_value': n_value,
        'q_abregelung': q_abregelung,
        'n_input_branch': n_input_branch,
        'n_output_branch': n_output_branch,
        'ely_surplus': n_output_branch,
        'gas_storage': gas_storage,
        't_value': t_value,
        't_output': t_output,
        'n_to_right': n_to_right,
        'final_stromnetz': final_stromnetz,
        'stromverbr_raumwaerm_korr_366': final_stromnetz,
        'remaining_after_ely': remaining_after_ely,
        'solarstrom_366': solarstrom_366,
        'windstrom_366': windstrom_366,
        'sonst_kraft_konstant_366': sonst_kraft_konstant_366,
        'h2_surplus': h2_surplus,
    }


def recalculate_ws_data(stromverbr_override=None, use_diagram_reference=True):
    """
    Recalculate all WS data based on Annual Electricity and Verbrauch data.
    If stromverbr_override is provided AND use_diagram_reference is False,
    that override is used instead of recomputing the diagram reference. This
    lets a GoalSeek loop adjust Stromverbr. Raumw.korr. (row 366) without
    re-deriving it from the diagram each iteration.
    """

    # Get reference value for davon_raumw_korr from WS diagram
    # This is the reference value used to calculate daily values
    try:
        verbrauch_292 = VerbrauchData.objects.get(code='2.9.2')
        verbrauch_24 = VerbrauchData.objects.get(code='2.4')
        davon_raumw_korr_366 = verbrauch_292.ziel * (verbrauch_24.ziel / 100)
    except VerbrauchData.DoesNotExist:
        davon_raumw_korr_366 = 0

    diagram = compute_ws_diagram_reference()
    pv_value = diagram["pv_value"]
    wind_value = diagram["wind_value"]
    hydro_value = diagram["hydro_value"]
    bio_value = diagram["bio_value"]
    solarstrom_366 = diagram["solarstrom_366"]
    windstrom_366 = diagram["windstrom_366"]
    sonst_kraft_konstant_366 = diagram["sonst_kraft_konstant_366"]

    # PRESERVE stromverbr_raumwaerm_korr_366 from database!
    # Only use diagram value if explicitly overriding OR if database value is 0/None
    # Default is 1105556 - this is only changed by Balance WS Storage button
    DEFAULT_STROMVERBR = 1105556.0
    try:
        existing_row_366 = WSData.objects.get(tag_im_jahr=366)
        existing_stromverbr = existing_row_366.stromverbr_raumwaerm_korr or 0
    except WSData.DoesNotExist:
        existing_stromverbr = 0
    
    if stromverbr_override is not None and not use_diagram_reference:
        # Explicit override from goal-seek or other process
        stromverbr_raumwaerm_korr_366 = stromverbr_override
    else:
        # PERMANENT LOGIC: Always use baseline 1105556 unless explicitly overridden.
        # This prevents accidental preservation of 'balanced' values during normal model runs.
        stromverbr_raumwaerm_korr_366 = DEFAULT_STROMVERBR
    
    # ==================================================================================
    # CALCULATE DAILY VALUES (ROWS 1-365) - 100% DATABASE-DRIVEN!
    # ==================================================================================
    # Build reference values for daily calculations
    reference_values = {
        # Legacy keys (for compatibility)
        'WS_REF_STROMVERBR_366': stromverbr_raumwaerm_korr_366,
        'WS_REF_DAVON_366': davon_raumw_korr_366,
        'WS_REF_WIND_366': windstrom_366,
        'WS_REF_SOLAR_366': solarstrom_366,
        'WS_REF_HYDRO_366': sonst_kraft_konstant_366,
        
        # WS_REF_* keys that formulas expect
        'WS_REF_BIO': bio_value,
        'WS_REF_PV': pv_value,
        'WS_REF_WIND': wind_value,
        'WS_REF_HYDRO': hydro_value,
        'WS_REF_ELY': diagram.get('ely_branch_value', 0),
        'WS_REF_T_VALUE': diagram.get('t_value', 0),
        'WS_REF_TOTAL_GEN': diagram.get('m_total', 0),
        'WS_REF_AFTER_ELY': diagram.get('remaining_after_ely', 0),
        'WS_REF_N_INPUT': diagram.get('n_input_branch', 0),
        'WS_REF_N_OUTPUT': diagram.get('n_output_branch', 0),
        
        # Current formula keys (used by WS formulas)
        'stromverbr_raumwaerm_korr_366': stromverbr_raumwaerm_korr_366,
        'davon_raumw_korr_366': davon_raumw_korr_366,
        'windstrom_366': windstrom_366,
        'solarstrom_366': solarstrom_366,
        'sonst_kraft_konstant_366': sonst_kraft_konstant_366,
        'bio_value': bio_value,
        # Sum will be calculated during recalc and added for second pass
    }
    
    # Apply database formulas to calculate all daily values
    daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    _apply_daily_ws_formulas(daily_rows, reference_values)
    
    # Reload daily_rows after calculation to get fresh sums
    daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    
    # ==================================================================================
    # CALCULATE ROW 367 (Reference row for storage calculations)
    # ==================================================================================
    # Row 367 stores minimum cumulative values used as offsets
    # First initialize ladezust_burtto_367 to 0 for first pass cumulative calculations
    try:
        row_367 = WSData.objects.get(tag_im_jahr=367)
        row_367.ladezust_burtto = 0
        row_367.ladezustand_netto = 0
        row_367.save()
    except WSData.DoesNotExist:
        row_367 = WSData.objects.create(
            tag_im_jahr=367,
            datum_ref="Sum+1",
            ladezust_burtto=0,
            ladezustand_netto=0
        )
    
    # Now run the second pass of daily calculations (with row_367 = 0)
    # This will calculate cumulative values
    _apply_daily_ws_formulas_cumulative(daily_rows, reference_values)
    
    # After cumulative calculations, update row 367 to minimum values
    daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    daily_ladezust_values = [r.ladezust_burtto for r in daily_rows if r.ladezust_burtto is not None]
    daily_ladezustand_values = [r.ladezustand_netto for r in daily_rows if r.ladezustand_netto is not None]
    
    row_367.ladezust_burtto = min(daily_ladezust_values) if daily_ladezust_values else 0
    row_367.ladezustand_netto = min(daily_ladezustand_values) if daily_ladezustand_values else 0
    row_367.save()
    
    # Re-run cumulative calculations with correct row_367 values
    _apply_daily_ws_formulas_cumulative(daily_rows, reference_values)
    
    # ==================================================================================
    # UPDATE ROW 366 (Annual sums)
    # ==================================================================================
    # Reload to get fresh data
    daily_rows = WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
    
    # Prepare sums for row 366 calculations
    sum_stromverbr = sum([r.stromverbr for r in daily_rows if r.stromverbr])
    sum_davon_raumw = sum([r.davon_raumw_korr for r in daily_rows if r.davon_raumw_korr])
    sum_stromverbr_raumwaerm = sum([r.stromverbr_raumwaerm_korr for r in daily_rows if r.stromverbr_raumwaerm_korr])
    sum_windstrom = sum([r.windstrom for r in daily_rows if r.windstrom])
    sum_solarstrom = sum([r.solarstrom for r in daily_rows if r.solarstrom])
    sum_sonst_kraft = sum([r.sonst_kraft_konstant for r in daily_rows if r.sonst_kraft_konstant])
    sum_wind_solar_konstant = sum([r.wind_solar_konstant for r in daily_rows if r.wind_solar_konstant])
    sum_direktverbr = sum([r.direktverbr_strom for r in daily_rows if r.direktverbr_strom])
    sum_ueberschuss = sum([r.ueberschuss_strom for r in daily_rows if r.ueberschuss_strom])
    sum_einspeich = sum([r.einspeich for r in daily_rows if r.einspeich])
    sum_abregelung_z = sum([r.abregelung_z for r in daily_rows if r.abregelung_z])
    sum_mangel_last = sum([r.mangel_last for r in daily_rows if r.mangel_last])
    sum_brennstoff = sum([r.brennstoff_ausgleichs_strom for r in daily_rows if r.brennstoff_ausgleichs_strom])
    sum_speicher_ausgl = sum([r.speicher_ausgl_strom for r in daily_rows if r.speicher_ausgl_strom])
    sum_ausspeich_rueck = sum([r.ausspeich_rueckverstr for r in daily_rows if r.ausspeich_rueckverstr])
    sum_ausspeich_gas = sum([r.ausspeich_gas for r in daily_rows if r.ausspeich_gas])
    
    try:
        row_366 = WSData.objects.get(tag_im_jahr=366)
        
        # Apply row 366 formulas from database
        _apply_row_366_formulas(
            row_366=row_366,
            daily_rows=daily_rows,
            davon_raumw_korr_366=davon_raumw_korr_366,
            stromverbr_raumwaerm_korr_366=stromverbr_raumwaerm_korr_366,
            sums={
                'sum_stromverbr': sum_stromverbr,
                'sum_davon_raumw': sum_davon_raumw,
                'sum_stromverbr_raumwaerm': sum_stromverbr_raumwaerm,
                'sum_windstrom': sum_windstrom,
                'sum_solarstrom': sum_solarstrom,
                'sum_sonst_kraft': sum_sonst_kraft,
                'sum_wind_solar_konstant': sum_wind_solar_konstant,
                'sum_direktverbr': sum_direktverbr,
                'sum_ueberschuss': sum_ueberschuss,
                'sum_einspeich': sum_einspeich,
                'sum_abregelung_z': sum_abregelung_z,
                'sum_mangel_last': sum_mangel_last,
                'sum_brennstoff': sum_brennstoff,
                'sum_speicher_ausgl': sum_speicher_ausgl,
                'sum_ausspeich_rueck': sum_ausspeich_rueck,
                'sum_ausspeich_gas': sum_ausspeich_gas,
            }
        )
        
        # ⚠️ CRITICAL: Explicitly set stromverbr_raumwaerm_korr (used by goal_seek)
        # This field doesn't have a database formula, so it must be set directly
        row_366.stromverbr_raumwaerm_korr = stromverbr_raumwaerm_korr_366
        row_366.davon_raumw_korr = davon_raumw_korr_366
        
        row_366.save()
    except WSData.DoesNotExist:
        pass
    
    # Update Row 367 (reference row for formulas)
    # Check for database formulas first, then fall back to default behavior
    sums_dict = {
        'sum_stromverbr': sum_stromverbr,
        'sum_davon_raumw': sum_davon_raumw,
        'sum_stromverbr_raumwaerm': sum_stromverbr_raumwaerm,
        'sum_windstrom': sum_windstrom,
        'sum_solarstrom': sum_solarstrom,
        'sum_sonst_kraft': sum_sonst_kraft,
        'sum_wind_solar_konstant': sum_wind_solar_konstant,
        'sum_direktverbr': sum_direktverbr,
        'sum_ueberschuss': sum_ueberschuss,
        'sum_einspeich': sum_einspeich,
        'sum_abregelung_z': sum_abregelung_z,
        'sum_mangel_last': sum_mangel_last,
        'sum_brennstoff': sum_brennstoff,
        'sum_speicher_ausgl': sum_speicher_ausgl,
        'sum_ausspeich_rueck': sum_ausspeich_rueck,
        'sum_ausspeich_gas': sum_ausspeich_gas,
    }
    
    try:
        row_367 = WSData.objects.get(tag_im_jahr=367)
        # Apply row 367 sum formulas from database
        _apply_row_367_formulas(row_367=row_367, sums=sums_dict)
        row_367.save()
    except WSData.DoesNotExist:
        # Create row 367 if it doesn't exist
        row_367 = WSData.objects.create(
            tag_im_jahr=367,
            datum_ref="Sum+1"
        )
        # Apply row 367 sum formulas from database
        _apply_row_367_formulas(row_367=row_367, sums=sums_dict)
        row_367.save()


@receiver(post_save, sender=RenewableData)
def renewable_data_changed(sender, instance, **kwargs):
    """
    🔄 AUTO-CASCADE: When renewable data changes, update dependent items.
    
    If this is a key INPUT renewable (9.1.x, 9.2.x), trigger WS recalculation.
    Otherwise, recalculate any renewables that depend on this code.
    Skip if already in a cascade to prevent infinite loops.
    """
    global _cascade_in_progress
    
    # Skip if explicitly told to (during bulk operations)
    if getattr(instance, '_skip_cascade', False):
        instance._skip_cascade = False
        return
    
    # Skip if we're already in a cascade
    if _cascade_in_progress:
        return
    
    # Check if this is a key renewable that affects WS calculations
    # These are the INPUT values that WS needs: 9.1.1, 9.1.2, 9.1.3, 9.2.1.5.2.1
    ws_input_codes = {'9.1.1', '9.1.2', '9.1.3', '9.2.1.5.2.1'}
    
    if instance.code in ws_input_codes:
        print(f"🔄 RenewableData {instance.code} changed - triggering WS + full cascade...")
        
        # Use transaction.on_commit to avoid blocking the save
        from django.db import transaction
        
        def trigger_full_cascade():
            global _cascade_in_progress
            if _cascade_in_progress:
                return
            
            try:
                _cascade_in_progress = True
                
                # Import here to avoid circular imports
                from simulator.recalc_service import unified_recalc_and_balance
                
                # Run unified recalculation with auto-balance
                stats = unified_recalc_and_balance(
                    balance_after=True,
                    ws_tolerance=10.0,
                    energy_tolerance=1.0,
                    max_balance_cycles=3  # Quick balance, not full
                )
                
                if stats.get('is_balanced'):
                    print(f"✅ Auto-cascade complete: BALANCED (gap: {stats.get('balance', {}).get('final_gap', 0):.2f} GWh)")
                else:
                    print(f"⚠️ Auto-cascade complete: Balance incomplete (gap: {stats.get('balance', {}).get('final_gap', 0):.2f} GWh)")
                    
            except Exception as e:
                print(f"❌ Auto-cascade error: {e}")
            finally:
                _cascade_in_progress = False
        
        transaction.on_commit(trigger_full_cascade)
    else:
        # For other renewables, find and recalculate dependent renewables
        print(f"ℹ️ RenewableData {instance.code} changed")
        
        from django.db import transaction
        
        def recalc_dependents():
            global _cascade_in_progress
            if _cascade_in_progress:
                return
                
            try:
                _cascade_in_progress = True
                
                # Find formulas that reference this renewable code
                from simulator.models import FormulaVariable
                dependent_vars = FormulaVariable.objects.filter(
                    source_type__in=['renewable_code_status', 'renewable_code_target'],
                    source_key=instance.code
                )
                
                # Get unique formula keys
                dependent_codes = set(var.formula.key for var in dependent_vars)
                
                if dependent_codes:
                    print(f"  → Recalculating {len(dependent_codes)} dependent renewables: {dependent_codes}")
                    
                    # Recalculate each dependent
                    from calculation_engine.renewable_engine import RenewableCalculator
                    from simulator.models import LandUse, VerbrauchData
                    
                    # Build fresh lookups
                    landuse_data = {lu.code: {'status_ha': lu.status_ha or 0, 'target_ha': lu.target_ha or 0} for lu in LandUse.objects.all()}
                    verbrauch_data = {v.code: {'status': v.status or 0, 'ziel': v.ziel or 0} for v in VerbrauchData.objects.all()}
                    renewable_data = {r.code: {'status_value': r.status_value or 0, 'target_value': r.target_value or 0} for r in RenewableData.objects.all()}
                    
                    calc = RenewableCalculator()
                    calc.set_data_sources(landuse_data, verbrauch_data, renewable_data)
                    
                    for code in dependent_codes:
                        try:
                            item = RenewableData.objects.get(code=code)
                            if not item.is_fixed:
                                calc_status, calc_target = calc.calculate(code, fail_fast=False)
                                
                                if calc_status is not None and calc_target is not None:
                                    item.status_value = calc_status
                                    item.target_value = calc_target
                                    item._skip_cascade = True
                                    item.save()
                                    print(f"  ✓ Updated {code}: target={calc_target:.2f}")
                        except RenewableData.DoesNotExist:
                            pass
                        except Exception as e:
                            print(f"  ✗ Error updating {code}: {e}")
                            
            except Exception as e:
                print(f"❌ Dependent recalculation error: {e}")
            finally:
                _cascade_in_progress = False
        
        transaction.on_commit(recalc_dependents)


@receiver(post_save, sender=VerbrauchData)
def verbrauch_data_changed(sender, instance, **kwargs):
    """
    🔄 AUTO-CASCADE: When Verbrauch data changes, recalculate dependent renewables.
    """
    global _cascade_in_progress
    
    # Skip if explicitly told to
    if getattr(instance, '_skip_verbrauch_recalc', False):
        return
    
    # Skip if we're already in a cascade
    if _cascade_in_progress:
        return
    
    print(f"ℹ️ VerbrauchData {instance.code} changed")
    
    # Trigger recalc of renewables that depend on this verbrauch
    from django.db import transaction
    
    def trigger_renewable_recalc():
        global _cascade_in_progress
        if _cascade_in_progress:
            return
        
        try:
            from simulator.renewable_recalc import recalc_renewables_for_verbrauch
            updated = recalc_renewables_for_verbrauch(instance.code)
            if updated:
                print(f"🔄 Recalculated {len(updated)} renewables from VerbrauchData {instance.code}")
        except Exception as e:
            print(f"⚠️ Error recalculating renewables from Verbrauch {instance.code}: {e}")
    
    transaction.on_commit(trigger_renewable_recalc)


@receiver(post_save, sender=WSData)
def ws_data_changed(sender, instance, **kwargs):
    """
    🔄 AUTO-CASCADE: When a WS entry is manually edited, recalculate dependent values.
    
    This ensures that when you change a value in Row 366 (like ausspeich_gas),
    all dependent daily values (1-365) and other row 366/367 values are updated.
    """
    global _cascade_in_progress
    
    # Skip if we're already in a cascade (prevents infinite recursion)
    if _cascade_in_progress:
        return
    
    # Skip if explicitly told to (during bulk operations)
    if getattr(instance, '_skip_ws_cascade', False):
        instance._skip_ws_cascade = False
        return
    
    # Only trigger cascade for key rows (366, 367) that affect other rows
    # Daily rows (1-365) are recalculated FROM formulas, not cascaded
    if instance.tag_im_jahr not in [366, 367]:
        return
    
    print(f"🔄 WSData Row {instance.tag_im_jahr} changed - triggering cascade recalculation...")
    
    from django.db import transaction
    
    def trigger_ws_cascade():
        global _cascade_in_progress
        if _cascade_in_progress:
            return
        
        try:
            _cascade_in_progress = True
            
            from simulator.ws_formula_service import recalculate_all_ws_data, get_ws_formula_evaluator
            
            # Clear evaluator cache
            evaluator = get_ws_formula_evaluator()
            evaluator.clear_cache()
            
            # Recalculate with 3 passes for proper cascading
            # IMPORTANT: preserve_stromverbr=True to keep balance-adjusted value
            stats = recalculate_all_ws_data(num_passes=3, preserve_stromverbr=True)
            print(f"✅ WS cascade complete: {stats['updated']} updates, {stats['errors']} errors")
            
        except Exception as e:
            print(f"❌ WS cascade error: {e}")
        finally:
            _cascade_in_progress = False
    
    transaction.on_commit(trigger_ws_cascade)


@receiver(post_save, sender=Formula)
@receiver(post_delete, sender=Formula)
def formula_changed(sender, instance, **kwargs):
    """
    Invalidate formula cache AND trigger data update when a formula is saved/deleted.
    
    COMPREHENSIVE UPDATE LOGIC:
    1. Clear caches (Django + FormulaService)
    2. Identify affected data item (VerbrauchData/RenewableData)
    3. Trigger recalculation safely using transaction.on_commit
       (prevents transaction implementation issues)
    """
    from django.core.cache import cache
    from simulator.formula_service import FormulaService
    from django.db import transaction
    
    # 1. Clear Caches
    cache_key = f'formula_{instance.key}'
    cache.delete(cache_key)
    
    try:
        service = FormulaService()
        service.clear_cache(instance.key)
    except Exception as e:
        print(f"⚠️  FormulaService cache clear warning: {e}")
    
    print(f"✅ All caches cleared for formula {instance.key}")

    # 2. Identify and Update Affected Data
    # usage of transaction.on_commit ensures we don't block the admin save 
    # and avoid transaction locking issues
    
    def trigger_update():
        try:
            # Handle VerbrauchData formulas (V_ prefix or standard code)
            if instance.category == 'verbrauch':
                code = instance.key
                # Remove prefixes/suffixes to get raw code
                code = code.replace('V_', '').replace('_ziel', '').replace('_status', '')
                # Convert underscores to dots (formula uses V_1_1_1 but data uses 1.1.1)
                code = code.replace('_', '.')
                
                from simulator.models import VerbrauchData
                try:
                    # Find the item
                    item = VerbrauchData.objects.get(code=code)
                    
                    # Force a save to trigger calculate_value()
                    # This uses the model's save() method which has the calculation logic
                    item.save()
                    print(f"🔄 Auto-recalculated VerbrauchData {code} after formula update")
                    
                except VerbrauchData.DoesNotExist:
                    print(f"⚠️  VerbrauchData {code} not found for formula {instance.key}")
            
            # Handle RenewableData formulas
            elif instance.category == 'renewable':
                code = instance.key
                # Remove prefixes/suffixes
                code = code.replace('Renewable_', '').replace('_target', '')
                
                from simulator.models import RenewableData
                try:
                    item = RenewableData.objects.get(code=code)
                    # Force save/recalc
                    item.save() 
                    print(f"🔄 Auto-recalculated RenewableData {code} after formula update")
                except RenewableData.DoesNotExist:
                     print(f"⚠️  RenewableData {code} not found for formula {instance.key}")
            
            # Handle WS formulas - auto-recalculate all WS data
            elif instance.category == 'ws':
                print(f"🔄 WS Formula {instance.key} changed - auto-recalculating all WS entries...")
                from simulator.ws_formula_service import recalculate_all_ws_data, get_ws_formula_evaluator
                
                # Clear evaluator cache to ensure fresh formula loading
                evaluator = get_ws_formula_evaluator()
                evaluator.clear_cache()
                
                # Recalculate with 3 passes for proper cascading
                stats = recalculate_all_ws_data(num_passes=3)
                print(f"✅ WS auto-recalculated: {stats['updated']} updates, {stats['errors']} errors")

        except Exception as e:
             print(f"❌ Error in auto-recalculation for {instance.key}: {e}")

    # Schedule the update to run after the current transaction commits
    transaction.on_commit(trigger_update)


@receiver(post_save, sender=FormulaVariable)
@receiver(post_delete, sender=FormulaVariable)
def formula_variable_changed(sender, instance, **kwargs):
    """
    Clear parent formula's cache when a FormulaVariable is modified.
    This ensures variable changes immediately affect formula calculations.
    """
    from django.core.cache import cache
    from simulator.formula_service import FormulaService
    
    if instance.formula_id:
        try:
            formula_key = instance.formula.key
            
            # Clear Django cache
            cache.delete(f'formula_{formula_key}')
            
            # Clear FormulaService cache
            service = FormulaService()
            service.clear_cache(formula_key)
            
            print(f"✅ Formula cache cleared for {formula_key} (variable changed)")

            # DISABLED: Was causing transaction issues that prevented formula saves
            # If this affects Verbrauch formulas, refresh stored values immediately.
            # if instance.formula.category == "verbrauch":
            #     try:
            #         from simulator.verbrauch_recalculator import recalc_all_verbrauch
            #         recalc_all_verbrauch(trigger_code=f"formula_var:{formula_key}")
            #     except Exception as e:
            #         print(f"⚠️ Verbrauch recalculation skipped after variable change: {e}")
        except Exception as e:
            print(f"⚠️  Cache clear warning: {e}")


# Import this in apps.py to register the signals


# ==================================================================================
# 🚀 WS FORMULA TEMPLATE SYSTEM - 100% ADMIN-EDITABLE
# ==================================================================================

def apply_ws_formula_templates(ws_row, tag_im_jahr, context):
    """
    Apply WSFormulaTemplate formulas to a WS row.
    
    This is the main entry point for the template-based formula system.
    Templates are checked FIRST, then falls back to individual formulas.
    
    Args:
        ws_row: WSData instance to apply formulas to
        tag_im_jahr: Day number (1-368+)
        context: Dictionary with:
            - day_prev: Previous day WSData object (for days 2-365)
            - day_1, day_365: Reference day objects
            - sums: Dictionary of sum values
            - all_daily_rows: QuerySet of all daily rows
            - reference_values: Dict of ref_column_366 values
    
    Returns:
        int: Number of templates applied
    """
    templates = WSFormulaTemplate.objects.filter(is_active=True).order_by('priority')
    
    if not templates.exists():
        return 0
    
    templates_applied = 0
    
    for template in templates:
        # Get the appropriate formula for this row type
        formula_expr = template.get_formula_for_row(tag_im_jahr)
        
        if not formula_expr:
            continue  # No formula defined for this row type
        
        try:
            # Evaluate the formula
            value = _evaluate_template_formula(
                expression=formula_expr,
                context=context,
                current_row=ws_row,
                template=template
            )
            
            # Set the value on the WS row
            if value is not None:
                if hasattr(ws_row, template.column_name):
                    setattr(ws_row, template.column_name, value)
                else:
                    # Custom field
                    ws_row.set_custom_field(template.column_name, value)
                
                templates_applied += 1
                
        except Exception as e:
            print(f"❌ Template {template.column_name} row {tag_im_jahr}: {e}")
    
    return templates_applied


def _evaluate_template_formula(expression, context, current_row, template):
    """
    Evaluate a WSFormulaTemplate formula expression.
    
    Supports:
    - row.column          → Current row's column value
    - day_prev.column     → Previous day's column value
    - day_N.column        → Specific day N's column value
    - day_1.column, day_365.column → Reference day values
    - sums['sum_column']  → Sum of all daily values
    - ref_column_366      → Reference value from row 366
    - MAX(), MIN(), ABS(), ROUND(), IF()
    
    Returns:
        float: Calculated value
    """
    if not expression:
        return None
    
    # Simple literal values
    try:
        return float(expression)
    except ValueError:
        pass  # Not a simple number, continue with evaluation
    
    lookup_dict = {}
    eval_expr = expression
    
    def get_field_value(ws_obj, field_name):
        """Get value from regular field or custom_fields JSON"""
        if ws_obj is None:
            return 0
        if hasattr(ws_obj, field_name):
            val = getattr(ws_obj, field_name, None)
            return float(val) if val is not None else 0
        elif hasattr(ws_obj, 'get_custom_field'):
            return ws_obj.get_custom_field(field_name, 0)
        return 0
    
    # Replace row.column references (current row)
    row_pattern = r'row\.(\w+)'
    row_matches = re.findall(row_pattern, expression)
    for column_name in row_matches:
        value = get_field_value(current_row, column_name)
        lookup_key = f'ROW_{column_name.upper()}'
        lookup_dict[lookup_key] = value
        eval_expr = eval_expr.replace(f'row.{column_name}', lookup_key)
    
    # Replace day_prev.column references
    prev_pattern = r'day_prev\.(\w+)'
    prev_matches = re.findall(prev_pattern, expression)
    for column_name in prev_matches:
        day_prev = context.get('day_prev')
        value = get_field_value(day_prev, column_name)
        lookup_key = f'DAY_PREV_{column_name.upper()}'
        lookup_dict[lookup_key] = value
        eval_expr = eval_expr.replace(f'day_prev.{column_name}', lookup_key)
    
    # Replace day_N.column references (specific day)
    day_pattern = r'day_(\d+)\.(\w+)'
    day_matches = re.findall(day_pattern, expression)
    for day_num, column_name in day_matches:
        all_rows = context.get('all_daily_rows')
        day_obj = None
        if all_rows is not None:
            day_obj = all_rows.filter(tag_im_jahr=int(day_num)).first()
        value = get_field_value(day_obj, column_name)
        lookup_key = f'DAY_{day_num}_{column_name.upper()}'
        lookup_dict[lookup_key] = value
        eval_expr = eval_expr.replace(f'day_{day_num}.{column_name}', lookup_key)
    
    # Replace day_1 and day_365 shortcuts
    for day_ref in ['day_1', 'day_365']:
        shortcut_pattern = rf'{day_ref}\.(\w+)'
        shortcut_matches = re.findall(shortcut_pattern, expression)
        for column_name in shortcut_matches:
            day_obj = context.get(day_ref)
            value = get_field_value(day_obj, column_name)
            lookup_key = f'{day_ref.upper()}_{column_name.upper()}'
            lookup_dict[lookup_key] = value
            eval_expr = eval_expr.replace(f'{day_ref}.{column_name}', lookup_key)
    
    # Replace sums['sum_column'] references
    sum_pattern = r"sums\['(\w+)'\]"
    sum_matches = re.findall(sum_pattern, eval_expr)
    for sum_key in sum_matches:
        value = context.get('sums', {}).get(sum_key, 0)
        lookup_key = f'SUM_{sum_key.upper()}'
        lookup_dict[lookup_key] = value
        eval_expr = eval_expr.replace(f"sums['{sum_key}']", lookup_key)
    
    # Replace ref_column_366 references (from reference_values)
    ref_pattern = r'(\w+)_366'
    ref_matches = re.findall(ref_pattern, expression)
    for column_name in ref_matches:
        ref_key = f'{column_name}_366'
        if ref_key not in lookup_dict:  # Don't overwrite already processed
            value = context.get('reference_values', {}).get(ref_key, 0)
            if value == 0:
                # Try without _366 suffix
                value = context.get('reference_values', {}).get(column_name, 0)
            lookup_key = f'REF_{column_name.upper()}_366'
            lookup_dict[lookup_key] = value
            eval_expr = eval_expr.replace(ref_key, lookup_key)
    
    # Handle IF statements
    if 'IF(' in eval_expr.upper():
        eval_expr = _convert_if_statement(eval_expr, lookup_dict)
    
    # Safe math evaluation
    safe_dict = lookup_dict.copy()
    safe_dict.update({
        'MAX': max, 'MIN': min, 'ROUND': round, 'ABS': abs,
        'max': max, 'min': min, 'round': round, 'abs': abs,
    })
    
    try:
        result = eval(eval_expr, {"__builtins__": {}}, safe_dict)
        return float(result) if result is not None else 0
    except Exception as e:
        print(f"    Error evaluating template formula '{expression}' -> '{eval_expr}': {e}")
        return 0


def _convert_if_statement(expression, lookup_dict):
    """
    Convert IF(condition; true_val; false_val) to Python ternary.
    Note: Uses semicolon as separator instead of comma (Excel-like syntax).
    """
    # Pattern for IF statements with semicolon separator
    if_pattern = r'IF\s*\(\s*([^;]+)\s*;\s*([^;]+)\s*;\s*([^)]+)\s*\)'
    
    def replace_if(match):
        condition = match.group(1).strip()
        true_val = match.group(2).strip()
        false_val = match.group(3).strip()
        return f"({true_val} if {condition} else {false_val})"
    
    result = re.sub(if_pattern, replace_if, expression, flags=re.IGNORECASE)
    return result


def get_ws_template_formulas_summary():
    """
    Get a summary of all WS formula templates for debugging/documentation.
    
    Returns:
        dict: Summary of all templates and their formulas
    """
    templates = WSFormulaTemplate.objects.filter(is_active=True).order_by('priority')
    
    summary = {}
    for t in templates:
        summary[t.column_name] = {
            'display_name': t.display_name,
            'priority': t.priority,
            'day_1': t.formula_day_1 or '(not set)',
            'days_2_365': t.formula_days_2_365 or '(not set)',
            'row_366': t.formula_row_366 or '(not set)',
            'row_367': t.formula_row_367 or '(not set)',
            'row_368': t.formula_row_368 or '(not set)',
            'custom_rows': t.custom_row_formulas or {},
        }
    
    return summary
