# ✅ 100% EXTENSIBLE Row 366/367 Formula System - Complete Guide

## 🎯 Summary: Is It Fully Extensible?

### ✅ YES - You Can NOW:

1. **Add formula for ANY row 366 column** - via database, no code changes
2. **Modify existing formulas** - changes reflected immediately
3. **Add formulas for NEW columns** - even columns not in the hardcoded defaults
4. **Changes take effect immediately** - on next WS recalculation

### ⚠️ Limitations:

1. **Adding entirely NEW WS columns** - requires model changes (Django migration)
2. **Formula complexity** - limited to basic math operations (no complex functions yet)
3. **Must trigger recalculation** - changes apply on next WS data save

---

## 📋 How to Add/Modify Row 366 Formulas

### Method 1: Django Admin (Easiest)

```
1. Go to: http://localhost:8000/admin/
2. Navigate to: Simulator → Formulas
3. Click: "Add Formula" or edit existing
4. Fill in:
   - Key: WS_COLUMNNAME_366 (e.g., WS_STROMVERBR_366)
   - Expression: Your formula (see examples below)
   - Description: What it does
   - Category: ws
   - Is Active: ✓ (checked)
5. Save
6. Trigger WS recalculation (save any Verbrauch entry)
7. Done! ✓
```

### Method 2: Django Shell (Programmatic)

```bash
python3 manage.py shell
```

```python
from simulator.models import Formula

# Add NEW formula
Formula.objects.create(
    key='WS_CUSTOM_COLUMN_366',
    expression='day_365.einspeich - day_1.einspeich',
    description='Custom: Net change in storage charge',
    category='ws',
    is_active=True
)

# Modify EXISTING formula
f = Formula.objects.get(key='WS_STROMVERBR_366')
f.expression = "sums['sum_stromverbr'] * 1.1"  # Add 10%
f.save()

# Disable a formula (without deleting)
f = Formula.objects.get(key='WS_EINSPEICH_366')
f.is_active = False
f.save()
```

### Method 3: Import Script (Bulk Operations)

Edit [simulator/management/commands/import_ws_formulas.py](simulator/management/commands/import_ws_formulas.py):

```python
ws_formulas = [
    # ... existing formulas ...
    
    # Add your new formula here
    {'key': 'WS_MY_CUSTOM_366', 
     'description': 'My custom calculation', 
     'expression': 'day_365.custom_field - day_1.custom_field', 
     'category': 'ws'},
]
```

Run:
```bash
python3 manage.py import_ws_formulas
```

---

## 📝 Formula Expression Syntax

### Supported Expressions

#### 1. Sum References
```python
Expression: "sums['sum_stromverbr']"
# Uses the sum of daily stromverbr values (rows 1-365)
```

#### 2. Day Differences (ANY column!)
```python
Expression: "day_365.ladezust_burtto - day_1.ladezust_burtto"
# End of year minus start of year
# Works for ANY column in WSData model!
```

#### 3. Reference Values
```python
Expression: "davon_raumw_korr_366"
# Uses a reference value from calculations
```

#### 4. Math Operations
```python
Expression: "sums['sum_einspeich'] * 1.1"
# Multiply by 110%

Expression: "day_365.stromverbr - day_1.stromverbr + 100"
# Difference plus constant

Expression: "(sums['sum_windstrom'] + sums['sum_solarstrom']) / 2"
# Average of two sums
```

#### 5. Literal Values
```python
Expression: "0"
# Fixed value
```

### Available Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `sums['sum_columnname']` | Sum of daily values | `sums['sum_stromverbr']` |
| `day_1.columnname` | Start of year value | `day_1.ladezust_burtto` |
| `day_365.columnname` | End of year value | `day_365.ladezust_burtto` |
| `davon_raumw_korr_366` | Reference from Verbrauch | `davon_raumw_korr_366` |
| `stromverbr_raumwaerm_korr_366` | Reference from WS diagram | `stromverbr_raumwaerm_korr_366` |

**✅ IMPORTANT**: `day_1.columnname` and `day_365.columnname` work for **ANY column** in the WSData model - not just the hardcoded ones!

---

## 🔄 When Do Changes Take Effect?

### Immediate in Database
```python
# Change is saved to database INSTANTLY
f = Formula.objects.get(key='WS_STROMVERBR_366')
f.expression = "new expression"
f.save()  # ← Database updated immediately
```

### Applied on Next Calculation
Changes are **applied** when WS data is recalculated:

