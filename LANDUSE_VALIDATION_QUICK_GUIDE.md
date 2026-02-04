# Land Use Validation - Quick Configuration Guide

## Current Setting
**Maximum Increase: 3 percentage points**

This means:
- If current land use = 10%, maximum allowed = 13% (10% + 3 points)
- If current land use = 20%, maximum allowed = 23% (20% + 3 points)
- If current land use = 50%, maximum allowed = 53% (50% + 3 points)

---

## How to Change the Limit

### Option 1: Set to 5 points (Allow Slightly More)
Edit `landuse_project/settings.py`, line 156:
```python
LANDUSE_MAX_INCREASE_PERCENT = 5  # Can increase by 5 percentage points
```

**Effect:**
- Current 10% → Max allowed: 15%
- Current 20% → Max allowed: 25%

---

### Option 2: Set to 10 points (More Flexible)
```python
LANDUSE_MAX_INCREASE_PERCENT = 10  # Can increase by 10 percentage points
```

**Effect:**
- Current 10% → Max allowed: 20%
- Current 20% → Max allowed: 30%

---

### Option 3: Set to 20 points (Very Flexible)
```python
LANDUSE_MAX_INCREASE_PERCENT = 20  # Can increase by 20 percentage points
```

**Effect:**
- Current 10% → Max allowed: 30%
- Current 20% → Max allowed: 40%

---

### Option 4: Disable Validation (No Limit)
```python
LANDUSE_MAX_INCREASE_PERCENT = 999999  # Effectively unlimited
```

**Effect:**
- Any increase allowed (not recommended for production)

---

## Testing Your Changes

### Step 1: Edit Settings
1. Open `landuse_project/settings.py`
2. Find line ~156: `LANDUSE_MAX_INCREASE_PERCENT = 3`
3. Change the value
4. Save the file

### Step 2: Restart Server
```bash
# Stop current server (Ctrl+C)
# Start again
python3 manage.py runserver
```

### Step 3: Test in Browser
1. Go to http://127.0.0.1:8000/landuse/
2. Find any land use entry with a percentage (e.g., 10%)
3. Try to increase it by more than 3% (e.g., to 10.5%)
4. You should see the validation message

---

## Examples by Use Case

### Academic/Research (VERY Strict - CURRENT)
```python
LANDUSE_MAX_INCREASE_PERCENT = 3
```
Use when: You want to enforce minimal, realistic changes only

### Production (Strict Control)
```python
LANDUSE_MAX_INCREASE_PERCENT = 10
```
Use when: You want to allow small changes but prevent large errors

### Development/Testing (Moderate)
```python
LANDUSE_MAX_INCREASE_PERCENT = 50
```
Use when: You're testing scenarios and need some freedom

### Demo/Sandbox (Very Flexible)
```python
LANDUSE_MAX_INCREASE_PERCENT = 999999
```
Use when: You want no restrictions (not recommended for real data)

---

## What Happens When Validation Triggers?

**User sees:**
```
⚠️ Cannot increase land use by more than 3 percentage points.

Current: 10.00%
Requested: 14.00%
Increase: 4.00 percentage points
Maximum allowed: 13.00%

Please increase gradually to maintain realistic land use changes.
```

**System does:**
1. Rejects the change (no database update)
2. Shows error message
3. Automatically reverts input field to maximum allowed value
4. Highlights field in orange for 3 seconds
5. User can immediately try again with correct value

**No data loss** - Everything stays safe! ✅
