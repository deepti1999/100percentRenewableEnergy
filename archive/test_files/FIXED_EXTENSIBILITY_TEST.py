#!/usr/bin/env python
"""
FIXED EXTENSIBILITY TEST
Tests if the system is 100% extensible via Admin (no code changes)
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, RenewableData
from calculation_engine.renewable_engine import RenewableCalculator

def cleanup():
    """Clean up test data"""
    Formula.objects.filter(key='TEST_EXTENSIBILITY').delete()
    RenewableData.objects.filter(code='TEST_EXTENSIBILITY').delete()

def test_extensibility():
    """
    Test if we can add a new formula via "Admin" and have it work immediately
    WITHOUT any code changes
    """
    print("\n" + "="*70)
    print("EXTENSIBILITY TEST: Add Formula Via Admin (No Code Changes)")
    print("="*70)
    
    # Clean up first
    cleanup()
    
    # Step 1: Create RenewableData entry (what Admin user would do)
    print("\n📝 Step 1: Create RenewableData entry in Admin...")
    test_data = RenewableData.objects.create(
        code='TEST_EXTENSIBILITY',
        description='Test formula for extensibility verification',
        is_fixed=False,
        status_value=0,
        target_value=0
    )
    print(f"   ✓ Created RenewableData: {test_data.code}")
    
    # Step 2: Create Formula entry (what Admin user would do)
    print("\n📝 Step 2: Create Formula in Admin...")
    formula = Formula.objects.create(
        key='TEST_EXTENSIBILITY',
        category='renewable',
        expression='pv + solar + wind',  # Use variable names, not numeric codes
        description='Sum of three renewable sources',
        is_fixed=False,
        is_active=True
    )
    print(f"   ✓ Created Formula: {formula.key}")
    print(f"   Expression: {formula.expression}")
    
    # Step 3: Create FormulaVariable mappings (what Admin user would do)
    print("\n📝 Step 3: Create FormulaVariable mappings in Admin...")
    
    variables = [
        ('pv', '10.3', 'Photovoltaik'),
        ('solar', '10.4', 'Solarthermie'),
        ('wind', '10.5', 'Windenergie')
    ]
    
    for var_name, source_code, description in variables:
        fv = FormulaVariable.objects.create(
            formula=formula,
            variable_name=var_name,
            source_type='renewable_status',  # For status value
            source_key=source_code,  # The code in RenewableData
            default_value=0
        )
        print(f"   ✓ Mapped {var_name} → RenewableData[{source_code}].status")
    
    # Step 4: Test if formula calculates WITHOUT code changes
    print("\n🧪 Step 4: Calculate formula (NO code changes needed)...")
    calculator = RenewableCalculator()
    status, target = calculator.calculate('TEST_EXTENSIBILITY')
    
    print(f"\n   Result:")
    print(f"     Status: {status}")
    print(f"     Target: {target}")
    
    if status is not None:
        print(f"\n   ✅ SUCCESS! Formula calculated: {status}")
        print(f"   🎉 SYSTEM IS 100% EXTENSIBLE!")
        print(f"   👉 Admin user can add formulas without developer help")
        return True
    else:
        print(f"\n   ❌ FAILED: Formula returned None")
        print(f"   ⚠️  System NOT fully extensible")
        
        # Debug why it failed
        print("\n🔍 Debugging...")
        
        # Check if variables can be resolved
        from simulator.formula_service import _resolve_variable
        for var in formula.variables.all():
            val = _resolve_variable(var, use_target=False)
            print(f"     {var.variable_name}: {val}")
        
        return False

def test_real_time_update():
    """
    Test if modifying a formula in Admin updates calculations immediately
    """
    print("\n" + "="*70)
    print("REAL-TIME UPDATE TEST: Modify Formula in Admin")
    print("="*70)
    
    # Modify the formula
    print("\n📝 Step 1: Modify formula in Admin...")
    formula = Formula.objects.get(key='TEST_EXTENSIBILITY', category='renewable')
    old_expr = formula.expression
    formula.expression = 'pv * 2'  # Simple doubling formula
    formula.save()
    print(f"   Old: {old_expr}")
    print(f"   New: {formula.expression}")
    
    # Also update FormulaVariable - remove old ones, add new one
    formula.variables.all().delete()
    FormulaVariable.objects.create(
        formula=formula,
        variable_name='pv',
        source_type='renewable_status',
        source_key='10.3',
        default_value=0
    )
    print(f"   ✓ Updated variable mappings")
    
    # Test if it calculates with new formula
    print("\n🧪 Step 2: Calculate with modified formula...")
    calculator = RenewableCalculator()
    # Clear cache to get fresh calculation
    cache_key = f'renewable_TEST_EXTENSIBILITY'
    from django.core.cache import cache
    cache.delete(cache_key)
    
    status, target = calculator.calculate('TEST_EXTENSIBILITY')
    
    # Get expected value (10.3 direct value * 2)
    val_10_3 = RenewableData.objects.get(code='10.3')
    # Use direct status_value, not calculated (avoid recursion in test)
    expected = val_10_3.status_value * 2
    
    print(f"\n   Result: {status}")
    print(f"   Expected: {expected}")
    
    if status is not None and expected is not None:
        diff = abs(status - expected)
        if diff < 0.01:  # Allow small floating point error
            print(f"\n   ✅ SUCCESS! Real-time update works!")
            print(f"   🎉 Formula modified in Admin → Instant calculation update")
            return True
    
    print(f"\n   ❌ FAILED: Real-time update didn't work")
    return False

if __name__ == '__main__':
    try:
        result1 = test_extensibility()
        result2 = test_real_time_update() if result1 else False
        
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(f"  Extensibility Test: {'✅ PASSED' if result1 else '❌ FAILED'}")
        print(f"  Real-Time Update:   {'✅ PASSED' if result2 else '❌ FAILED'}")
        
        if result1 and result2:
            print("\n🎉🎉🎉 SYSTEM IS 100% EXTENSIBLE! 🎉🎉🎉")
            print("Admin users can add/modify formulas without developer help!")
        else:
            print("\n⚠️  System needs fixes for full extensibility")
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        cleanup()
        print("   ✓ Done")