**Triggers**:
- Saving VerbrauchData entry
- Saving RenewableData entry
- Running `python3 manage.py calculate_ws` (if exists)
- Any signal that calls `recalculate_ws_data()`

**Watch Console For**:
```
✓ Row 366.stromverbr: Using database formula 'WS_STROMVERBR_366' = 123456.78
✓ Row 366.custom_field: Using database formula 'WS_CUSTOM_FIELD_366' = 999.99
```

---

## 📊 Examples

### Example 1: Add 10% Buffer to Einspeich
```python
from simulator.models import Formula

f = Formula.objects.get(key='WS_EINSPEICH_366')
f.expression = "sums['sum_einspeich'] * 1.1"
f.save()
```

### Example 2: Custom Net Change Column
```python
Formula.objects.create(
    key='WS_NET_GENERATION_366',
    expression='day_365.wind_solar_konstant - day_1.wind_solar_konstant',
    description='Net change in total generation',
    category='ws',
    is_active=True
)
```

### Example 3: Combined Formula
```python
Formula.objects.create(
    key='WS_TOTAL_SURPLUS_366',
    expression="(sums['sum_ueberschuss'] + sums['sum_abregelung_z'])",
    description='Total surplus + curtailment',
    category='ws',
    is_active=True
)
```

### Example 4: Disable Formula (Use Default Instead)
```python
f = Formula.objects.get(key='WS_STROMVERBR_366')
f.is_active = False  # System will use default (sum)
f.save()
```

---

## ❓ FAQ

### Q: Can I add a formula for a column that doesn't exist in column_defaults?
**A: YES!** The system is now 100% extensible. Add formula for ANY column.

### Q: What happens if my formula fails?
**A:** System falls back to default if available, or skips the column.

### Q: Can I add a completely new column to WS?
**A:** Adding a new **database field** requires:
1. Edit [simulator/ws_models.py](simulator/ws_models.py)
2. Add field: `new_column = models.FloatField(...)`
3. Run migration: `python3 manage.py makemigrations && python3 manage.py migrate`
4. Add formula: Via admin or shell
5. Add sum calculation: Edit signals.py to include in sums dict

### Q: How do I test my formula without affecting production?
**A:** 
```python
# Set is_active = False initially
Formula.objects.create(
    key='WS_TEST_366',
    expression='your test formula',
    category='ws',
    is_active=False  # Won't be applied
)

# Test it
f = Formula.objects.get(key='WS_TEST_366')
f.is_active = True  # Enable for testing
f.save()

# Disable if needed
f.is_active = False
f.save()
```

### Q: Can I use formulas from other tables (Renewable, Verbrauch)?
**A:** Not directly in row 366 formulas. Those are for reference values only (davon_raumw_korr_366, stromverbr_raumwaerm_korr_366).

---

## 🎯 What's Fully Extensible vs. What Needs Code

### ✅ 100% Extensible (No Code Changes)

- Add row 366 formula for **any existing column**
- Modify any formula expression
- Enable/disable formulas
- Add row 367 formulas
- Use any column in day_1.column or day_365.column expressions

### ⚠️ Requires Code Changes

- Add **new database columns** to WSData model → Need migration
- Add new **sum calculations** → Need to edit signals.py
- Support complex functions (sin, cos, IF, etc.) → Need to enhance evaluator
- Reference other tables directly → Need to extend context

---

## 🚀 Best Practices

1. **Test formulas before enabling**
   - Create with `is_active=False`
   - Test the expression syntax
   - Enable when ready

2. **Use descriptive keys**
   - `WS_TOTAL_SURPLUS_366` ✓
   - `WS_FORMULA1_366` ✗

3. **Add notes**
   - Document what the formula does
   - Explain any magic numbers

4. **Version control**
   - Keep import script updated
   - Document formula changes

5. **Monitor console output**
   - Watch for formula evaluation errors
   - Check if formulas are being applied

---

## ✅ Summary

**YES, the system is now 100% extensible for row 366 and 367 formulas!**

You can:
- ✅ Add formulas via Django admin (immediate effect on next calculation)
- ✅ Modify formulas via shell or admin (changes saved to database)
- ✅ Use ANY column in formulas (not limited to hardcoded list)
- ✅ Add custom calculations without touching code
- ✅ Enable/disable formulas dynamically

Only limitation:
- ⚠️ Adding **new database columns** requires migration (normal Django process)
- ⚠️ Adding **new sum calculations** requires editing signals.py

**For row 366/367 formulas on existing columns: 100% database-driven! 🎉**
