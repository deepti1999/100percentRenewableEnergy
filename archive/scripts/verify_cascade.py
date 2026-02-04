import os
import django
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse, RenewableData, Formula, FormulaVariable
from simulator.recalc_service import run_full_recalc

def verify_cascade():
    print("🚀 Starting Cascade Verification...")
    
    # 1. Setup Test Data
    # Let's use a simple chain: LandUse -> Renewable Item A -> Renewable Item B
    # Item A = LandUse * 10
    # Item B = Item A * 2
    
    # Create or get LandUse
    lu, _ = LandUse.objects.get_or_create(code='TEST_LU', defaults={'status_ha': 100, 'target_ha': 100, 'name': 'Test Land Use'})
    lu.status_ha = 100
    lu.save()
    
    # Create Renewable Item A
    item_a, _ = RenewableData.objects.get_or_create(code='TEST_A', defaults={'status_value': 0, 'target_value': 0, 'name': 'Test Item A'})
    
    # Formula for A: LandUse_TEST_LU * 10
    Formula.objects.update_or_create(
        key='TEST_A', 
        category='renewable',
        defaults={'expression': 'LandUse_TEST_LU * 10', 'is_active': True, 'is_fixed': False}
    )
    FormulaVariable.objects.update_or_create(
        formula=Formula.objects.get(key='TEST_A', category='renewable'),
        variable_name='LandUse_TEST_LU',
        defaults={'source_type': 'landuse_status', 'source_key': 'TEST_LU', 'default_value': 0}
    )
    
    # Create Renewable Item B
    item_b, _ = RenewableData.objects.get_or_create(code='TEST_B', defaults={'status_value': 0, 'target_value': 0, 'name': 'Test Item B'})
    
    # Formula for B: Renewable_TEST_A * 2
    Formula.objects.update_or_create(
        key='TEST_B', 
        category='renewable',
        defaults={'expression': 'Renewable_TEST_A * 2', 'is_active': True, 'is_fixed': False}
    )
    FormulaVariable.objects.update_or_create(
        formula=Formula.objects.get(key='TEST_B', category='renewable'),
        variable_name='Renewable_TEST_A',
        defaults={'source_type': 'renewable_status', 'source_key': 'TEST_A', 'default_value': 0}
    )
    
    print("\n✅ Test Data Setup Complete")
    
    # 2. Modify LandUse and Trigger Recalc
    print("\n📝 Modifying LandUse status_ha to 500...")
    lu.status_ha = 500
    lu.save()
    
    # Manually trigger the full recalc (simulating the button press)
    print("🔄 Running run_full_recalc()...")
    start_time = time.time()
    
    # This function uses the new lookup-aware logic
    from simulator.recalc_service import recalc_all_renewables_full
    summary = recalc_all_renewables_full()
    
    duration = time.time() - start_time
    print(f"⏱️ Recalc finished in {duration:.2f}s")
    
    # 3. Verify Results
    item_a.refresh_from_db()
    item_b.refresh_from_db()
    
    expected_a = 500 * 10  # 5000
    expected_b = 5000 * 2  # 10000
    
    print(f"\n🔍 Verification Results:")
    print(f"   LandUse: {lu.status_ha} (Expected: 500)")
    print(f"   Item A:  {item_a.status_value} (Expected: {expected_a})")
    print(f"   Item B:  {item_b.status_value} (Expected: {expected_b})")
    
    if item_a.status_value == expected_a and item_b.status_value == expected_b:
        print("\n✨ SUCCESS! Cascade worked correctly with fresh values.")
    else:
        print("\n❌ FAILED! Values are incorrect.")
        if item_a.status_value != expected_a:
             print(f"   Item A mismatch: Got {item_a.status_value}, expected {expected_a}")
        if item_b.status_value != expected_b:
             print(f"   Item B mismatch: Got {item_b.status_value}, expected {expected_b}")
             if item_b.status_value == 2000: # 100 * 10 * 2 (Old value)
                 print("   ⚠️  Item B used STALE value of Item A!")

    # Cleanup
    Formula.objects.filter(key__in=['TEST_A', 'TEST_B']).delete()
    RenewableData.objects.filter(code__in=['TEST_A', 'TEST_B']).delete()
    LandUse.objects.filter(code='TEST_LU').delete()

if __name__ == '__main__':
    verify_cascade()
