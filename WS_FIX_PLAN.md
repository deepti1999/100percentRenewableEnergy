# WS Formula System - Current Status and Fix Plan

## Current Situation

### ✅ What's Done
1. **Database formulas converted** - All 29 WS formulas now use FormulaVariable entries
2. **No row[] syntax** - All formulas use direct variable names
3. **FormulaVariable entries created** - Proper source tracking (ws_current_row, ws_row_366, etc.)

### ❌ What's Broken
The balance button calls still use the OLD evaluation system that doesn't know about FormulaVariable:

**In signals.py:**
- `_apply_daily_ws_formulas()` - Calls `_evaluate_ws_formula()` with plain dict context
- `_apply_row_366_formulas()` - Same issue
- `_evaluate_ws_formula()` - Doesn't resolve FormulaVariable entries

**The Problem:**
The evaluation code passes a simple dict with values, but doesn't resolve FormulaVariable entries like:
- `ws_current_row` - Should get value from current WSData row being calculated
- `ws_row_366` - Should get value from row 366
- `ws_previous_row` - Should get value from previous day
- `renewable` - Should get value from RenewableData

## The Fix

We need to create a new WS formula evaluator that properly resolves FormulaVariable entries, similar to how Renewable and Verbrauch formulas work.

### Option 1: Use FormulaService Directly
Modify the WS recalculation to use `FormulaService.evaluate_formula()` which already handles FormulaVariable resolution.

### Option 2: Create WS-Specific Evaluator  
Create `WSFormulaService` that extends/wraps FormulaService with WS-specific source type handlers.

### Recommended: Option 1 (Simpler)
Update `_apply_daily_ws_formulas()` to:
1. Get Formula object from database (already has FormulaVariable entries)
2. Call FormulaService.evaluate_formula() with proper context
3. FormulaService will automatically resolve all FormulaVariable entries

## Implementation Steps

1. Update `_apply_daily_ws_formulas()` to use FormulaService
2. Add WS source type handlers to FormulaService:
   - `ws_current_row` - Get from current row being processed
   - `ws_row_366` - Get from row 366
   - `ws_previous_row` - Get from previous row
3. Update `_apply_row_366_formulas()` similarly
4. Remove old `_evaluate_ws_formula()` function

## Source Type Mapping

```python
source_type='ws_current_row', source_key='stromverbr'
→ Get stromverbr from current WSData row being processed

source_type='ws_row_366', source_key='windstrom'  
→ Get windstrom from WSData.objects.get(tag_im_jahr=366)

source_type='ws_previous_row', source_key='ladezustand_netto'
→ Get ladezustand_netto from previous day's row

source_type='renewable', source_key='9.1'
→ Get target_value from RenewableData.objects.get(code='9.1')
```

This will make WS formulas work exactly like Renewable and Verbrauch formulas!
