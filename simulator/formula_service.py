"""
Formula Service - Database-Driven Formula Management
====================================================

This service provides a centralized way to load and manage formulas.
It implements a hybrid approach:
1. Load from database first (if available)
2. Fall back to Python files for backward compatibility
3. Cache for performance

ENHANCED FEATURES:
- Database-first formula loading
- Fallback to Python files (renewable_energy_complete_formulas.py)
- Caching for performance
- Formula validation
- Version control support
"""

from typing import Dict, Optional, List
from django.db import models
from django.core.cache import cache
from django.utils import timezone
import logging
import re

from simulator.models import (
    Formula,
    FormulaVariable,
    LandUse,
    RenewableData,
    VerbrauchData,
)

logger = logging.getLogger(__name__)


def evaluate_formula_by_key(formula_key: str, extra_context: Optional[Dict] = None) -> Optional[float]:
    """
    Evaluate a formula by its key using FormulaVariable mappings to resolve inputs.

    Returns:
        float or None if not found/failed.
    """
    formula = Formula.objects.filter(key=formula_key).prefetch_related("variables").first()
    if not formula:
        return None

    context = _build_context(formula)
    if extra_context:
        context.update(extra_context)

    try:
        return _safe_eval(formula.expression, context, formula_key=formula_key)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"❌ Error evaluating formula '{formula_key}': {exc}")
        return None


def _build_context(formula: Formula, use_target: bool = False, status_lookup: Optional[Dict] = None, target_lookup: Optional[Dict] = None) -> Dict[str, float]:
    """
    Resolve all variables for a formula into a plain dict.
    
    Args:
        formula: The Formula object
        use_target: If True, resolve variables using target/ziel values instead of status
    """
    # NOTE: Removed connection.close()/connect() that was breaking transactions!
    # The ORM cache is fine; if fresh values are needed, use refresh_from_db() on objects.
    context: Dict[str, float] = {}
    for var in formula.variables.all():
        # Determine if we should use target based on:
        # 1. The use_target parameter (for ziel formulas)
        # 2. The variable's source_type (if it explicitly requests ziel/target)
        use_var_target = use_target or ('ziel' in var.source_type.lower() or 'target' in var.source_type.lower())
        
        resolved = _resolve_variable(var, use_target=use_var_target, status_lookup=status_lookup, target_lookup=target_lookup)
        if resolved is None:
            resolved = var.default_value
        if resolved is None:
            # No value available; use 0 to keep evaluation resilient
            resolved = 0
        context[var.variable_name] = resolved
    return context


def _resolve_variable(var: FormulaVariable, use_target: bool = False) -> Optional[float]:
    """
    Resolve a single FormulaVariable to a numeric value.
    
    IMPORTANT: The source_type determines which field to read:
    - verbrauch_status -> always read .status field
    - verbrauch_ziel -> always read .ziel field
    The use_target parameter is NOT used for verbrauch (it's for landuse/renewable)
    """
    source_key = var.source_key

    if var.source_type == FormulaVariable.LITERAL:
        try:
            return float(source_key)
        except (TypeError, ValueError):
            return None

    # FIXED: source_type determines the field, NOT use_target!
    if var.source_type == FormulaVariable.LANDUSE_STATUS:
        # Always read status_ha field
        return _get_value(LandUse, "code", source_key, "status_ha")
    if var.source_type == FormulaVariable.LANDUSE_TARGET:
        # Always read target_ha field
        return _get_value(LandUse, "code", source_key, "target_ha")
    if var.source_type == FormulaVariable.RENEWABLE_STATUS:
        # Always read status_value field
        return _get_value(RenewableData, "code", source_key, "status_value")
    if var.source_type == FormulaVariable.RENEWABLE_TARGET:
        # Always read target_value field
        return _get_value(RenewableData, "code", source_key, "target_value")
    
    # FIXED: For verbrauch, the source_type determines the field, NOT use_target!
    if var.source_type == FormulaVariable.VERBRAUCH_STATUS:
        # Always read status field
        return _get_value(VerbrauchData, "code", source_key, "status")
    if var.source_type == FormulaVariable.VERBRAUCH_ZIEL:
        # Always read ziel field
        return _get_value(VerbrauchData, "code", source_key, "ziel")

    return None


