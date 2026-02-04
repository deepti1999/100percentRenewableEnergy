"""
Formula Evaluator - Generic formula evaluation engine
====================================================

Handles:
- Mathematical expressions (2.1 + 3.5 * 4)
- Code references (6.1.3, VerbrauchData_1.4, LandUse_LU_2.1)
- IF statements (IF(condition; true_value; false_value))
- Safe evaluation with proper error handling
"""

import re


class FormulaEvaluator:
    """Generic formula evaluator for all calculation types"""
    
    def __init__(self):
        self.status_lookup = {}
        self.target_lookup = {}
    
    def set_lookups(self, status_lookup, target_lookup):
        """Set the lookup dictionaries for code references"""
        self.status_lookup = status_lookup
        self.target_lookup = target_lookup
    
    def evaluate(self, formula, use_target=False):
        """
        Evaluate a formula and return the result.
        
        Args:
            formula: The formula string to evaluate
            use_target: If True, use target values; if False, use status values
            
        Returns:
            float or None: The calculated result, or None if evaluation fails
        """
        if not formula:
            return None
        
        formula = self._normalize_target_tokens(formula)

        data_lookup = self.target_lookup if use_target else self.status_lookup
        
        # Handle IF statements
        if formula.startswith('IF('):
            return self._evaluate_if_statement(formula, data_lookup)
        
        # Handle simple mathematical expressions
        return self._evaluate_expression(formula, data_lookup)
    
    def _evaluate_expression(self, formula, data_lookup):
        """Evaluate a mathematical expression with code references"""
        expression = self._normalize_target_tokens(formula)
        
        # Handle % symbol (convert to /100)
        expression = re.sub(r'(\d+(?:\.\d+)*)\s*%', r'(\1/100)', expression)
        
        # IMPORTANT: Process prefixed references FIRST (VerbrauchData_, LandUse_, etc.)
        # This prevents "1.4" in "VerbrauchData_1.4" from being replaced prematurely
        
        # Handle VerbrauchData_ references
        # CRITICAL: Sort by length DESC to replace longest codes first
        verbrauchdata_pattern = r'VerbrauchData_(\d+(?:\.\d+)*)'
        verbrauchdata_matches = re.findall(verbrauchdata_pattern, expression)
        verbrauchdata_matches_sorted = sorted(set(verbrauchdata_matches), key=len, reverse=True)
        for code in verbrauchdata_matches_sorted:
            full_key = f'VerbrauchData_{code}'
            if full_key in data_lookup:
                value = data_lookup[full_key]
                expression = expression.replace(full_key, str(value))
            else:
                return None  # Code not found
        
        # Handle Verbrauch_ references (with underscores OR dots)
        # CRITICAL: Sort by length DESC to replace longest codes first (prevents partial overlap)
        verbrauch_pattern = r'Verbrauch_([\d_\.]+)'
        verbrauch_matches = re.findall(verbrauch_pattern, expression)
        verbrauch_matches_sorted = sorted(set(verbrauch_matches), key=len, reverse=True)
        for code in verbrauch_matches_sorted:
            full_key = f'Verbrauch_{code}'
            if full_key in data_lookup:
                value = data_lookup[full_key]
                expression = expression.replace(full_key, str(value))
            else:
                return None
        
        # Handle Renewable_ references
        # CRITICAL: Sort by length DESC to replace longest codes first
        renewable_pattern = r'Renewable_(\d+(?:\.\d+)*)'
        renewable_matches = re.findall(renewable_pattern, expression)
        renewable_matches_sorted = sorted(set(renewable_matches), key=len, reverse=True)
        for code in renewable_matches_sorted:
            full_key = f'Renewable_{code}'
            if full_key in data_lookup:
                value = data_lookup[full_key]
                expression = expression.replace(full_key, str(value))
            else:
                return None
        
        # Handle LandUse_ references
        # CRITICAL: Sort by length DESC to replace longest codes first
        landuse_pattern = r'LandUse_([A-Za-z0-9_.]+)'
        landuse_matches = re.findall(landuse_pattern, expression)
        landuse_matches_sorted = sorted(set(landuse_matches), key=len, reverse=True)
        for code in landuse_matches_sorted:
            full_key = f'LandUse_{code}'
            if full_key in data_lookup:
                value = data_lookup[full_key]
                expression = expression.replace(full_key, str(value))
            else:
                return None
        
        # Now handle standalone numeric code references (e.g., "6.1.3", "2.1.1")
        # These are RenewableData references without explicit prefix
        # Use placeholders to avoid overlapping replacements
        code_pattern = r'\b(\d+(?:\.\d+)+)\b'
        code_matches = sorted(set(re.findall(code_pattern, expression)), key=len, reverse=True)
        
        placeholder_map = {}
        placeholder_counter = 0
        
        # First pass: replace codes with placeholders
        for code in code_matches:
            # Standalone codes are RenewableData references
            renewable_key = f'RenewableData_{code}'
            if renewable_key in data_lookup:
                value = data_lookup[renewable_key]
                placeholder = f'__PH{placeholder_counter}__'
                placeholder_map[placeholder] = str(value)
                placeholder_counter += 1
                expression = re.sub(r'\b' + re.escape(code) + r'\b', placeholder, expression)
            else:
                # Code not found - don't fail silently, just skip
                pass
        
        # Second pass: replace placeholders with actual values
        for placeholder, value in placeholder_map.items():
            expression = expression.replace(placeholder, value)
        
        # Evaluate the mathematical expression
        try:
            # Safety check: only allow safe mathematical operations
            allowed_chars = set('0123456789+-*/.() eE-')
            if all(c in allowed_chars or c.isspace() for c in expression):
                result = eval(expression)
                return float(result)
            else:
                # Expression contains non-numeric characters (likely unresolved codes)
                return None
        except ZeroDivisionError:
            return 0.0
        except (SyntaxError, NameError, ValueError, TypeError):
            return None
        except Exception as e:
            print(f"Unexpected error evaluating expression '{expression}': {e}")
            return None
    
    def _evaluate_if_statement(self, formula, data_lookup):
        """
        Evaluate IF statement: IF(condition; true_value; false_value)
        """
        formula = self._normalize_target_tokens(formula)
        # Extract IF statement parts
        if_pattern = r'IF\(([^;]+);([^;]+);([^)]+)\)'
        match = re.match(if_pattern, formula)
        
        if not match:
            print(f"Invalid IF statement format: {formula}")
            return None
        
        condition_str, true_value_str, false_value_str = match.groups()
        
        # Evaluate condition
        condition_result = self._evaluate_condition(condition_str.strip(), data_lookup)
        if condition_result is None:
            return None
        
        # Evaluate the appropriate branch
        if condition_result:
            return self._evaluate_expression(true_value_str.strip(), data_lookup)
        else:
            return self._evaluate_expression(false_value_str.strip(), data_lookup)
    
    def _evaluate_condition(self, condition_str, data_lookup):
        """Evaluate a condition (e.g., "VerbrauchData_4.3.5 > (VerbrauchData_3.7 + ...)")"""
        # Replace all code references in the condition
        expression = self._normalize_target_tokens(condition_str)
        
        # Handle VerbrauchData_ references
        verbrauchdata_pattern = r'VerbrauchData_(\d+(?:\.\d+)*)'
        for code in re.findall(verbrauchdata_pattern, expression):
            if code in data_lookup:
                expression = expression.replace(f'VerbrauchData_{code}', str(data_lookup[code]))
            else:
                return None
        
        # Handle other code references
        code_pattern = r'\b(\d+(?:\.\d+)+)\b'
        code_matches = sorted(set(re.findall(code_pattern, expression)), key=len, reverse=True)
        
        for code in code_matches:
            if code in data_lookup:
                expression = re.sub(r'\b' + re.escape(code) + r'\b', str(data_lookup[code]), expression)
        
        # Evaluate the condition
        try:
            # Safety check for condition evaluation
            allowed_chars = set('0123456789+-*/.()<>= ')
            if all(c in allowed_chars or c.isspace() for c in expression):
                result = eval(expression)
                return bool(result)
            else:
                return None
        except Exception as e:
            print(f"Error evaluating condition '{expression}': {e}")
            return None

    def _normalize_target_tokens(self, expression):
        """
        Normalize target/ziel tokens like Renewable_1_2_ziel -> Renewable_1_2.
        """
        if not expression or ("_ziel" not in expression and "_target" not in expression):
            return expression
        patterns = [
            r'\b(LandUse_[A-Za-z0-9_.]+)_(ziel|target)\b',
            r'\b(Renewable_[0-9_.]+)_(ziel|target)\b',
            r'\b(Verbrauch_[0-9_.]+)_(ziel|target)\b',
            r'\b(RenewableData_[0-9.]+)_(ziel|target)\b',
            r'\b(VerbrauchData_[0-9.]+)_(ziel|target)\b',
        ]
        for pattern in patterns:
            expression = re.sub(pattern, r'\1', expression)
        return expression
