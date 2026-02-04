import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse, RenewableData
from simulator.recalc_service import unified_recalc_all

def test_cascade():
    # 1. Get LU_1.1
    try:
        lu_11 = LandUse.objects.get(code='LU_1.1')
    except LandUse.DoesNotExist:
        print("❌ LU_1.1 not found")
        return

    # 2. Get 9.1.2 Renewable
    try:
        r_912 = RenewableData.objects.get(code='9.1.2')
    except RenewableData.DoesNotExist:
        print("❌ 9.1.2 not found")
        return

    old_lu_target = lu_11.target_ha
    old_r_target = r_912.target_value

    print(f"Initial LU_1.1 target_ha: {old_lu_target}")
    print(f"Initial 9.1.2 target_value: {old_r_target}")

    # 3. Modify LU_1.1
    new_lu_target = (old_lu_target or 0) + 1000
    print(f"\n🔄 Modifying LU_1.1 target_ha to {new_lu_target}...")
    lu_11.target_ha = new_lu_target
    lu_11.save() # This triggers the signal

    # 4. Check if 9.1.2 updated
    r_912.refresh_from_db()
    new_r_target = r_912.target_value

    print(f"Updated 9.1.2 target_value: {new_r_target}")

    if new_r_target != old_r_target:
        print("✅ 9.1.2 target_value UPDATED!")
    else:
        print("❌ 9.1.2 target_value DID NOT UPDATE!")
        
        # Manually trigger recalc to see if it works when forced
        print("\n🔄 Manually triggering unified_recalc_all()...")
        unified_recalc_all()
        r_912.refresh_from_db()
        if r_912.target_value != old_r_target:
            print(f"✅ 9.1.2 target_value UPDATED after manual recalc! (Value: {r_912.target_value})")
        else:
            print("❌ 9.1.2 target_value STILL DID NOT UPDATE!")

if __name__ == "__main__":
    test_cascade()
