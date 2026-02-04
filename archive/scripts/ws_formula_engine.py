"""
WS Formula Evaluation Service
Handles cascading formula evaluation for WS calculations
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable
from simulator.formula_service import _resolve_variable, _safe_eval
import logging

logger = logging.getLogger(__name__)

def evaluate_ws_formula(formula_key: str, ws_context: dict = None) -> float:
    """
    Evaluate a WS formula with cascading support.
    
    Args:
        formula_key: The WS formula key to evaluate
        ws_context: Additional context (for ws_current_row, ws_sum, etc.)
    
    Returns:
        Calculated value or None
    """
    # Cache for already-evaluated formulas in this call chain
    _cache = {}
    
    def _evaluate_recursive(key: str) -> float:
        """Recursively evaluate formulas, caching results."""
        if key in _cache:
            return _cache[key]
        
        try:
            formula = Formula.objects.prefetch_related('variables').get(
                key=key,
                category='ws',
                is_active=True
            )
        except Formula.DoesNotExist:
            logger.warning(f"WS Formula not found: {key}")
            return None
        
        # Build context
        context = ws_context.copy() if ws_context else {}
        
        # Add variable values
        for var in formula.variables.all():
            value = _resolve_variable(var, use_target=True)
            if value is not None:
                context[var.variable_name] = value
        
        # Parse expression to find referenced formulas
        import re
        # Find all WS_* tokens in the expression
        ws_refs = set(re.findall(r'WS_[A-Z_0-9]+', formula.expression))
        
        # Recursively evaluate referenced formulas
        for ref_key in ws_refs:
            if ref_key != key:  # Avoid self-reference
                ref_value = _evaluate_recursive(ref_key)
                if ref_value is not None:
                    context[ref_key] = ref_value
        
        # Evaluate the expression
        try:
            result = _safe_eval(formula.expression, context, use_target=True)
            _cache[key] = result
            return result
        except Exception as e:
            logger.error(f"Error evaluating WS formula {key}: {e}")
            logger.error(f"Expression: {formula.expression}")
            logger.error(f"Context: {context}")
            return None
    
    return _evaluate_recursive(formula_key)


# Test the cascading evaluation
if __name__ == "__main__":
    print("="*80)
    print("TESTING WS CASCADING FORMULA EVALUATION")
    print("="*80)
    
    print("\n1. Testing Row 366 Reference Formulas...")
    print("-" * 80)
    
    test_formulas = [
        'WS_DAVON_RAUMW_KORR_366',
        'WS_REF_PV',
        'WS_REF_WIND',
        'WS_REF_HYDRO',
        'WS_REF_BIO',
        'WS_REF_TOTAL_GEN',
        'WS_REF_AFTER_ELY',
        'WS_STROMVERBR_RAUMWAERM_KORR_366',
        'WS_SOLARSTROM_366',
        'WS_WINDSTROM_366',
        'WS_SONST_KRAFT_KONSTANT_366',
    ]
    
    results = {}
    for key in test_formulas:
        result = evaluate_ws_formula(key)
        results[key] = result
        status = "✓" if result is not None else "✗"
        print(f"{status} {key}: {result}")
    
    print("\n2. Verifying Annual Electricity Diagram Logic...")
    print("-" * 80)
    
    print(f"\nTotal Generation (M): {results.get('WS_REF_TOTAL_GEN')}")
    print(f"After Electrolysis (N): {results.get('WS_REF_AFTER_ELY')}")
    print(f"Final Grid Supply: {results.get('WS_STROMVERBR_RAUMWAERM_KORR_366')}")
    
    print("\n3. Testing Daily Formula Structure...")
    print("-" * 80)
    
    # Test daily formulas with mock WS context
    mock_ws_context = {
        'verbrauch_promille': 2.74,  # Example from row 1
        'heizung_abwaerm_promille': 0.0,
        'wind_promille': 1.5,
        'solar_promille': 0.0,
    }
    
    print("\nMock context (row 1 example):")
    for k, v in mock_ws_context.items():
        print(f"  {k} = {v}")
    
    daily_formulas = [
        'WS_STROMVERBR',
        'WS_DAVON_RAUMW_KORR',
        'WS_STROMVERBR_RAUMWAERM_KORR',
        'WS_WINDSTROM',
        'WS_SOLARSTROM',
        'WS_SONST_KRAFT_KONSTANT',
        'WS_WIND_SOLAR_KONSTANT',
        'WS_DIREKTVERBR_STROM',
        'WS_UEBERSCHUSS_STROM',
    ]
    
    print("\nDaily formula results:")
    for key in daily_formulas:
        result = evaluate_ws_formula(key, mock_ws_context)
        status = "✓" if result is not None else "✗"
        print(f"{status} {key}: {result}")
    
    print("\n" + "="*80)
    print("✅ WS Cascading Formula Test Complete")
    print("="*80)
