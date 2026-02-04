from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from .models import (
    Formula,
    FormulaVariable,
    LandUse,
    RenewableData,
    VerbrauchData,
    WSData,
)
from .ws_formula_template import WSFormulaTemplate

class DataTypeFilter(SimpleListFilter):
    title = 'Data Type'
    parameter_name = 'data_type'
    
    def lookups(self, request, model_admin):
        return (
            ('klik', 'KLIK'),
            ('gebaeudewaerme', 'Gebäudewärme'),
            ('prozesswaerme', 'Prozesswärme'),
            ('mobile_anwendungen', 'Mobile Anwendungen'),
            ('strom_endverbrauch', 'Strom-Endverbrauch'),
            ('endenergieverbrauch', 'Endenergieverbrauch'),
            ('other', 'Other'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'klik':
            return queryset.filter(code__startswith='1')
        elif self.value() == 'gebaeudewaerme':
            return queryset.filter(code__startswith='2')
        elif self.value() == 'prozesswaerme':
            return queryset.filter(code__startswith='3')
        elif self.value() == 'mobile_anwendungen':
            return queryset.filter(code__startswith='4')
        elif self.value() == 'strom_endverbrauch':
            return queryset.filter(code='5')
        elif self.value() == 'endenergieverbrauch':
            return queryset.filter(code='6')
        elif self.value() == 'other':
            return queryset.exclude(code__regex=r'^[1-6]')

class FormulaVariableInline(admin.TabularInline):
    model = FormulaVariable
    extra = 1
    fields = ("variable_name", "source_type", "source_key", "default_value", "is_required", "notes")
    classes = ['collapse']


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ("status_icon", "key", "formula_type_badge", "ws_row_type_badge", "category", "expression_short", "is_active", "version", "validation_badge", "updated_at")
    list_filter = ("category", "formula_type", "ws_row_type", "is_active", "validation_status", "is_fixed")
    search_fields = ("key", "expression", "description", "notes")
    inlines = [FormulaVariableInline]
    ordering = ("category", "key",)
    list_per_page = 50
    
    # Make fields editable in list view
    list_editable = ("is_active",)
    
    # Action buttons - INCLUDING CACHE CLEARING!
    actions = ['activate_formulas', 'deactivate_formulas', 'validate_formulas', 'export_formulas', 'clear_cache_action', 'clear_all_cache_action']
    
    fieldsets = (
        ('Formula Identification', {
            'fields': ('key', 'category', 'formula_type', 'is_fixed'),
            'description': 'Key will be auto-suffixed based on formula type: Status = no suffix, Ziel = _ziel or _target'
        }),
        ('🔧 WS Row Type (Energy Storage Only)', {
            'fields': ('ws_row_type',),
            'description': '📌 FOR WS FORMULAS ONLY: Select which rows this formula applies to:\n'
                          '• Day 1 Only - First day (no day_prev available)\n'
                          '• Days 2-365 - Pattern formula using day_prev.column\n'
                          '• Row 366 - Annual summary (can reference Verbrauch/Renewable data)\n'
                          '• Row 367 - Reference row for storage calculations'
        }),
        ('Formula Expression', {
            'fields': ('expression', 'description'),
            'description': 'Use references like:\n'
                          '• Verbrauch: V_2_9_2_ziel, V_2_4_status\n'
                          '• Renewable: Renewable_1_1_2_1_2, Renewable_9_4_3\n'
                          '• WS sums: sums["sum_stromverbr"]\n'
                          '• WS pattern: day_prev.column, row.column'
        }),
        ('Status & Validation', {
            'fields': ('is_active', 'validation_status', 'validation_message', 'last_validated'),
            'classes': ('collapse',)
        }),
        ('Version & Notes', {
            'fields': ('version', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_validated')
    
    def status_icon(self, obj):
        """Show active/inactive icon"""
        if obj.is_active:
            return format_html('<span style="color: {}; font-size: 16px;">●</span>', 'green')
        return format_html('<span style="color: {}; font-size: 16px;">○</span>', 'red')
    status_icon.short_description = ''
    
    def formula_type_badge(self, obj):
        """Show formula type as colored badge"""
        if obj.formula_type == 'ziel':
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                '#0066cc',
                'ZIEL'
            )
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            '#666',
            'STATUS'
        )
    formula_type_badge.short_description = 'Type'
    
    def ws_row_type_badge(self, obj):
        """Show WS row type as colored badge (only for WS category)"""
        if obj.category != 'ws' or not obj.ws_row_type or obj.ws_row_type == 'all':
            return ''
        
        colors = {
            'day_1': '#28a745',        # Green
            'days_2_365': '#007bff',   # Blue
            'row_366': '#fd7e14',      # Orange
            'row_367': '#6c757d',      # Gray
            'row_368': '#17a2b8',      # Cyan
        }
        labels = {
            'day_1': 'Day 1',
            'days_2_365': '2-365',
            'row_366': '366',
            'row_367': '367',
            'row_368': '368+',
        }
        color = colors.get(obj.ws_row_type, '#999')
        label = labels.get(obj.ws_row_type, obj.ws_row_type)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            label
        )
    ws_row_type_badge.short_description = 'WS Row'
    
    def expression_short(self, obj):
        """Show shortened expression"""
        expr = obj.expression or ''
        if len(expr) > 60:
            return format_html('<span title="{}">{}</span>', expr, expr[:60] + '...')
        return format_html('{}', expr) if expr else ''
    expression_short.short_description = 'Expression'
    
    def validation_badge(self, obj):
        """Show validation status as colored badge"""
        colors = {
            'valid': 'green',
            'invalid': 'red',
            'pending': 'orange',
            'warning': 'darkorange',
        }
        status = obj.validation_status or 'pending'
        color = colors.get(status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            status.upper()
        )
    validation_badge.short_description = 'Status'
    
    # Admin actions
    def activate_formulas(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} formula(s) activated.')
    activate_formulas.short_description = "✓ Activate selected formulas"
    
    def deactivate_formulas(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} formula(s) deactivated.')
    deactivate_formulas.short_description = "✗ Deactivate selected formulas"
    
    def validate_formulas(self, request, queryset):
        """Validate selected formulas using comprehensive validator"""
        valid_count = 0
        invalid_count = 0
        warning_count = 0
        
        for formula in queryset:
            is_valid = formula.validate_expression()
            
            if formula.validation_status == 'valid':
                valid_count += 1
            elif formula.validation_status == 'warning':
                warning_count += 1
            else:
                invalid_count += 1
        
        total = queryset.count()
        self.message_user(
            request, 
            f'Validated {total} formulas: ✓ {valid_count} valid, ⚠ {warning_count} warnings, ✗ {invalid_count} invalid'
        )
    validate_formulas.short_description = "🔍 Validate selected formulas"
    
    def export_formulas(self, request, queryset):
        """Export selected formulas as JSON"""
        import json
        from django.http import HttpResponse
        
        formulas = []
        for formula in queryset:
            formulas.append({
                'key': formula.key,
                'expression': formula.expression,
                'description': formula.description,
                'category': formula.category,
                'formula_type': formula.formula_type,
                'is_fixed': formula.is_fixed,
                'is_active': formula.is_active,
            })
        
        response = HttpResponse(json.dumps(formulas, indent=2), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="formulas.json"'
        return response
    export_formulas.short_description = "📥 Export selected formulas as JSON"
    
    def clear_cache_action(self, request, queryset):
        """Clear cache for selected formulas - ensures changes are immediately visible"""
        from django.core.cache import cache
        from simulator.formula_service import FormulaService
        
        count = 0
        for formula in queryset:
            # Clear Django cache
            cache.delete(f'formula_{formula.key}')
            # Clear FormulaService cache
            service = FormulaService()
            service.clear_cache(formula.key)
            count += 1
        
        self.message_user(request, f"✅ Cache cleared for {count} formula(s) - changes will be visible immediately!")
    clear_cache_action.short_description = "🔄 Clear cache for selected formulas"
    
    def clear_all_cache_action(self, request, queryset):
        """Clear ALL formula caches - nuclear option for when formulas aren't updating"""
        from django.core.cache import cache
        from simulator.formula_service import FormulaService
        
        # Clear all Django cache
        cache.clear()
        
        # Clear FormulaService cache
        service = FormulaService()
        service.clear_cache()
        
        self.message_user(request, "✅ ALL formula caches cleared! All formula changes are now active.")
    clear_all_cache_action.short_description = "🔄 Clear ALL formula caches"
    
    def save_model(self, request, obj, form, change):
        """Override to show cache clearing message - WS recalculation is handled by signals"""
        super().save_model(request, obj, form, change)
        if change:
            self.message_user(request, f"✅ Formula {obj.key} updated - dependent values will auto-recalculate!")
        else:
            self.message_user(request, f"✅ Formula {obj.key} created - dependent values will auto-recalculate!")
        
        # Note: WS recalculation is now handled by the formula_changed signal in signals.py
        # This ensures consistent behavior whether saving from admin or programmatically
    
    def delete_model(self, request, obj):
        """Override to show cache clearing message"""
        key = obj.key
        category = obj.category
        super().delete_model(request, obj)
        self.message_user(request, f"✅ Formula {key} deleted - dependent values will auto-recalculate!")
        # Note: WS recalculation is handled by the formula_changed signal


@admin.register(LandUse)
class LandUseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status_ha', 'target_ha', 'parent', 'quelle']
    list_filter = ['quelle', 'parent']
    search_fields = ['code', 'name']
    ordering = ['code']
    
    # REMOVE list_editable - it often causes save issues in Django admin
    # Instead, users should click on a row to edit in detail form
    list_per_page = 25
    
    # Add action to manually trigger cascade updates
    actions = ['trigger_cascade_update', 'force_save_selected']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'parent', 'quelle')
        }),
        ('Data (Editable)', {
            'fields': ('status_ha', 'target_ha', 'user_percent', 'target_locked'),
            'description': '⚠️ IMPORTANT: After changing status_ha or target_ha, click SAVE to trigger cascade updates to dependent Renewable records.'
        }),
        ('Formulas (Optional)', {
            'fields': ('status_formula_key', 'target_formula_key'),
            'description': 'Provide formula keys to calculate values from DB-driven formulas instead of hardcoding.',
            'classes': ('collapse',)
        }),
    )
    
    def trigger_cascade_update(self, request, queryset):
        """Manually trigger cascade update for selected LandUse records"""
        updated_count = 0
        for landuse in queryset:
            # Force recalculation by calling the cascade method
            landuse._recalculate_renewable_dependents()
            updated_count += 1
        
        self.message_user(
            request,
            f'✅ Triggered cascade update for {updated_count} LandUse record(s). '
            f'Dependent Renewable records have been recalculated.',
            level='SUCCESS'
        )
    trigger_cascade_update.short_description = "🔄 Trigger cascade update to Renewable data"
    
    def force_save_selected(self, request, queryset):
        """Force save selected records to ensure database persistence"""
        count = 0
        for landuse in queryset:
            landuse.save()
            count += 1
        
        self.message_user(
            request,
            f'✅ Force-saved {count} LandUse record(s) to database.',
            level='SUCCESS'
        )
    force_save_selected.short_description = "💾 Force save selected records"
    
    def save_model(self, request, obj, form, change):
        """Save and allow cascade so dependent renewables update automatically."""
        super().save_model(request, obj, form, change)
        self.message_user(
            request,
            f'✅ Saved {obj.code}: status_ha={obj.status_ha}, target_ha={obj.target_ha}',
            level='SUCCESS'
        )