def _get_value(model: models.Model, lookup_field: str, lookup_value: str, value_field: str) -> Optional[float]:
    """Helper to fetch a numeric field from a model instance."""
    try:
        obj = model.objects.only(value_field).get(**{lookup_field: lookup_value})
        return getattr(obj, value_field)
    except model.DoesNotExist:
        return None
    except Exception:
        return None


def _preprocess_if_syntax(expression: str) -> str:
    """
    Convert Excel-style IF(condition;true;false) to Python-compatible IF(condition,true,false).
    Keeps commas intact; only replaces semicolons inside IF(...) blocks.
    """
    if "IF(" not in expression and ";" not in expression:
        return expression
    # Simplest robust approach: all semicolons become commas
    return expression.replace(";", ",")

def _normalize_target_tokens(expression: str) -> str:
    """
    Normalize target/ziel tokens like LandUse_LU_2.1_ziel -> LandUse_LU_2.1.
    This keeps expressions consistent while allowing target values to be resolved.
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


def _auto_context_from_tokens(expression: str, use_target: bool) -> Dict[str, float]:
    """
    Build a context dict by resolving Verbrauch_/Renewable_/LandUse_ tokens found
    in the expression.
    """
    from simulator.models import LandUse, RenewableData, VerbrauchData
    context: Dict[str, float] = {}

    # 1. Verbrauch tokens - improved regex (greedy code capture)
    # Matches Verbrauch_ followed by digits/dots/underscores, then optional suffix
    pattern_v = r'[Vv]erbrauch_([0-9\._]+?)(?:_(status|ziel|target))?(?![a-zA-Z0-9\._])'
    for match in re.finditer(pattern_v, expression):
        token = match.group(0)
        code_raw = match.group(1).strip('_').strip('.')
        suffix = match.group(2)
        
        token_use_target = use_target
        if suffix in ['ziel', 'target']:
            token_use_target = True
        elif suffix == 'status':
            token_use_target = False
            
        # Try exact code first, then try with dots
        codes_to_try = [code_raw, code_raw.replace("_", ".")]
        
        value = 0
        for code in codes_to_try:
            try:
                obj = VerbrauchData.objects.only("status", "ziel").get(code=code)
                value = float((obj.ziel if token_use_target else obj.status) or 0)
                break
            except (VerbrauchData.DoesNotExist, ValueError):
                continue
        context[token] = value

    # 2. Renewable tokens
    pattern_r = r'[Rr]enewable_([0-9\._]+?)(?:_(status|target|value))?(?![a-zA-Z0-9\._])'
    for match in re.finditer(pattern_r, expression):
        token = match.group(0)
        code_raw = match.group(1).strip('_').strip('.')
        suffix = match.group(2)
        
        token_use_target = use_target
        if suffix == 'target':
            token_use_target = True
        elif suffix == 'status':
            token_use_target = False
            
        codes_to_try = [code_raw, code_raw.replace("_", ".")]
        value = 0
        for code in codes_to_try:
            try:
                obj = RenewableData.objects.only("status_value", "target_value").get(code=code)
                value = float((obj.target_value if token_use_target else obj.status_value) or 0)
                break
            except (RenewableData.DoesNotExist, ValueError):
                continue
        context[token] = value

    # 3. LandUse tokens
    pattern_lu = r'[Ll]andUse_([A-Za-z0-9\._]+?)(?:_(status|target))?(?![a-zA-Z0-9\._])'
    for match in re.finditer(pattern_lu, expression):
        token = match.group(0)
        code_raw = match.group(1).strip('_').strip('.')
        suffix = match.group(2)
        
        token_use_target = use_target
        if suffix == 'target':
            token_use_target = True
        elif suffix == 'status':
            token_use_target = False
            
        # LandUse codes can be complex (LU_2.1)
        codes_to_try = [code_raw, code_raw.replace("_", ".")]
        value = 0
        for code in codes_to_try:
            try:
                obj = LandUse.objects.only("status_ha", "target_ha").get(code=code)
                value = float((obj.target_ha if token_use_target else obj.status_ha) or 0)
                break
            except LandUse.DoesNotExist:
                continue
        context[token] = value

    # 4. Bare numeric codes (RenewableData fallback) like 9.4.3.3 or 9.4.3.3_target
    # Matches codes with dots, optional suffix, must NOT start with 0.
    pattern_bare = r'\b[1-9]\d*(?:\.\d+)+(?:_(?:target|ziel|status))?\b'
    for token in set(re.findall(pattern_bare, expression)):
        if token not in context:
            try:
                # Handle suffix
                base_code = token
                is_target = use_target
                if token.endswith('_target') or token.endswith('_ziel'):
                    base_code = token.rsplit('_', 1)[0]
                    is_target = True
                elif token.endswith('_status'):
                    base_code = token.rsplit('_', 1)[0]
                    is_target = False
                
                obj = RenewableData.objects.only("status_value", "target_value").get(code=base_code)
                context[token] = float((obj.target_value if is_target else obj.status_value) or 0)
            except RenewableData.DoesNotExist:
                context[token] = 0

    # 5. WS tokens (WS_366_column_name format) - reads WS row data
    # Enables formulas like: WS_366_einspeich, WS_366_abregelung_z
    pattern_ws = r'WS_(\d+)_(\w+)'
    for match in re.finditer(pattern_ws, expression):
        token = match.group(0)
        if token not in context:  # Don't overwrite if already set
            try:
                row_num = int(match.group(1))
                column_name = match.group(2)
                from simulator.ws_models import WSData
                ws_row = WSData.objects.filter(tag_im_jahr=row_num).first()
                if ws_row:
                    value = getattr(ws_row, column_name, 0) or 0
                    context[token] = float(value)
                else:
                    context[token] = 0
            except Exception as e:
                context[token] = 0

    # 6. WS Constants (ETA_STROM_GAS, ETA_GAS_STROM, etc.)
    # These are defined in Formula model with category='ws_constant'
    ws_constant_names = ['ETA_STROM_GAS', 'ETA_GAS_STROM', 'ABREGELUNG_THRESHOLD']
    for const_name in ws_constant_names:
        if const_name in expression and const_name not in context:
            try:
                from simulator.signals import get_ws_constants
                ws_consts = get_ws_constants()
                context[const_name] = ws_consts.get(const_name, 0)
            except Exception:
                # Default values if get_ws_constants fails
                defaults = {'ETA_STROM_GAS': 0.65, 'ETA_GAS_STROM': 0.585, 'ABREGELUNG_THRESHOLD': 200}
                context[const_name] = defaults.get(const_name, 0)

    return context


def _safe_eval(expression: str, names: Dict[str, float], use_target: bool = False, formula_key: str = "unknown") -> Optional[float]:
    """
    Evaluate a math expression safely using a controlled names dict.
    Supports +, -, *, /, parentheses, IF(), and basic helpers (max/min/abs/round).
    
    STABILITY: Automatically prefixes naked numeric tokens (e.g., 2_7_ziel -> Verbrauch_2_7_ziel)
    to avoid SyntaxErrors.
    """
    if not expression:
        return None

    # 1. Normalize IF syntax and trim whitespace
    expression = _preprocess_if_syntax(expression.strip())
    
    # 2. Auto-prefix naked tokens (e.g., 2_7_ziel -> Verbrauch_2_7_ziel)
    # This specifically targets tokens starting with a digit that contain underscores
    naked_pattern = r'\b([0-9]+(?:_[0-9]+)+(?:_ziel|_status|_target)?)\b'
    def prefix_token(match):
        t = match.group(1)
        if t in (names or {}): return t
        # If it's a pure number (no underscores), leave it alone
        if "_" not in t: return t
        return f"Verbrauch_{t}"
    expression = re.sub(naked_pattern, prefix_token, expression)

    # 3. Normalize target/ziel tokens to base tokens (e.g. LandUse_X_ziel -> LandUse_X)
    expression = _normalize_target_tokens(expression)

    # 4. Auto-resolve any missing tokens directly from the database
    auto_ctx = _auto_context_from_tokens(expression, use_target=use_target)
    
    scope = {"__builtins__": {}}
    scope.update({
        "max": max,
        "min": min,
        "abs": abs,
        "round": round,
        "IF": lambda cond, t, f: t if cond else f,
    })
    if names:
        scope.update(names)
    
    # Fill gaps from auto-resolution
    for k, v in auto_ctx.items():
        scope.setdefault(k, v)

    # 5. Aggressive Token replacement for anything that isn't a valid variable name
    # Python eval() doesn't like dots (or starting with digits) in variable names.
    # We sort by length descending to replace longer tokens (e.g. LU_2.1.1) before shorter ones (LU_2.1)
    for token, value in sorted(scope.items(), key=lambda kv: len(kv[0]), reverse=True):
        if isinstance(value, (int, float)):
            # Greedily replace tokens that are not valid Python variable names
            # (starts with digit OR contains dots)
            if re.match(r'^[0-9]', token) or "." in token:
                # Use regex sub with negative lookaround to avoid replacing substrings
                # (e.g., avoid replacing 9.1 inside 9.1.1, also 9.1.1 inside 9.1.1_target)
                pattern = r'(?<![0-9.])' + re.escape(token) + r'(?![0-9.])'
                expression = re.sub(pattern, str(value), expression)

    try:
        result = eval(expression, scope, {})
        return float(result)
    except ZeroDivisionError:
        return 0
    except Exception as e:
        # Check if we have unresolved tokens that cause syntax errors
        logger.error(f"❌ Safe eval failed for '{formula_key}': {e} | Expr: {expression}")
        return None


# =============================================================================
# ENHANCED FORMULA SERVICE - Database-First with Python Fallback
# =============================================================================

class FormulaService:
    """
    Centralized formula management service.
    Loads formulas from database with fallback to Python files.
    """
    
    CACHE_PREFIX = 'formula_'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, use_cache=True):
        """
        Initialize the formula service.
        
        Args:
            use_cache: Whether to use Django cache for formulas
        """
        self.use_cache = use_cache
    
    def get_formula(self, key: str, category: str = 'renewable') -> Optional[Dict]:
        """
        Get formula definition by key.
        
        100% DATABASE-DRIVEN - NO PYTHON FALLBACKS!
        
        Args:
            key: Formula key (e.g., '1.1.2.1.2')
            category: Formula category (renewable, verbrauch, landuse, etc.)
            
        Returns:
            Dictionary with formula details or None if not found
        """
        # Try cache first
        if self.use_cache:
            cached = cache.get(f'{self.CACHE_PREFIX}{key}')
            if cached is not None:
                return cached
        
        # Load from database ONLY - no fallbacks
        formula = self._get_from_database(key, category)
        if formula:
            if self.use_cache:
                cache.set(f'{self.CACHE_PREFIX}{key}', formula, self.CACHE_TIMEOUT)
            return formula
        
        # No formula found - return None (caller must handle)
        return None
    
    def _get_from_database(self, key: str, category: str) -> Optional[Dict]:
        """Load formula from database"""
        try:
            # NOTE: Removed connection.close()/connect() that was breaking transactions!
            # Using standard queryset - ORM caching is not an issue for Formula lookups.
            formula_obj = Formula.objects.filter(
                key=key,
                is_active=True
            ).first()
            
            if formula_obj:
                return {
                    'key': formula_obj.key,
                    'expression': formula_obj.expression,
                    'description': formula_obj.description,
                    'is_active': formula_obj.is_active,
                    'is_fixed': formula_obj.is_fixed,
                    'category': formula_obj.category,
                    'version': formula_obj.version,
                    'validation_status': formula_obj.validation_status,
                }
        except Exception as e:
            logger.warning(f"Error loading formula {key} from database: {e}")
        
        return None
    
    def get_all_formulas(self, category: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """
        Get all formulas from database ONLY.
        
        100% DATABASE-DRIVEN - NO PYTHON FILE FALLBACKS!
        
        Args:
            category: Filter by category (renewable, verbrauch, etc.)
            active_only: Only return active formulas
            
        Returns:
            List of formula dictionaries
        """
        formulas = []
        
        # Get from database ONLY - no Python file fallbacks
        try:
            queryset = Formula.objects.all()
            if active_only:
                queryset = queryset.filter(is_active=True)
            if category:
                queryset = queryset.filter(category=category)
            
            for formula_obj in queryset:
                formulas.append({
                    'key': formula_obj.key,
                    'expression': formula_obj.expression,
                    'description': formula_obj.description,
                    'is_active': formula_obj.is_active,
                    'is_fixed': formula_obj.is_fixed,
                    'category': formula_obj.category,
                    'version': formula_obj.version,
                    'validation_status': formula_obj.validation_status,
                })
        except Exception as e:
            logger.error(f"Error loading formulas from database: {e}")
            raise ValueError(f"Cannot load formulas from database. Please import formulas first. Error: {e}")
        
        return formulas
    
    def save_formula(self, key: str, expression: str, description: str = '', 
                    category: str = 'renewable', is_fixed: bool = False) -> bool:
        """
        Save or update a formula in the database.
        
        Args:
            key: Formula key
            expression: Formula expression
            description: Human-readable description
            category: Formula category
            is_fixed: Whether this is a fixed value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            formula, created = Formula.objects.update_or_create(
                key=key,
                defaults={
                    'expression': expression,
                    'description': description,
                    'category': category,
                    'is_fixed': is_fixed,
                    'is_active': True,
                    'validation_status': 'pending',
                }
            )
            
            if not created:
                formula.increment_version()
            
            # Invalidate cache
            if self.use_cache:
                cache.delete(f'{self.CACHE_PREFIX}{key}')
            
            logger.info(f"{'Created' if created else 'Updated'} formula {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving formula {key}: {e}")
            return False
    
    def clear_cache(self, key: Optional[str] = None):
        """
        Clear cached formulas.
        
        Args:
            key: Specific formula key to clear, or None to clear all
        """
        if self.use_cache:
            if key:
                # Clear specific formula
                cache.delete(f'{self.CACHE_PREFIX}{key}')
                logger.info(f"Formula cache cleared for {key}")
            else:
                # Clear all formulas
                try:
                    cache.delete_pattern(f'{self.CACHE_PREFIX}*')
                except:
                    # Fallback for cache backends that don't support delete_pattern
                    pass
                logger.info("All formula cache cleared")


