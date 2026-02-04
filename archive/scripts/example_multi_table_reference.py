#!/usr/bin/env python
"""
Example: Create formula referencing LandUse and Verbrauch
Shows how to reference data from multiple tables
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, RenewableData, LandUse, VerbrauchData

print('=' * 70)
print('EXAMPLE: Multi-Table Reference Formula')
print('=' * 70)
print()

# Create a test formula that references ALL THREE tables
print('📝 Creating Formula 99.9: Mixed Energy System Efficiency')
print()

# Step 1: Create the renewable data
renewable, created = RenewableData.objects.get_or_create(
    code='99.9',
    defaults={
        'name': 'Mixed Energy System Efficiency (Test)',
        'status_value': 0,
        'target_value': 0,
        'category': 'renewable'
    }
)
print(f'✅ RenewableData 99.9: {"created" if created else "exists"}')

# Step 2: Create the formula
formula, created = Formula.objects.get_or_create(
    key='99.9',
    defaults={
        'name': 'Mixed Energy System Efficiency',
        'expression': '(solar_energy * land_efficiency) / energy_demand',
        'category': 'renewable',
        'is_fixed': False
    }
)
print(f'✅ Formula 99.9: {"created" if created else "exists"}')
print(f'   Expression: {formula.expression}')
print()

# Step 3: Create mappings
mappings = [
    {
        'variable_name': 'solar_energy',
        'source_type': 'renewable_target',
        'source_key': '1.1',  # References RenewableData 1.1
        'description': 'Solar photovoltaic from RenewableData'
    },
    {
        'variable_name': 'land_efficiency',
        'source_type': 'landuse_target',
        'source_key': 'LU_2.1',  # References LandUse LU_2.1
        'description': 'Ground area efficiency from LandUse'
    },
    {
        'variable_name': 'energy_demand',
        'source_type': 'verbrauch_ziel',
        'source_key': '5',  # References VerbrauchData 5
        'description': 'Total energy demand from VerbrauchData'
    }
]

print('🔗 Creating variable mappings:')
for mapping_data in mappings:
    mapping, created = FormulaVariable.objects.get_or_create(
        formula=formula,
        variable_name=mapping_data['variable_name'],
        defaults={
            'source_type': mapping_data['source_type'],
            'source_key': mapping_data['source_key']
        }
    )
    status = "✅" if created else "ℹ️ "
    print(f"{status} {mapping_data['variable_name']:20} → {mapping_data['source_type']:20} {mapping_data['source_key']}")
    print(f"   ({mapping_data['description']})")

print()
print('📊 FORMULA DETAILS:')
print(f'Code: {formula.key}')
print(f'Name: {formula.name}')
print(f'Expression: {formula.expression}')
print(f'Mappings: {formula.variables.count()}')
print()

# Test calculation
print('🧪 TESTING CALCULATION:')
from simulator.formula_service import evaluate_with_mappings
try:
    status, target = evaluate_with_mappings('99.9')
    print(f'✅ Calculation successful!')
    print(f'   Status value: {status}')
    print(f'   Target value: {target}')
except Exception as e:
    print(f'❌ Calculation failed: {e}')

print()
print('=' * 70)
print('✅ Multi-table reference formula created!')
print()
print('This formula demonstrates:')
print('1. ✅ Referencing RenewableData (solar_energy)')
print('2. ✅ Referencing LandUse (land_efficiency)')
print('3. ✅ Referencing VerbrauchData (energy_demand)')
print()
print('View in Django Admin at: /admin/simulator/formula/')
print('=' * 70)
