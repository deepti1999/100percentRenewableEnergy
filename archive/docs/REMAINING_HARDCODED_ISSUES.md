# REMAINING HARDCODED ISSUES - Complete Analysis
## Date: 2025-12-12

## 🚨 CRITICAL: System is NOT 100% Extensible Yet

Despite recent cleanup, the system still has **MAJOR hardcoded dependencies**:

---

## 1. ❌ Formula Service Python Fallbacks

**File:** `simulator/formula_service.py`

**Problem:**
```python
def _load_python_formulas(self, category):
    # Falls back to Python files when DB is empty
    from renewable_energy_complete_formulas import RENEWABLE_FORMULAS
    return RENEWABLE_FORMULAS  # ❌ HARDCODED FALLBACK
```

**Impact:** Calculations use Python files instead of database

**Fix Required:** Remove `_load_python_formulas()` entirely, raise error if DB empty

---

## 2. ❌ Renewable Engine Hardcoded Formulas

**File:** `calculation_engine/renewable_engine.py`

**Problem:**
```python
RENEWABLE_FORMULAS = {
    '1': {'name': 'Solarenergie', 'formula': None, 'is_fixed': True},
    '1.1': {'name': 'Solare Dachflächen', ...},
    # ... 100+ hardcoded formulas
}
```

**Impact:** Entire renewable calculation system has hardcoded formula dict

**Fix Required:** Delete RENEWABLE_FORMULAS dict, use ONLY database

---

## 3. ❌ Verbrauch Calculations (2,678 lines of hardcoded formulas!)

**File:** `simulator/verbrauch_calculations.py`

**Problem:**
```python
def calculate_value_method(self):
    if self.code == "1.1.1.1":
        return base_1_1.status * (percent_1_1_1.status / 100.0)
    elif self.code == "1.1.1.3":
        return ...
    # ... THOUSANDS of lines of hardcoded formulas
    elif self.code == "2.1.2":
        return 100.0  # ❌ HARDCODED CONSTANT
```

**Impact:** ALL Verbrauch calculations are hardcoded, not database-driven

**Fix Required:** 
- Migrate ALL formulas to Formula + FormulaVariable tables
- Delete verbrauch_calculations.py entirely
- Make VerbrauchCalculator fail if DB formula missing

---

## 4. ❌ WS Data Hardcoded Constants & Math

**Files:** 
- `simulator/signals.py:recalculate_ws_data()`
- `calculation_engine/ws_engine.py`

**Problem:**
```python
# Hardcoded efficiency constants
t_output = ws_row_366.ausspeich_rueckverstr * 0.585  # ❌ HARDCODED
gas_storage = n_output_branch * 0.65  # ❌ HARDCODED

# Hardcoded storage capacity
storage_capacity_MWh = 160 * 1000  # ❌ HARDCODED

# Hardcoded daily calculations
for day_idx in range(365):
    # ... procedural math, not DB formulas
```

**Impact:** 
- Row 366/367 use DB formulas
- Daily rows (1-365) use hardcoded math
- Storage logic hardcoded
- Missing formulas → fields set to 0 (masking errors)

**Fix Required:**
- Move 0.585, 0.65, 160 to database as Formula constants
- Convert daily WS calculations to DB formulas
- Delete procedural math in signals.py

---

## 5. ❌ Annual Electricity View Hardcoded

**File:** `simulator/views.py:annual_electricity_view()`

**Problem:**
```python
# Hardcoded constants
t_output = ws_row_366.ausspeich_rueckverstr * 0.585  # ❌
gas_storage = n_output_branch * 0.65  # ❌

# Hardcoded fallback
if ws_row_366.ausspeich_rueckverstr is not None:
    t_output = ws_row_366.ausspeich_rueckverstr * 0.585
else:
    t_output = t_value * 0.585  # ❌ FALLBACK
```

**Impact:** Annual Electricity page uses hardcoded logic, not DB formulas

**Fix Required:** 
- Store constants in database
- Remove fallback logic
- Use ONLY database formulas

---

## 6. ❌ LandUse Percentages Hardcoded

