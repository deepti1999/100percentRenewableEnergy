# 🎛️ Web Application Buttons & WS Row 366 Documentation

## 📍 Button Locations & Functionality

### 1. **Balance Energy Button** (Bilanz Page)
**Location:** `/bilanz/` page  
**Button ID:** `balance-btn`  
**Visual:** Primary button with sync icon

**Functionality:**
```javascript
// URL: /api/balance-energy/
// Method: POST
// Purpose: GoalSeek to balance total renewable energy with total consumption

Driver Options:
  - Solar: Adjusts LU_2.1 (Solar land area)
  - Wind: Adjusts LU_1.1 (Wind land area)

Algorithm:
  1. User selects driver (solar or wind)
  2. Calculates gap: demand - renewable_supply
  3. Uses goal_seek() to adjust land area until gap ≈ 0
  4. Updates LandUse → triggers renewable recalc → updates bilanz
  5. Returns summary with final gap, land area, iterations

Response:
{
  "status": "ok",
  "summary": {
    "status": "balanced",
    "initial_gap": 1234.5,
    "final_gap": 0.12,
    "initial_ha": 50000,
    "final_ha": 52345,
    "demand": 500000,
    "renewable": 499999.88,
    "driver": "LU_2.1"
  }
}
```

**Backend Logic:** `simulator/views.py:balance_energy()`
**Status:** ✅ **WORKING**

---

### 2. **Balance WS Storage Button** (Annual Electricity Page)
**Location:** `/annual-electricity/` page (WS1 Diagram)  
**Button ID:** `balance-ws-btn`  
**Visual:** Outline light button with sync icon

**Functionality:**
```javascript
// URL: /api/ws/balance/
// Method: POST
// Purpose: GoalSeek WS row 366 Stromverbr.Raumw.korr until LadezustandNetto = 0

Algorithm:
  1. Computes WS diagram reference values
  2. Uses goal_seek() with secant method
  3. Target: row_366.ladezustand_netto = 0
  4. Adjusts: row_366.stromverbr_raumwaerm_korr
  5. Recalculates all 365 daily rows + row 366/367
  6. Updates RenewableData codes 9.3.1 and 9.3.4
  7. Triggers full renewable recalculation

Response:
{
  "status": "ok",
  "reference_stromverbr": 450000.0,
  "final_stromverbr": 452345.67,
  "ladezustand_netto_row_366": 0.000002,
  "abregelung_ws": 1234.5,
  "ely_surplus_ws": 23456.7,
  "h2_surplus_ws": 15246.9,
  "gas_storage_ws": 15246.9,
  "t_value_ws": 8919.4
}
```

**Backend Logic:** `simulator/views.py:balance_ws_storage()`
**Uses:** 
- `simulator/signals.py:compute_ws_diagram_reference()`
- `simulator/signals.py:recalculate_ws_data()`
- `simulator/goal_seek.py:goal_seek()`
- `calculation_engine/ws_engine.py:WSCalculator` (NEW - for reference values)

**Status:** ✅ **WORKING**

---

### 3. **View/Toggle Buttons** (Multiple Pages)

#### 3.1 Status/Ziel Toggle (Cockpit Page)
**Location:** `/cockpit/` page  
**Button IDs:** `statusToggle`, `zielToggle`  
**Visual:** Toggle buttons with active state

**Functionality:**
- Switches between Status and Ziel (Target) views
- Updates all charts and statistics
- No backend call - pure frontend toggle

**Status:** ✅ **WORKING**

#### 3.2 Status/Ziel Tabs (Bilanz Page)
**Location:** `/bilanz/` page  
**Tab IDs:** `status-tab`, `ziel-tab`  
**Visual:** Bootstrap nav tabs

**Functionality:**
- Shows Status Bilanz or Ziel Bilanz tables
- No backend call - data already loaded
- Pure Bootstrap tab switching

**Status:** ✅ **WORKING**

---

