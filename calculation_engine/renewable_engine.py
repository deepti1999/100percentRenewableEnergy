"""
Renewable Energy Calculator - 100% Database-Driven FAIL-FAST
==============================================================

✅ FULLY EXTENSIBLE - ALL FORMULAS FROM DATABASE!
✅ FAIL FAST - RAISES on missing formulas (NO SILENT FALLBACKS!)

This enforces:
- All formulas MUST be in database
- Missing formulas RAISE ValueError
- NO fallback to stored values
- NO silent returns of (None, None)
"""

from .formula_evaluator import FormulaEvaluator
from simulator.formula_service import FormulaService, evaluate_with_mappings


class RenewableCalculator:
    """
    100% DATABASE-DRIVEN Calculator for renewable energy values.
    
    FAIL-FAST BEHAVIOR:
    - Raises ValueError if formula is missing from database
    - Raises ValueError if formula evaluation fails
    - NO silent fallbacks to stored values
    - Fixed values MUST have is_fixed=True flag in database
    """
    
    def __init__(self):
        self.evaluator = FormulaEvaluator()
        self.formula_service = FormulaService(use_cache=True)
        self.cache = {}
    
    def set_data_sources(self, landuse_data, verbrauch_data, renewable_data):
        """
        Set up lookup dictionaries from data sources.
        
        Args:
            landuse_data: Dict of {code: {'status_ha': x, 'target_ha': y}}
            verbrauch_data: Dict of {code: {'status': x, 'ziel': y}}
            renewable_data: Dict of {code: {'status_value': x, 'target_value': y}}
        """
        self.cache = {}  # Clear cache when new data sources are set
        
        status_lookup = {}
        target_lookup = {}
        
        # Add LandUse data
        for code, data in landuse_data.items():
            clean_code = code.replace('LU_', '') if code.startswith('LU_') else code
            landuse_key = f'LandUse_{clean_code}'
            landuse_key_raw = f'LandUse_{code}'
            if data.get('status_ha') is not None:
                status_lookup[landuse_key] = float(data['status_ha'])
                status_lookup[landuse_key_raw] = float(data['status_ha'])
            if data.get('target_ha') is not None:
                target_lookup[landuse_key] = float(data['target_ha'])
                target_lookup[landuse_key_raw] = float(data['target_ha'])
        
        # Add VerbrauchData
        for code, data in verbrauch_data.items():
            verbrauch_key = f'VerbrauchData_{code}'
            if data.get('status') is not None:
                status_lookup[verbrauch_key] = float(data['status'])
            if data.get('ziel') is not None:
                target_lookup[verbrauch_key] = float(data['ziel'])
        
        # Add RenewableData
        for code, data in renewable_data.items():
            renewable_key = f'RenewableData_{code}'
            if data.get('status_value') is not None:
                status_lookup[renewable_key] = float(data['status_value'])
            if data.get('target_value') is not None:
                target_lookup[renewable_key] = float(data['target_value'])
        
        self.evaluator.set_lookups(status_lookup, target_lookup)
        
        # Store lookups in cache for the formula service to use
        self.cache['status_lookup'] = status_lookup
        self.cache['target_lookup'] = target_lookup
    
    def calculate(self, code, fail_fast=True):
        """
        Calculate status and target values for a renewable energy item.
        
        FAIL-FAST MODE (default):
        - Raises ValueError if formula missing from database
        - Raises ValueError if formula evaluation returns None
        - NO silent fallbacks
        
        Args:
            code: The renewable energy code
            fail_fast: If True (default), raises on missing/invalid formulas
            
        Returns:
            tuple: (status_value, target_value)
            
        Raises:
            ValueError: If formula is missing or evaluation fails (when fail_fast=True)
        """
        # Check cache first
        if code in self.cache:
            return self.cache[code]
        
        # Check if this is a fixed value
        from simulator.models import RenewableData, Formula
        
        try:
            renewable = RenewableData.objects.get(code=code)
        except RenewableData.DoesNotExist:
            if fail_fast:
                raise ValueError(f"RenewableData {code} not found in database")
            return (None, None)
        
        # NOTE: 9.3.1 and 9.3.4 values are now updated directly in database by ws_365_service
        # No special handling needed here - they read from database like all other rows
        
        # Try to load formula (may be missing or flagged fixed)
        formula_obj = Formula.objects.filter(
            key=code, category='renewable', is_active=True
        ).first()

        # If no active formula and record is fixed, return stored values
        if not formula_obj and renewable.is_fixed:
            result = (renewable.status_value, renewable.target_value)
            self.cache[code] = result
            return result

        # If an active formula exists with variables, treat as calculated even if is_fixed flags are True
        has_variables = bool(formula_obj and formula_obj.variables.exists())

        if not has_variables and renewable.is_fixed:
            result = (renewable.status_value, renewable.target_value)
            self.cache[code] = result
            return result

        if not formula_obj:
            if fail_fast:
                raise ValueError(
                    f"Formula for {code} (category=renewable) NOT FOUND in database. "
                    f"Add formula to database or set is_fixed=True."
                )
            return (None, None)

        # Evaluate status formula using FormulaVariable mappings
        # NEW: Use formula service with LOOKUP support for proper cascading
        # Pass our in-memory lookups so the formula service doesn't hit the DB for stale values
        status, _ = evaluate_with_mappings(
            code, 
            category='renewable',
            status_lookup=self.cache.get('status_lookup', {}),
            target_lookup=self.cache.get('target_lookup', {})
        )

        # Resolve target formula key (supports legacy _ziel_target keys)
        target = None
        target_formula_key = None
        target_key_candidates = [f"{code}_target", f"{code}_ziel_target", f"{code}_ziel"]
        for candidate in target_key_candidates:
            target_formula = Formula.objects.filter(
                key=candidate, category='renewable', is_active=True
            ).first()
            if target_formula:
                target_formula_key = candidate
                t_status, t_target = evaluate_with_mappings(
                    candidate, 
                    category='renewable',
                    status_lookup=self.cache.get('status_lookup', {}),
                    target_lookup=self.cache.get('target_lookup', {})
                )
                target = t_target if t_target is not None else t_status
                break

        # Fail fast if evaluation returns None
        if fail_fast and (status is None or target is None):
            missing_target = target is None and target_formula_key is None
            hint = f"Missing target formula (tried {', '.join(target_key_candidates)})" if missing_target else "Target formula evaluation failed"
            raise ValueError(
                f"Formula evaluation for {code} returned None. "
                f"{hint}. Formula: {formula_obj.expression}. "
                f"Check FormulaVariables or formula expression."
            )

        self.cache[code] = (status, target)
        return status, target
    
    def get_formula(self, code):
        """Get the formula expression from database."""
        formula_def = self.formula_service.get_formula(code, category='renewable')
        if formula_def:
            return formula_def.get('expression')
        return None
    
    def is_fixed(self, code):
        """Check if a code is a fixed value."""
        formula_def = self.formula_service.get_formula(code, category='renewable')
        if formula_def:
            return formula_def.get('is_fixed', True)
        return True