# Global instance for easy access
_formula_service = None

def get_formula_service() -> FormulaService:
    """Get or create global FormulaService instance"""
    global _formula_service
    if _formula_service is None:
        _formula_service = FormulaService()
    return _formula_service


def evaluate_with_mappings(formula_key: str, category: str = 'renewable', status_lookup: Optional[Dict] = None, target_lookup: Optional[Dict] = None) -> tuple:
    """
    NEW: Evaluate formula using FormulaVariable mappings.
    This is the FULLY EXTENSIBLE approach.
    
    Returns:
        tuple: (status_value, target_value) or (None, None)
    """
    try:
        # NOTE: Removed connection.close()/connect() that was breaking transactions!
        # If fresh data is needed, callers should use refresh_from_db() on specific objects.
        formula = Formula.objects.prefetch_related('variables').get(
            key=formula_key,
            category=category,
            is_active=True
        )
    except Formula.DoesNotExist:
        return None, None
    
    # Determine if this is a target/ziel formula
    is_target_formula = (
        formula.formula_type == 'ziel'
        or formula_key.endswith('_ziel')
        or formula_key.endswith('_target')
    )
    
    # Build context - the source_type in FormulaVariable determines which field to read
    # For verbrauch_ziel variables, it will read the .ziel field
    # For verbrauch_status variables, it will read the .status field
    context = _build_context(formula, use_target=is_target_formula, status_lookup=status_lookup, target_lookup=target_lookup)  # use_target affects token auto-resolution
    
    # Evaluate the formula
    result = _safe_eval(formula.expression, context, use_target=is_target_formula, formula_key=formula_key)
    
    # Return based on formula type
    if is_target_formula:
        return (None, result)
    else:
        return (result, None)


