# Row 366 Formula System - Database-Driven Configuration

## Overview

Row 366 calculations are now **fully extensible** - you can add custom formulas directly in the database without changing code!

## How It Works

The system checks for formulas with the naming pattern `WS_COLUMNNAME_366`:
- If a formula exists → Uses the formula
- If no formula exists → Uses default behavior (sum or difference)

## Adding a Row 366 Formula

### Option 1: Via Django Admin

1. Go to Django Admin → Formulas
2. Click "Add Formula"
3. Fill in:
   - **Key**: `WS_COLUMNNAME_366` (e.g., `WS_LADEZUST_BURTTO_366`)
   - **Expression**: Your formula (see examples below)
   - **Category**: `ws`
   - **Description**: What the formula does
   - **Is Active**: ✓ (checked)
4. Save

### Option 2: Via Database Script

Add to `simulator/management/commands/import_ws_formulas.py`:

```python
{'key': 'WS_LADEZUST_BURTTO_366', 
 'description': 'Row 366: Custom gross storage calculation', 
 'expression': 'day_365.ladezust_burtto - day_1.ladezust_burtto', 
 'category': 'ws'},
```

Then run:
```bash
python manage.py import_ws_formulas
```

## Formula Expressions

### Available Variables

In your formula expression, you can use:

#### Daily Row References
- `day_1` - First day (row 1)
- `day_365` - Last day (row 365)

Access any column via dot notation:
- `day_365.ladezust_burtto`
- `day_1.ladezust_burtto`
- `day_365.einspeich`
- etc.

#### Sums
- `sums['sum_stromverbr']` - Sum of daily stromverbr
- `sums['sum_windstrom']` - Sum of daily windstrom
- `sums['sum_einspeich']` - Sum of daily einspeich
- `sums['sum_abregelung_z']` - Sum of daily abregelung
- `sums['sum_mangel_last']` - Sum of daily mangel_last
- etc.

#### Reference Values
- `davon_raumw_korr_366` - From Verbrauch calculation
- `stromverbr_raumwaerm_korr_366` - From WS diagram

### Example Formulas

#### 1. Difference Formula (for cumulative columns)
```python
# LADEZUST_BURTTO - difference between last and first day
{'key': 'WS_LADEZUST_BURTTO_366',
 'expression': 'day_365.ladezust_burtto - day_1.ladezust_burtto',
 'category': 'ws'}
```

#### 2. Sum Formula
```python
# STROMVERBR - sum of all daily values
{'key': 'WS_STROMVERBR_366',
 'expression': "sums['sum_stromverbr']",
 'category': 'ws'}
```

#### 3. Custom Calculation
```python
# EINSPEICH - double the sum (example)
{'key': 'WS_EINSPEICH_366',
 'expression': "sums['sum_einspeich'] * 2",
 'category': 'ws'}
```

#### 4. Reference Value
```python
# DAVON_RAUMW_KORR - use reference value
{'key': 'WS_DAVON_RAUMW_KORR_366',
 'expression': 'davon_raumw_korr_366',
 'category': 'ws'}
```

#### 5. Complex Formula
```python
# Combine multiple sources
{'key': 'WS_CUSTOM_COLUMN_366',
 'expression': "(day_365.einspeich - day_1.einspeich) + sums['sum_stromverbr']",
 'category': 'ws'}
```

## Default Behaviors (When No Formula Exists)

| Column Type | Default Calculation | Example |
|-------------|---------------------|---------|
| **Reference Values** | From calculation | `davon_raumw_korr`, `stromverbr_raumwaerm_korr` |
| **Sums** | Sum of rows 1-365 | `stromverbr`, `windstrom`, `einspeich` |
| **Cumulative Storage** | day_365 - day_1 | `ladezust_burtto`, `ladezustand_netto` |

## Column Mapping

To add a formula for a column, use this naming:

| Database Column | Formula Key |
|-----------------|-------------|
| `stromverbr` | `WS_STROMVERBR_366` |
| `davon_raumw_korr` | `WS_DAVON_RAUMW_KORR_366` |
| `stromverbr_raumwaerm_korr` | `WS_STROMVERBR_RAUMWAERM_KORR_366` |
| `windstrom` | `WS_WINDSTROM_366` |
| `solarstrom` | `WS_SOLARSTROM_366` |
| `einspeich` | `WS_EINSPEICH_366` |
| `abregelung_z` | `WS_ABREGELUNG_Z_366` |
| `mangel_last` | `WS_MANGEL_LAST_366` |
| `ladezust_burtto` | `WS_LADEZUST_BURTTO_366` |
| `ladezustand_netto` | `WS_LADEZUSTAND_NETTO_366` |
| `ladezustand_abs` | `WS_LADEZUSTAND_ABS_366` |

## Testing Your Formula

1. Add the formula via admin or script
2. Trigger WS recalculation (e.g., save a VerbrauchData entry)
3. Check the console output for: `✓ Row 366.columnname: Using database formula 'WS_COLUMNNAME_366'`
4. Verify the value in row 366

## Troubleshooting

### Formula Not Applied
- Check that `is_active = True`
- Verify the key ends with `_366`
- Check the key starts with `WS_`
- Column name must match exactly (lowercase, underscores)

### Formula Fails
- Check console for error message: `⚠️ Row 366.columnname: Formula failed, using default`
- Verify your expression syntax
- Make sure variables exist in context

### Need More Variables?
Edit `_evaluate_row_366_formula()` in `simulator/signals.py` to add more context variables.

## Benefits

✅ **No code changes needed** - all configuration in database  
✅ **Easy to modify** - change formulas via admin panel  
✅ **Automatic fallback** - uses defaults if formula fails  
✅ **Version control** - formulas are tracked in import script  
✅ **Flexible** - support for sums, differences, custom calculations  

## Next Steps

Want to add a new formula for row 366? Just:
1. Decide which column
2. Write the expression
3. Add to database via admin or import script
4. Test!

No code changes required! 🎉