@admin.register(RenewableData)
class RenewableDataAdmin(admin.ModelAdmin):
    # Show all entries with values only for fixed items
    list_display = ['code', 'name', 'category', 'subcategory', 'unit', 'status_display', 'target_display', 'is_fixed', 'parent_code']
    list_filter = ['category', 'subcategory', 'is_fixed', 'created_at']
    search_fields = ['code', 'name', 'category', 'subcategory']
    ordering = ['code']
    
    # Enable editing for status and target values in the list for fixed items only
    list_editable = ['is_fixed']
    list_per_page = 100  # Show more entries per page
    
    # Add JavaScript for instant field toggling
    class Media:
        js = ('admin/js/renewable_toggle.js',)
    
    def status_display(self, obj):
        """Show status value only for fixed items (non-formula items)"""
        if obj.is_fixed:
            return obj.status_value if obj.status_value is not None else "-"
        return ""  # Empty for calculated items
    status_display.short_description = 'Status Value'
    
    def target_display(self, obj):
        """Show target value only for fixed items (non-formula items)"""
        if obj.is_fixed:
            return obj.target_value if obj.target_value is not None else "-"
        return ""  # Empty for calculated items
    target_display.short_description = 'Target Value'
    
    fieldsets = (
        ('Identification', {
            'fields': ('code', 'name', 'category', 'subcategory', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent_code',),
            'description': 'Hierarchical parent relationship.'
        }),
        ('Data Values - Editable for Fixed Items Only', {
            'fields': ('unit', 'status_value', 'target_value', 'user_input'),
            'description': 'Edit values for fixed items. Formula items are calculated automatically.'
        }),
        ('Calculation', {
            'fields': ('is_fixed', 'formula'),
            'description': 'Whether value is fixed or calculated, and formula if applicable.'
        }),
        ('Metadata', {
            'fields': ('source', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make value fields readonly for calculated items, editable for fixed items"""
        # For new objects, only formula is readonly - allow setting code
        if not obj:
            return ['formula']
        
        # For existing objects: code, created_at, updated_at, formula are readonly
        readonly = ['code', 'created_at', 'updated_at', 'formula']
        
        # For existing objects with formulas (is_fixed=False), make values readonly
        if not obj.is_fixed:
            readonly.extend(['status_value', 'target_value', 'user_input'])
        
        return readonly
    
    # No longer need these display methods in detail view
    # Remove the old status_value_display, target_value_display, user_input_display methods


@admin.register(VerbrauchData)
class VerbrauchDataAdmin(admin.ModelAdmin):
    list_display = ['code', 'category_display', 'unit', 'status_display', 'ziel_display', 'user_percent_display', 'is_calculated', 'user_editable', 'data_type']
    list_filter = [DataTypeFilter, 'is_calculated', 'user_editable', 'unit', 'created_at']
    search_fields = ['code', 'category']
    ordering = ['code']
    
    # Enable editing for key fields - only for non-calculated items
    list_editable = ['is_calculated', 'user_editable']
    list_per_page = 30
    
    fieldsets = (
        ('Identification', {
            'fields': ('code', 'category')
        }),
        ('Data Values', {
            'fields': ('unit', 'status', 'ziel', 'user_percent'),
            'description': 'Current status, target (Ziel), and user percentage values. Only editable for fixed values.'
        }),
        ('User Frontend Control', {
            'fields': ('user_editable',),
            'description': '✅ Check this box to allow users to edit this field in the frontend. Users will be able to modify the value and trigger recalculations.'
        }),
        ('Calculation', {
            'fields': ('is_calculated',),
            'description': 'Whether this value should be calculated via formula. Formulas are managed in the Formula admin page.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make status/ziel readonly for calculated items"""
        readonly = list(self.readonly_fields)
        if obj and obj.is_calculated:
            readonly.extend(['status', 'ziel', 'user_percent'])
        return readonly
    
    readonly_fields = ['created_at', 'updated_at']
    
    def category_display(self, obj):
        """Truncate long category names for better display and add CSS classes"""
        category_text = obj.category
        if len(category_text) > 50:
            category_text = category_text[:47] + "..."
        
        # Add bold styling for "Strom-Endverbrauch insgesamt"
        if "Strom-Endverbrauch insgesamt" in obj.category:
            return format_html('<span style="font-weight: bold;">{}</span>', category_text)
        
        # Add bold styling for "Endenergieverbrauch insgesamt"
        if "Endenergieverbrauch insgesamt" in obj.category:
            return format_html('<span style="font-weight: bold;">{}</span>', category_text)
        
        # Add green styling for FC-Traktion alternative entries
        if "Alternativ zur" in obj.category and "Brennstoffzellen (FC)" in obj.category:
            return format_html('<span style="color: green; font-style: italic;">{}</span>', category_text)
        
        return category_text
    category_display.short_description = 'Category'
    
    def format_number(self, value):
        """Format number properly: commas for thousands (>=1000), decimals for smaller"""
        if value is None:
            return "-"
        
        # Always check if it's a whole number first
        if value == int(value):
            if value >= 1000:
                return f"{int(value):,}"  # Comma separator, no decimals for whole numbers
            else:
                return f"{int(value):,}"    # No decimals, comma for smaller whole numbers too
        else:
            # For non-whole numbers
            return f"{value:,.4f}".rstrip('0').rstrip('.')  # up to 4 decimals, comma thousands
    
    def status_display(self, obj):
        """Format status value for display - only show for fixed values"""
        # Special list of fixed items that should show values
        fixed_items = ['4.2.1', '4.2.2', '4.2.4']
        
        # 4.3.x series should never show values (all calculated by formulas)
        if obj.code.startswith('4.3.'):
            return ""
        
        # Only show values for fixed items or non-calculated items (legacy)
        if obj.code in fixed_items or not obj.is_calculated:
            # Special case: 2.4.5 status is always stored (0), never calculated
            if obj.code == '2.4.5':
                result = self.format_number(obj.status)
                return f"{result}✓" if result == "0" else result
            # Only show if value exists
            if obj.status is not None:
                return self.format_number(obj.status)
        return ""  # Empty for calculated items or items without values
    status_display.short_description = 'Status'
    
    def ziel_display(self, obj):
        """Format ziel value for display - only show for fixed values"""
        # Special case: FC-Traktion alternative entries show "(Passiv)" in Ziel column
        if "Alternativ zur" in obj.category and "Brennstoffzellen (FC)" in obj.category:
            return "(Passiv)"
        
        # 4.3.x series should never show values (all calculated by formulas)
        if obj.code.startswith('4.3.'):
            return ""
        
        # Special list of fixed items that should show values
        fixed_items = ['4.2.1', '4.2.2', '4.2.4']
        
        # Only show values for fixed items or non-calculated items (legacy)
        if obj.code in fixed_items or not obj.is_calculated:
            # Only show if value exists
            if obj.ziel is not None:
                return self.format_number(obj.ziel)
        return ""  # Empty for calculated items or items without values
    ziel_display.short_description = 'Ziel'
    
    def user_percent_display(self, obj):
        """Format user_percent value for display - only show for fixed values"""
        # 4.3.x series should never show values (all calculated by formulas)
        if obj.code.startswith('4.3.'):
            return ""
        
        # Special list of fixed items that should show values
        fixed_items = ['4.2.1', '4.2.2', '4.2.4']
        
        # Only show values for fixed items or non-calculated items (legacy)
        if obj.code in fixed_items or not obj.is_calculated:
            if obj.user_percent is not None:
                return self.format_number(obj.user_percent)
        return ""  # Empty for calculated items or items without values
    user_percent_display.short_description = 'User %'

    def save_model(self, request, obj, form, change):
        """Save the verbrauch data entry."""
        super().save_model(request, obj, form, change)
    
    def data_type(self, obj):
        """Show whether this is KLIK, Gebäudewärme, Prozesswärme, Mobile Anwendungen, Strom-Endverbrauch, or Endenergieverbrauch data"""
        if obj.code.startswith('1'):
            return "KLIK"
        elif obj.code.startswith('2'):
            return "Gebäudewärme"
        elif obj.code.startswith('3'):
            return "Prozesswärme"
        elif obj.code.startswith('4'):
            return "Mobile Anwendungen"
        elif obj.code == '5':
            return "Strom-Endverbrauch"
        elif obj.code == '6':
            return "Endenergieverbrauch"
        else:
            return "Other"
    data_type.short_description = 'Type'


@admin.register(WSData)
class WSDataAdmin(admin.ModelAdmin):
    """
    Admin interface for WS (Wärmespeicher/Energy Storage) Data
    Displays all columns from the Excel sheet in a structured grid
    ALL FIELDS ARE FULLY EDITABLE
    """
    
    def format_decimal(self, value):
        """Format decimal number in English format: 1,234.567890"""
        if value is None:
            return "-"
        # Format with up to 15 decimal places, remove trailing zeros
        formatted = f"{float(value):,.15f}".rstrip('0').rstrip('.')
        return formatted
    
    # Create display methods for all numeric fields
    def wind_promille_display(self, obj):
        return self.format_decimal(obj.wind_promille)
    wind_promille_display.short_description = 'Wind Promille'
    
    def solar_promille_display(self, obj):
        return self.format_decimal(obj.solar_promille)
    solar_promille_display.short_description = 'Solar Promille'
    
    def heizung_abwaerm_promille_display(self, obj):
        return self.format_decimal(obj.heizung_abwaerm_promille)
    heizung_abwaerm_promille_display.short_description = 'Heizung Abwärm Promille'
    
    def verbrauch_promille_display(self, obj):
        return self.format_decimal(obj.verbrauch_promille)
    verbrauch_promille_display.short_description = 'Verbrauch Promille'
    
    def stromverbr_display(self, obj):
        return self.format_decimal(obj.stromverbr)
    stromverbr_display.short_description = 'Stromverbr'
    
    def davon_raumw_korr_display(self, obj):
        return self.format_decimal(obj.davon_raumw_korr)
    davon_raumw_korr_display.short_description = 'Davon Raumw Korr'
    
    def stromverbr_raumwaerm_korr_display(self, obj):
        return self.format_decimal(obj.stromverbr_raumwaerm_korr)
    stromverbr_raumwaerm_korr_display.short_description = 'Stromverbr Raumwärm Korr'
    
    def windstrom_display(self, obj):
        return self.format_decimal(obj.windstrom)
    windstrom_display.short_description = 'Windstrom'
    
    def solarstrom_display(self, obj):
        return self.format_decimal(obj.solarstrom)
    solarstrom_display.short_description = 'Solarstrom'
    
    def sonst_kraft_konstant_display(self, obj):
        return self.format_decimal(obj.sonst_kraft_konstant)
    sonst_kraft_konstant_display.short_description = 'Sonst Kraft Konstant'
    
    def wind_solar_konstant_display(self, obj):
        return self.format_decimal(obj.wind_solar_konstant)
    wind_solar_konstant_display.short_description = 'Wind+Solar Konstant'
    
    def direktverbr_strom_display(self, obj):
        return self.format_decimal(obj.direktverbr_strom)
    direktverbr_strom_display.short_description = 'Direktverbr Strom'
    
    def ueberschuss_strom_display(self, obj):
        return self.format_decimal(obj.ueberschuss_strom)
    ueberschuss_strom_display.short_description = 'Ueberschuss Strom'
    
    def einspeich_display(self, obj):
        return self.format_decimal(obj.einspeich)
    einspeich_display.short_description = 'Einspeich'
    
    def abregelung_z_display(self, obj):
        return self.format_decimal(obj.abregelung_z)
    abregelung_z_display.short_description = 'Abregelung Z'
    
    def mangel_last_display(self, obj):
        return self.format_decimal(obj.mangel_last)
    mangel_last_display.short_description = 'Mangel Last'
    
    def brennstoff_ausgleichs_strom_display(self, obj):
        return self.format_decimal(obj.brennstoff_ausgleichs_strom)
    brennstoff_ausgleichs_strom_display.short_description = 'Brennstoff Ausgleichs Strom'
    
    def speicher_ausgl_strom_display(self, obj):
        return self.format_decimal(obj.speicher_ausgl_strom)
    speicher_ausgl_strom_display.short_description = 'Speicher Ausgl Strom'
    
    def ausspeich_rueckverstr_display(self, obj):
        return self.format_decimal(obj.ausspeich_rueckverstr)
    ausspeich_rueckverstr_display.short_description = 'Ausspeich Rückverstr'
    
    def ausspeich_gas_display(self, obj):
        return self.format_decimal(obj.ausspeich_gas)
    ausspeich_gas_display.short_description = 'Ausspeich Gas'
    
    def ladezust_burtto_display(self, obj):
        return self.format_decimal(obj.ladezust_burtto)
    ladezust_burtto_display.short_description = 'Ladezust Burtto'
    
    def ladezustand_abs_vorl_tl_display(self, obj):
        return self.format_decimal(obj.ladezustand_abs_vorl_tl)
    ladezustand_abs_vorl_tl_display.short_description = 'Ladezustand Abs Vorl TL'
    
    def selbstentl_display(self, obj):
        return self.format_decimal(obj.selbstentl)
    selbstentl_display.short_description = 'Selbstentl'
    
    def ladezustand_netto_display(self, obj):
        return self.format_decimal(obj.ladezustand_netto)
    ladezustand_netto_display.short_description = 'Ladezustand Netto'
    
    def ladezustand_abs_display(self, obj):
        return self.format_decimal(obj.ladezustand_abs)
    ladezustand_abs_display.short_description = 'Ladezustand Abs.'
    
    list_display = [
        'tag_im_jahr', 'datum_ref', 
        'wind_promille_display', 'solar_promille_display', 'heizung_abwaerm_promille_display', 'verbrauch_promille_display',
        'stromverbr_display', 'davon_raumw_korr_display', 'stromverbr_raumwaerm_korr_display',
        'windstrom_display', 'solarstrom_display', 'sonst_kraft_konstant_display', 'wind_solar_konstant_display',
        'direktverbr_strom_display', 'ueberschuss_strom_display', 'einspeich_display', 'abregelung_z_display',
        'mangel_last_display', 'brennstoff_ausgleichs_strom_display', 'speicher_ausgl_strom_display',
        'ausspeich_rueckverstr_display', 'ausspeich_gas_display', 'ladezust_burtto_display', 'ladezustand_abs_vorl_tl_display', 'selbstentl_display', 'ladezustand_netto_display', 'ladezustand_abs_display'
    ]
    
    list_filter = ['datum_ref']
    search_fields = ['tag_im_jahr', 'datum_ref']
    ordering = ['tag_im_jahr']
    
    # Disable inline editing in list view (use detail form instead for proper number formatting)
    list_editable = []
    
    list_per_page = 50
    
    # All fields organized in logical groups - ALL EDITABLE
    fieldsets = (
        ('Date Information', {
            'fields': ('tag_im_jahr', 'datum_ref'),
            'description': 'Day number and date reference'
        }),
        ('Promille Values (Columns C-F)', {
            'fields': ('wind_promille', 'solar_promille', 'heizung_abwaerm_promille', 'verbrauch_promille'),
            'description': 'Wind, Solar, Heizung, and Verbrauch in Promille'
        }),
        ('Primary Energy Values (Columns G-N)', {
            'fields': (
                'stromverbr',                    # Column G: Stromverbr.
                'davon_raumw_korr',             # Column H: davon Raumw.korr.
                'raumwaerm_korr',               # Column I: Raumwärm.Korr.
                'stromverbr_raumwaerm_korr',    # Column J: Stromverbr. Raumwärm.Korr.
                'windstrom',                     # Column K: Windstrom
                'solarstrom',                    # Column L: Solarstrom
                'sonst_kraft_konstant',          # Column M: Sonst.Kraft(konstant)
                'wind_solar_konstant'            # Column N: Wind+Solar Konstant
            ),
            'description': 'Columns G through N - Primary energy calculations'
        }),
        ('Distribution & Usage (Columns O-S)', {
            'fields': (
                'direktverbr_strom',    # Column O
                'ueberschuss_strom',    # Column P
                'mangel_last'           # Column S
            ),
            'description': 'Energy distribution and usage parameters'
        }),
        ('Storage & Compensation (Columns Q-AB)', {
            'fields': (
                'einspeich',                     # Column Q
                'abregelung_z',                  # Column R
                'brennstoff_ausgleichs_strom',   # Column T
                'speicher_ausgl_strom',          # Column U
                'ausspeich_rueckverstr',         # Column V
                'ausspeich_gas',                 # Column W
                'ladezust_burtto',               # Column X
                'ladezustand_abs_vorl_tl',       # Column Y
                'selbstentl',                    # Column Z
                'ladezustand_netto',             # Column AA
                'ladezustand_abs',               # Column AB
                'aussprech_rueckwaerts',         # Old Column V
                'aussprech_gas'                  # Old Column W
            ),
            'description': 'Storage and compensation values'
        }),
        ('Load & State Parameters (Columns AB-AD)', {
            'fields': (
                'netto',                    # Column AB
                'ladeabbzustan',            # Column AC
                'abacadae'                  # Column AD
            ),
            'description': 'Load and state parameters'
        }),
        ('Overview Parameters (Columns AF-AH)', {
            'fields': (
                'uebersicht_speich_last',   # Column AF
                'uebersicht_aussprech',     # Column AG
                'uebersicht_entspeich'      # Column AH
            ),
            'description': 'Overview summary values'
        }),
        ('Conversion & Technical Parameters (Columns AI-AP)', {
            'fields': (
                'umrechnun',            # Column AI
                'tl_mwh_1y',           # Column AJ
                'konstanstr_tl',       # Column AK
                'solarstrom_tl',       # Column AL
                'windstrom_tl',        # Column AM
                'solar_konst_tl',      # Column AN
                'konst_win_solar_tl',  # Column AO
                'verbrauch_tl'         # Column AP
            ),
            'description': 'TL (Technical Load) conversion parameters'
        }),
        ('Additional Calculations (Columns AQ-AZ)', {
            'fields': (
                'konstantstr',              # Column AQ
                'solar_kons_1_tageay',     # Column AR
                'wind_sol_win_tv',         # Column AS
                'unterbedeck',             # Column AT
                'solar_tv',                # Column AU
                'wind_tv',                 # Column AV
                'ladeabzustan_d_abs_tl',   # Column AW
                'unterbedeck_ohne_wind',   # Column AX
                'additional_column_ay',    # Column AY
                'additional_column_az'     # Column AZ
            ),
            'description': 'Additional calculation columns'
        }),
    )
    
    # NO readonly fields - everything is editable
    def get_readonly_fields(self, request, obj=None):
        return []
    
    # Enable bulk actions
    actions = ['duplicate_entries', 'recalculate_all_ws']
    
    def duplicate_entries(self, request, queryset):
        """Allow duplicating selected entries for quick data entry"""
        for obj in queryset:
            obj.pk = None
            obj.save()
        self.message_user(request, f"{queryset.count()} entries duplicated successfully.")
    duplicate_entries.short_description = "Duplicate selected entries"
    
    def recalculate_all_ws(self, request, queryset):
        """
        Manual full recalculation of ALL WS data using formulas from the Formula model.
        
        NOTE: This is rarely needed! WS values now auto-recalculate when:
        - A WS formula is changed (via signals)
        - Row 366 or 367 values are edited manually (via signals)
        - Renewable/Verbrauch data changes that affect WS inputs
        
        Use this only for recovery/debugging purposes.
        """
        try:
            from simulator.ws_formula_service import recalculate_all_ws_data, get_ws_formula_evaluator
            
            # Clear cache before recalculation
            evaluator = get_ws_formula_evaluator()
            evaluator.clear_cache()
            
            stats = recalculate_all_ws_data(num_passes=3)
            
            self.message_user(
                request,
                f"✅ WS Full Recalculation complete! "
                f"Updated: {stats['updated']} | Errors: {stats['errors']} | Skipped: {stats['skipped']}",
                level='SUCCESS'
            )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Recalculation failed: {str(e)}",
                level='ERROR'
            )
    recalculate_all_ws.short_description = "🔄 Force Full WS Recalculation (debug only)"


@admin.register(WSFormulaTemplate)
class WSFormulaTemplateAdmin(admin.ModelAdmin):
    """
    ⚠️ DEPRECATED - Use Formula model (category='ws') instead!
    
    This WSFormulaTemplate model is kept for backward compatibility only.
    All WS formulas should be defined in the main Formula admin with category='ws'.
    """
    
    list_display = [
        'status_icon', 'column_name', 'display_name', 'priority', 
        'has_day_1', 'has_days_2_365', 'has_row_366', 'has_row_367',
        'is_active', 'updated_at'
    ]
    list_filter = ['is_active', 'priority']
    search_fields = ['column_name', 'display_name', 'description']
    ordering = ['priority', 'column_name']
    list_editable = ['is_active', 'priority']
    list_per_page = 50
    
    fieldsets = (
        ('Column Identification', {
            'fields': ('column_name', 'display_name', 'description'),
            'description': 'column_name must match exact field name in WSData model (e.g., stromverbr, windstrom)'
        }),
        ('📅 Day 1 Formula', {
            'fields': ('formula_day_1',),
            'description': 'Formula for Day 1 ONLY. No day_prev available.\n'
                          'Example: stromverbr_raumwaerm_korr_366 * row.verbrauch_promille / 1000'
        }),
        ('📅 Days 2-365 Formula (Pattern)', {
            'fields': ('formula_days_2_365',),
            'description': 'Pattern applied to days 2-365. Use day_prev.column for previous day.\n'
                          'Example: stromverbr_raumwaerm_korr_366 * row.verbrauch_promille / 1000\n'
                          'Example with cumulative: day_prev.ladezust_burtto + row.einspeich - row.ausspeich'
        }),
        ('📊 Row 366 Formula (Annual Summary)', {
            'fields': ('formula_row_366',),
            'description': 'Annual summary formula. Use sums[\'sum_column\'] for totals.\n'
                          'Example: sums[\'sum_stromverbr\']\n'
                          'Note: This row often contains reference values that drive daily calculations.'
        }),
        ('📊 Row 367 Formula (Reference)', {
            'fields': ('formula_row_367',),
            'description': 'Reference row, often used for storage calculations.\n'
                          'Example: MIN(0, day_1.ladezust_burtto)'
        }),
        ('📊 Row 368+ Formula', {
            'fields': ('formula_row_368', 'custom_row_formulas'),
            'description': 'Additional rows. Use custom_row_formulas JSON for rows 369+.\n'
                          'JSON format: {"369": "formula", "370": "formula"}',
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'priority', 'depends_on'),
            'description': 'Priority determines calculation order (lower = first). '
                          'Use depends_on to document which columns must be calculated first.'
        }),
    )
    
    def status_icon(self, obj):
        """Show active/inactive icon"""
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 16px;">●</span>')
        return format_html('<span style="color: red; font-size: 16px;">○</span>')
    status_icon.short_description = ''
    
    def has_day_1(self, obj):
        return '✓' if obj.formula_day_1 else ''
    has_day_1.short_description = 'Day 1'
    
    def has_days_2_365(self, obj):
        return '✓' if obj.formula_days_2_365 else ''
    has_days_2_365.short_description = '2-365'
    
    def has_row_366(self, obj):
        return '✓' if obj.formula_row_366 else ''
    has_row_366.short_description = '366'
    
    def has_row_367(self, obj):
        return '✓' if obj.formula_row_367 else ''
    has_row_367.short_description = '367'
    
    actions = ['activate_templates', 'deactivate_templates', 'test_formulas', 'recalculate_all_ws']
    
    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} template(s) activated.')
    activate_templates.short_description = "✓ Activate selected templates"
    
    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'✅ {updated} template(s) deactivated.')
    deactivate_templates.short_description = "✗ Deactivate selected templates"
    
    def test_formulas(self, request, queryset):
        """Test formulas without saving - just validate syntax"""
        from simulator.ws_formula_service import get_ws_formula_evaluator
        
        evaluator = get_ws_formula_evaluator()
        evaluator.clear_cache()
        evaluator.load_ws_data()
        evaluator.calculate_sums()
        
        results = []
        for template in queryset:
            errors = []
            
            # Test each formula
            if template.formula_day_1:
                result = evaluator.evaluate_formula(template.formula_day_1, 1, template.column_name)
                if result is None:
                    errors.append("Day 1 formula failed")
                else:
                    results.append(f"{template.column_name} Day 1: {result:.2f}")
            
            if template.formula_days_2_365:
                result = evaluator.evaluate_formula(template.formula_days_2_365, 50, template.column_name)
                if result is None:
                    errors.append("Days 2-365 formula failed (tested on day 50)")
                else:
                    results.append(f"{template.column_name} Day 50: {result:.2f}")
            
            if errors:
                self.message_user(request, f"❌ {template.column_name}: {', '.join(errors)}", level='ERROR')
            else:
                self.message_user(request, f"✅ {template.column_name}: Formulas OK - {'; '.join(results)}")
                
    test_formulas.short_description = "🧪 Test selected formulas (no save)"

    def recalculate_all_ws(self, request, queryset=None):
        """
        Recalculate ALL WS data using formulas from WSFormulaTemplate.
        This can be called as an action or directly.
        """
        try:
            from simulator.ws_formula_service import recalculate_all_ws_data
            
            stats = recalculate_all_ws_data()
            
            self.message_user(
                request,
                f"✅ WS Recalculation complete! "
                f"Updated: {stats['updated']} | Errors: {stats['errors']} | Skipped: {stats['skipped']}",
                level='SUCCESS'
            )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Recalculation failed: {str(e)}",
                level='ERROR'
            )
            
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('admin:simulator_wsformulatemplate_changelist'))
        
    recalculate_all_ws.short_description = "🔄 Recalculate ALL WS Data (using formulas)"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('recalculate-all/', self.admin_site.admin_view(self.recalculate_all_ws), name='recalculate-all-ws-data'),
        ]
        return custom_urls + urls