**File:** `simulator/views.py:landuse_list()`

**Problem:**
```python
def calculate_percentages(items):
    # Hardcoded percentage calculation in view
    for item in items:
        if item.parent:
            item.status_percent = (item.status_ha / item.parent.status_ha) * 100
            # ❌ NOT DATABASE-DRIVEN
```

**Impact:** LandUse percentages computed in code, not from DB formulas

**Fix Required:**
- Create Formula entries for all LandUse percentage calculations
- Delete calculate_percentages() function
- Make view use ONLY database formulas

---

## 7. ❌ Bilanz/Cockpit Use Stored Values

**File:** `calculation_engine/bilanz_engine.py`

**Problem:**
```python
def calculate_bilanz_data(scenario='status'):
    # Uses stored values WITHOUT enforcing DB formulas
    renewable = RenewableData.objects.get(code='1.1.2.1.2')
    value = renewable.status_value  # ❌ May be stale/None
```

**Impact:** Bilanz/Cockpit show stored values even if formulas missing

**Fix Required:**
- Force recalculation from DB formulas before displaying
- Raise error if formula missing

---

## 📊 Page-by-Page Issues

### LandUse Page
- ❌ Uses `calculate_percentages()` - hardcoded math
- ❌ Formulas optional via `_apply_formula_overrides()`
- ❌ Missing formulas → blank values shown

### Renewable Page
- ❌ Falls back to Python RENEWABLE_FORMULAS dict
- ❌ Missing DB formulas → uses stored values or None

### Verbrauch Page
- ❌ Uses verbrauch_calculations.py (2,678 lines hardcoded)
- ❌ Missing DB formulas → VerbrauchCalculator returns (None, None)
- ❌ Page shows None for is_calculated items without DB formulas

### Annual Electricity Page
- ❌ Hardcoded constants (0.585, 0.65, 160)
- ❌ Fallback to renewable values if WS 366 missing
- ❌ Procedural flow calculations not in DB

### WS Page
- ✅ Row 366/367 use DB formulas (GOOD!)
- ❌ Daily rows (1-365) use hardcoded math
- ❌ Storage logic hardcoded
- ❌ Missing formulas → 0 values (masks errors)

### Bilanz/Cockpit
- ❌ Uses stored values without DB formula enforcement
- ❌ Will show stale/None values if formulas missing

---

## 🎯 Required Actions for TRUE 100% Extensibility

### Phase 1: Remove All Python Formula Fallbacks
1. ✅ Delete `_load_python_formulas()` from formula_service.py
2. ✅ Delete RENEWABLE_FORMULAS dict from renewable_engine.py
3. ✅ Make FormulaService raise error if DB empty

### Phase 2: Migrate Verbrauch to Database
1. ✅ Extract all formulas from verbrauch_calculations.py
2. ✅ Import into Formula + FormulaVariable tables
3. ✅ Delete verbrauch_calculations.py
4. ✅ Make VerbrauchCalculator fail if formula missing

### Phase 3: Move WS Constants to Database
1. ✅ Create Formula entries for: ELY_EFFICIENCY (0.65), RUECKVERSTR_EFFICIENCY (0.585), STORAGE_CAPACITY (160)
2. ✅ Update signals.py to load from DB
3. ✅ Delete hardcoded constants

### Phase 4: Convert WS Daily Calculations
1. ✅ Create Formula entries for daily WS calculations
2. ✅ Update ws_engine.py to use DB formulas only
3. ✅ Delete procedural math

### Phase 5: Fix Annual Electricity View
1. ✅ Use DB constants instead of hardcoded
2. ✅ Remove fallback logic
3. ✅ Fail explicitly if data missing

### Phase 6: Database-Driven LandUse
1. ✅ Create Formula entries for percentage calculations
2. ✅ Delete calculate_percentages()
3. ✅ Make formulas mandatory, not optional

### Phase 7: Enforce Formulas in Bilanz/Cockpit
1. ✅ Trigger recalculation before display
2. ✅ Raise error if formulas missing

---

## 🚀 Starting Implementation

Let me begin systematically removing ALL hardcoded dependencies...
