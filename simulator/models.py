from django.db import models
from django.conf import settings
from typing import Optional, List
import threading

# Thread-local storage to prevent infinite cascade loops
_cascade_context = threading.local()

# ALL FORMULAS ARE STORED IN DATABASE (simulator_renewabledata.formula column)
# No external Python files are used for formula storage

# Import WS Data model
from .ws_models import WSData

# WSFormulaTemplate removed - all WS data is now edited directly in WSData entries


class CategoryDisplayName(models.Model):
    """
    Simple mapping of category codes to display names.
    
    Allows renaming pages freely without breaking backend logic:
    - category_code: Hardcoded string used in backend (e.g., 'renewable')
    - display_name: User-friendly name shown in UI (e.g., 'Solar & Wind Power')
    
    Change display names anytime via admin panel - backend code unchanged!
    """
    category_code = models.CharField(
        max_length=50,
        unique=True,
        choices=[
            ('renewable', 'Renewable Energy'),
            ('verbrauch', 'Energy Consumption'),
            ('landuse', 'Land Use'),
            ('bilanz', 'Energy Balance'),
            ('ws', 'Energy Storage (WS)'),
            ('ws_constant', 'WS Constants'),
            ('bilanz_constant', 'Bilanz Constants'),
            ('other', 'Other'),
        ],
        help_text="Internal category code (hardcoded in backend)"
    )
    display_name = models.CharField(
        max_length=200,
        help_text="Display name shown in UI (change freely!)"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this category"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon class or emoji"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Show/hide in UI"
    )
    
    class Meta:
        ordering = ['order', 'display_name']
        verbose_name = 'Category Display Name'
        verbose_name_plural = 'Category Display Names'
    
    def __str__(self):
        return f"{self.display_name} ({self.category_code})"
    
    @staticmethod
    def get_display_name(category_code):
        """Get display name for a category code, with fallback"""
        try:
            return CategoryDisplayName.objects.get(category_code=category_code, is_active=True).display_name
        except CategoryDisplayName.DoesNotExist:
            # Fallback to default names
            defaults = {
                'renewable': 'Renewable Energy',
                'verbrauch': 'Energy Consumption',
                'landuse': 'Land Use',
                'bilanz': 'Energy Balance',
                'ws': 'Energy Storage',
                'ws_constant': 'WS Constants',
                'bilanz_constant': 'Bilanz Constants',
            }
            return defaults.get(category_code, category_code.title())


