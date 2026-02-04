# LandUse User % → Target Percentage Flow

## 📋 What Happens When User Changes "User (%)" from 5% to 8%

### **Step-by-Step Flow:**

```
User enters 8% in "User (%)" input field
            ↓
JavaScript captures change
            ↓
AJAX POST to /api/save-user-input/
            ↓
views.py: save_user_input() function
            ↓
Sets landuse.user_percent = 8.0
            ↓
Calls landuse.save()
            ↓
models.py: LandUse.save() method
            ↓
Calculates: target_ha = parent.target_ha × 8 / 100
            ↓
Sets: target_percent = 8.0 (same as user_percent)
            ↓
Saves to database
            ↓
Webapp reloads/updates display
            ↓
Shows new target_ha and target_percent values
```

---

## 🔍 **Code Locations**

### **1. Frontend (Webapp) - User Input**
**File:** `simulator/templates/simulator/landuse_list.html`
**Lines:** ~1380-1465

```javascript
// When user types in "User (%)" field
function saveUserInput(code, value) {
    fetch('/api/save-user-input/', {
        method: 'POST',
        body: JSON.stringify({
            code: code,
            user_percent: value  // e.g., 8
        })
    })
}
```

---

### **2. Backend View - Receives Input**
**File:** `simulator/views.py`
**Lines:** 660-680

```python
@login_required
@require_http_methods(["POST"])
def save_user_input(request):
    """API endpoint to save user percentage input"""
    data = json.loads(request.body)
    code = data.get('code')              # e.g., "LU_1.1"
    user_percent = data.get('user_percent')  # e.g., 8
    
    landuse = get_object_or_404(LandUse, code=code)
    landuse.user_percent = float(user_percent)  # Store 8.0
    landuse.save()  # ← This triggers the calculation!
```

---

### **3. Model Logic - Calculates target_ha**
**File:** `simulator/models.py`
**Lines:** 370-378

```python
def save(self, *args, **kwargs):
    # ... (tracking old values) ...
    
    # KEY LOGIC: If user_percent changed, calculate target_ha from it
    elif self.user_percent is not None and self.parent and self.parent.target_ha:
        # CALCULATION HAPPENS HERE:
        self.target_ha = (self.parent.target_ha * self.user_percent) / 100.0
        #                     ↑                      ↑
        #                 Parent's target        User's 8%
        
        # Set target_percent to match user_percent
        self.target_percent = self.user_percent  # 8.0
        
        # Lock this value so parent cascades don't overwrite it
        self.target_locked = True
```

**Example Calculation:**
```python
# If parent has target_ha = 35,759,529 ha
# And user sets user_percent = 8%

target_ha = (35,759,529 × 8) / 100
target_ha = 2,860,762.32 ha

target_percent = 8.0%
```

---

### **4. Display Calculation - Shows in Webapp**
**File:** `simulator/views.py`
**Lines:** 119-178 (calculate_percentages function)

```python
def calculate_percentages(landuse):
    """Calculate percentages using DATABASE FORMULAS"""
    
    # Calculate target percentage using formula from database
    if landuse.parent and landuse.parent.target_ha and landuse.target_ha:
        # Uses formula: child_target / parent_target * 100
        formula = Formula.objects.get(key='LANDUSE_TARGET_PERCENT')
        context = {
            'child_target': landuse.target_ha,      # e.g., 2,860,762
            'parent_target': landuse.parent.target_ha  # e.g., 35,759,529
        }
        result = eval(formula.expression, {}, context)
        # result = 2,860,762 / 35,759,529 * 100 = 8.0%
        
        data['target_percent'] = round(result, 1)  # 8.0%
```

---

## 📊 **Complete Example: User Changes 5% → 8%**

### **Before:**
```
LandUse: LU_1.1
Parent: LU_1 (target_ha = 3,575,953 ha)
user_percent: 5.0%
target_ha: 178,797 ha  (calculated: 3,575,953 × 5 / 100)
target_percent: 5.0%
```

### **User Action:**
User types **8** in "User (%)" field and presses Enter

### **After:**
```
LandUse: LU_1.1
Parent: LU_1 (target_ha = 3,575,953 ha)
user_percent: 8.0%  ← Changed
target_ha: 286,076 ha  ← Recalculated: 3,575,953 × 8 / 100
target_percent: 8.0%  ← Updated to match user_percent
```

---

## 🎯 **Key Points:**

1. **user_percent** is the INPUT from user (what they type)
2. **target_ha** is CALCULATED from: `parent.target_ha × user_percent / 100`
3. **target_percent** is SET TO match user_percent (8.0%)
4. **Target (%)** column displays the calculated percentage

### **Why target_percent = user_percent?**

In [models.py line 376](simulator/models.py#L376):
```python
self.target_percent = self.user_percent
```

This means: **"The target percentage IS what the user specified"**

So if user says "I want 8%", then:
- `user_percent = 8.0` (what they typed)
- `target_ha = parent × 8%` (calculated)
- `target_percent = 8.0` (same as user input)

---

## 🔄 **Cascade Effect:**

After saving, if this LandUse change affects Renewable data:

```python
# In models.py save() method, after saving:
if status_ha_changed or target_ha_changed:
    self._recalculate_renewable_dependents()
```

This triggers updates to any RenewableData records that reference this LandUse code.

---

## 📝 **Summary:**

| What | Where | Logic |
|------|-------|-------|
| **User Input** | Webapp template | User types 8 in "User (%)" field |
| **Save to DB** | views.py:660 | `landuse.user_percent = 8.0` |
| **Calculate target_ha** | models.py:373 | `target_ha = parent.target_ha × 8 / 100` |
| **Set target_percent** | models.py:376 | `target_percent = 8.0` |
| **Display** | views.py:119 | Shows calculated target_percent |

**The logic is split across 3 files:**
1. **Template** - Captures user input
2. **Views** - Saves user_percent
3. **Models** - Calculates target_ha and sets target_percent
