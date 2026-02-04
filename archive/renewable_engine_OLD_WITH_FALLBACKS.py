"""
Renewable Energy Calculator - 100% Database-Driven
===================================================

✅ FULLY EXTENSIBLE - ALL FORMULAS FROM DATABASE!

This provides:
- Editable formulas via Django Admin
- Real-time formula updates without code changes
- Versioning and validation
- NO hardcoded formulas - database only!
"""

from .formula_evaluator import FormulaEvaluator
from simulator.formula_service import FormulaService


class RenewableCalculator:
    """
    Calculator for renewable energy values.
    100% DATABASE-DRIVEN - NO HARDCODED FORMULAS!
    
    Now uses FormulaService to load formulas from database only.
    """
    
    def __init__(self):
        self.evaluator = FormulaEvaluator()
        self.formula_service = FormulaService(use_cache=True)

class RenewableCalculator:
    """
    Calculator for renewable energy values.
    Now uses FormulaService to load formulas from database.
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
        # Clear cache when new data sources are set
        self.cache = {}
        
        status_lookup = {}
        target_lookup = {}
        
        # Add LandUse data with LandUse_ prefix to match formula references
        # Strip LU_ prefix from codes since formulas use numeric codes (e.g., "1.1" not "LU_1.1")
        for code, data in landuse_data.items():
            # Convert LU_1.1 -> 1.1, LU_2.1 -> 2.1, etc.
            clean_code = code.replace('LU_', '') if code.startswith('LU_') else code
            landuse_key = f'LandUse_{clean_code}'
            if data.get('status_ha') is not None:
                status_lookup[landuse_key] = float(data['status_ha'])
            if data.get('target_ha') is not None:
                target_lookup[landuse_key] = float(data['target_ha'])
        
        # Add VerbrauchData with VerbrauchData_ prefix
        for code, data in verbrauch_data.items():
            verbrauch_key = f'VerbrauchData_{code}'
            if data.get('status') is not None:
                status_lookup[verbrauch_key] = float(data['status'])
            if data.get('ziel') is not None:
                target_lookup[verbrauch_key] = float(data['ziel'])
        
        # Add RenewableData with prefix to prevent conflicts with VerbrauchData
        for code, data in renewable_data.items():
            renewable_key = f'RenewableData_{code}'
            if data.get('status_value') is not None:
                status_lookup[renewable_key] = float(data['status_value'])
            if data.get('target_value') is not None:
                target_lookup[renewable_key] = float(data['target_value'])
        
        self.evaluator.set_lookups(status_lookup, target_lookup)
    
    def calculate(self, code):
        """
        Calculate status and target values for a renewable energy item.
        Now loads formula from database via FormulaService.
        
        UPDATED: Now tries FormulaVariable mappings first (fully extensible approach).
        Falls back to stored values for fixed entries.
        
        Args:
            code: The renewable energy code
            
        Returns:
            tuple: (status_value, target_value) or (None, None) if error
        """
        # Check cache first
        if code in self.cache:
            return self.cache[code]
        
        # NEW: Try evaluating with FormulaVariable mappings first
        from simulator.formula_service import evaluate_with_mappings
        status, target = evaluate_with_mappings(code, category='renewable')
        
        # If formula evaluation succeeded, cache and return
        if status is not None or target is not None:
            self.cache[code] = (status, target)
            return status, target
        
        # For fixed values or when formula evaluation returns (None, None),
        # fall back to stored values in RenewableData. This also covers formulas
        # with no variables (fixed entries) where evaluate_with_mappings returns None.
        try:
            from simulator.models import RenewableData, Formula
            formula_obj = Formula.objects.filter(key=code, category='renewable').first()
            renewable = RenewableData.objects.get(code=code)
            
            # Use stored values for fixed entries or formulas without variables
            if renewable.is_fixed or (formula_obj and not formula_obj.variables.exists()):
                result = (renewable.status_value, renewable.target_value)
                self.cache[code] = result
                return result
        except:
            pass
        
        # If nothing worked, return None
        self.cache[code] = (None, None)
        return None, None
    
    def _is_simple_reference(self, formula):
        """Check if formula is a simple code reference"""
        return (
            formula and
            not any(op in formula for op in ['+', '-', '*', '/', '(', ')', 'IF']) and
            ('.' in formula or formula.startswith('VerbrauchData_') or formula.startswith('LandUse_'))
        )
    
    def _get_simple_reference_values(self, formula):
        """Get values for simple code references"""
        if formula.startswith('VerbrauchData_'):
            # VerbrauchData is stored with prefix in lookup
            lookup_key = formula
        elif formula.startswith('LandUse_'):
            # LandUse is stored with prefix in lookup  
            lookup_key = formula
        elif formula.startswith('Verbrauch_'):
            code = formula.replace('Verbrauch_', '')
            lookup_key = f'VerbrauchData_{code}'
        elif formula.startswith('Renewable_'):
            code = formula.replace('Renewable_', '')
            lookup_key = f'RenewableData_{code}'
        else:
            # Standalone code - default to RenewableData namespace
            lookup_key = f'RenewableData_{formula}'
        
        status = self.evaluator.status_lookup.get(lookup_key)
        target = self.evaluator.target_lookup.get(lookup_key)
        return (status, target)
    
    def get_formula(self, code):
        """
        Get the formula for a code from database.
        """
        formula_def = self.formula_service.get_formula(code, category='renewable')
        if formula_def:
            return formula_def.get('expression')
        return None
    
    def is_fixed(self, code):
        """
        Check if a code is a fixed value from database.
        """
        formula_def = self.formula_service.get_formula(code, category='renewable')
        if formula_def:
            return formula_def.get('is_fixed', True)
        return True
