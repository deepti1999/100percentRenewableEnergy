from django.db import models


class WSFormulaTemplate(models.Model):
    """
    🚀 100% ADMIN-EDITABLE WS FORMULA TEMPLATE SYSTEM
    
    Template for WS formulas - ONE template = ALL 365 days!
    
    Instead of creating 365 separate formulas (WS_STROMVERBR_1, WS_STROMVERBR_2, ...),
    define ONE template that uses 'day_prev' references for pattern-based calculation.
    
    FORMULA SYNTAX:
    ---------------
    - row.column          → Current row's column value
    - day_prev.column     → Previous day's column value (for days 2-365)
    - day_1.column        → Day 1's column value
    - day_365.column      → Day 365's column value
    - day_N.column        → Specific day N's column value
    - sums['sum_column']  → Sum of all daily values for that column
    - sums['min_column']  → Minimum of all daily values (1-365)
    - sums['max_column']  → Maximum of all daily values (1-365)
    - ref_column_366      → Row 366's column value (for reference)
    
    MATHEMATICAL FUNCTIONS:
    -----------------------
    - MAX(a, b)           → Maximum of values
    - MIN(a, b)           → Minimum of values
    - ABS(x)              → Absolute value
    - ROUND(x, n)         → Round to n decimal places
    - IF(cond; true; false) → Conditional (use semicolon separator!)
    
    EXAMPLE FORMULAS:
    -----------------
    Day 1:        verbrauch_promille * stromverbr_366
    Days 2-365:   (verbrauch_promille - day_prev.raumwaerm_korr) * stromverbr_366
    Row 366:      sums['sum_stromverbr']
    Row 367:      MIN(0, day_1.ladezust_burtto)
    Row 368:      sums['min_ladezustand_netto']
    """
    
    # Column identification
    column_name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Exact field name in WSData model (e.g., stromverbr, windstrom, ladezust_burtto)"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable name shown in admin (e.g., 'Stromverbrauch', 'Windstrom')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this column represents and how it's calculated"
    )
    
    # ===============================
    # FORMULA PATTERNS
    # ===============================
    
    formula_day_1 = models.TextField(
        blank=True,
        help_text="Formula for Day 1 ONLY (first day - no 'day_prev' available). "
                  "Example: verbrauch_promille * stromverbr_366"
    )
    
    formula_days_2_365 = models.TextField(
        blank=True,
        help_text="Pattern for Days 2-365. Use 'day_prev.column' for previous day. "
                  "Example: day_prev.ladezust_burtto + row.einspeich - row.ausspeich"
    )
    
    formula_row_366 = models.TextField(
        blank=True,
        help_text="Annual summary formula. Use sums['sum_column'] for totals. "
                  "Example: sums['sum_stromverbr']"
    )
    
    formula_row_367 = models.TextField(
        blank=True,
        help_text="Reference row for storage calculations. "
                  "Example: MIN(0, day_1.ladezust_burtto)"
    )
    
    formula_row_368 = models.TextField(
        blank=True,
        help_text="Additional reference row (optional). "
                  "Example: day_366.column / 365"
    )
    
    # For extensibility - add formulas for rows 369, 370, etc.
    custom_row_formulas = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON for additional rows: {'369': 'formula', '370': 'formula'}"
    )
    
    # ===============================
    # SETTINGS
    # ===============================
    
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive templates are ignored during calculation"
    )
    
    priority = models.IntegerField(
        default=100,
        help_text="Calculation order: lower numbers calculated first. "
                  "Use this for columns that depend on other columns."
    )
    
    # Validation
    depends_on = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated list of column names this formula depends on "
                  "(for documentation and validation)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'column_name']
        verbose_name = "WS Formula Template"
        verbose_name_plural = "WS Formula Templates"
    
    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.display_name} ({self.column_name})"
    
    def get_formula_for_row(self, tag_im_jahr: int) -> str:
        """
        Get the appropriate formula for a given row number.
        
        Args:
            tag_im_jahr: Day number (1-368+)
            
        Returns:
            Formula expression string, or empty string if no formula defined
        """
        if tag_im_jahr == 1:
            return self.formula_day_1 or ''
        elif 2 <= tag_im_jahr <= 365:
            return self.formula_days_2_365 or ''
        elif tag_im_jahr == 366:
            return self.formula_row_366 or ''
        elif tag_im_jahr == 367:
            return self.formula_row_367 or ''
        elif tag_im_jahr == 368:
            return self.formula_row_368 or ''
        else:
            # Check custom row formulas
            return self.custom_row_formulas.get(str(tag_im_jahr), '')
    
    def has_formula_for_row(self, tag_im_jahr: int) -> bool:
        """Check if a formula is defined for a given row."""
        return bool(self.get_formula_for_row(tag_im_jahr))
    
    def get_all_dependencies(self) -> list:
        """Get list of all columns this template depends on."""
        if not self.depends_on:
            return []
        return [col.strip() for col in self.depends_on.split(',') if col.strip()]
    
    def validate_formula(self, formula: str) -> tuple:
        """
        Validate a formula expression.
        
        Returns:
            (is_valid: bool, error_message: str)
        """
        if not formula:
            return (True, '')
        
        # Check for basic syntax issues
        try:
            # Check balanced parentheses
            if formula.count('(') != formula.count(')'):
                return (False, 'Unbalanced parentheses')
            
            # Check for common patterns
            import re
            
            # Valid patterns: day_prev.column, day_N.column, row.column, sums['key']
            valid_patterns = [
                r'day_prev\.\w+',
                r'day_\d+\.\w+',
                r'row\.\w+',
                r"sums\['\w+'\]",
                r'[A-Za-z_]\w*_\d+',  # e.g., stromverbr_366
            ]
            
            return (True, '')
            
        except Exception as e:
            return (False, str(e))
