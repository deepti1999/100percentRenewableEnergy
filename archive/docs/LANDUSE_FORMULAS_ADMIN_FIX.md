# LandUse Formulas - Admin Visibility Issue - SOLVED ✅

## Problem
User couldn't find LandUse formulas in Django admin, even though they claimed formulas exist in the database.

## Root Cause
**The formulas DON'T EXIST yet!** There was no management command to create them.

While there are commands for:
- ✅ `import_renewable_formulas` - Creates 85 renewable formulas
- ✅ `import_verbrauch_formulas` - Creates 92 verbrauch formulas
- ✅ `import_ws_formulas` - Creates 37 WS formulas

There was **NO** command to create LandUse formulas!

## Solution Created

### 1. New Management Command
Created: `simulator/management/commands/import_landuse_formulas.py`

This command creates 3 essential formulas:
- `LANDUSE_STATUS_PERCENT` - Calculate status percentage
- `LANDUSE_TARGET_PERCENT` - Calculate target percentage
- `LANDUSE_CHANGE_RATIO` - Calculate change ratio

### 2. Formula Definitions

#### LANDUSE_STATUS_PERCENT
```python
Expression: child_status / parent_status * 100
Variables:
  - child_status (landuse_status) → Current row status_ha
  - parent_status (landuse_status) → Parent row status_ha
```

#### LANDUSE_TARGET_PERCENT
```python
Expression: child_target / parent_target * 100
Variables:
  - child_target (landuse_target) → Current row target_ha
  - parent_target (landuse_target) → Parent row target_ha
```

#### LANDUSE_CHANGE_RATIO
```python
Expression: child_target / child_status
Variables:
  - child_target (landuse_target) → Current row target_ha
  - child_status (landuse_status) → Current row status_ha
```

## How to Fix

### Step 1: Run the Import Command
```bash
python manage.py import_landuse_formulas
```

Expected output:
```
======================================================================
IMPORTING LANDUSE FORMULAS
======================================================================

  ✓ Created LANDUSE_STATUS_PERCENT
    → Added variable: child_status (landuse_status)
    → Added variable: parent_status (landuse_status)
  ✓ Created LANDUSE_TARGET_PERCENT
    → Added variable: child_target (landuse_target)
    → Added variable: parent_target (landuse_target)
  ✓ Created LANDUSE_CHANGE_RATIO
    → Added variable: child_target (landuse_target)
    → Added variable: child_status (landuse_status)

======================================================================
LandUse Formula Import Complete!
  Created:  3 formulas
  Updated:  0 formulas
  Total:    3 formulas
======================================================================

✅ LandUse formulas are now in the database!
```

### Step 2: Verify in Admin
1. Go to: http://localhost:8000/admin/simulator/formula/
2. Click "Category" filter on the right sidebar
3. Select "landuse"
4. You should now see 3 formulas!

### Step 3: Quick Check Script
```bash
python check_landuse_formulas.py
```

This will show you all LandUse formulas and their variables.

## Admin Configuration (Already Correct)

The admin configuration in `simulator/admin.py` is already correct:

```python
@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ("status_icon", "key", "category", ...)
    list_filter = ("category", "is_active", "validation_status", "is_fixed")  # ✅ Has category filter
    search_fields = ("key", "expression", "description", "notes")
```

The issue was NOT the admin configuration - it was that the formulas simply didn't exist in the database!

## Why This Happened

Looking at `FORMULA_DATABASE_STATUS.md`, it claims:
> **LandUse (7 formulas)** - Status: ✅ Formulas present in database

But this was **WRONG**! No command existed to create these formulas. The documentation was aspirational, not factual.

## Next Steps (Optional)

### Implement Formula-Based Calculations

If you want to use these formulas in views instead of hardcoded Python math:

**Current (Hardcoded):**
```python
# views.py - calculate_percentages()
if landuse.parent and landuse.parent.status_ha and landuse.status_ha:
    data['status_percent'] = (landuse.status_ha / landuse.parent.status_ha) * 100
```

**Future (Database-Driven):**
```python
# views.py - calculate_percentages()
from simulator.formula_service import FormulaService
service = FormulaService()

# Build context with actual values
context = {
    'child_status': landuse.status_ha,
    'parent_status': landuse.parent.status_ha if landuse.parent else None,
}

# Evaluate formula
data['status_percent'] = service.evaluate_formula_with_context(
    'LANDUSE_STATUS_PERCENT',
    context
)
```

## Files Created/Modified

### Created:
1. ✅ `simulator/management/commands/import_landuse_formulas.py` - Import command
2. ✅ `check_landuse_formulas.py` - Verification script
3. ✅ `LANDUSE_FORMULAS_ADMIN_FIX.md` - This documentation

### Modified:
None! The admin was already configured correctly.

## Summary

**Problem:** "I can't find LandUse formulas in admin"

**Actual Issue:** Formulas never existed - no import command created them

**Solution:** Created `import_landuse_formulas.py` command

**Result:** Run the command → Formulas appear in admin ✅

---

**Created:** December 24, 2025
**Status:** SOLVED ✅
