# 🚀 MIGRATION PLAN: Making Your System Fully Extensible

## 📋 **OVERVIEW**

This document outlines how to migrate from the current direct-reference approach to a fully extensible FormulaVariable-based system.

---

## 🎯 **GOAL**

Transform formulas from:
```
expression='LandUse_1.1 * 1.1.2.1 / 100 * 1.1.2.1.1 / 1000'
```

To:
```
expression='roof_area * pv_percentage / 100 * pv_yield / 1000'

+ FormulaVariable mappings:
  - roof_area → LandUse LU_1.1 target_ha
  - pv_percentage → RenewableData 1.1.2.1 target_value
  - pv_yield → RenewableData 1.1.2.1.1 target_value
```

---

## 📊 **MIGRATION PHASES**

### **PHASE 1: Create Management Command to Convert Formulas** ⏳

Create a command that:
1. Reads existing formula expressions
2. Identifies variables (LandUse_X, VerbrauchData_Y, direct codes)
3. Creates generic variable names
4. Creates FormulaVariable mappings
5. Updates formula expressions

File: `simulator/management/commands/migrate_to_formulavariable.py`

```python
from django.core.management.base import BaseCommand
from simulator.models import Formula, FormulaVariable
import re

class Command(BaseCommand):
    help = 'Migrate formulas to use FormulaVariable mappings'
    
    def handle(self, *args, **options):
        formulas = Formula.objects.filter(is_active=True)
        
        for formula in formulas:
            if not formula.expression or formula.is_fixed:
                continue
            
            # Find all variables in expression
            variables = self.extract_variables(formula.expression)
            
            # Create generic expression and mappings
            new_expression, mappings = self.create_mappings(
                formula.expression,
                variables,
                formula
            )
            
            # Update formula
            formula.expression = new_expression
            formula.save()
            
            # Create FormulaVariable records
            for var_name, source_info in mappings.items():
                FormulaVariable.objects.create(
                    formula=formula,
                    variable_name=var_name,
                    source_type=source_info['type'],
                    source_key=source_info['key']
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Migrated {formula.key}')
            )
    
    def extract_variables(self, expression):
        """Extract all data references from expression"""
        # Find LandUse_X.X, VerbrauchData_X.X, or standalone codes like 1.1.2.1
        pattern = r'(LandUse_[A-Za-z0-9\._]+|VerbrauchData_[\d\.]+|\b\d+(?:\.\d+)+\b)'
        return re.findall(pattern, expression)
    
    def create_mappings(self, expression, variables, formula):
        """Create generic variable names and mappings"""
        mappings = {}
        new_expr = expression
        
        for i, var in enumerate(variables):
            # Create generic name
            if var.startswith('LandUse_'):
                generic_name = f'landuse_var_{i}'
                source_key = var.replace('LandUse_', '')
                source_type = FormulaVariable.LANDUSE_TARGET
            elif var.startswith('VerbrauchData_'):
                generic_name = f'verbrauch_var_{i}'
                source_key = var.replace('VerbrauchData_', '')
                source_type = FormulaVariable.VERBRAUCH_ZIEL
            else:
                # Direct renewable code reference
                generic_name = f'renewable_var_{i}'
                source_key = var
                source_type = FormulaVariable.RENEWABLE_TARGET
            
            mappings[generic_name] = {
                'type': source_type,
                'key': source_key
            }
            
            # Replace in expression
            new_expr = new_expr.replace(var, generic_name)
        
        return new_expr, mappings
```

---

### **PHASE 2: Update RenewableCalculator to Use Mappings** ⏳

Update `calculation_engine/renewable_engine.py`:

```python
class RenewableCalculator:
    def __init__(self):
        self.evaluator = FormulaEvaluator()
        self.formula_service = FormulaService(use_cache=True)
        self.cache = {}
    
    def calculate(self, code):
        """Calculate using FormulaVariable mappings if available"""
        
        # Try new mapping-based approach first
        result = self.formula_service.evaluate_with_mappings(
            code,
            category='renewable'
        )
        
        if result != (None, None):
            return result  # Successfully used mappings!
        
        # Fall back to old direct-reference approach
        formula_def = self.formula_service.get_formula(code, category='renewable')
        
        if not formula_def or formula_def.get('is_fixed'):
            return None, None
        
        # Old evaluation logic continues here...
```

---

### **PHASE 3: Create User-Friendly Variable Names** ⏳

Instead of `landuse_var_0`, use meaningful names:

```python
VARIABLE_NAME_MAPPINGS = {
    'LU_1.1': 'solar_roof_area',
    'LU_2.1': 'solar_ground_area',
    'LU_6': 'wind_park_area',
    '1.1.1.1': 'solar_thermal_percentage',
    '1.1.1.1.1': 'solar_thermal_yield',
    '1.1.2.1': 'solar_pv_percentage',
    '1.1.2.1.1': 'solar_pv_yield',
    '1.1.2.1.2.1': 'pv_full_load_hours',
    '2.1.1.1': 'wind_area_per_mw',
    '2.1.1.2.1': 'wind_full_load_hours',
    # ... define all commonly used variables
}
```

---

### **PHASE 4: Test Migration** ⏳

```bash
# 1. Backup database
cp db.sqlite3 db.sqlite3.backup

# 2. Run migration on ONE formula first
python manage.py migrate_to_formulavariable --formula-key="1.1.2.1.2"

# 3. Test calculation
python manage.py shell
>>> from calculation_engine.renewable_engine import RenewableCalculator
>>> calc = RenewableCalculator()
>>> result = calc.calculate('1.1.2.1.2')
>>> print(result)

# 4. If successful, migrate all
python manage.py migrate_to_formulavariable --all
```

---

### **PHASE 5: Verify Results Match** ⏳

```python
# Compare old vs new calculations
python manage.py compare_calculation_methods
```

---

## ✅ **BENEFITS AFTER MIGRATION**

1. **Add New Data Sources** - Just create new source_type in FormulaVariable
2. **Reuse Formulas** - Same formula, different mappings
3. **Handle Data Changes** - Update mapping, not formulas
4. **Admin-Editable Mappings** - Non-technical users can change data sources
5. **API Integration** - Map external data to your formulas

---

## ⚠️ **EFFORT REQUIRED**

- **Time**: 2-3 days full-time work
- **Risk**: Medium (major architectural change)
- **Complexity**: High (need thorough testing)
- **Lines of code**: ~500-1000 changes

---

## 🎯 **RECOMMENDATION**

**Start with a pilot:**
1. Migrate 10 simple formulas
2. Test thoroughly
3. If successful, migrate the rest
4. Keep old approach as fallback during transition

**Or keep current system if:**
- Your data structure is stable ✅
- You don't need to integrate external data sources ✅
- Current extensibility is sufficient for your use case ✅
