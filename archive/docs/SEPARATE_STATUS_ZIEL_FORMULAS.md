# Separate Status vs Ziel/Target Formulas

## Problem

Some items have **different formulas** for:
- **Status** (current value)
- **Ziel/Target** (target value)

Example: Item 2.4.2
- **Status formula**: `2.4.1 / 2.4.1%` (current divided by percent)
- **Ziel formula**: `(2.4.1_target - 2.4.1_status) / 2.4.1_status` (change calculation)

If you use only ONE formula entry, both status and ziel will use the SAME formula, which gives incorrect results!

## Solution

Create **TWO separate Formula entries** in the admin:

### 1. Base Formula (for Status)
- **Key**: `V_2.4.2` (for VerbrauchData) or `9.2.1` (for RenewableData)
- **Expression**: Formula for calculating STATUS value
- **Example**: `Verbrauch_2_4_1 / (Verbrauch_2_4_1_percent / 100)`

### 2. Ziel/Target Formula
- **Key**: `V_2.4.2_ziel` (for VerbrauchData) or `9.2.1_target` (for RenewableData)
- **Expression**: Formula for calculating ZIEL/TARGET value
- **Example**: `(Verbrauch_2_4_1_target - Verbrauch_2_4_1_status) / Verbrauch_2_4_1_status * 100`

## Key Naming Convention

### VerbrauchData (Energy Consumption)
- **Status formula key**: `V_X.X.X` (e.g., `V_2.4.2`, `V_2.1.9`)
- **Ziel formula key**: `V_X.X.X_ziel` (e.g., `V_2.4.2_ziel`, `V_2.1.9_ziel`)
- **Important**: Use `_ziel` suffix (with underscore)

### RenewableData (Renewable Energy)
- **Status formula key**: `X.X.X` (e.g., `9.2.1`, `11.1.2`)
- **Target formula key**: `X.X.X_target` (e.g., `9.2.1_target`, `11.1.2_target`)
- **Important**: Use `_target` suffix (with underscore)

## How It Works

1. **When calculating STATUS**: System looks for base formula (e.g., `V_2.4.2`)
2. **When calculating ZIEL**: System FIRST looks for separate formula (e.g., `V_2.4.2_ziel`)
   - If found: Uses the separate formula
   - If NOT found: Falls back to base formula (same as status)

This means:
- ✅ **Same formula for both**: Create only ONE entry (base formula)
- ✅ **Different formulas**: Create TWO entries (base + _ziel/_target)

## Example: VerbrauchData 2.4.2

### If Status and Ziel use SAME formula

Create only ONE entry in admin:
```
Key: V_2.4.2
Category: verbrauch
Expression: Verbrauch_2_4_1 / (Verbrauch_2_4_1_percent / 100)
Is Active: ✓
```

Both status and ziel will use this formula.

### If Status and Ziel use DIFFERENT formulas

Create TWO entries in admin:

**Entry 1 (Status)**:
```
Key: V_2.4.2
Category: verbrauch
Expression: Verbrauch_2_4_1 / (Verbrauch_2_4_1_percent / 100)
Is Active: ✓
```

**Entry 2 (Ziel)**:
```
Key: V_2.4.2_ziel
Category: verbrauch
Expression: (Verbrauch_2_4_1_target - Verbrauch_2_4_1) / Verbrauch_2_4_1 * 100
Is Active: ✓
```

Status calculation uses first formula, ziel calculation uses second formula.

## Example: RenewableData 9.2.1

### Same formula for both

Create only ONE entry:
```
Key: 9.2.1
Category: renewable
Expression: Renewable_9_2 * Renewable_9_2_1_percent / 100
Is Active: ✓
```

### Different formulas

Create TWO entries:

**Entry 1 (Status)**:
```
Key: 9.2.1
Category: renewable
Expression: Renewable_9_2 * Renewable_9_2_1_percent / 100
Is Active: ✓
```

**Entry 2 (Target)**:
```
Key: 9.2.1_target
Category: renewable
Expression: Renewable_9_2_target * Renewable_9_2_1_target_percent / 100
Is Active: ✓
```

## Step-by-Step Guide

### Adding Separate Formulas in Admin

1. **Go to Django Admin** → **Formulas** section

2. **Add base formula** (for STATUS):
   - Click "Add Formula"
   - Key: `V_2.4.2` (or `9.2.1` for renewable)
   - Category: Select `verbrauch` or `renewable`
   - Expression: Enter formula for STATUS calculation
   - Is Fixed: Uncheck (this is a calculated value)
   - Is Active: Check
   - Save

3. **Add ziel/target formula** (if different):
   - Click "Add Formula" again
   - Key: `V_2.4.2_ziel` (or `9.2.1_target` for renewable)
   - Category: Same as above
   - Expression: Enter formula for ZIEL/TARGET calculation
   - Is Fixed: Uncheck
   - Is Active: Check
   - Save

4. **Test the calculation**:
   - Open webapp (e.g., `/verbrauch/` or `/renewable/`)
   - Click "Save & Recalculate" button
   - Verify both status and ziel values are correct

## Common Mistakes to Avoid

❌ **DON'T**: Use same key for both formulas (will overwrite)
❌ **DON'T**: Forget the underscore (`V_2.4.2ziel` ← wrong, should be `V_2.4.2_ziel`)
❌ **DON'T**: Mix up suffixes (use `_ziel` for verbrauch, `_target` for renewable)
❌ **DON'T**: Create ziel formula without base formula (status won't calculate)

✅ **DO**: Use correct suffix (`_ziel` for verbrauch, `_target` for renewable)
✅ **DO**: Create base formula first, then ziel/target formula
✅ **DO**: Test both values after creating formulas
✅ **DO**: Use "Save & Recalculate" button to update all values

## Variable Names in Formulas

When referencing other items in formulas:

### VerbrauchData
- **For status**: `Verbrauch_X_X_X` (e.g., `Verbrauch_2_4_1`)
- **For ziel**: System auto-switches to ziel values when evaluating _ziel formula

### RenewableData
- **For status**: `Renewable_X_X_X` (e.g., `Renewable_9_2_1`)
- **For target**: System auto-switches to target values when evaluating _target formula

### Example Formula with References

Status formula:
```
Verbrauch_2_4_1 / (Verbrauch_2_4_1_percent / 100)
```

When this is evaluated:
- For STATUS: Uses `Verbrauch_2_4_1.status` and `Verbrauch_2_4_1_percent.status`
- For ZIEL: Uses `Verbrauch_2_4_1.ziel` and `Verbrauch_2_4_1_percent.ziel`

Separate ziel formula:
```
(Verbrauch_2_4_1 - Verbrauch_2_4_1_status) / Verbrauch_2_4_1_status * 100
```

Can explicitly reference status values if needed in ziel formula.

## Troubleshooting

### Values not updating correctly

1. Check both formulas exist in admin (base and _ziel/_target if needed)
2. Verify Key format is correct (exact match with underscores)
3. Click "Save & Recalculate" button in webapp
4. Check Django terminal for error messages

### Status works but ziel is wrong

- Likely using same formula for both
- Create separate `_ziel` or `_target` formula entry

### Both values are wrong

- Check formula expressions for syntax errors
- Verify variable names match database codes
- Check if referenced items have values

## Summary

**To use separate formulas for status and ziel/target:**

1. **Create base formula**: Key = `V_X.X.X` or `X.X.X`
2. **Create ziel/target formula**: Key = `V_X.X.X_ziel` or `X.X.X_target`
3. **Both must have same category**
4. **Test with "Save & Recalculate" button**

This gives you full flexibility - use same formula when appropriate, different formulas when needed!
