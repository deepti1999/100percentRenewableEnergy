"""
Formula Validators - Advanced Formula Validation
================================================

This module provides comprehensive formula validation including:
- Syntax checking
- Code reference validation
- Circular dependency detection
- Sample data testing
- Performance analysis
"""

from typing import Dict, List, Optional, Tuple
import re
from django.db.models import Q


class FormulaValidator:
    """Validates formula expressions for correctness and dependencies"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate(self, formula_key: str, expression: str, category: str = 'renewable') -> Tuple[bool, Dict]:
        """
        Comprehensive formula validation.
        
        Args:
            formula_key: Formula identifier
            expression: Formula expression to validate
            category: Formula category
            
        Returns:
            Tuple of (is_valid, result_dict)
            result_dict contains: {
                'valid': bool,
                'errors': list,
                'warnings': list,
                'info': list,
                'referenced_codes': list,
                'has_circular_dependency': bool
            }
        """
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Basic checks
        if not expression or expression.strip() == '':
            self.errors.append("Expression is empty")
            return False, self._build_result()
        
        if expression == 'None':
            self.errors.append("Expression is 'None' string literal")
            return False, self._build_result()
        
        # Syntax validation
        self._validate_syntax(expression)
        
        # Reference validation
        referenced_codes = self._extract_code_references(expression)
        self._validate_code_references(referenced_codes, category)
        
        # Circular dependency check
        has_circular = self._check_circular_dependency(formula_key, referenced_codes)
        
        # Build result
        result = self._build_result()
        result['referenced_codes'] = referenced_codes
        result['has_circular_dependency'] = has_circular
        
        is_valid = len(self.errors) == 0
        result['valid'] = is_valid
        
        return is_valid, result
    
    def _validate_syntax(self, expression: str):
        """Check for basic syntax errors"""
        # Check parentheses balance
        if expression.count('(') != expression.count(')'):
            self.errors.append(f"Unbalanced parentheses: {expression.count('(')} opening, {expression.count(')')} closing")
        
        # Check for invalid characters
        allowed_chars = set('0123456789+-*/.()_% \t\nABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
        invalid_chars = set(expression) - allowed_chars
        if invalid_chars:
            self.warnings.append(f"Potentially invalid characters found: {', '.join(invalid_chars)}")
        
        # Check for division by zero patterns
        if re.search(r'/\s*0(?:\D|$)', expression):
            self.errors.append("Potential division by zero detected")
        
        # Check for consecutive operators
        if re.search(r'[+\-*/]{2,}', expression.replace('**', '')):
            self.errors.append("Consecutive operators detected")
        
        # Check for dangling operators
        if re.search(r'[+\-*/]\s*$', expression):
            self.errors.append("Expression ends with an operator")
        if re.search(r'^\s*[+*/]', expression):
            self.errors.append("Expression starts with an operator (except -)")
    
    def _extract_code_references(self, expression: str) -> List[str]:
        """Extract all code references from expression"""
        codes = []
        
        # Pattern 1: Prefixed codes (LandUse_X.X, VerbrauchData_X.X, Renewable_X.X, Verbrauch_X.X)
        prefixed_pattern = r'(?:LandUse|VerbrauchData|Verbrauch|Renewable)_([A-Za-z0-9_.]+)'
        prefixed_matches = list(re.finditer(prefixed_pattern, expression))
        
        for match in prefixed_matches:
            codes.append(match.group(0))  # Full match including prefix
        
        # Pattern 2: Standalone numeric codes (X.X.X)
        # Only add if they don't overlap with prefixed codes
        standalone_pattern = r'\b(\d+(?:\.\d+)+)\b'
        standalone_matches = list(re.finditer(standalone_pattern, expression))
        
        for match in standalone_matches:
            code = match.group(1)
            # Check if this match overlaps with any prefixed match (by position)
            overlaps_with_prefixed = any(
                match.start() >= p.start() and match.end() <= p.end() 
                for p in prefixed_matches
            )
            
            if '.' in code and not overlaps_with_prefixed:
                codes.append(code)
        
        return list(set(codes))  # Remove duplicates
    
    def _validate_code_references(self, codes: List[str], category: str):
        """Validate that referenced codes exist"""
        from simulator.models import LandUse, RenewableData, VerbrauchData
        
        for code in codes:
            if code.startswith('LandUse_'):
                # Check LandUse table
                # Formulas use numeric codes (e.g., LandUse_1.1)
                # Database stores codes with LU_ prefix (e.g., LU_1.1)
                lookup_code = code.replace('LandUse_', '')
                # Try both with and without LU_ prefix for backwards compatibility
                if not (LandUse.objects.filter(code=f'LU_{lookup_code}').exists() or 
                        LandUse.objects.filter(code=lookup_code).exists()):
                    self.warnings.append(f"LandUse code not found: {lookup_code}")
                else:
                    self.info.append(f"✓ LandUse reference valid: {lookup_code}")
                    
            elif code.startswith('VerbrauchData_') or code.startswith('Verbrauch_'):
                # Check VerbrauchData table
                lookup_code = code.replace('VerbrauchData_', '').replace('Verbrauch_', '')
                if not VerbrauchData.objects.filter(code=lookup_code).exists():
                    self.warnings.append(f"VerbrauchData code not found: {lookup_code}")
                else:
                    self.info.append(f"✓ VerbrauchData reference valid: {lookup_code}")
                    
            elif code.startswith('Renewable_'):
                # Check RenewableData table
                lookup_code = code.replace('Renewable_', '')
                if not RenewableData.objects.filter(code=lookup_code).exists():
                    self.warnings.append(f"RenewableData code not found: {lookup_code}")
                else:
                    self.info.append(f"✓ RenewableData reference valid: {lookup_code}")
                    
            else:
                # Standalone code - check based on formula category
                if category == 'verbrauch':
                    # For Verbrauch formulas, check VerbrauchData
                    if not VerbrauchData.objects.filter(code=code).exists():
                        self.warnings.append(f"VerbrauchData code not found: {code}")
                    else:
                        self.info.append(f"✓ VerbrauchData reference valid: {code}")
                elif category == 'renewable':
                    # For Renewable formulas, check RenewableData
                    if not RenewableData.objects.filter(code=code).exists():
                        self.warnings.append(f"RenewableData code not found: {code}")
                    else:
                        self.info.append(f"✓ RenewableData reference valid: {code}")
                else:
                    # For other categories, just note the reference
                    self.info.append(f"→ Code reference: {code} (category: {category})")
    
    def _check_circular_dependency(self, formula_key: str, referenced_codes: List[str]) -> bool:
        """
        Check for circular dependencies in formula references.
        A circular dependency exists if formula A references B, and B references A (directly or indirectly).
        """
        from simulator.models import Formula
        
        visited = set()
        path = [formula_key]
        
        def has_cycle(current_key: str, depth: int = 0) -> bool:
            if depth > 20:  # Prevent infinite recursion
                return True
            
            if current_key in visited:
                if current_key in path:
                    cycle_path = ' → '.join(path + [current_key])
                    self.errors.append(f"Circular dependency detected: {cycle_path}")
                    return True
                return False
            
            visited.add(current_key)
            path.append(current_key)
            
            # Get formula for current key
            try:
                formula = Formula.objects.get(key=current_key, is_active=True)
                child_codes = self._extract_code_references(formula.expression or '')
                
                for child_code in child_codes:
                    # Extract just the code part (remove prefixes)
                    clean_code = child_code
                    for prefix in ['LandUse_', 'VerbrauchData_', 'Verbrauch_', 'Renewable_']:
                        clean_code = clean_code.replace(prefix, '')
                    
                    if has_cycle(clean_code, depth + 1):
                        return True
                        
            except Formula.DoesNotExist:
                pass
            
            path.pop()
            return False
        
        return has_cycle(formula_key)
    
    def _build_result(self) -> Dict:
        """Build validation result dictionary"""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'info': self.info.copy(),
            'referenced_codes': [],
            'has_circular_dependency': False,
        }
    
    def test_with_sample_data(self, expression: str, sample_data: Dict[str, float]) -> Tuple[bool, Optional[float], str]:
        """
        Test formula with sample data.
        
        Args:
            expression: Formula expression
            sample_data: Dictionary mapping codes to values
                        e.g., {'LandUse_1.1': 100, '1.1.2.1': 50}
        
        Returns:
            Tuple of (success, result, message)
        """
        try:
            # Replace all code references with values
            test_expr = expression
            
            for code, value in sample_data.items():
                # Replace with placeholder first to avoid overlap
                placeholder = f'__VAL_{hash(code)}__'
                test_expr = test_expr.replace(code, placeholder)
            
            # Replace placeholders with actual values
            for code, value in sample_data.items():
                placeholder = f'__VAL_{hash(code)}__'
                test_expr = test_expr.replace(placeholder, str(value))
            
            # Evaluate
            result = eval(test_expr, {"__builtins__": {}}, {})
            return True, float(result), f"Formula evaluated successfully: {result}"
            
        except ZeroDivisionError:
            return False, None, "Division by zero error"
        except SyntaxError as e:
            return False, None, f"Syntax error: {str(e)}"
        except Exception as e:
            return False, None, f"Evaluation error: {str(e)}"


# Convenience functions
def validate_formula(formula_key: str, expression: str, category: str = 'renewable') -> Tuple[bool, Dict]:
    """
    Quick validation function.
    
    Returns:
        Tuple of (is_valid, result_dict)
    """
    validator = FormulaValidator()
    return validator.validate(formula_key, expression, category)


def get_formula_dependencies(formula_key: str) -> List[str]:
    """
    Get list of all codes that a formula depends on.
    
    Args:
        formula_key: Formula identifier
        
    Returns:
        List of code strings
    """
    from simulator.models import Formula
    
    try:
        formula = Formula.objects.get(key=formula_key)
        validator = FormulaValidator()
        return validator._extract_code_references(formula.expression or '')
    except Formula.DoesNotExist:
        return []
