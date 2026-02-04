import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, LandUse
import re

# Check all renewable formulas for missing variables
print('=== Adding missing FormulaVariables ===')
added = 0

for f in Formula.objects.filter(category='renewable', is_active=True):
    # Extract variable names from expression
    var_pattern = r'(Renewable_[\w_]+|LandUse_[\w_]+|Verbrauch_[\w_]+)'
    expr_vars = set(re.findall(var_pattern, f.expression))
    
    # Get defined variables
    defined_vars = set(v.variable_name for v in f.variables.all())
    
    # Find missing
    missing = expr_vars - defined_vars
    
    for var_name in missing:
        # Determine source type and key
        if var_name.startswith('LandUse_'):
            # Extract the LU code - e.g., LandUse_LU_1 -> LU_1, LandUse_LU_2.1 -> LU_2.1
            lu_code = var_name.replace('LandUse_', '')
            
            # Check if it exists (try variations)
            lu = LandUse.objects.filter(code=lu_code).first()
            if not lu:
                # Try with .1 suffix
                lu = LandUse.objects.filter(code=f'{lu_code}.1').first()
                if lu:
                    lu_code = lu.code
            
            if lu:
                # Determine if status or target based on formula type
                if f.formula_type == 'ziel' or '_ziel' in f.key:
                    source_type = 'landuse_target'
                else:
                    source_type = 'landuse_status'
                
                fv = FormulaVariable.objects.create(
                    formula=f,
                    variable_name=var_name,
                    source_type=source_type,
                    source_key=lu_code,
                    default_value=0
                )
                print(f'Added {var_name} -> {source_type}:{lu_code} for formula {f.key}')
                added += 1
            else:
                print(f'WARNING: LandUse code {lu_code} not found for {f.key}')
        
        elif var_name.startswith('Renewable_'):
            # Convert variable name to code: Renewable_10_3_1 -> 10.3.1
            code = var_name.replace('Renewable_', '').replace('_', '.')
            # Handle _ziel suffix
            code = code.replace('.ziel', '_ziel')
            
            if f.formula_type == 'ziel' or '_ziel' in f.key:
                source_type = 'renewable_target'
            else:
                source_type = 'renewable_status'
            
            fv = FormulaVariable.objects.create(
                formula=f,
                variable_name=var_name,
                source_type=source_type,
                source_key=code,
                default_value=0
            )
            print(f'Added {var_name} -> {source_type}:{code} for formula {f.key}')
            added += 1
        
        elif var_name.startswith('Verbrauch_'):
            # Convert variable name to code: Verbrauch_1_4 -> 1.4
            code = var_name.replace('Verbrauch_', '').replace('_', '.')
            
            if f.formula_type == 'ziel' or '_ziel' in f.key:
                source_type = 'verbrauch_ziel'
            else:
                source_type = 'verbrauch_status'
            
            fv = FormulaVariable.objects.create(
                formula=f,
                variable_name=var_name,
                source_type=source_type,
                source_key=code,
                default_value=0
            )
            print(f'Added {var_name} -> {source_type}:{code} for formula {f.key}')
            added += 1

print(f'\nTotal added: {added}')
