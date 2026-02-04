# 📘 COMPLETE GUIDE: Add & Modify Renewable Sources

## ✅ YES! You can add ANY new renewable energy source now!

---

## 🆕 QUESTION 1: How to Add a COMPLETELY NEW Source

### Example: Adding "Hydrogen Energy" (code: 101.1)

#### **METHOD 1: Via Django Admin (Recommended for non-programmers)**

**Step 1: Add Base Data**
```
1. Open: http://127.0.0.1:8000/admin/simulator/renewabledata/add/

2. Fill in:
   Code:         101.1
   Name:         Hydrogen Energy Production
   Category:     renewable
   Status value: 800    (current hydrogen production in MW)
   Target value: 3000   (target production)
   
3. Click "Save and add another"
```

**Step 2: Add Supporting Data**
```
1. Still on Add page:
   
   Code:         101.1.1
   Name:         Hydrogen Efficiency Factor
   Status value: 0.60   (60% efficiency)
   Target value: 0.75   (75% target)
   
2. Click "Save and add another"

3. Add more if needed:
   Code:         101.1.2
   Name:         Hydrogen Operating Hours
   Status value: 7000
   Target value: 8000
   
4. Click "Save"
```

**Step 3: Create Formula**
```
1. Go to: http://127.0.0.1:8000/admin/simulator/formula/add/

2. Fill in:
   Key:        101.1.3
   Name:       Hydrogen Annual Production
   Category:   renewable
   Expression: hydrogen_base * hydrogen_efficiency * hydrogen_hours
   Is fixed:   ☐ (unchecked)
   Is active:  ☑ (checked)
```

**Step 4: Add Variable Mappings (SAME PAGE, scroll down)**
```
In "FORMULA VARIABLES" section:

1. Click "Add another Formula variable"
   Variable name: hydrogen_base
   Source type:   renewable_status
   Source key:    101.1
   
2. Click "Add another Formula variable"
   Variable name: hydrogen_efficiency
   Source type:   renewable_status
   Source key:    101.1.1
   
3. Click "Add another Formula variable"
   Variable name: hydrogen_hours
   Source type:   renewable_status
   Source key:    101.1.2
   
4. Click "Save"
```

**Step 5: Test It**
```bash
source .venv/bin/activate
python manage.py shell
```

```python
from simulator.formula_service import evaluate_with_mappings

status, target = evaluate_with_mappings('101.1.3')
print(f"Hydrogen Status: {status} MWh/year")
print(f"Hydrogen Target: {target} MWh/year")

# Expected: 800 * 0.60 * 7000 = 3,360,000 MWh/year
```

✅ **DONE! New source added without touching Python code!**

---

#### **METHOD 2: Via Python Script (For bulk additions)**

Create file: `add_hydrogen.py`

```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, Formula, FormulaVariable

# Step 1: Add data
RenewableData.objects.create(
    code='101.1',
    name='Hydrogen Energy Production',
    status_value=800,
    target_value=3000,
    category='renewable'
)

RenewableData.objects.create(
    code='101.1.1',
    name='Hydrogen Efficiency Factor',
    status_value=0.60,
    target_value=0.75,
    category='renewable'
)

RenewableData.objects.create(
    code='101.1.2',
    name='Hydrogen Operating Hours',
    status_value=7000,
    target_value=8000,
    category='renewable'
)

# Step 2: Create formula
formula = Formula.objects.create(
    key='101.1.3',
    name='Hydrogen Annual Production',
    category='renewable',
    expression='hydrogen_base * hydrogen_efficiency * hydrogen_hours',
    is_fixed=False,
    is_active=True
)

# Step 3: Create mappings
FormulaVariable.objects.create(
    formula=formula,
    variable_name='hydrogen_base',
    source_type='renewable_status',
    source_key='101.1'
)

FormulaVariable.objects.create(
    formula=formula,
    variable_name='hydrogen_efficiency',
    source_type='renewable_status',
    source_key='101.1.1'
)

FormulaVariable.objects.create(
    formula=formula,
    variable_name='hydrogen_hours',
    source_type='renewable_status',
    source_key='101.1.2'
)

print("✅ Hydrogen energy source added!")
```

Run it:
```bash
python add_hydrogen.py
```

---

## 🔗 QUESTION 2: How Formulas Reference LandUse or Verbrauch

### ACTUAL Examples from Your Database:

#### **Example 1: Formula Referencing LandUse**

**Formula 1.2** (Solar ground area)
```
Expression: solar_ground_area

Variable Mapping:
  solar_ground_area → landuse_target LU_2.1
  
Meaning:
  Gets land area from LandUse table:
  solar_ground_area = LandUse.objects.get(code="LU_2.1").target_ha
```

#### **Example 2: Formula Referencing Verbrauch**

**Formula 10.2.1** (Uses consumption data)
```
Expression: verbrauch_5

Variable Mapping:
  verbrauch_5 → verbrauch_ziel 5
  
Meaning:
  Gets consumption from VerbrauchData table:
  verbrauch_5 = VerbrauchData.objects.get(code="5").ziel
```

---

### 📋 Available Source Types

When creating FormulaVariable mappings, use these **source_type** values:

