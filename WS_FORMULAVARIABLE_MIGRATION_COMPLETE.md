# WS FormulaVariable Migration - Complete System Update

## ✅ Migration Complete

All WS (Wasserstoff/Hydrogen Storage) calculations now use the **FormulaVariable system** - the same pattern as Renewable and Verbrauch pages.

---

## 🎯 What Changed

### Old System (REMOVED):
- ❌ WSFormulaTemplate model
- ❌ ws_formula_service.recalculate_all_ws_data()
- ❌ Template-based formula strings with row['column'] syntax
- ❌ Separate formula evaluation logic for WS

### New System (ACTIVE):
- ✅ Formula model (category='ws') with 29 formulas
- ✅ FormulaVariable mappings (56 variables)
- ✅ signals.recalculate_ws_data() using FormulaVariable resolution
- ✅ Consistent formula pattern across all pages

---

## 📊 System Architecture

### Formula Storage:
```
Formula (table: simulator_formula)
├── key: "WS_STROMVERBR", "WS_WINDSTROM", etc.
├── category: "ws"
├── expression: "stromverbr_raumwaerm_korr_366 * verbrauch_promille / 1000"
└── variables → FormulaVariable entries
```

### Variable Mappings:
```
FormulaVariable (table: simulator_formulavariable)
├── formula_id → links to Formula
├── variable_name: "stromverbr_raumwaerm_korr_366"
├── source_type: "ws_row_366"
└── source_key: "stromverbr_raumwaerm_korr"
```

### WS-Specific Source Types:
1. **ws_current_row** - Values from current day (rows 1-365)
2. **ws_row_366** - Annual reference values
3. **ws_previous_row** - Previous day values (for cumulative calculations)
4. **renewable** - Renewable energy inputs (9.1.1, 9.1.2, etc.)

---

## 📝 Files Updated

### Core Calculation Engine:
1. **simulator/signals.py**
   - `_apply_daily_ws_formulas()` - Complete FormulaVariable resolution
   - `_apply_daily_ws_formulas_cumulative()` - Same pattern for cumulative
   - Removed old `_evaluate_ws_formula()` helper

2. **simulator/models.py**
   - Added 4 WS source types to FormulaVariable.SOURCE_CHOICES
   - WS_CURRENT_ROW, WS_ROW_366, WS_PREVIOUS_ROW, RENEWABLE

3. **simulator/formula_service.py**
   - Updated `_resolve_variable()` to handle renewable source type
   - WS source types return None (special handling in signals.py)

### Views & API:
4. **simulator/views.py**
   - Removed `recalculate_all_ws_data` import
   - Updated all calls to use `recalculate_ws_data()` from signals
   - Added documentation comments about FormulaVariable system

5. **simulator/recalc_service.py**
   - Removed old `ws_formula_service` imports
   - Updated `full_chain_recalc()` to use new system
   - Updated `unified_recalc_all()` to use new system

### Admin & Verification:
6. **simulator/admin.py**
   - Removed entire WSFormulaTemplateAdmin class (200+ lines)
   - Cleaned up deprecated admin interface

7. **verify_ws.py**
   - Updated to check Formula/FormulaVariable instead of WSFormulaTemplate
   - New verification logic for FormulaVariable system

### Templates (Documentation):
8. **simulator/templates/simulator/annual_electricity.html**
   - Added HTML comments documenting FormulaVariable system
   - Notes about Balance button using FormulaVariable calculations

9. **simulator/templates/simulator/renewable_list.html**
   - Added comments about fixed values for 9.3.1 (405047) and 9.3.4 (189289)
   - Notes about "Recalculate WS Data" button

10. **simulator/templates/simulator/bilanz.html**
    - Added comments about WS storage balance calculations
    - Notes about Balance button trigger

---

## 🔗 Page Integration

