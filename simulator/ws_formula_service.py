"""
WS Formula Service - 100% Database-Driven Formula Evaluation
============================================================

This service evaluates WS formulas stored in WSFormulaTemplate entries.
All formulas are editable via Django Admin - NO HARDCODING!

FORMULA SYNTAX SUPPORTED:
-------------------------
- row.column          → Current row's column value (e.g., row.verbrauch_promille)
- day_prev.column     → Previous day's column value (for days 2-365)
- day_N.column        → Specific day N's column value (e.g., day_1.stromverbr)
- column_366          → Row 366's column value (reference value)
- sums['sum_column']  → Sum of all daily values (1-365) for that column
- sums['min_column']  → Minimum of all daily values (1-365)
- sums['max_column']  → Maximum of all daily values (1-365)

MATHEMATICAL FUNCTIONS:
-----------------------
- MAX(a, b)           → Maximum of values
- MIN(a, b)           → Minimum of values
- ABS(x)              → Absolute value
- IF(cond; true; false) → Conditional (use semicolon separator)

EXAMPLE FORMULAS:
-----------------
- stromverbr: stromverbr_raumwaerm_korr_366 * row.verbrauch_promille / 1000
- windstrom: row.wind_promille * windstrom_366 / 1000
- wind_solar_konstant: row.windstrom + row.solarstrom + row.sonst_kraft_konstant
- direktverbr_strom: MIN(row.wind_solar_konstant, row.stromverbr_raumwaerm_korr)
"""

import re
import math
from typing import Dict, Optional, Any, List
from decimal import Decimal
from simulator.formula_service import _auto_context_from_tokens, _normalize_target_tokens, _preprocess_if_syntax