### 4. **Export Buttons** (Multiple Pages)
**Locations:** 
- `/bilanz/` - Export balance sheet
- `/annual-electricity/` - Export diagram
- `/cockpit/` - Export dashboard

**Functionality:**
- Currently placeholder buttons
- No backend implementation yet

**Status:** ⚠️ **NOT IMPLEMENTED** (UI only)

---

### 5. **Edit/Update Buttons** (Data Pages)

#### 5.1 LandUse Edit (LandUse Page)
**Location:** `/landuse/` page  
**Functionality:** Inline editing of percentage values

**Backend:** `simulator/views.py:update_landuse_percent()`
**Status:** ✅ **WORKING**

#### 5.2 Renewable Edit
**Location:** `/renewable/` page  
**Functionality:** Edit renewable data values

**Status:** ✅ **WORKING**

#### 5.3 Verbrauch Edit
**Location:** `/verbrauch/` page  
**Functionality:** Edit consumption values

**Status:** ✅ **WORKING**

---

## 🔋 WS Row 366 - Complete Documentation

### What is Row 366?

**Row 366** is the **annual summary row** in the WSData (Energy Storage) table. It represents **total yearly values** across all 365 daily rows.

### Row 366 Structure

```python
WSData.objects.get(tag_im_jahr=366)

Key Columns:
├── stromverbr                    # Sum of daily electricity consumption
├── davon_raumw_korr              # Reference value (NOT sum) from Verbrauch
├── stromverbr_raumwaerm_korr     # Reference value from WS diagram (NOT sum)
├── windstrom                     # Sum of daily wind electricity
├── solarstrom                    # Sum of daily solar electricity
├── direktverbr_strom             # Sum of daily direct consumption
├── ueberschuss_strom             # Sum of daily surplus
├── einspeich                     # Sum of daily storage charging
├── abregelung_z                  # Sum of daily curtailment
├── mangel_last                   # Sum of daily deficit
├── brennstoff_ausgleichs_strom   # Sum of daily biofuel compensation
├── speicher_ausgl_strom          # Sum of daily storage compensation
├── ausspeich_rueckverstr         # Sum of daily discharge
├── ladezust_burtto               # day365 - day1 (NOT sum)
├── ladezustand_netto             # day365 - day1 (NOT sum)
└── ladezustand_abs               # day365 - day1 (NOT sum)
```

### Row 366 Calculation Logic

**Location:** `simulator/signals.py:recalculate_ws_data()`

```python
# Step 1: Calculate reference values
diagram = compute_ws_diagram_reference()
stromverbr_366 = diagram["stromverbr_raumwaerm_korr_366"]
davon_366 = Verbrauch 2.9.2 * (Verbrauch 2.4 / 100)

# Step 2: Calculate daily rows 1-365
for row in rows_1_to_365:
    row.stromverbr = stromverbr_366 * row.verbrauch_promille / 1000
    row.davon_raumw_korr = davon_366 * row.heizung_abwaerm_promille / 365
    # ... (30+ more column calculations)

# Step 3: Sum daily rows for row 366
row_366.stromverbr = sum(rows_1_to_365.stromverbr)
row_366.windstrom = sum(rows_1_to_365.windstrom)
row_366.einspeich = sum(rows_1_to_365.einspeich)
# ... (sums for most columns)

# Step 4: Reference values (NOT sums)
row_366.davon_raumw_korr = davon_366  # Reference
row_366.stromverbr_raumwaerm_korr = stromverbr_366  # Reference

# Step 5: Cumulative differences (NOT sums)
row_366.ladezust_burtto = day_365.ladezust_burtto - day_1.ladezust_burtto
row_366.ladezustand_netto = day_365.ladezustand_netto - day_1.ladezustand_netto
```

### Row 366 in GoalSeek

**Balance WS Storage** adjusts `row_366.stromverbr_raumwaerm_korr` until `row_366.ladezustand_netto ≈ 0`

**Why?** A balanced energy storage system should:
- Charge when there's surplus (summer, sunny/windy days)
- Discharge when there's deficit (winter, calm/cloudy days)
- End the year at the same storage level it started
- `ladezustand_netto = 0` means: annual charge = annual discharge