class Formula(models.Model):
    """
    Stores a formula expression identified by a unique key.
    The expression is evaluated with variables supplied via FormulaVariable rows.
    
    EXTENSIBLE FORMULA SYSTEM:
    - Formulas stored in database, editable via Admin UI
    - Version control for audit trail
    - Active/inactive status for testing
    - Category organization for renewable, verbrauch, landuse, etc.
    """

    key = models.CharField(max_length=50, unique=True, help_text="Unique identifier (e.g., '1.1.2.1.2')")
    expression = models.TextField(help_text="Formula expression (e.g., 'LandUse_1.1 * 1.1.2.1 / 100')")
    description = models.TextField(blank=True, help_text="Human-readable description of what this formula calculates")
    
    # Category - hardcoded choices (backend logic), display names customizable
    category = models.CharField(
        max_length=50, 
        default='renewable',
        choices=[
            ('renewable', 'Renewable Energy'),
            ('verbrauch', 'Energy Consumption'),
            ('landuse', 'Land Use'),
            ('bilanz', 'Energy Balance'),
            ('ws', 'Energy Storage (WS)'),
            ('ws_constant', 'WS Constants'),
            ('bilanz_constant', 'Bilanz Constants'),
            ('other', 'Other'),
        ],
        help_text="Category for organizing formulas (use CategoryDisplayName to change display)"
    )
    
    # Formula Type - for status or ziel/target
    formula_type = models.CharField(
        max_length=20,
        default='status',
        choices=[
            ('status', 'Status (Current Value)'),
            ('ziel', 'Ziel/Target (Target Value)'),
        ],
        help_text="Select 'Status' for current value formula, 'Ziel' for target value formula. System will add _ziel/_target suffix automatically."
    )
    
    # WS Row Type - ONLY for WS category formulas
    # Specifies which rows this formula applies to
    ws_row_type = models.CharField(
        max_length=20,
        default='all',
        blank=True,
        choices=[
            ('all', 'All Rows (Default)'),
            ('day_1', 'Day 1 Only'),
            ('days_2_365', 'Days 2-365 (Pattern)'),
            ('row_366', 'Row 366 (Annual Summary)'),
            ('row_367', 'Row 367 (Reference)'),
            ('row_368', 'Row 368+'),
        ],
        help_text="🔧 FOR WS FORMULAS ONLY: Which rows this formula applies to. "
                  "Use 'Days 2-365' for patterns with day_prev references."
    )
    
    is_active = models.BooleanField(
        default=True, 
        help_text="Inactive formulas are ignored by calculation engine"
    )
    version = models.IntegerField(
        default=1, 
        help_text="Version number for tracking changes"
    )
    is_fixed = models.BooleanField(
        default=False,
        help_text="True if this represents a fixed value, False if calculated"
    )
    
    # Metadata
    notes = models.TextField(blank=True, help_text="Internal notes for developers")
    last_validated = models.DateTimeField(null=True, blank=True, help_text="Last time formula was validated")
    validation_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending Validation'),
            ('valid', 'Valid'),
            ('invalid', 'Invalid'),
            ('warning', 'Valid with Warnings'),
        ]
    )
    validation_message = models.TextField(blank=True, help_text="Result of last validation check")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "key"]
        verbose_name = "Formula"
        verbose_name_plural = "Formulas"
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['key']),
        ]

    def __str__(self):
        status = "✓" if self.is_active else "✗"
        cat_display = CategoryDisplayName.get_display_name(self.category)
        type_suffix = " [ZIEL]" if self.formula_type == 'ziel' else ""
        return f"{status} {self.key}{type_suffix} - {cat_display}"
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically add suffix based on formula_type.
        - If formula_type is 'ziel' and key doesn't have suffix, add it
        - Suffix: _ziel for verbrauch, _target for renewable
        """
        # Only auto-add suffix if formula_type is 'ziel'
        if self.formula_type == 'ziel':
            # Determine the correct suffix based on category
            if self.category == 'verbrauch':
                suffix = '_ziel'
            elif self.category == 'renewable':
                suffix = '_target'
            else:
                suffix = '_target'  # Default for other categories
            
            # Add suffix if not already present
            if self.category == 'renewable' and self.key.endswith('_ziel_target'):
                # Normalize legacy renewable suffix to _target
                self.key = f"{self.key[:-12]}{suffix}"
            elif self.category == 'renewable' and self.key.endswith('_ziel'):
                # Normalize legacy renewable suffix to _target
                self.key = f"{self.key[:-5]}{suffix}"
            elif not self.key.endswith(suffix):
                self.key = f"{self.key}{suffix}"
        
        # If formula_type is 'status', remove any suffix if present
        elif self.formula_type == 'status':
            if self.category == 'verbrauch' and self.key.endswith('_ziel'):
                self.key = self.key[:-5]  # Remove '_ziel'
            elif self.category == 'renewable' and self.key.endswith('_target'):
                self.key = self.key[:-7]  # Remove '_target'
        
        # Clear formula cache when saving
        try:
            from simulator.formula_service import FormulaService
            service = FormulaService()
            old_key = None
            if self.pk:
                try:
                    old_formula = Formula.objects.get(pk=self.pk)
                    old_key = old_formula.key
                except Formula.DoesNotExist:
                    pass
            
            super().save(*args, **kwargs)
            
            # Clear cache for both old and new keys
            service.clear_cache(self.key)
            if old_key and old_key != self.key:
                service.clear_cache(old_key)
            
            print(f"✅ Formula cache cleared for {self.key}")
        except Exception as e:
            # If cache clearing fails, still save the formula
            super().save(*args, **kwargs)
    
    def increment_version(self):
        """Increment version number when formula is updated"""
        self.version += 1
        self.save(update_fields=['version', 'updated_at'])
    
    def validate_expression(self):
        """
        Validate this formula's expression.
        Updates validation_status and validation_message fields.
        
        Returns:
            bool: True if valid, False otherwise
        """
        from simulator.formula_validators import validate_formula
        from django.utils import timezone
        
        is_valid, result = validate_formula(self.key, self.expression or '', self.category)
        
        # Update validation fields
        self.last_validated = timezone.now()
        
        if is_valid:
            self.validation_status = 'valid'
            msg_parts = []
            if result.get('info'):
                msg_parts.append(f"✓ Valid formula with {len(result['referenced_codes'])} references")
            if result.get('warnings'):
                self.validation_status = 'warning'
                msg_parts.extend([f"⚠ {w}" for w in result['warnings']])
            self.validation_message = '\n'.join(msg_parts) if msg_parts else 'Formula is valid'
        else:
            self.validation_status = 'invalid'
            error_msg = '\n'.join([f"✗ {e}" for e in result.get('errors', [])])
            warning_msg = '\n'.join([f"⚠ {w}" for w in result.get('warnings', [])])
            self.validation_message = f"{error_msg}\n{warning_msg}".strip()
        
        self.save(update_fields=['validation_status', 'validation_message', 'last_validated'])
        return is_valid
    
    def get_dependencies(self) -> List[str]:
        """Get list of all code references this formula depends on"""
        from simulator.formula_validators import get_formula_dependencies
        return get_formula_dependencies(self.key)


class FormulaVariable(models.Model):
    """
    Maps a variable name used inside a formula to an actual data source.
    Example: variable_name="wind_area" -> LandUse target_ha for code "LU_2.1".
    
    ENHANCED VARIABLE SYSTEM:
    - Support for multiple data sources
    - Default values for missing data
    - Transformation functions (future: e.g., scale, round)
    """

    LANDUSE_STATUS = "landuse_status"
    LANDUSE_TARGET = "landuse_target"
    RENEWABLE_STATUS = "renewable_status"
    RENEWABLE_TARGET = "renewable_target"
    RENEWABLE_CODE_STATUS = "renewable_code_status"  # NEW: Reference another renewable code's status
    RENEWABLE_CODE_TARGET = "renewable_code_target"  # NEW: Reference another renewable code's target
    VERBRAUCH_STATUS = "verbrauch_status"
    VERBRAUCH_ZIEL = "verbrauch_ziel"
    VERBRAUCH_CODE_STATUS = "verbrauch_code_status"  # NEW: Reference another verbrauch code's status
    VERBRAUCH_CODE_ZIEL = "verbrauch_code_ziel"      # NEW: Reference another verbrauch code's ziel
    # WS (Wärmespeicher) source types
    WS_ROW_VALUE = "ws_row_value"          # Current row's column value
    WS_ROW_366 = "ws_row_366"              # Row 366 reference value (annual summary)
    WS_SUM = "ws_sum"                       # Sum of column for days 1-365
    WS_DAY_PREV = "ws_day_prev"            # Previous day's column value
    LITERAL = "literal"

    SOURCE_CHOICES = [
        (LANDUSE_STATUS, "LandUse status_ha"),
        (LANDUSE_TARGET, "LandUse target_ha"),
        (RENEWABLE_STATUS, "RenewableData status_value (self)"),
        (RENEWABLE_TARGET, "RenewableData target_value (self)"),
        (RENEWABLE_CODE_STATUS, "➜ Other RenewableData code - status"),  # NEW!
        (RENEWABLE_CODE_TARGET, "➜ Other RenewableData code - target"),  # NEW!
        (VERBRAUCH_STATUS, "VerbrauchData status (self)"),
        (VERBRAUCH_ZIEL, "VerbrauchData ziel (self)"),
        (VERBRAUCH_CODE_STATUS, "➜ Other VerbrauchData code - status"),  # NEW!
        (VERBRAUCH_CODE_ZIEL, "➜ Other VerbrauchData code - ziel"),      # NEW!
        # WS (Wärmespeicher) source types
        (WS_ROW_VALUE, "➜ WSData current row column value"),
        (WS_ROW_366, "➜ WSData row 366 reference value"),
        (WS_SUM, "➜ WSData sum of column (days 1-365)"),
        (WS_DAY_PREV, "➜ WSData previous day column value"),
        (LITERAL, "Literal number"),
    ]

    formula = models.ForeignKey(
        Formula, on_delete=models.CASCADE, related_name="variables"
    )
    variable_name = models.CharField(
        max_length=50,
        help_text="Variable name used in formula expression"
    )
    source_type = models.CharField(
        max_length=30, 
        choices=SOURCE_CHOICES,
        help_text="Type of data source"
    )
    source_key = models.CharField(
        max_length=100,
        help_text="Code or value used to resolve the data (e.g., LU_2.1, 1.4, or literal).",
    )
    default_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Fallback if the source cannot be resolved.",
    )
    
    # Enhanced fields
    is_required = models.BooleanField(
        default=True,
        help_text="If True, formula fails if this variable cannot be resolved"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this variable"
    )

    class Meta:
        unique_together = ("formula", "variable_name")
        ordering = ["formula__key", "variable_name"]
        verbose_name = "Formula Variable"
        verbose_name_plural = "Formula Variables"

    def __str__(self):
        return f"{self.formula.key}:{self.variable_name} → {self.source_type}"
    
    def save(self, *args, **kwargs):
        """Override save to clear parent formula's cache when variable changes"""
        super().save(*args, **kwargs)
        # Clear cache for parent formula
        if self.formula_id:
            try:
                from simulator.formula_service import FormulaService
                from django.core.cache import cache
                service = FormulaService()
                service.clear_cache(self.formula.key)
                cache.delete(f'formula_{self.formula.key}')
                print(f"✅ Formula cache cleared for {self.formula.key} (variable changed)")
            except Exception as e:
                # Don't fail save if cache clearing fails
                print(f"⚠️  Cache clear warning for {self.formula.key}: {e}")
    
    def delete(self, *args, **kwargs):
        """Override delete to clear parent formula's cache when variable is removed"""
        formula_key = self.formula.key if self.formula else None
        super().delete(*args, **kwargs)
        # Clear cache for parent formula
        if formula_key:
            try:
                from simulator.formula_service import FormulaService
                from django.core.cache import cache
                service = FormulaService()
                service.clear_cache(formula_key)
                cache.delete(f'formula_{formula_key}')
                print(f"✅ Formula cache cleared for {formula_key} (variable deleted)")
            except Exception as e:
                print(f"⚠️  Cache clear warning for {formula_key}: {e}")