class WSFormulaEvaluator:
    """
    Evaluates WS formulas from database templates.
    100% dynamic - all formulas come from WSFormulaTemplate model.
    """
    
    def __init__(self):
        self.ws_data_cache = {}  # Cache for WS row data
        self.sums_cache = {}     # Cache for column sums
        self.row_366_cache = {}  # Cache for row 366 reference values
        self.numeric_fields_cache = None  # Cache for model field names
        self.renewable_914_target = 0     # Cache for specific renewable value
        self._ws_ref_cache = {}           # Cache for WS_REF_* formula values
        
    def clear_cache(self):
        """Clear all caches - call before recalculating"""
        self.ws_data_cache = {}
        self.sums_cache = {}
        self.row_366_cache = {}
        self._ws_ref_cache = {}
    
    def calculate_row_366_from_renewable(self, preserve_stromverbr=False):
        """
        Calculate Row 366 reference values from RenewableData.
        This is called BEFORE formula evaluation to ensure Row 366 has correct values.
        
        Reference percentage = (9.1.1 + 9.1.2 + 9.1.3 - 9.2.1.5.2.1) / (9.1.1 + 9.1.2 + 9.1.3)
        windstrom_366 = 9.1.1 × reference_percentage
        solarstrom_366 = 9.1.2 × reference_percentage  
        sonst_kraft_konstant_366 = 9.1.3 × reference_percentage
        
        NOTE: stromverbr_raumwaerm_korr now DEFAULTS to 1105556.0 unless preserve_stromverbr is True.
              This value is only modified by the 'Balance WS Storage' mechanism.
        """
        from simulator.models import RenewableData, VerbrauchData
        from simulator.ws_models import WSData
        
        print("📊 Calculating Row 366 from Renewable data...")
        
        # Get renewable values
        r_911 = RenewableData.objects.filter(code='9.1.1').first()
        r_912 = RenewableData.objects.filter(code='9.1.2').first()
        r_913 = RenewableData.objects.filter(code='9.1.3').first()
        r_921521 = RenewableData.objects.filter(code='9.2.1.5.2.1').first()
        
        v_911 = r_911.target_value if r_911 and r_911.target_value else 0
        v_912 = r_912.target_value if r_912 and r_912.target_value else 0
        v_913 = r_913.target_value if r_913 and r_913.target_value else 0
        v_921521 = r_921521.target_value if r_921521 and r_921521.target_value else 0
        
        # Calculate reference percentage
        total_addition = v_911 + v_912 + v_913
        if total_addition > 0:
            difference = total_addition - v_921521
            reference_percentage = difference / total_addition
        else:
            reference_percentage = 0
        
        print(f"   Reference: ({total_addition:,.0f} - {v_921521:,.0f}) / {total_addition:,.0f} = {reference_percentage:.4f} ({reference_percentage*100:.2f}%)")
        
        # Calculate Row 366 values
        windstrom_366 = v_911 * reference_percentage
        solarstrom_366 = v_912 * reference_percentage
        sonst_kraft_366 = v_913 * reference_percentage
        
        # Get davon_raumw_korr_366 from Verbrauch
        v_292 = VerbrauchData.objects.filter(code='2.9.2').first()
        v_24 = VerbrauchData.objects.filter(code='2.4').first()
        davon_366 = (v_292.ziel or 0) * ((v_24.ziel or 0) / 100) if v_292 and v_24 else 0
        
        # Update Row 366 in database
        try:
            row_366 = WSData.objects.get(tag_im_jahr=366)
            row_366.windstrom = windstrom_366
            row_366.solarstrom = solarstrom_366
            row_366.sonst_kraft_konstant = sonst_kraft_366
            row_366.davon_raumw_korr = davon_366
            
            # stromverbr_raumwaerm_korr logic:
            # If not preserving, reset to baseline 1105556.0
            # If preserving, keep existing value (e.g. from balance process)
            DEFAULT_STROMVERBR_RAUMWAERM_KORR = 1105556.0
            if not preserve_stromverbr:
                row_366.stromverbr_raumwaerm_korr = DEFAULT_STROMVERBR_RAUMWAERM_KORR
                print(f"   stromverbr_raumwaerm_korr_366 = {DEFAULT_STROMVERBR_RAUMWAERM_KORR:,.2f} (reset to default)")
            else:
                print(f"   stromverbr_raumwaerm_korr_366 = {row_366.stromverbr_raumwaerm_korr or 0:,.2f} (preserved)")
            
            row_366.save()
            
            print(f"   windstrom_366 = {windstrom_366:,.2f}")
            print(f"   solarstrom_366 = {solarstrom_366:,.2f}")
            print(f"   sonst_kraft_konstant_366 = {sonst_kraft_366:,.2f}")
            print(f"   davon_raumw_korr_366 = {davon_366:,.2f}")
            print(f"   ✅ Row 366 updated from Renewable data")
        except WSData.DoesNotExist:
            print(f"   ❌ Row 366 not found!")
    
    def load_ws_data(self):
        """Load all WS data into cache for fast formula evaluation"""
        from simulator.ws_models import WSData
        
        self.ws_data_cache = {}
        for row in WSData.objects.all():
            self.ws_data_cache[row.tag_im_jahr] = row
            
        # Cache row 366 values separately with _366 suffix keys
        if 366 in self.ws_data_cache:
            row_366 = self.ws_data_cache[366]
            for field in self._get_numeric_fields():
                value = getattr(row_366, field, None) or 0
                self.row_366_cache[f"{field}_366"] = value
    
    def calculate_sums(self):
        """Calculate sums, mins, and maxes of all columns for days 1-365"""
        self.sums_cache = {}
        
        if not self.ws_data_cache:
            self.load_ws_data()
        
        for field in self._get_numeric_fields():
            total = 0
            values = []
            for day in range(1, 366):
                if day in self.ws_data_cache:
                    value = getattr(self.ws_data_cache[day], field, None) or 0
                    total += value
                    values.append(value)
            
            self.sums_cache[f"sum_{field}"] = total
            self.sums_cache[f"min_{field}"] = min(values) if values else 0
            self.sums_cache[f"max_{field}"] = max(values) if values else 0
    
    def _get_numeric_fields(self) -> List[str]:
        """Get list of all numeric field names from WSData model (with caching)"""
        if self.numeric_fields_cache is not None:
            return self.numeric_fields_cache
            
        from simulator.ws_models import WSData
        from django.db import models as django_models
        
        numeric_fields = []
        for field in WSData._meta.fields:
            if isinstance(field, (django_models.FloatField, django_models.IntegerField, django_models.DecimalField)):
                if field.name not in ['id', 'tag_im_jahr']:
                    numeric_fields.append(field.name)
        
        self.numeric_fields_cache = numeric_fields
        return numeric_fields
    
    def evaluate_formula(self, formula: str, tag_im_jahr: int, column_name: str) -> Optional[float]:
        """
        Evaluate a formula expression for a specific row.
        
        Args:
            formula: Formula expression from WSFormulaTemplate
            tag_im_jahr: Day number (1-368)
            column_name: Column being calculated (for context)
            
        Returns:
            Calculated value, or None if evaluation fails
        """
        if not formula or not formula.strip():
            return None
        
        try:
            # Build evaluation context
            context = self._build_context(tag_im_jahr)
            
            # Transform formula to Python syntax
            python_formula = self._transform_formula(formula, tag_im_jahr)
            
            # Safe evaluation
            result = self._safe_eval(python_formula, context)
            
            return float(result) if result is not None else None
            
        except Exception as e:
            print(f"❌ Formula error for {column_name} day {tag_im_jahr}: {e}")
            print(f"   Formula: {formula}")
            return None
    
    def _build_context(self, tag_im_jahr: int) -> Dict[str, Any]:
        """Build evaluation context with all available variables"""
        from simulator.models import RenewableData, Formula
        from simulator.formula_service import _safe_eval, _auto_context_from_tokens
        
        context = {}
        
        # Add row 366 reference values (e.g., stromverbr_raumwaerm_korr_366)
        context.update(self.row_366_cache)
        
        # Add sums (e.g., sums['sum_stromverbr'])
        context['sums'] = self.sums_cache
        
        # ALSO add sums with _366 suffix for direct access in formulas
        # This allows formulas to use either sums['sum_mangel_last'] OR sum_mangel_last_366
        for key, value in self.sums_cache.items():
            context[f"{key}_366"] = value
        
        # Add renewable references (CACHED)
        context['renewable_914_target'] = self.renewable_914_target
        
        # Add WS_REF_* values from Formula model (for formulas like WS_REF_BIO)
        # These are pre-computed reference values needed for daily calculations
        if not hasattr(self, '_ws_ref_cache') or not self._ws_ref_cache:
            self._ws_ref_cache = {}
            ws_ref_formulas = list(Formula.objects.filter(key__startswith='WS_REF_', category='ws', is_active=True))
            
            # Run multiple passes to handle dependencies between WS_REF formulas
            max_passes = 5
            for pass_num in range(max_passes):
                resolved_any = False
                for formula in ws_ref_formulas:
                    if formula.key in self._ws_ref_cache:
                        continue  # Already computed
                    try:
                        # Build context for evaluating this formula
                        ref_context = _auto_context_from_tokens(formula.expression, use_target=True)
                        # Add already computed WS_REF values
                        ref_context.update(self._ws_ref_cache)
                        ref_context['max'] = max
                        ref_context['min'] = min
                        value = _safe_eval(formula.expression, ref_context, use_target=True)
                        if value is not None:
                            self._ws_ref_cache[formula.key] = float(value)
                            resolved_any = True
                    except Exception:
                        # Skip - will try again in next pass
                        pass
                if not resolved_any:
                    break  # No progress made, stop
        context.update(self._ws_ref_cache)
        
        # Add current row values as 'row' object
        if tag_im_jahr in self.ws_data_cache:
            current_row = self.ws_data_cache[tag_im_jahr]
            row_dict = self._row_to_dict(current_row)
            context['row'] = row_dict
            
            # ALSO add WS_* uppercase versions of current row values
            # This allows formulas to use WS_MANGEL_LAST instead of row.mangel_last
            for field, value in row_dict.items():
                ws_key = f"WS_{field.upper()}"
                context[ws_key] = value
        else:
            context['row'] = {}
        
        # Add previous day values as 'day_prev' object
        if tag_im_jahr > 1 and (tag_im_jahr - 1) in self.ws_data_cache:
            prev_row = self.ws_data_cache[tag_im_jahr - 1]
            prev_row_dict = self._row_to_dict(prev_row)
            context['day_prev'] = prev_row_dict
        else:
            context['day_prev'] = {}
            prev_row_dict = {}
        
        # Add specific day references (day_1, day_365, etc.)
        for day in [1, 365, 366, 367, 368, 369]:
            if day in self.ws_data_cache:
                day_row = self.ws_data_cache[day]
                context[f'day_{day}'] = self._row_to_dict(day_row)
                
                # CRITICAL: Also add WS_*_DAY scalar variables for formulas like
                # WS_LADEZUSTAND_NETTO - WS_LADEZUSTAND_NETTO_367
                for field in self._get_numeric_fields():
                    value = getattr(day_row, field, None)
                    if value is not None:
                        context[f'WS_{field.upper()}_{day}'] = float(value)
            else:
                context[f'day_{day}'] = {}
        
        # Add math functions
        context['MAX'] = max
        context['MIN'] = min
        context['ABS'] = abs
        context['ROUND'] = round
        context['max'] = max
        context['min'] = min
        context['abs'] = abs
        
        return context
    
    def _resolve_formula_variables(self, formula, tag_im_jahr: int, context: Dict) -> Dict[str, float]:
        """
        Resolve FormulaVariables for a WS formula, adding them to context.
        
        This allows WS formulas to use FormulaVariables like other pages.
        WS-specific source types (ws_row_value, ws_day_prev) are resolved
        contextually based on the current row.
        """
        from simulator.models import FormulaVariable
        from simulator.formula_service import _resolve_variable
        
        result = {}
        
        for var in formula.variables.all():
            source_key = var.source_key
            
            # Handle WS-specific source types that need row context
            if var.source_type == 'ws_row_value':
                # Current row's column value
                if 'row' in context and source_key in context['row']:
                    result[var.variable_name] = context['row'][source_key]
                else:
                    result[var.variable_name] = var.default_value or 0
                    
            elif var.source_type == 'ws_day_prev':
                # Previous day's column value
                if 'day_prev' in context and source_key in context['day_prev']:
                    result[var.variable_name] = context['day_prev'][source_key]
                else:
                    result[var.variable_name] = var.default_value or 0
                    
            elif var.source_type == 'ws_row_366':
                # Row 366 reference value
                if f'{source_key}_366' in self.row_366_cache:
                    result[var.variable_name] = self.row_366_cache[f'{source_key}_366']
                elif 366 in self.ws_data_cache:
                    value = getattr(self.ws_data_cache[366], source_key, None)
                    result[var.variable_name] = float(value) if value is not None else (var.default_value or 0)
                else:
                    result[var.variable_name] = var.default_value or 0
                    
            elif var.source_type == 'ws_sum':
                # Sum of column for days 1-365
                sum_key = f'sum_{source_key}'
                if sum_key in self.sums_cache:
                    result[var.variable_name] = self.sums_cache[sum_key]
                else:
                    result[var.variable_name] = var.default_value or 0
                    
            else:
                # Use standard formula_service resolution for other source types
                # This handles LandUse, Renewable, Verbrauch, etc.
                resolved = _resolve_variable(var, use_target=False)
                result[var.variable_name] = resolved if resolved is not None else (var.default_value or 0)
        
        return result
    
    def _row_to_dict(self, row) -> Dict[str, float]:
        """Convert WSData row to dictionary of field values"""
        result = {}
        for field in self._get_numeric_fields():
            value = getattr(row, field, None)
            result[field] = float(value) if value is not None else 0.0
        return result
    
    def _transform_formula(self, formula: str, tag_im_jahr: int) -> str:
        """
        Transform formula syntax to Python-compatible syntax.
        
        Transforms:
        - row.column -> row['column']
        - day_prev.column -> day_prev['column']
        - day_N.column -> day_N['column']
        - IF(cond; true; false) -> (true if cond else false)
        """
        result = formula
        
        # IMPORTANT: Transform IF statements FIRST (before row/day transforms)
        # because nested IFs need consistent semicolon parsing
        result = self._transform_if_statements(result)
        
        # Transform row.column to row['column']
        result = re.sub(r'row\.(\w+)', r"row['\1']", result)
        
        # Transform day_prev.column to day_prev['column']
        result = re.sub(r'day_prev\.(\w+)', r"day_prev['\1']", result)
        
        # Transform day_N.column to day_N['column']
        result = re.sub(r'day_(\d+)\.(\w+)', r"day_\1['\2']", result)
        
        return result
    
    def _transform_if_statements(self, formula: str) -> str:
        """
        Transform IF(cond; true_val; false_val) to Python ternary.
        Handles nested IF statements correctly using bracket matching.
        NOTE: Only matches uppercase IF( to avoid matching Python's 'if' keyword
        """
        result = formula
        
        # Find IF( pattern - CASE SENSITIVE (only uppercase IF, not Python's 'if')
        if_pattern = re.compile(r'IF\s*\(')
        
        while True:
            match = if_pattern.search(result)
            if not match:
                break
            
            start_pos = match.start()
            paren_start = match.end() - 1  # Position of opening '('
            
            # Find matching closing parenthesis
            paren_count = 1
            pos = paren_start + 1
            while pos < len(result) and paren_count > 0:
                if result[pos] == '(':
                    paren_count += 1
                elif result[pos] == ')':
                    paren_count -= 1
                pos += 1
            
            if paren_count != 0:
                # Unbalanced parentheses - leave as is
                break
            
            paren_end = pos - 1  # Position of closing ')'
            
            # Extract content between parentheses
            content = result[paren_start + 1:paren_end]
            
            # Split by semicolons (but not within nested parentheses)
            parts = self._split_by_semicolon(content)
            
            if len(parts) == 3:
                condition = parts[0].strip()
                true_val = parts[1].strip()
                false_val = parts[2].strip()
                
                # Convert to Python ternary: (true_val if condition else false_val)
                python_ternary = f"(({true_val}) if ({condition}) else ({false_val}))"
                
                # Replace IF(...) with the Python ternary
                result = result[:start_pos] + python_ternary + result[paren_end + 1:]
            else:
                # Invalid IF syntax - break to avoid infinite loop
                print(f"   Warning: Invalid IF syntax, expected 3 parts got {len(parts)}: {content[:50]}...")
                break
        
        return result
    
    def _split_by_semicolon(self, text: str) -> list:
        """
        Split text by semicolons, but respect parentheses.
        Example: "a > 0; IF(b; c; d); e" -> ["a > 0", "IF(b; c; d)", "e"]
        """
        parts = []
        current = ""
        paren_count = 0
        
        for char in text:
            if char == '(':
                paren_count += 1
                current += char
            elif char == ')':
                paren_count -= 1
                current += char
            elif char == ';' and paren_count == 0:
                parts.append(current)
                current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts

    
    def _safe_eval(self, expression: str, context: Dict) -> Optional[float]:
        """
        Safely evaluate a mathematical expression.
        Only allows safe operations - no exec, import, etc.
        """
        # Allowed names (safe math operations)
        allowed_names = {
            'MAX', 'MIN', 'ABS', 'ROUND',
            'max', 'min', 'abs', 'round',
            'True', 'False', 'None',
            'row', 'day_prev', 'day_1', 'day_365', 'day_366', 'day_367',
            'sums',
        }
        
        # Add all _366 reference keys
        for key in self.row_366_cache.keys():
            allowed_names.add(key)
        
        # 1. Normalize formula and check for token resolution
        # This handles cases like: Verbrauch_X.Y.Z, Renewable_X.Y.Z, etc.
        # It also handles target/ziel variants.
        expression = _preprocess_if_syntax(expression.strip())
        expression = _normalize_target_tokens(expression)
        
        # 2. Add tokens from database if they are not in the context
        # This is where Renewable_9.1.1 etc get their values
        auto_ctx = _auto_context_from_tokens(expression, use_target=False)
        context.update(auto_ctx)
        
        # 3. Aggressive Token replacement for anything that isn't a valid variable name
        # Python eval() doesn't like dots (or starting with digits) in variable names.
        # e.g., Renewable_9.1.1 -> 123.45
        for token, value in sorted(context.items(), key=lambda kv: len(kv[0]) if isinstance(kv[0], str) else 0, reverse=True):
            if isinstance(value, (int, float, Decimal)):
                # Replace tokens that start with digit OR contain dots
                if isinstance(token, str) and (re.match(r'^[0-9]', token) or "." in token):
                    # Use regex sub with negative lookaround to avoid replacing substrings
                    # (e.g., avoid replacing 9.1 inside 9.1.1, also 9.1.1 inside 9.1.1_target)
                    pattern = r'(?<![0-9.])' + re.escape(token) + r'(?![0-9.])'
                    expression = re.sub(pattern, str(value), expression)
        
        try:
            # Simple safety check - no dangerous keywords
            dangerous = ['import', 'exec', 'eval', 'compile', '__', 'open', 'file']
            expr_lower = expression.lower()
            for word in dangerous:
                if word in expr_lower:
                    raise ValueError(f"Dangerous keyword '{word}' not allowed")
            
            # Evaluate
            result = eval(expression, {"__builtins__": {}}, context)
            return result
            
        except Exception as e:
            # print(f"   Eval error: {e} | Expression: {expression}") # Reduced logging
            if "division by zero" in str(e) or "syntax" in str(e) or "literal" in str(e):
                 print(f"   ❌ Eval error: {e}")
                 print(f"      Expr: {expression}")
            return None
    
    def recalculate_all(self, progress_callback=None, num_passes=3, preserve_stromverbr=False) -> Dict[str, int]:
        """
        Recalculate ALL WS data using formulas from Formula model (category='ws') 
        or WSFormulaTemplate as fallback.
        
        This is the main entry point for recalculation.
        
        HYBRID APPROACH (Option A):
        1. First, check for formulas in the Formula model with category='ws'
        2. If found, use those (unified with other pages like Verbrauch/Renewable)
        3. Fall back to WSFormulaTemplate for backward compatibility
        
        IMPORTANT: Runs multiple passes to handle interdependent formulas.
        Some formulas depend on other columns that may not have been calculated
        yet in the current pass. Running multiple passes ensures convergence.
        
        Args:
            progress_callback: Optional function to call with progress updates
            num_passes: Number of passes to run (default 3 for convergence)
            preserve_stromverbr: If True, keep current stromverbr_raumwaerm_korr value (for balance process)
            
        Returns:
            Dict with statistics: {'updated': N, 'errors': N, 'skipped': N}
        """
        from simulator.ws_models import WSData
        from simulator.models import Formula
        
        stats = {'updated': 0, 'errors': 0, 'skipped': 0}
        
        # FIRST: Calculate Row 366 values from Renewable/Verbrauch data
        # This ensures Row 366 reference values are up-to-date before formulas run
        self.calculate_row_366_from_renewable(preserve_stromverbr=preserve_stromverbr)
        
        # CACHE Renewable Data for the entire run to avoid DB queries in row loop
        from simulator.models import RenewableData
        r_914 = RenewableData.objects.filter(code='9.1.4').first()
        self.renewable_914_target = r_914.target_value if r_914 and r_914.target_value else 0
        
        # Clear and reload caches (now includes updated Row 366)
        self.clear_cache()
        self.load_ws_data()
        self.calculate_sums()
        
        # Load formulas from unified Formula model (NO FALLBACK)
        formula_templates = self._load_formulas_from_formula_model()
        
        if not formula_templates:
            print("⚠️ No WS formulas found in Formula model (category='ws')!")
            print("   Run 'python manage.py migrate_ws_templates' to migrate from WSFormulaTemplate")
            return stats
        
        print(f"📋 Using unified Formula model: found {len(formula_templates)} WS column formulas")
        print(f"🔄 Running {num_passes} passes for formula convergence...")
        
        # Recalculation using unified Formula model
        return self._recalculate_with_formula_model(formula_templates, num_passes, stats)
    
    def _load_formulas_from_formula_model(self) -> Dict[str, Dict[str, Any]]:
        """
        Load WS formulas from the unified Formula model (category='ws').
        
        Returns a dictionary mapping column_name to a dict of row_type -> {expression, formula}.
        Example: {'stromverbr': {'day_1': {'expression': 'expr1', 'formula': Formula}, ...}}
        
        The key naming convention in the Formula model is:
        - WS_stromverbr (ws_row_type='all' or 'days_2_365')
        - WS_stromverbr_day_1 (ws_row_type='day_1')
        - WS_stromverbr_366 (ws_row_type='row_366')
        
        Or just use ws_row_type field to determine which rows the formula applies to.
        """
        from simulator.models import Formula
        
        # Prefetch variables for FormulaVariable resolution
        formulas = Formula.objects.filter(
            category='ws', 
            is_active=True
        ).prefetch_related('variables').order_by('key')
        
        result = {}
        
        for formula in formulas:
            # Parse the key to extract column name
            # Key format: WS_columnname or WS_columnname_rowtype
            key = formula.key
            if not key.startswith('WS_'):
                continue
                
            key_part = key[3:]  # Remove 'WS_' prefix
            
            # Determine column name and row type
            # If ws_row_type is explicitly set, use it
            ws_row_type = formula.ws_row_type or 'all'
            
            # Handle key formats like WS_stromverbr_day_1, WS_stromverbr_days_2_365, WS_stromverbr_row_366
            column_name = key_part.lower()
            if column_name.endswith('_day_1'):
                column_name = column_name[:-6]
                ws_row_type = 'day_1'
            elif column_name.endswith('_days_2_365'):
                column_name = column_name[:-11]
                ws_row_type = 'days_2_365'
            elif column_name.endswith('_row_366'):
                column_name = column_name[:-8]
                ws_row_type = 'row_366'
            elif column_name.endswith('_row_367'):
                column_name = column_name[:-8]
                ws_row_type = 'row_367'
            elif column_name.endswith('_row_368'):
                column_name = column_name[:-8]
                ws_row_type = 'row_368'
            # Legacy formats (for backward compatibility)
            elif column_name.endswith('_366'):
                column_name = column_name[:-4]
                ws_row_type = 'row_366'
            elif column_name.endswith('_367'):
                column_name = column_name[:-4]
                ws_row_type = 'row_367'
            elif column_name.endswith('_368'):
                column_name = column_name[:-4]
                ws_row_type = 'row_368'
            
            # Initialize column entry if not exists
            if column_name not in result:
                result[column_name] = {}
            
            # Store formula expression AND formula object for this row type
            result[column_name][ws_row_type] = {
                'expression': formula.expression,
                'formula': formula,  # Store for FormulaVariable access
            }
        
        return result
    
    def _recalculate_with_formula_model(self, formula_templates: Dict[str, Dict[str, Any]], 
                                         num_passes: int, stats: Dict[str, int]) -> Dict[str, int]:
        """
        Recalculate WS data using formulas from the unified Formula model.
        
        Now supports FormulaVariables for each formula, allowing WS formulas
        to reference other data sources (LandUse, Renewable, Verbrauch, etc.)
        just like formulas on other pages.
        
        Args:
            formula_templates: Dict of column_name -> {row_type: {expression, formula}}
            num_passes: Number of passes for convergence
            stats: Statistics dictionary to update
        
        Returns:
            Updated stats dictionary
        """
        from simulator.ws_models import WSData
        
        # Run multiple passes to handle interdependent formulas
        for pass_num in range(1, num_passes + 1):
            print(f"\n{'='*50}")
            print(f"📌 PASS {pass_num} of {num_passes}")
            print(f"{'='*50}")
            
            pass_updated = 0
            
            # Process each column's formulas
            for column_name, row_formulas in formula_templates.items():
                print(f"   🔧 {column_name}")
                
                rows_updated = 0
                
                # Get formula data for different row types
                day1_data = row_formulas.get('day_1')
                days_data = row_formulas.get('days_2_365') or row_formulas.get('all')
                row_366_data = row_formulas.get('row_366')
                row_367_data = row_formulas.get('row_367')
                row_368_data = row_formulas.get('row_368')
                
                # Extract expressions (handle both old string format and new dict format)
                f_day1_expr = day1_data.get('expression') if isinstance(day1_data, dict) else day1_data
                f_days_expr = days_data.get('expression') if isinstance(days_data, dict) else days_data
                f_366_expr = row_366_data.get('expression') if isinstance(row_366_data, dict) else row_366_data
                f_367_expr = row_367_data.get('expression') if isinstance(row_367_data, dict) else row_367_data
                f_368_expr = row_368_data.get('expression') if isinstance(row_368_data, dict) else row_368_data
                
                # Extract Formula objects for FormulaVariable resolution
                day1_formula = day1_data.get('formula') if isinstance(day1_data, dict) else None
                days_formula = days_data.get('formula') if isinstance(days_data, dict) else None
                row_366_formula = row_366_data.get('formula') if isinstance(row_366_data, dict) else None
                row_367_formula = row_367_data.get('formula') if isinstance(row_367_data, dict) else None
                row_368_formula = row_368_data.get('formula') if isinstance(row_368_data, dict) else None
                
                # Transform formulas ONCE per column
                f_day1 = self._transform_formula(f_day1_expr, 1) if f_day1_expr else None
                f_days = self._transform_formula(f_days_expr, 2) if f_days_expr else None
                f_366 = self._transform_formula(f_366_expr, 366) if f_366_expr else None
                f_367 = self._transform_formula(f_367_expr, 367) if f_367_expr else None
                f_368 = self._transform_formula(f_368_expr, 368) if f_368_expr else None
                
                # Day 1
                if f_day1:
                    context = self._build_context(1)
                    if day1_formula and day1_formula.variables.exists():
                        context.update(self._resolve_formula_variables(day1_formula, 1, context))
                    result = self._safe_eval(f_day1, context)
                    if result is not None:
                        self._update_row(1, column_name, result)
                        rows_updated += 1
                elif f_days:
                    # If no separate day_1 formula, use the general pattern
                    context = self._build_context(1)
                    if days_formula and days_formula.variables.exists():
                        context.update(self._resolve_formula_variables(days_formula, 1, context))
                    result = self._safe_eval(f_days, context)
                    if result is not None:
                        self._update_row(1, column_name, result)
                        rows_updated += 1
                
                # Days 2-365
                if f_days:
                    for day in range(2, 366):
                        context = self._build_context(day)
                        if days_formula and days_formula.variables.exists():
                            context.update(self._resolve_formula_variables(days_formula, day, context))
                        result = self._safe_eval(f_days, context)
                        if result is not None:
                            self._update_row(day, column_name, result)
                            rows_updated += 1
                        else:
                            stats['errors'] += 1
                
                # Row 366
                if f_366:
                    # Recalculate sums before processing row 366 because it often uses sums
                    self.calculate_sums()
                    context = self._build_context(366)
                    if row_366_formula and row_366_formula.variables.exists():
                        context.update(self._resolve_formula_variables(row_366_formula, 366, context))
                    result = self._safe_eval(f_366, context)
                    if result is not None:
                        self._update_row(366, column_name, result)
                        rows_updated += 1
                
                # Row 367
                if f_367:
                    context = self._build_context(367)
                    if row_367_formula and row_367_formula.variables.exists():
                        context.update(self._resolve_formula_variables(row_367_formula, 367, context))
                    result = self._safe_eval(f_367, context)
                    if result is not None:
                        self._update_row(367, column_name, result)
                        rows_updated += 1
                
                # Row 368
                if f_368:
                    context = self._build_context(368)
                    if row_368_formula and row_368_formula.variables.exists():
                        context.update(self._resolve_formula_variables(row_368_formula, 368, context))
                    result = self._safe_eval(f_368, context)
                    if result is not None:
                        self._update_row(368, column_name, result)
                        rows_updated += 1
                
                pass_updated += rows_updated
                print(f"   ✅ Updated {rows_updated} rows")
            
            stats['updated'] += pass_updated
            print(f"\n📊 Pass {pass_num} completed: {pass_updated} row-column updates")
            
            # Recalculate sums after each pass for the next pass
            self.calculate_sums()
        
        # Save all changes to database using bulk_update for efficiency
        self._save_changes_to_database(stats, num_passes)
        
        return stats
    
    def _recalculate_with_legacy_templates(self, templates, num_passes: int, stats: Dict[str, int]) -> Dict[str, int]:
        """
        Legacy recalculation using WSFormulaTemplate model.
        This is the fallback when no Formula model entries exist.
        
        Args:
            templates: QuerySet of WSFormulaTemplate entries
            num_passes: Number of passes for convergence
            stats: Statistics dictionary to update
        
        Returns:
            Updated stats dictionary
        """
        from simulator.ws_models import WSData
        
        # Run multiple passes to handle interdependent formulas
        for pass_num in range(1, num_passes + 1):
            print(f"\n{'='*50}")
            print(f"📌 PASS {pass_num} of {num_passes}")
            print(f"{'='*50}")
            
            pass_updated = 0
            
            # Process each template
            for template in templates:
                column_name = template.column_name.lower()
                print(f"   🔧 {template.display_name} ({column_name})")
                
                # Transform formulas ONCE per template
                f_day1 = self._transform_formula(template.formula_day_1, 1) if template.formula_day_1 else None
                f_days = self._transform_formula(template.formula_days_2_365, 2) if template.formula_days_2_365 else None
                f_366 = self._transform_formula(template.formula_row_366, 366) if template.formula_row_366 else None
                f_367 = self._transform_formula(template.formula_row_367, 367) if template.formula_row_367 else None
                f_368 = self._transform_formula(template.formula_row_368, 368) if template.formula_row_368 else None
                
                rows_updated = 0
                
                # Day 1
                if f_day1:
                    result = self._safe_eval(f_day1, self._build_context(1))
                    if result is not None:
                        self._update_row(1, column_name, result)
                        rows_updated += 1
                
                # Days 2-365
                if f_days:
                    for day in range(2, 366):
                        result = self._safe_eval(f_days, self._build_context(day))
                        if result is not None:
                            self._update_row(day, column_name, result)
                            rows_updated += 1
                        else:
                            stats['errors'] += 1
                
                # Row 366
                if f_366:
                    # Recalculate sums before processing row 366 because it often uses sums
                    self.calculate_sums()
                    result = self._safe_eval(f_366, self._build_context(366))
                    if result is not None:
                        self._update_row(366, column_name, result)
                        rows_updated += 1
                
                # Row 367
                if f_367:
                    result = self._safe_eval(f_367, self._build_context(367))
                    if result is not None:
                        self._update_row(367, column_name, result)
                        rows_updated += 1
                
                # Row 368
                if f_368:
                    result = self._safe_eval(f_368, self._build_context(368))
                    if result is not None:
                        self._update_row(368, column_name, result)
                        rows_updated += 1

                # Custom rows (369, 370...)
                for row_num, formula in template.custom_row_formulas.items():
                    try:
                        day_num = int(row_num)
                        f_custom = self._transform_formula(formula, day_num)
                        result = self._safe_eval(f_custom, self._build_context(day_num))
                        if result is not None:
                            self._update_row(day_num, column_name, result)
                            rows_updated += 1
                    except:
                        continue
                
                pass_updated += rows_updated
                print(f"   ✅ Updated {rows_updated} rows")
            
            stats['updated'] += pass_updated
            print(f"\n📊 Pass {pass_num} completed: {pass_updated} row-column updates")
            
            # Recalculate sums after each pass for the next pass
            self.calculate_sums()
        
        # Save all changes to database using bulk_update for efficiency
        self._save_changes_to_database(stats, num_passes)
        
        return stats
    
    def _save_changes_to_database(self, stats: Dict[str, int], num_passes: int):
        """Save all cached WS data changes to the database using bulk update."""
        from simulator.ws_models import WSData
        
        print("\n💾 Saving all changes to database (bulk update)...")
        if self.ws_data_cache:
            rows = list(self.ws_data_cache.values())
            # Get all fields except 'id' and 'tag_im_jahr'
            fields_to_update = self._get_numeric_fields()
            
            # Perform bulk update in batches
            batch_size = 100
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                WSData.objects.bulk_update(batch, fields_to_update)
        
        print(f"\n✅ Recalculation complete ({num_passes} passes)!")
        print(f"   Updated: {stats['updated']} | Errors: {stats['errors']} | Skipped: {stats['skipped']}")
    
    def _update_row(self, tag_im_jahr: int, column_name: str, value: float):
        """Update a row's column value in cache"""
        if tag_im_jahr in self.ws_data_cache:
            row = self.ws_data_cache[tag_im_jahr]
            setattr(row, column_name, value)
            
            # Also update the row dict cache for subsequent formula evaluations
            if tag_im_jahr == 366:
                self.row_366_cache[f"{column_name}_366"] = value


# Singleton instance for easy access
_evaluator_instance = None

def get_ws_formula_evaluator() -> WSFormulaEvaluator:
    """Get or create the WS formula evaluator singleton"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = WSFormulaEvaluator()
    return _evaluator_instance


def recalculate_all_ws_data(preserve_stromverbr=False, num_passes=3) -> Dict[str, int]:
    """
    Convenience function to recalculate all WS data.
    Call this from admin actions or management commands.
    
    Args:
        preserve_stromverbr: If True, keep current stromverbr_raumwaerm_korr value.
        num_passes: Number of passes to run.
    """
    evaluator = get_ws_formula_evaluator()
    return evaluator.recalculate_all(preserve_stromverbr=preserve_stromverbr, num_passes=num_passes)