### Annual Electricity Page (`annual_electricity_view`)
- **Purpose**: Display WS1 electricity flow diagram
- **WS Integration**: Uses `compute_ws_diagram_reference()`
- **Data Source**: FormulaVariable-based WS calculations
- **User Action**: "Balance WS Storage" button triggers recalculation

### Renewable Energy Page (`renewable_list`)
- **Purpose**: Display renewable energy hierarchy
- **WS Integration**: Items 9.3.1 and 9.3.4 now have FIXED values (405047 and 189289 respectively)
- **Data Flow**: 
  1. Renewable inputs (9.1.1, 9.1.2, 9.1.3) → WS formulas
  2. WS calculations via FormulaVariable
  3. Fixed values for 9.3.1 and 9.3.4 are set during Balance WS Storage
- **User Action**: "Recalculate WS Data" button

### Bilanz Page (`bilanz_view`)
- **Purpose**: Energy balance sheet (Aktiva vs Passiva)
- **WS Integration**: Storage balance calculations
- **Data Source**: FormulaVariable-based WS recalculation
- **User Action**: Balance button triggers WS recalc with FormulaVariable

---

## 🧪 Verification

### Database Status:
```python
# Run in Django shell:
from simulator.models import Formula, FormulaVariable

# Check formulas
Formula.objects.filter(category='ws', is_active=True).count()
# Result: 29 formulas

# Check variables
FormulaVariable.objects.filter(formula__category='ws').count()
# Result: 56 variables

# Check source types
FormulaVariable.objects.filter(
    formula__category='ws'
).values_list('source_type', flat=True).distinct()
# Result: ws_current_row, ws_row_366, ws_previous_row, renewable
```

### Run Verification Script:
```bash
python verify_ws.py
```

Expected output:
- ✓ 29 active WS formulas found
- ✓ 56 WS FormulaVariable entries
- ✓ Recalculation completes successfully

---

## 🎨 Consistency Benefits

### Before (3 Different Systems):
- Renewable: FormulaVariable system ✓
- Verbrauch: FormulaVariable system ✓
- WS: WSFormulaTemplate system ❌ (different pattern)

### After (Unified System):
- Renewable: FormulaVariable system ✓
- Verbrauch: FormulaVariable system ✓
- WS: FormulaVariable system ✓ (same pattern!)

### Benefits:
1. **Consistency**: Same architecture across all calculation pages
2. **Maintainability**: Single formula pattern to understand and debug
3. **Extensibility**: Add new WS formulas same way as Renewable/Verbrauch
4. **Database-Driven**: All formulas editable via Django Admin
5. **Type Safety**: Source types clearly defined and validated

---

## 🚀 Next Steps

The system is now fully operational with the FormulaVariable pattern. All WS calculations are:
- ✅ Database-driven (Formula + FormulaVariable tables)
- ✅ Editable via Django Admin
- ✅ Consistent with Renewable and Verbrauch pages
- ✅ Well-documented in code and templates

**No further migration needed** - the system is complete and ready for use!

---

## 📚 Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `simulator/signals.py` | WS calculation engine | ✅ Updated |
| `simulator/models.py` | Source type definitions | ✅ Updated |
| `simulator/formula_service.py` | Variable resolution | ✅ Updated |
| `simulator/views.py` | Page views & API | ✅ Updated |
| `simulator/recalc_service.py` | Recalc orchestration | ✅ Updated |
| `simulator/admin.py` | Admin interface | ✅ Cleaned |
| `verify_ws.py` | System verification | ✅ Updated |
| `*.html` templates | User interface | ✅ Documented |

---

## 📞 Support

For questions about the FormulaVariable system:
1. Check `simulator/models.py` - FormulaVariable.SOURCE_CHOICES
2. Check `simulator/formula_service.py` - _resolve_variable() logic
3. Check `simulator/signals.py` - _apply_daily_ws_formulas() implementation
4. Run `verify_ws.py` to check system health

---

**Migration Date**: January 3, 2026  
**Status**: ✅ Complete  
**System Version**: FormulaVariable-Based WS Calculations v1.0