class LandUse(models.Model):
    code = models.CharField(max_length=20)  # e.g. "2.2.1"
    name = models.CharField(max_length=255)  # Clean name from CSV
    
    # Store hectare values from CSV
    status_ha = models.FloatField(null=True, blank=True)       # Status_ha from CSV
    target_ha = models.FloatField(null=True, blank=True)       # Target_ha from CSV

    # Optional formula keys for dynamic calculation (DB-driven)
    status_formula_key = models.CharField(
        max_length=50, null=True, blank=True, help_text="Formula key to calculate status_ha"
    )
    target_formula_key = models.CharField(
        max_length=50, null=True, blank=True, help_text="Formula key to calculate target_ha"
    )
    
    # User input for custom percentage calculations
    user_percent = models.FloatField(null=True, blank=True, help_text="User-defined percentage for target calculations")
    increase_limit_baseline_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Fixed baseline percent for max-increase validation (+LANDUSE_MAX_INCREASE_PERCENT points).",
    )
    target_locked = models.BooleanField(default=False, help_text="Preserve manual target_ha edits from parent cascades")
    
    # Hierarchical relationship - will be set from Parent_Code in CSV
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    
    # Meta information
    quelle = models.CharField(max_length=100, null=True, blank=True)  # Quelle (reference)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        """
        SIMPLIFIED save - just save the values, no automatic recalculation.
        Use skip_cascade=True to prevent signal from triggering renewable recalc.
        """
        skip_cascade = kwargs.pop('skip_cascade', False)
        kwargs.pop('force_recalc', None)  # Remove but ignore
        kwargs.pop('skip_user_percent_recalc', None)  # Remove but ignore
        
        # Set flag on instance for signal to check
        if skip_cascade:
            self._skip_cascade = True
        
        # Just save - no automatic recalculation of target_ha
        super(LandUse, self).save(*args, **kwargs)


    def _apply_formula_overrides(self, force_recalc=False):
        """
        Optionally calculate status_ha/target_ha from DB-stored formulas instead of hardcoded logic.
        This keeps land use calculations configurable without code edits.
        """
        if not self.status_formula_key and not self.target_formula_key:
            return

        try:
            from simulator.formula_service import evaluate_formula_by_key
        except Exception as exc:  # pragma: no cover - defensive guard
            print(f"❌ Unable to import formula service: {exc}")
            return

        if self.status_formula_key:
            status_val = evaluate_formula_by_key(self.status_formula_key)
            if status_val is not None:
                self.status_ha = status_val

        if self.target_formula_key and (force_recalc or not self.target_locked):
            target_val = evaluate_formula_by_key(self.target_formula_key)
            if target_val is not None:
                self.target_ha = target_val
    
    def _recalculate_renewable_dependents(self):
        """
        Find and recalculate all RenewableData items that reference this LandUse code.
        This is called automatically when LandUse values change.
        
        CASCADE MECHANISM:
        1. Find dependents via legacy inline formulas (LandUse_X.X).
        2. Find dependents via FormulaVariable mappings (DB-first path).
        3. Recalculate those items with fresh data.
        """
        if not self.code:
            return
        
        # Import here to avoid circular dependency
        import re
        from simulator.models import Formula, FormulaVariable  # local import
        from calculation_engine.renewable_engine import RenewableCalculator

        # Legacy inline-formula detection
        clean_code = self.code.replace("LU_", "") if self.code.startswith("LU_") else self.code
        landuse_pattern = f"LandUse_{self.code}"
        alt_landuse_pattern = f"LandUse_{clean_code}"

        legacy_items = list(
            RenewableData.objects.filter(formula__isnull=False).filter(
                models.Q(formula__contains=landuse_pattern)
                | (models.Q(formula__contains=alt_landuse_pattern) if alt_landuse_pattern else models.Q())
            )
        )

        # DB-backed dependents via FormulaVariable mappings
        fv_keys = Formula.objects.filter(
            category="renewable",
            is_active=True,
            variables__source_type__in=[FormulaVariable.LANDUSE_STATUS, FormulaVariable.LANDUSE_TARGET],
            variables__source_key__in=[self.code, clean_code, f"LU_{clean_code}"],
        ).values_list("key", flat=True)
        db_items = list(RenewableData.objects.filter(code__in=set(fv_keys)))

        dependent_items = {item.pk: item for item in legacy_items + db_items}.values()

        if not dependent_items:
            return

        # Build shared lookups once
        landuse_data = {
            lu.code: {
                "status_ha": lu.status_ha or 0,
                "target_ha": lu.target_ha or 0,
            }
            for lu in LandUse.objects.all()
        }
        verbrauch_data = {
            v.code: {"status": v.status or 0, "ziel": v.ziel or 0}
            for v in VerbrauchData.objects.all()
        }
        renewable_data = {
            r.code: {
                "status_value": r.status_value or 0,
                "target_value": r.target_value or 0,
            }
            for r in RenewableData.objects.all()
        }

        calculator = RenewableCalculator()
        updated_count = 0

        for item in dependent_items:
            calculator.set_data_sources(landuse_data, verbrauch_data, renewable_data)
            try:
                calc_status, calc_target = calculator.calculate(item.code, fail_fast=False)
            except Exception as e:
                print(f"❌ Error recalculating RenewableData {item.code} from LandUse {self.code}: {str(e)}")
                continue

            values_changed = False
            if calc_status is not None and item.status_value != calc_status:
                item.status_value = calc_status
                values_changed = True

            if calc_target is not None and item.target_value != calc_target:
                item.target_value = calc_target
                values_changed = True

            if values_changed:
                item.save(skip_verbrauch_recalc=True)
                renewable_data[item.code] = {
                    "status_value": item.status_value or 0,
                    "target_value": item.target_value or 0,
                }
                updated_count += 1

        # Silent by default - set settings.LOG_CASCADE_UPDATES = True to enable logging
        if updated_count and getattr(settings, "LOG_CASCADE_UPDATES", False):
            print(f"✅ LandUse {self.code} → {updated_count} renewable(s) recalculated")
    
    def _cascade_to_children(self):
        """
        When this LandUse item's target_ha changes, cascade the update to all children.
        Children will recalculate their target_ha based on their user_percent and new parent value.
        
        Example: If LU_1 target_ha changes from 100 to 200:
        - LU_1.1 has user_percent=20% → target_ha becomes 200 * 20% = 40
        - LU_1.2 has user_percent=30% → target_ha becomes 200 * 30% = 60
        """
        # Get all direct children of this item
        children = LandUse.objects.filter(parent=self)
        
        for child in children:
            # NEVER overwrite a child that has target_locked=True
            if child.target_locked:
                print(f"   🔒 Skipping locked child: {child.code} (target_ha={child.target_ha})")
                continue
            
            # Only update if child has a user_percent set
            if child.user_percent is not None and self.target_ha is not None:
                try:
                    # Recalculate child's target_ha based on new parent value
                    old_child_target = child.target_ha
                    child.target_ha = (self.target_ha * child.user_percent) / 100.0
                    
                    # Save child (this will trigger its own cascade to grandchildren)
                    child.save()
                    
                    print(f"🔄 Cascaded: {child.code} target_ha: {old_child_target} → {child.target_ha}")
                except Exception as e:
                    print(f"❌ Error cascading to child {child.code}: {str(e)}")


class RenewableData(models.Model):
    """
    Unified model for all renewable energy data types
    Flexible structure to handle Solar, Wind, Water, Biomass, etc.
    """
    # Main categorization
    category = models.CharField(max_length=50)  # Solar, Wind, Water, Biomass, etc.
    subcategory = models.CharField(max_length=100, blank=True, null=True)  # e.g. "Photovoltaik", "Onshore", etc.
    
    # Identification
    code = models.CharField(max_length=20, blank=True, null=True)  # Optional code for ordering
    name = models.CharField(max_length=200)  # e.g. "Bruttostromerzeugung", "Anlagenanzahl"
    description = models.TextField(blank=True, null=True)  # Additional details
    
    # Data values
    unit = models.CharField(max_length=20)  # ha, %, GWh/a, MW, Anzahl, etc.
    status_value = models.FloatField(null=True, blank=True)  # Current/existing value
    target_value = models.FloatField(null=True, blank=True)  # Future target value
    
    # User interaction
    user_input = models.FloatField(null=True, blank=True)  # User-defined value
    formula = models.TextField(blank=True, null=True)  # Calculation formula (e.g. "M6*M8*M9/1000")
    
    # New fields for enhanced structure
    is_fixed = models.BooleanField(default=True)  # Whether value is fixed (YES) or calculated (NO)
    parent_code = models.CharField(max_length=20, blank=True, null=True)  # Parent hierarchical reference
    
    # Metadata
    source = models.CharField(max_length=100, blank=True, null=True)  # Data source reference
    notes = models.TextField(blank=True, null=True)  # Additional notes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'subcategory', 'code', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['category', 'subcategory']),
        ]
    
    def __str__(self):
        if self.subcategory:
            return f"{self.category} - {self.subcategory} - {self.name}"
        return f"{self.category} - {self.name}"
    
    def save(self, *args, **kwargs):
        """
        Override save to recalculate dependent formulas when ANY value changes.
        This ensures that when you edit ANY value (fixed or calculated), all items
        that depend on it automatically update their calculated values.
        
        CASCADE UPDATE SYSTEM:
        - When a fixed value changes (e.g., 2.1.1.1), all formulas using it recalculate
        - When a calculated value changes, its dependents also recalculate
        - Prevents infinite recursion by tracking update chain
        - Updates happen immediately without manual intervention
        """
        # Track if values actually changed to avoid unnecessary cascades
        skip_cascade = kwargs.pop('skip_cascade', False)
        skip_verbrauch_recalc = kwargs.pop('skip_verbrauch_recalc', False)
        # Hint to post_save signal to optionally skip heavy Verbrauch recalc when cascading LandUse updates
        self._skip_verbrauch_recalc = skip_verbrauch_recalc
        # Set _skip_cascade for signals to read (they check this attribute)
        self._skip_cascade = skip_cascade
        old_status = None
        old_target = None
        
        if self.pk:  # Only check for existing records
            try:
                old_obj = RenewableData.objects.get(pk=self.pk)
                old_status = old_obj.status_value
                old_target = old_obj.target_value
            except RenewableData.DoesNotExist:
                pass
        
        # Save the current object first
        super().save(*args, **kwargs)
        
        # Cascade updates to dependents if values changed and cascade not disabled
        if not skip_cascade and self.code:
            status_changed = old_status != self.status_value
            target_changed = old_target != self.target_value
            
            if status_changed or target_changed:
                self._recalculate_dependents()

        # Reset skip flag after save to avoid leaking into unrelated operations
        self._skip_verbrauch_recalc = False
    
    def _recalculate_dependents(self):
        """
        Find and recalculate all RenewableData items that reference this code in their formulas.
        This is called automatically when ANY value changes (fixed or calculated).
        Uses the centralized calculation_engine for all calculations.
        
        CASCADE MECHANISM:
        1. Find all items with formulas referencing this code
        2. Load fresh data from all sources (LandUse, VerbrauchData, RenewableData)
        3. Use calculation_engine.RenewableCalculator to recalculate values
        4. Save with skip_cascade=False to trigger further cascades
        5. Builds complete dependency chain automatically
        """
        if not self.code:
            return
        
        # Find all items that have formulas referencing this code
        import re
        pattern = r'\b' + re.escape(self.code) + r'\b'
        
        dependent_items = RenewableData.objects.filter(
            is_fixed=False,
            formula__isnull=False
        ).exclude(code=self.code)
        
        # Find items that actually depend on this code
        items_to_update = []
        for item in dependent_items:
            if item.formula and re.search(pattern, item.formula):
                items_to_update.append(item)
        
        if not items_to_update:
            return
        
        try:
            # Import calculation engine
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from calculation_engine.renewable_engine import RenewableCalculator
            from simulator.models import LandUse, VerbrauchData
            
            # Initialize calculator with fresh data
            calculator = RenewableCalculator()
            
            # Load all data sources (keys without prefix, prefixes added inside set_data_sources)
            landuse_data = {
                i.code: {'status_ha': i.status_ha or 0, 'target_ha': i.target_ha or 0}
                for i in LandUse.objects.all()
            }
            verbrauch_data = {
                i.code: {'status': i.status or 0, 'ziel': i.ziel or 0}
                for i in VerbrauchData.objects.all()
            }
            renewable_data = {
                i.code: {'status_value': i.status_value or 0, 'target_value': i.target_value or 0}
                for i in RenewableData.objects.all()
            }
            
            calculator.set_data_sources(landuse_data, verbrauch_data, renewable_data)
            
            # Recalculate each dependent item
            for item in items_to_update:
                try:
                    calc_status, calc_target = calculator.calculate(item.code)
                    
                    if calc_status is not None and calc_target is not None:
                        # Check if values changed
                        status_changed = abs((item.status_value or 0) - calc_status) > 0.01
                        target_changed = abs((item.target_value or 0) - calc_target) > 0.01
                        
                        if status_changed or target_changed:
                            item.status_value = calc_status
                            item.target_value = calc_target
                            # Save and trigger cascade
                            super(RenewableData, item).save(update_fields=['status_value', 'target_value', 'updated_at'])
                            item._recalculate_dependents()
                        
                except Exception as e:
                    print(f"❌ Error recalculating {item.code}: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error in cascade calculation: {str(e)}")
        
        # Cascade complete - silent by default
        # Set settings.LOG_CASCADE_UPDATES = True to enable logging
        pass
    
    def get_effective_value(self):
        """
        Return the most relevant value:
        1. User input (if provided)
        2. Calculated value (if not fixed and has formula)
        3. Target value (if available) 
        4. Status value (fallback)
        """
        if self.user_input is not None:
            return self.user_input
        
        # If not fixed and has formula, use calculated values
        if not self.is_fixed and self.formula:
            calc_status, calc_target = self.get_calculated_values()
            if calc_target is not None:
                return calc_target
            elif calc_status is not None:
                return calc_status
        
        # Fallback to stored values
        if self.target_value is not None:
            return self.target_value
        return self.status_value
    
    def has_user_modification(self):
        """Check if user has provided input"""
        return self.user_input is not None
    
    def get_calculated_values(self, _cache=None, status_lookup=None, target_lookup=None, fail_fast=False):
        """
        Calculate status_value and target_value from formula if not fixed.
        NOW USES CALCULATION ENGINE - centralized formula management.
        
        FAIL-FAST MODE (optional):
        - If fail_fast=True, raises ValueError on missing formulas or None results
        - If fail_fast=False (default), falls back to stored values on error
        
        Args:
            _cache: deprecated parameter (kept for compatibility)
            status_lookup: optional dict with updated values (used during cascade updates)
            target_lookup: optional dict with updated values (used during cascade updates)
            fail_fast: If True, raises on errors instead of returning stored values
        
        Returns:
            tuple: (status_value, target_value)
            
        Raises:
            ValueError: If fail_fast=True and formula is missing or evaluation fails
        """
        has_status_formula = Formula.objects.filter(
            key=self.code, category='renewable', is_active=True
        ).exists()
        has_target_formula = Formula.objects.filter(
            key__in=[f"{self.code}_target", f"{self.code}_ziel_target", f"{self.code}_ziel"],
            category='renewable',
            is_active=True
        ).exists()

        if not has_status_formula and not has_target_formula and self.is_fixed:
            return self.status_value, self.target_value
        
        # Use calculation engine for all calculations
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from calculation_engine.renewable_engine import RenewableCalculator
            from simulator.models import LandUse, VerbrauchData
            
            calculator = RenewableCalculator()
            
            # If lookups provided, use them (for cascade updates with latest values)
            # Otherwise fetch fresh from database
            if status_lookup is not None and target_lookup is not None:
                # Extract LandUse data from lookups (keys with LandUse_ prefix)
                landuse_data = {}
                for key, value in status_lookup.items():
                    if key.startswith('LandUse_'):
                        code = key.replace('LandUse_', '')
                        if code not in landuse_data:
                            landuse_data[code] = {}
                        landuse_data[code]['status_ha'] = value
                
                for key, value in target_lookup.items():
                    if key.startswith('LandUse_'):
                        code = key.replace('LandUse_', '')
                        if code not in landuse_data:
                            landuse_data[code] = {}
                        landuse_data[code]['target_ha'] = value
                
                # Extract RenewableData from lookups
                renewable_data = {}
                for key, value in status_lookup.items():
                    if not key.startswith('LandUse_'):
                        if key not in renewable_data:
                            renewable_data[key] = {}
                        renewable_data[key]['status_value'] = value
                
                for key, value in target_lookup.items():
                    if not key.startswith('LandUse_'):
                        if key not in renewable_data:
                            renewable_data[key] = {}
                        renewable_data[key]['target_value'] = value
                
                # Get VerbrauchData from DB (doesn't change during LandUse cascade)
                verbrauch_data = {
                    i.code: {'status': i.status or 0, 'ziel': i.ziel or 0}
                    for i in VerbrauchData.objects.all()
                }
            else:
                # Load all data sources from database
                landuse_data = {
                    i.code: {'status_ha': i.status_ha or 0, 'target_ha': i.target_ha or 0}
                    for i in LandUse.objects.all()
                }
                verbrauch_data = {
                    i.code: {'status': i.status or 0, 'ziel': i.ziel or 0}
                    for i in VerbrauchData.objects.all()
                }
                renewable_data = {
                    i.code: {'status_value': i.status_value or 0, 'target_value': i.target_value or 0}
                    for i in RenewableData.objects.all()
                }
            
            calculator.set_data_sources(landuse_data, verbrauch_data, renewable_data)
            
            # Calculate using engine (pass fail_fast parameter)
            calc_status, calc_target = calculator.calculate(self.code, fail_fast=fail_fast)
            
            # Return calculated values when available, fall back to stored for missing ones
            # This allows showing status even when target formula is missing (and vice versa)
            final_status = calc_status if calc_status is not None else self.status_value
            final_target = calc_target if calc_target is not None else self.target_value
            
            # If fail_fast and BOTH are still None, raise error
            if fail_fast and final_status is None and final_target is None:
                raise ValueError(
                    f"Calculation for {self.code} returned None for both status and target. "
                    f"Formula: {self.formula}. Check FormulaVariables."
                )
            
            return final_status, final_target
                
        except Exception as e:
            if fail_fast:
                raise ValueError(f"Error calculating {self.code}: {e}") from e
            print(f"Error in get_calculated_values for {self.code}: {e}")
            return self.status_value, self.target_value


class VerbrauchData(models.Model):
    """
    Energy Consumption Data (Verbrauch) Model
    Based on KLIK_Hierarchy_BlankForCalculated.csv structure
    Handles energy consumption categories and subcategories with hierarchical codes
    """
    # Hierarchical identification
    code = models.CharField(max_length=20, unique=True)  # e.g. "1", "1.1", "1.1.1", etc.
    category = models.CharField(max_length=200)  # Energy consumption category description
    
    # Data values
    unit = models.CharField(max_length=20)  # GWh/a, %, etc.
    status = models.FloatField(null=True, blank=True)  # Current status value
    ziel = models.FloatField(null=True, blank=True)  # Target value (Ziel)
    
    # Calculation control
    is_calculated = models.BooleanField(default=False)  # True if this should be calculated via formula
    status_calculated = models.BooleanField(default=False)  # True if STATUS should be calculated
    ziel_calculated = models.BooleanField(default=False)  # True if ZIEL should be calculated
    
    # User interaction
    user_percent = models.FloatField(null=True, blank=True)  # User-defined percentage
    user_editable = models.BooleanField(default=False)  # True if this field is editable by user in frontend
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.category}"
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically calculate values for calculated fields.
        Enhanced with CASCADE UPDATE SYSTEM:
        - Recalculates own values if marked as calculated
        - Triggers recalculation of all dependent VerbrauchData entries
        - Prevents infinite recursion by tracking update chain
        - Updates happen immediately when any value changes
        - Applies user_percent to ziel for percentage fields
        - PERCENTAGE REBALANCING: When a percentage in a group changes,
          siblings auto-adjust to maintain 100% total
        """
        skip_cascade = kwargs.pop('skip_cascade', False)
        skip_recalc = kwargs.pop('skip_recalc', False)
        skip_rebalance = kwargs.pop('skip_rebalance', False)  # Skip percentage rebalancing
        old_status = None
        old_ziel = None
        old_user_percent = None
        
        # Track old values for change detection
        if self.pk:
            try:
                old_obj = VerbrauchData.objects.get(pk=self.pk)
                old_status = old_obj.status
                old_ziel = old_obj.ziel
                old_user_percent = old_obj.user_percent
            except VerbrauchData.DoesNotExist:
                pass
        
        # IMPORTANT: Calculated fields should NEVER have user_percent or be user_editable
        if self.is_calculated:
            self.user_percent = None
            self.user_editable = False
        
        # Apply user_percent to ziel if this is a user-editable field and user_percent is set
        # This works for ALL user_editable fields, not just percentage fields
        if self.user_editable and self.user_percent is not None:
            self.ziel = self.user_percent
        
        # Calculate values if this is a calculated field
        if self.is_calculated or self.status_calculated or self.ziel_calculated:
            try:
                if self.status_calculated or self.is_calculated:
                    calculated_status = self.calculate_value()
                    if calculated_status is not None:
                        self.status = calculated_status
                
                if self.ziel_calculated or self.is_calculated:
                    calculated_ziel = self.calculate_ziel_value()
                    if calculated_ziel is not None:
                        self.ziel = calculated_ziel
            except Exception as e:
                # Log error but don't fail the save
                print(f"Error calculating values for {self.code}: {str(e)}")
        
        super(VerbrauchData, self).save(*args, **kwargs)
        
        # PERCENTAGE REBALANCING: When user changes a percentage in a group,
        # automatically adjust siblings to maintain 100% total
        if not skip_rebalance and self.unit == '%' and self.code:
            user_percent_changed = old_user_percent != self.user_percent
            
            if user_percent_changed and self.user_percent is not None:
                try:
                    from simulator.percentage_rebalancer import rebalance_if_in_group
                    rebalance_if_in_group(self.code, self.user_percent)
                except Exception as e:
                    print(f"⚠️ Error rebalancing percentages for {self.code}: {e}")
        
        # SMART CASCADE: Prevents infinite loops using thread-local tracking
        if not skip_cascade and self.code:
            status_changed = old_status != self.status
            ziel_changed = old_ziel != self.ziel
            
            if status_changed or ziel_changed:
                # Initialize cascade chain if not exists
                if not hasattr(_cascade_context, 'chain'):
                    _cascade_context.chain = set()
                
                # Only cascade if we haven't processed this item yet
                if self.code not in _cascade_context.chain:
                    _cascade_context.chain.add(self.code)
                    try:
                        self._recalculate_dependents()
                    finally:
                        # Clean up after cascade completes
                        _cascade_context.chain.discard(self.code)
                        if len(_cascade_context.chain) == 0:
                            delattr(_cascade_context, 'chain')

        # Skip full recalc - too slow for individual saves
        # Use "Recalculate All" button for full system recalc
    
    def _recalculate_dependents(self):
        """
        Find and recalculate all VerbrauchData items that depend on this code.
        This is called automatically when values change.
        
        CASCADE MECHANISM FOR VERBRAUCH:
        1. Find all items that use this code in their formulas
        2. Recalculate each dependent item
        3. Save and trigger further cascades automatically
        4. Handles complex hierarchies like: 1.1 -> 1.4 -> 1 -> [top levels]
        """
        if not self.code:
            return
        
        import re
        
        # NO TRANSACTION - we need each save to commit so dependent calcs see fresh values
        # Find all calculated items
        dependent_items = VerbrauchData.objects.filter(
            models.Q(is_calculated=True) | 
            models.Q(status_calculated=True) | 
            models.Q(ziel_calculated=True)
        ).exclude(code=self.code)
        
        updated_count = 0
        # Check each item to see if it might depend on this code
        # We check by seeing if recalculation produces different results
        for item in dependent_items:
            try:
                # CRITICAL: Refresh from database to get latest values
                item.refresh_from_db()
                
                old_status = item.status
                old_ziel = item.ziel
                
                # Recalculate values
                new_status = None
                new_ziel = None
                
                if item.status_calculated or item.is_calculated:
                    new_status = item.calculate_value()
                    
                if item.ziel_calculated or item.is_calculated:
                    new_ziel = item.calculate_ziel_value()
                
                # Check if values changed
                values_changed = False
                if new_status is not None and old_status != new_status:
                    item.status = new_status
                    values_changed = True
                if new_ziel is not None and old_ziel != new_ziel:
                    item.ziel = new_ziel
                    values_changed = True
                
                if values_changed:
                    # Save and trigger cascade for this item too
                    item.save(skip_cascade=False)
                    updated_count += 1
                    
            except Exception as e:
                # Log error but don't fail
                print(f"❌ Error recalculating dependent VerbrauchData {item.code}: {str(e)}")
        
        if updated_count > 0:
            print(f"✅ Cascaded update: VerbrauchData {self.code} -> {updated_count} dependent(s) recalculated")
        
        # CASCADE TO RENEWABLEDATA with smart loop prevention
        if not hasattr(_cascade_context, 'renewable_chain'):
            _cascade_context.renewable_chain = set()
        
        if self.code not in _cascade_context.renewable_chain:
            _cascade_context.renewable_chain.add(self.code)
            try:
                self._recalculate_renewable_dependents()
            finally:
                _cascade_context.renewable_chain.discard(self.code)
                if len(_cascade_context.renewable_chain) == 0:
                    delattr(_cascade_context, 'renewable_chain')
    
    def _recalculate_renewable_dependents(self):
        """
        Find and recalculate all RenewableData items that reference this VerbrauchData code.
        This is called automatically when VerbrauchData values change.
        
        CASCADE MECHANISM:
        1. Find all RenewableData with formulas like "VerbrauchData_X" 
        2. Use calculation_engine to recalculate those items
        3. Those items will trigger their own cascades in RenewableData
        """
        if not self.code:
            return
        
        # Import here to avoid circular dependency
        import re
        
        # NOTE: Removed transaction.atomic() wrapper - it was causing nested transaction
        # conflicts with Django admin's implicit transaction, leading to silent rollbacks
        # of new VerbrauchData entries. Individual saves already manage their own transactions.
        
        # Pattern to find references to this VerbrauchData code
        # Can be "VerbrauchData_5" or just "Verbrauch_5" in formulas
        verbrauch_pattern = f"VerbrauchData_{self.code}"
        
        # Get all calculated RenewableData items
        dependent_items = RenewableData.objects.filter(
            is_fixed=False,
            formula__isnull=False
        )
        
        # Find items that reference this VerbrauchData
        items_to_update = []
        for item in dependent_items:
            if item.formula and verbrauch_pattern in item.formula:
                items_to_update.append(item)
        
        if not items_to_update:
            return
        
        try:
            # Import calculation engine
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from calculation_engine.renewable_engine import RenewableCalculator
            from simulator.models import LandUse
            
            calculator = RenewableCalculator()
            
            # Load all data sources with fresh values
            landuse_data = {
                i.code: {'status_ha': i.status_ha or 0, 'target_ha': i.target_ha or 0}
                for i in LandUse.objects.all()
            }
            verbrauch_data = {
                i.code: {'status': i.status or 0, 'ziel': i.ziel or 0}
                for i in VerbrauchData.objects.all()
            }
            renewable_data = {
                i.code: {'status_value': i.status_value or 0, 'target_value': i.target_value or 0}
                for i in RenewableData.objects.all()
            }
            
            calculator.set_data_sources(landuse_data, verbrauch_data, renewable_data)
            
            # Recalculate each dependent item
            updated_count = 0
            for item in items_to_update:
                try:
                    calc_status, calc_target = calculator.calculate(item.code)
                    
                    if calc_status is not None and calc_target is not None:
                        status_changed = abs((item.status_value or 0) - calc_status) > 0.01
                        target_changed = abs((item.target_value or 0) - calc_target) > 0.01
                        
                        if status_changed or target_changed:
                            item.status_value = calc_status
                            item.target_value = calc_target
                            item.save(skip_cascade=False)  # Trigger further cascades
                            updated_count += 1
                
                except Exception as e:
                    print(f"❌ Error recalculating RenewableData {item.code} from VerbrauchData {self.code}: {str(e)}")
            
            if updated_count > 0:
                print(f"✅ VerbrauchData {self.code} → {updated_count} RenewableData item(s) recalculated")
        
        except Exception as e:
            print(f"❌ Error in VerbrauchData._recalculate_renewable_dependents for {self.code}: {str(e)}")
    
    def get_hierarchy_level(self):
        """Calculate hierarchy level based on code (1=0, 1.1=1, 1.1.1=2, etc.)"""
        return self.code.count('.')
    
    def get_parent_code(self):
        """Get parent code (1.1.1 -> 1.1, 1.1 -> 1)"""
        if '.' in self.code:
            return '.'.join(self.code.split('.')[:-1])
        return None
    
    def get_effective_value(self):
        """Return the most relevant STATUS value: user_percent > calculated > status"""
        if self.user_percent is not None:
            return self.user_percent
        elif self.status_calculated or self.is_calculated:
            calculated = self.calculate_value()
            if calculated is not None:
                return calculated
        # Return status (not ziel) - this is for status calculations
        return self.status
    
    def get_effective_ziel_value(self):
        """Return the most relevant ziel value: user_percent > calculated_ziel > ziel"""
        if self.user_percent is not None:
            return self.user_percent
        elif self.ziel_calculated or self.is_calculated:
            calculated = self.calculate_ziel_value()
            if calculated is not None:
                return calculated
        return self.ziel
    
    # =============================================================================
    # VERBRAUCH CALCULATION SOURCE: calculation_engine/verbrauch_engine.py
    # =============================================================================
    # ✅ 100% DATABASE-DRIVEN FORMULAS via FormulaService
    # Formulas stored in Formula model, editable via Admin UI
    # NO FALLBACKS - Database only!
    # =============================================================================
    
    def calculate_value(self):
        """Calculate STATUS value using calculation_engine.VerbrauchCalculator (database-driven)"""
        # If this is a fixed value (user input), return it directly
        if not self.is_calculated:
            return self.status
        
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from calculation_engine.verbrauch_engine import VerbrauchCalculator
            
            # Initialize calculator
            calculator = VerbrauchCalculator()
            
            # Load all data sources
            verbrauch_data = {
                i.code: {'status': i.status or 0, 'ziel': i.ziel or 0}
                for i in VerbrauchData.objects.all()
            }
            renewable_data = {
                i.code: {'status_value': i.status_value or 0, 'target_value': i.target_value or 0}
                for i in RenewableData.objects.all()
            }
            landuse_data = {
                i.code: {'status_ha': i.status_ha or 0, 'target_ha': i.target_ha or 0}
                for i in LandUse.objects.all()
            }
            
            calculator.set_data_sources(verbrauch_data, renewable_data, landuse_data)
            
            # Calculate status value
            status_value, _ = calculator.calculate(self.code)
            return status_value
            
        except Exception as e:
            print(f"ERROR: calculation_engine failed for {self.code}: {e}")
            print(f"All formulas must be in database. No fallback available.")
            raise ValueError(f"Formula calculation failed for {self.code}. Please check database formulas.")
    
    def calculate_ziel_value(self):
        """Calculate ZIEL value using calculation_engine.VerbrauchCalculator (database-driven)"""
        # If this is a fixed value (user input), return it directly
        # Check BOTH is_calculated AND ziel_calculated flags
        if not self.is_calculated and not self.ziel_calculated:
            return self.ziel
        
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from calculation_engine.verbrauch_engine import VerbrauchCalculator
            
            # Initialize calculator
            calculator = VerbrauchCalculator()
            
            # Load all data sources
            verbrauch_data = {
                i.code: {'status': i.status or 0, 'ziel': i.ziel or 0}
                for i in VerbrauchData.objects.all()
            }
            renewable_data = {
                i.code: {'status_value': i.status_value or 0, 'target_value': i.target_value or 0}
                for i in RenewableData.objects.all()
            }
            landuse_data = {
                i.code: {'status_ha': i.status_ha or 0, 'target_ha': i.target_ha or 0}
                for i in LandUse.objects.all()
            }
            
            calculator.set_data_sources(verbrauch_data, renewable_data, landuse_data)
            
            # Calculate ziel value
            _, ziel_value = calculator.calculate(self.code)
            return ziel_value
            
        except Exception as e:
            print(f"ERROR: calculation_engine failed for {self.code} ziel: {e}")
            print(f"All formulas must be in database. No fallback available.")
            raise ValueError(f"Formula calculation failed for {self.code} ziel. Please check database formulas.")