| Source Type | Gets Value From | Field Used |
|-------------|----------------|------------|
| `renewable_status` | RenewableData | status_value |
| `renewable_target` | RenewableData | target_value |
| `landuse_status` | LandUse | status_ha |
| `landuse_target` | LandUse | target_ha |
| `verbrauch_status` | VerbrauchData | status |
| `verbrauch_ziel` | VerbrauchData | ziel (target) |

---

### 🧪 HOW TO: Add Formula that References LandUse AND Verbrauch

**Example: Solar energy adjusted by consumption**

**Step 1: Add data (if needed)**
```
Already exists:
- LandUse code "LU_1.1" (roof area)
- VerbrauchData code "7.1" (building consumption)
```

**Step 2: Create formula**
```
Via Django Admin → Formulas → Add:

Key:        102.1
Expression: roof_area * consumption_factor * 0.001
Category:   renewable
```

**Step 3: Add mappings**
```
Mapping 1:
  Variable name: roof_area
  Source type:   landuse_target
  Source key:    LU_1.1
  
Mapping 2:
  Variable name: consumption_factor
  Source type:   verbrauch_ziel
  Source key:    7.1
```

**Step 4: Test**
```bash
python manage.py shell
```
```python
from simulator.formula_service import evaluate_with_mappings
status, target = evaluate_with_mappings('102.1')
print(f"Result: {status}")
```

✅ **Formula now uses BOTH LandUse and Verbrauch data!**

---

## 🔧 QUESTION 3: How to Modify Existing Formula (Example: 10.1)

### Current State of Formula 10.1

```
Code:       10.1
Name:       Endenergie aus Erneuerbaren Q. gesamt
Expression: renewable_10_3 + renewable_10_4 + renewable_10_5 + renewable_10_6

Mappings:
  renewable_10_3 → renewable_target 10.3
  renewable_10_4 → renewable_target 10.4
  renewable_10_5 → renewable_target 10.5
  renewable_10_6 → renewable_target 10.6
```

---

### ✏️ SCENARIO 1: Change the Formula Expression

**Goal:** Add a new component (10.7) to the sum

**Via Django Admin:**
```
1. Go to: http://127.0.0.1:8000/admin/simulator/formula/
2. Search for "10.1"
3. Click on it
4. Edit Expression to:
   renewable_10_3 + renewable_10_4 + renewable_10_5 + renewable_10_6 + renewable_10_7
5. Scroll down to "FORMULA VARIABLES" section
6. Click "Add another Formula variable"
7. Fill in:
   Variable name: renewable_10_7
   Source type:   renewable_target
   Source key:    10.7
8. Click "Save"
```

✅ **Formula updated! No Python code needed!**

---

### 🔄 SCENARIO 2: Change Data Source

**Goal:** Instead of using renewable_10_3, use consumption data

**Via Django Admin:**
```
1. Go to: http://127.0.0.1:8000/admin/simulator/formula/
2. Search for "10.1"
3. Click on it
4. Find the mapping for "renewable_10_3"
5. Change:
   Source type: verbrauch_ziel
   Source key:  4.3  (or whichever Verbrauch code you want)
6. Click "Save"
```

✅ **Same formula expression, different data source!**
✅ **This is the POWER of extensibility!**

---

### 🆕 SCENARIO 3: Add LandUse Reference to 10.1

**Goal:** Multiply result by land area factor

**Via Django Admin:**
```
1. Go to: http://127.0.0.1:8000/admin/simulator/formula/
2. Search for "10.1"
3. Click on it
4. Edit Expression to:
   (renewable_10_3 + renewable_10_4 + renewable_10_5 + renewable_10_6) * land_factor
5. In "FORMULA VARIABLES" section
6. Click "Add another Formula variable"
7. Fill in:
   Variable name: land_factor
   Source type:   landuse_target
   Source key:    LU_1.1
8. Click "Save"
```

✅ **Formula now uses Renewable data AND LandUse data!**

---

## 📝 COMPLETE PRACTICAL EXAMPLE

Let me create a complete new source with all types of references:

### Adding "Mixed Energy System" (Uses Renewable + LandUse + Verbrauch)

**Step 1: Add base data**
```
RenewableData:
  Code: 103.1
  Name: Mixed Energy Base
  Status: 1000
  Target: 3000
```

**Step 2: Create formula**
```
Formula:
  Key: 103.1.1
  Expression: energy_base * land_area * (1 - consumption_ratio)
```

**Step 3: Add mappings**
```
Mapping 1:
  Variable: energy_base
  Source:   renewable_status
  Key:      103.1
  
Mapping 2:
  Variable: land_area
  Source:   landuse_target
  Key:      LU_2.1
  
Mapping 3:
  Variable: consumption_ratio
  Source:   verbrauch_ziel
  Key:      7.1
```

✅ **One formula references 3 different data sources!**

---

## 🎯 QUICK REFERENCE CHEAT SHEET

### To Add New Source:
```
1. RenewableData → Add entry
2. Formula → Create with meaningful variable names
3. FormulaVariable → Map variables to sources
```

### To Reference LandUse:
```
Source type: landuse_target
Source key:  LU_1.1 (or any LandUse code)
```

### To Reference Verbrauch:
```
Source type: verbrauch_ziel
Source key:  4.3 (or any VerbrauchData code)
```

### To Modify Existing Formula:
```
Admin → Formulas → Find formula → Edit expression and/or mappings
```

---

## 🧪 TEST SCRIPTS

I've created test scripts for you:

