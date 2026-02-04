# WS Formula Conversion - Summary

## ✅ COMPLETED: Converted WS Formulas to FormulaVariable Pattern

### What Was Done
Converted all WS (Wasserstoff/Hydrogen) formulas from template-based with `row['column']` syntax to FormulaVariable-based pattern, making them consistent with Renewable and Verbrauch pages.

### The Problem
- WS formulas were using `row['column_name']` dictionary syntax
- This caused `name 'row' is not defined` errors during evaluation
- WS formulas were inconsistent with other pages (Renewable/Verbrauch)
- Template system was complex and error-prone

### The Solution
Created `convert_ws_to_formula_variables.py` script that:
1. Deleted all old WS formulas with `row[]` syntax
2. Created 29 new WS formulas using FormulaVariable entries
3. Made WS formulas work exactly like Renewable and Verbrauch pages

### Formula Breakdown
- **Daily formulas (1-365):** 19 formulas
  - WS_STROMVERBR
  - WS_DAVON_RAUMW_KORR
  - WS_STROMVERBR_RAUMWAERM_KORR
  - WS_WINDSTROM
  - WS_SOLARSTROM
  - WS_SONST_KRAFT_KONSTANT
  - WS_WIND_SOLAR_KONSTANT
  - WS_DIREKTVERBR_STROM
  - WS_UEBERSCHUSS_STROM
  - WS_EINSPEICH (fixed from row[] syntax!)
  - WS_ABREGELUNG_Z
  - WS_MANGEL_LAST
  - WS_AUSSPEICH_RUECKVERSTR
  - WS_AUSSPEICH_GAS
  - WS_BRENNSTOFF_AUSGLEICHS_STROM
  - WS_LADEZUSTAND_ABS
  - WS_LADEZUSTAND_NETTO
  - WS_LADEZUST_BURTTO
  - WS_SPEICHER_AUSGL_STROM

- **Row 366 formulas:** 7 formulas
  - WS_STROMVERBR_366
  - WS_DAVON_RAUMW_KORR_366
  - WS_STROMVERBR_RAUMWAERM_KORR_366
  - WS_WINDSTROM_366
  - WS_SOLARSTROM_366
  - WS_SONST_KRAFT_KONSTANT_366
  - WS_WIND_SOLAR_KONSTANT_366

- **Row 367 formulas:** 3 formulas
  - WS_BRENNSTOFF_AUSGLEICHS_STROM_367
  - WS_LADEZUSTAND_NETTO_367
  - WS_LADEZUST_BURTTO_367

### Key Benefits
1. **No more `row['column']` syntax errors** - All formulas use direct variable names
2. **Consistent with other pages** - Same pattern as Renewable and Verbrauch
3. **Proper dependency tracking** - FormulaVariable entries define all dependencies
4. **Row 366 and 367 included** - Special row formulas properly handled
5. **Cleaner code** - Eliminated complex template system

### How It Works Now
Each formula has:
- **Expression:** Python expression using simple variable names (e.g., `windstrom + solarstrom`)
- **FormulaVariable entries:** Define where each variable comes from
  - `ws_current_row` - Current row being calculated
  - `ws_row_366` - Annual total row (row 366)
  - `ws_previous_row` - Previous day's value
  - `renewable` - Renewable energy data
  - `verbrauch` - Consumption data

### Example: Before vs After

**Before (with row[] syntax):**
```python
expression = "(row['ueberschuss_strom'] if row['stromverbr_raumwaerm_korr'] > 0 ...)"
# Error: name 'row' is not defined
```

**After (with FormulaVariable):**
```python
expression = "(ueberschuss_strom * 0.65) if (stromverbr_raumwaerm_korr > 0 ...) else 0"

FormulaVariable:
  - ueberschuss_strom <- ws_current_row:ueberschuss_strom
  - stromverbr_raumwaerm_korr <- ws_current_row:stromverbr_raumwaerm_korr
```

### Verification
✅ All 29 WS formulas created successfully
✅ No `row[]` syntax found in any formula
✅ All formulas have proper FormulaVariable entries
✅ Row 366 and 367 formulas properly defined

### Next Steps
1. Test the balancing button in the UI
2. Verify calculations match expected values
3. Monitor for any evaluation errors

### Files Created/Modified
- `convert_ws_to_formula_variables.py` - Conversion script
- `test_ws_formula_variables.py` - Test script
- Database: 29 new Formula records + FormulaVariable entries