def _resolve_variable(var, use_target: bool = False, status_lookup: Optional[Dict] = None, target_lookup: Optional[Dict] = None):
    """
    Resolve a FormulaVariable to its numeric value.
    PRIORITIZES IN-MEMORY LOOKUPS over database fetches.
    """
    source_key = var.source_key
    
    # Literal number
    if var.source_type == 'literal':
        try:
            return float(source_key)
        except (TypeError, ValueError):
            return var.default_value
            
    # CHECK LOOKUPS FIRST (Fast Path)
    if status_lookup is not None and target_lookup is not None:
        # RenewableData Code Lookup
        if var.source_type in ['renewable_code_status', 'renewable_code_target']:
            # status/target map directly to the lookups
            lookup = target_lookup if use_target else status_lookup
            if source_key in lookup:
                val = lookup[source_key]
                # Handle dictionary format from calc engine
                if isinstance(val, dict):
                    return val.get('target_value' if use_target else 'status_value', 0)
                return val
        
        # LandUse - check if present in lookup (usually it's ren/ver lookup, but landuse might be there)
        if var.source_type in ['landuse_status', 'landuse_target']:
            pass # LandUse lookups usually separate, but could be added here if passed

    # SLOW PATH - Database Fallback
    
    # LandUse
    if var.source_type == 'landuse_status':
        from simulator.models import LandUse
        return _get_value(LandUse, 'code', source_key, 'status_ha') or var.default_value
    if var.source_type == 'landuse_target':
        from simulator.models import LandUse
        return _get_value(LandUse, 'code', source_key, 'target_ha') or var.default_value
    
    # RenewableData
    if var.source_type == 'renewable_status':
        from simulator.models import RenewableData
        return _get_value(RenewableData, 'code', source_key, 'status_value') or var.default_value
    if var.source_type == 'renewable_target':
        from simulator.models import RenewableData
        return _get_value(RenewableData, 'code', source_key, 'target_value') or var.default_value
    
    # RenewableData CODE reference
    if var.source_type in ['renewable_code_status', 'renewable_code_target']:
        from simulator.models import RenewableData
        try:
            renewable = RenewableData.objects.get(code=source_key)
            if not renewable.is_fixed:
                status_calc, target_calc = renewable.get_calculated_values()
                return target_calc if use_target else status_calc
            else:
                return renewable.target_value if use_target else renewable.status_value
        except RenewableData.DoesNotExist:
            return var.default_value or 0
        except Exception as e:
            # logger.error(f"Error resolving renewable code {source_key}: {e}")
            return var.default_value or 0
    
    # VerbrauchData
    if var.source_type in ['verbrauch_status', 'verbrauch_ziel']:
        from simulator.models import VerbrauchData
        field = 'ziel' if var.source_type == 'verbrauch_ziel' else 'status'
        return _get_value(VerbrauchData, 'code', source_key, field) or var.default_value
    
    # VerbrauchData CODE reference
    if var.source_type in ['verbrauch_code_status', 'verbrauch_code_ziel']:
        from simulator.models import VerbrauchData
        try:
            verbrauch = VerbrauchData.objects.get(code=source_key)
            if verbrauch.is_calculated:
                status_calc, ziel_calc = verbrauch.get_calculated_values()
                return ziel_calc if use_target else status_calc
            else:
                return verbrauch.ziel if use_target else verbrauch.status
        except VerbrauchData.DoesNotExist:
            return var.default_value or 0
        except Exception as e:
            return var.default_value or 0
    
    # WS-specific source types
    if var.source_type == 'ws_row_value':
        # Current row's column value
        # source_key should be column name (e.g., "stromverbr")
        # This requires a row context to be passed - return default for now
        # The ws_formula_service handles this contextually
        return var.default_value or 0
    
    if var.source_type == 'ws_row_366':
        # Row 366 reference value
        # source_key should be column name (e.g., "windstrom")
        from simulator.ws_models import WSData
        try:
            ws_row = WSData.objects.filter(tag_im_jahr=366).only(source_key).first()
            if ws_row:
                value = getattr(ws_row, source_key, None)
                return float(value) if value is not None else (var.default_value or 0)
        except Exception:
            pass
        return var.default_value or 0
    
    if var.source_type == 'ws_sum':
        # Sum of column for days 1-365
        # source_key should be column name (e.g., "mangel_last")
        from simulator.ws_models import WSData
        from django.db.models import Sum
        try:
            result = WSData.objects.filter(
                tag_im_jahr__gte=1, 
                tag_im_jahr__lte=365
            ).aggregate(total=Sum(source_key))
            total = result.get('total')
            return float(total) if total is not None else (var.default_value or 0)
        except Exception:
            pass
        return var.default_value or 0
    
    if var.source_type == 'ws_day_prev':
        # Previous day's column value
        # This requires a row context to be passed - return default for now
        # The ws_formula_service handles this contextually
        return var.default_value or 0
    
    return var.default_value

def _get_value(model, lookup_field, lookup_value, value_field):
    """Helper to safely get a value from a model."""
    try:
        obj = model.objects.only(value_field).get(**{lookup_field: lookup_value})
        val = getattr(obj, value_field)
        return float(val) if val is not None else None
    except (model.DoesNotExist, ValueError, TypeError):
        return None
