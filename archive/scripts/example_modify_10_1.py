#!/usr/bin/env python
"""
Example: Modify Formula 10.1 to add a new component
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, RenewableData

print('=' * 70)
print('EXAMPLE: Modifying Formula 10.1')
print('=' * 70)
print()

# Show current state
formula = Formula.objects.get(key='10.1')
print('📊 BEFORE:')
print(f'Expression: {formula.expression}')
print(f'Mappings: {formula.variables.count()}')
print()

# Option 1: Add new component to formula
print('✏️  MODIFICATION: Adding renewable_10_7 to the sum')
print()

# First, ensure 10.7 data exists
renewable_10_7, created = RenewableData.objects.get_or_create(
    code='10.7',
    defaults={
        'name': 'Additional Renewable Source (Test)',
        'status_value': 5000,
        'target_value': 10000,
        'category': 'renewable'
    }
)
if created:
    print(f'✅ Created RenewableData 10.7')
else:
    print(f'ℹ️  RenewableData 10.7 already exists')

# Update formula expression
old_expression = formula.expression
formula.expression = old_expression + ' + renewable_10_7'
formula.save()
print(f'✅ Updated expression')

# Add mapping
mapping, created = FormulaVariable.objects.get_or_create(
    formula=formula,
    variable_name='renewable_10_7',
    defaults={
        'source_type': 'renewable_target',
        'source_key': '10.7'
    }
)
if created:
    print(f'✅ Created mapping for renewable_10_7')
else:
    print(f'ℹ️  Mapping already exists')

print()
print('📊 AFTER:')
print(f'Expression: {formula.expression}')
print(f'Mappings: {formula.variables.count()}')
print()

# Test calculation
print('🧪 TESTING CALCULATION:')
from simulator.formula_service import evaluate_with_mappings
status, target = evaluate_with_mappings('10.1')
print(f'Status: {status}')
print(f'Target: {target}')
print()

print('=' * 70)
print('✅ Formula 10.1 successfully modified!')
print()
print('To revert changes:')
print('1. Edit formula 10.1 in Django Admin')
print('2. Remove "+ renewable_10_7" from expression')
print('3. Delete the renewable_10_7 mapping')
print('=' * 70)