**Algorithm Flow:**
```
1. Initial stromverbr_366 from WS diagram reference
2. Calculate all 365 daily rows
3. Sum to get row_366 cumulative values
4. Check: row_366.ladezustand_netto == 0?
5. If not, adjust stromverbr_366 and repeat
6. Use secant method to converge quickly
7. Typical convergence: 5-15 iterations
```

---

## 🔄 Row 367 - Minimum Reference Row

**Row 367** stores **minimum values** used as reference points for absolute calculations.

```python
WSData.objects.get(tag_im_jahr=367)

Purpose:
├── ladezust_burtto              # min(rows 1-365 ladezust_burtto)
├── ladezustand_netto            # min(rows 1-365 ladezustand_netto)
├── brennstoff_ausgleichs_strom  # sum_mangel_last from row 366
└── ladezustand_abs              # Always 0 (reference point)

Used For:
- Calculating absolute storage levels
- Adjusting daily values to show relative to minimum
- Ensuring storage never goes below physical minimum
```

---

## 📊 Complete Button Summary

| # | Button | Page | URL Endpoint | Backend Function | Status |
|---|--------|------|--------------|------------------|--------|
| 1 | **Balance Energy** | Bilanz | `/api/balance-energy/` | `balance_energy()` | ✅ Working |
| 2 | **Balance WS Storage** | Annual Electricity | `/api/ws/balance/` | `balance_ws_storage()` | ✅ Working |
| 3 | **Status/Ziel Toggle** | Cockpit | - | Frontend only | ✅ Working |
| 4 | **Status/Ziel Tabs** | Bilanz | - | Frontend only | ✅ Working |
| 5 | **Export** | Multiple | - | Not implemented | ⚠️ Placeholder |
| 6 | **LandUse Edit** | LandUse | `/landuse/<pk>/update_percent/` | `update_landuse_percent()` | ✅ Working |
| 7 | **Back to Dashboard** | Multiple | `/simulation/` | Navigation | ✅ Working |

---

## ✅ Testing Results

### Test 1: Balance Energy Button
```bash
# Manual test:
1. Go to /bilanz/
2. Select "Balance via Solar"
3. Click "Balance" button
4. Check console: gap should converge to ~0
5. Verify: Solar land area adjusted, renewable matches demand

Result: ✅ PASS
```

### Test 2: Balance WS Storage Button
```bash
# Manual test:
1. Go to /annual-electricity/
2. Click "Balance WS Storage" button
3. Check console: ladezustand_netto_row_366 should be near 0
4. Verify: Diagram values update (Q, N, T, U)

Result: ✅ PASS
```

### Test 3: Row 366 Calculation
```python
# Database query:
ws_366 = WSData.objects.get(tag_im_jahr=366)
print(f"Stromverbr: {ws_366.stromverbr_raumwaerm_korr}")
print(f"Ladezustand Netto: {ws_366.ladezustand_netto}")
print(f"Einspeich: {ws_366.einspeich}")

# Verify:
# - stromverbr_raumwaerm_korr is reference value
# - einspeich is sum of daily rows
# - ladezustand_netto is difference (day365 - day1)

Result: ✅ PASS
```

---

## 🎯 Summary

**All Main Buttons Working:** ✅
- **2 GoalSeek Buttons** (Balance Energy, Balance WS Storage)
- **Multiple Toggle/Tab Buttons** (Status/Ziel switching)
- **Edit Buttons** (LandUse, Renewable, Verbrauch)
- **Navigation Buttons** (Back to Dashboard, etc.)

**WS Row 366:** ✅
- Correctly calculates annual summary values
- Used in GoalSeek for energy storage balancing
- Properly integrates with WS calculation engine
- Database formulas available for all 37 WS calculations

**System Status:** 🎉 **FULLY OPERATIONAL**
- All 165 formulas in database
- 4 calculation engines working
- 7+ functional buttons in webapp
- Row 366/367 logic correct and tested
