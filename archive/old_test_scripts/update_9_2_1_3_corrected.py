import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def update_renewable_values():
    """
    Update renewable energy values:
    9.2.1.3: 0 / 95330 (not 95.330)
    9.2.1.3.1: 0 / 63
    9.2.1.3.2: 0 / calculated (9.2.1.3 × 9.2.1.3.1%)
    """
    
    print("Updating renewable energy values...")
    print("=" * 70)
    
    # Update 9.2.1.3
    code_9_2_1_3 = '9.2.1.3'
    item_9_2_1_3 = RenewableData.objects.filter(code=code_9_2_1_3).first()
    
    if item_9_2_1_3:
        old_status = item_9_2_1_3.status_value
        old_target = item_9_2_1_3.target_value
        
        item_9_2_1_3.status_value = 0
        item_9_2_1_3.target_value = 95330  # 95330 not 95.330
        item_9_2_1_3.save()
        
        print(f"\n✓ Updated {code_9_2_1_3}: {item_9_2_1_3.name}")
        print(f"  Status: {old_status} → 0")
        print(f"  Target: {old_target} → 95330")
    else:
        print(f"\n⚠ No records found for code: {code_9_2_1_3}")
    
    # Update 9.2.1.3.1
    code_9_2_1_3_1 = '9.2.1.3.1'
    item_9_2_1_3_1 = RenewableData.objects.filter(code=code_9_2_1_3_1).first()
    
    if item_9_2_1_3_1:
        old_status = item_9_2_1_3_1.status_value
        old_target = item_9_2_1_3_1.target_value
        
        item_9_2_1_3_1.status_value = 0
        item_9_2_1_3_1.target_value = 63
        item_9_2_1_3_1.save()
        
        print(f"\n✓ Updated {code_9_2_1_3_1}: {item_9_2_1_3_1.name}")
        print(f"  Status: {old_status} → 0")
        print(f"  Target: {old_target} → 63")
    else:
        print(f"\n⚠ No records found for code: {code_9_2_1_3_1}")
    
    # Calculate and update 9.2.1.3.2
    if item_9_2_1_3 and item_9_2_1_3_1:
        # Calculate: 9.2.1.3 × 9.2.1.3.1%
        calculated_target = item_9_2_1_3.target_value * (item_9_2_1_3_1.target_value / 100.0)
        
        print(f"\n📐 Calculated 9.2.1.3.2 target = {item_9_2_1_3.target_value} × {item_9_2_1_3_1.target_value}% = {calculated_target}")
        
        code_9_2_1_3_2 = '9.2.1.3.2'
        item_9_2_1_3_2 = RenewableData.objects.filter(code=code_9_2_1_3_2).first()
        
        if item_9_2_1_3_2:
            old_status = item_9_2_1_3_2.status_value
            old_target = item_9_2_1_3_2.target_value
            
            item_9_2_1_3_2.status_value = 0
            item_9_2_1_3_2.target_value = calculated_target
            item_9_2_1_3_2.formula = '9.2.1.3 * 9.2.1.3.1%'
            item_9_2_1_3_2.is_fixed = False  # This is a calculated value
            item_9_2_1_3_2.save()
            
            print(f"\n✓ Updated {code_9_2_1_3_2}: {item_9_2_1_3_2.name}")
            print(f"  Status: {old_status} → 0")
            print(f"  Target: {old_target} → {calculated_target}")
            print(f"  Formula: 9.2.1.3 * 9.2.1.3.1%")
            print(f"  Is Fixed: False (calculated)")
        else:
            print(f"\n⚠ No records found for code: {code_9_2_1_3_2}")
    
    print("\n" + "=" * 70)
    print("Update complete!")
    
    # Verify the updates
    print("\n\nVerifying updates:")
    print("=" * 70)
    
    for code in ['9.2.1.3', '9.2.1.3.1', '9.2.1.3.2']:
        records = RenewableData.objects.filter(code=code)
        if records.exists():
            for record in records:
                print(f"\n{code}: {record.name}")
                print(f"  Status: {record.status_value}")
                print(f"  Target: {record.target_value}")
                if record.formula:
                    print(f"  Formula: {record.formula}")
                print(f"  Is Fixed: {record.is_fixed}")

if __name__ == '__main__':
    update_renewable_values()