class GebaeudewaermeData(models.Model):
    """
    Building Heat Data (Gebäudewärme) Model
    Based on Gebaudewarme_fixed_values.csv structure
    Handles building heating categories and subcategories with hierarchical codes
    """
    # Hierarchical identification
    code = models.CharField(max_length=20, unique=True)  # e.g. "2.0", "2.1", "2.1.1", etc.
    category = models.CharField(max_length=200)  # Building heat category description
    
    # Data values
    unit = models.CharField(max_length=30)  # GWh/a, %, qm/Person, kWh/qm/a, etc.
    status = models.FloatField(null=True, blank=True)  # Current status value
    ziel = models.FloatField(null=True, blank=True)  # Target value (Ziel)
    formula = models.CharField(max_length=100, null=True, blank=True)  # Formula description
    
    # Calculation control
    is_calculated = models.BooleanField(default=False)  # True if this should be calculated via formula
    status_calculated = models.BooleanField(default=False)  # True if STATUS should be calculated
    ziel_calculated = models.BooleanField(default=False)  # True if ZIEL should be calculated
    
    # User interaction (for future functionality)
    user_percent = models.FloatField(null=True, blank=True)  # User-defined percentage
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.category}"
    
    def get_hierarchy_level(self):
        """Calculate hierarchy level based on code (2=0, 2.1=1, 2.1.1=2, etc.)"""
        return self.code.count('.')
    
    def get_parent_code(self):
        """Get parent code (2.1.1 -> 2.1, 2.1 -> 2.0)"""
        if '.' in self.code:
            return '.'.join(self.code.split('.')[:-1])
        return None
    
    def get_effective_value(self):
        """Return the most relevant value: user_percent > calculated > ziel > status"""
        if self.user_percent is not None:
            return self.user_percent
        elif self.is_calculated:
            return self.calculate_value()
        elif self.ziel is not None:
            return self.ziel
        return self.status
    
    def get_effective_ziel_value(self):
        """Return the most relevant ziel value: user_percent > calculated_ziel > ziel"""
        if self.user_percent is not None:
            return self.user_percent
        elif self.is_calculated:
            return self.calculate_ziel_value()
        return self.ziel
    
    def calculate_value(self, lookup: Optional[dict] = None):
        """
        Placeholder: no calculations currently wired for GebaeudewaermeData.
        """
        return None
    
    def calculate_ziel_value(self, lookup: Optional[dict] = None):
        """
        Placeholder: no calculations currently wired for GebaeudewaermeData.
        """
        return None


class CalculationRun(models.Model):
    """
    Snapshot of an explicit full recalculation (renewable + Verbrauch + WS).
    Stored to let pages read the latest run metadata without re-running heavy steps.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    duration_ms = models.PositiveIntegerField()
    summary = models.JSONField(default=dict, blank=True)
    triggered_by = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Run at {self.created_at.isoformat()} ({self.duration_ms} ms)"
