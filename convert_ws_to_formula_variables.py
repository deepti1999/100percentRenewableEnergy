"""
Convert WS Formulas to use FormulaVariables

This script:
1. Parses each WS formula expression
2. Identifies references (row.*, day_prev.*, sums['*'], *_366, *_367)
3. Creates FormulaVariables for each reference
4. Updates the expression to use variable names

Usage:
    python manage.py shell < convert_ws_to_formula_variables.py
"""

import re
from simulator.models import Formula, FormulaVariable

# Pattern matchers for different reference types
PATTERNS = {
    'row_column': re.compile(r'row\.(\w+)'),           # row.column
    'day_prev_column': re.compile(r'day_prev\.(\w+)'), # day_prev.column
    'sums': re.compile(r"sums\['(\w+)'\]"),            # sums['sum_x']
    'ref_366': re.compile(r'(\w+)_366(?![0-9])'),      # column_366
    'ref_367': re.compile(r'(\w+)_367(?![0-9])'),      # column_367
    'ref_368': re.compile(r'(\w+)_368(?![0-9])'),      # column_368
}

def convert_expression_to_variables(formula):
    """
    Convert a WS formula expression to use FormulaVariables.
    Returns: (new_expression, list of FormulaVariable dicts)
    """
    expression = formula.expression
    variables = []
    var_counter = {}  # To create unique variable names
    
    # Process each pattern type
    
    # 1. row.column -> current_column
    for match in PATTERNS['row_column'].finditer(expression):
        column = match.group(1)
        var_name = f"current_{column}"
        
        if var_name not in var_counter:
            var_counter[var_name] = True
            variables.append({
                'variable_name': var_name,
                'source_type': 'ws_row_value',
                'source_key': column,
                'description': f'Current row {column}'
            })
    
    # 2. day_prev.column -> prev_column
    for match in PATTERNS['day_prev_column'].finditer(expression):
        column = match.group(1)
        var_name = f"prev_{column}"
        
        if var_name not in var_counter:
            var_counter[var_name] = True
            variables.append({
                'variable_name': var_name,
                'source_type': 'ws_day_prev',
                'source_key': column,
                'description': f'Previous day {column}'
            })
    
    # 3. sums['sum_x'] -> sum_x
    for match in PATTERNS['sums'].finditer(expression):
        sum_key = match.group(1)
        var_name = sum_key  # Keep same name like sum_stromverbr
        
        # Extract column name (remove 'sum_' or 'max_' prefix)
        if sum_key.startswith('sum_'):
            column = sum_key[4:]
        elif sum_key.startswith('max_'):
            column = sum_key[4:]
        else:
            column = sum_key
        
        if var_name not in var_counter:
            var_counter[var_name] = True
            variables.append({
                'variable_name': var_name,
                'source_type': 'ws_sum',
                'source_key': column,
                'description': f'Sum/Max of {column}'
            })
    
    # 4. column_366 -> ref_column_366
    for match in PATTERNS['ref_366'].finditer(expression):
        column = match.group(1)
        # Skip if this is actually a key reference (like stromverbr_raumwaerm_korr_366)
        if column in ['sum', 'max', 'row', 'day']:
            continue
        var_name = f"ref_{column}_366"
        
        if var_name not in var_counter:
            var_counter[var_name] = True
            variables.append({
                'variable_name': var_name,
                'source_type': 'ws_row_366',
                'source_key': column,
                'description': f'Row 366 {column}'
            })
    
    # 5. column_367 -> ref_column_367
    for match in PATTERNS['ref_367'].finditer(expression):
        column = match.group(1)
        if column in ['sum', 'max', 'row', 'day']:
            continue
        var_name = f"ref_{column}_367"
        
        if var_name not in var_counter:
            var_counter[var_name] = True
            variables.append({
                'variable_name': var_name,
                'source_type': 'ws_row_366',  # Use ws_row_366 but for row 367
                'source_key': column,
                'description': f'Row 367 {column}'
            })
    
    # Now create the new expression with variable names
    new_expression = expression
    
    # Replace row.column with current_column
    new_expression = PATTERNS['row_column'].sub(r'current_\1', new_expression)
    
    # Replace day_prev.column with prev_column
    new_expression = PATTERNS['day_prev_column'].sub(r'prev_\1', new_expression)
    
    # Replace sums['sum_x'] with sum_x
    new_expression = PATTERNS['sums'].sub(r'\1', new_expression)
    
    # Replace column_366 with ref_column_366
    def replace_366(match):
        column = match.group(1)
        if column in ['sum', 'max', 'row', 'day']:
            return match.group(0)
        return f"ref_{column}_366"
    new_expression = PATTERNS['ref_366'].sub(replace_366, new_expression)
    
    # Replace column_367 with ref_column_367
    def replace_367(match):
        column = match.group(1)
        if column in ['sum', 'max', 'row', 'day']:
            return match.group(0)
        return f"ref_{column}_367"
    new_expression = PATTERNS['ref_367'].sub(replace_367, new_expression)
    
    return new_expression, variables


def main(dry_run=True):
    """Main conversion function"""
    ws_formulas = Formula.objects.filter(category='ws', is_active=True)
    
    print(f"Found {ws_formulas.count()} WS formulas to convert")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)
    
    total_formulas = 0
    total_variables = 0
    
    for formula in ws_formulas:
        new_expression, variables = convert_expression_to_variables(formula)
        
        if variables:  # Only show if there are variables to create
            total_formulas += 1
            total_variables += len(variables)
            
            print(f"\n{formula.key}:")
            print(f"  OLD: {formula.expression[:80]}...")
            print(f"  NEW: {new_expression[:80]}...")
            print(f"  Variables ({len(variables)}):")
            for var in variables:
                print(f"    - {var['variable_name']} = {var['source_type']}({var['source_key']})")
            
            if not dry_run:
                # Update formula expression
                formula.expression = new_expression
                formula.save()
                
                # Create FormulaVariables
                for var in variables:
                    FormulaVariable.objects.get_or_create(
                        formula=formula,
                        variable_name=var['variable_name'],
                        defaults={
                            'source_type': var['source_type'],
                            'source_key': var['source_key'],
                            'default_value': 0,
                            'is_required': False,
                        }
                    )
    
    print("\n" + "=" * 60)
    print(f"Total: {total_formulas} formulas with {total_variables} variables")
    
    if dry_run:
        print("\nDRY RUN - No changes made")
        print("Run with dry_run=False to apply changes")
    else:
        print("\n✅ All changes applied!")


if __name__ == '__main__':
    # Run in dry-run mode first
    main(dry_run=True)
