import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def update_9_2_1_3_values():
    """
    Update renewable energy values for codes 9.2.1.3.x
    9.2.1.3.1: status=0, target=63
    9.2.1.3.2: status=0, target=formula (9.2.1.3 * 9.2.1.3.1%)
    """
    
    print("Updating renewable energy values for 9.2.1.3.x...")
    print("=" * 60)
    
    # Update 9.2.1.3.1
    code_9_2_1_3_1 = '9.2.1.3.1'
    records_9_2_1_3_1 = RenewableData.objects.filter(code=code_9_2_1_3_1)
    
    if records_9_2_1_3_1.exists():
        for record in records_9_2_1_3_1:
            old_status = record.status_value
            old_target = record.target_value
            
            record.status_value = 0
            record.target_value = 63
            record.save()
            
            print(f"\n✓ Updated {code_9_2_1_3_1}: {record.name}")
            print(f"  Status: {old_status} → 0")
            print(f"  Target: {old_target} → 63")
    else:
        print(f"\n⚠ No records found for code: {code_9_2_1_3_1}")
    
    # Get 9.2.1.3 target value for formula calculation
    code_9_2_1_3 = '9.2.1.3'
    records_9_2_1_3 = RenewableData.objects.filter(code=code_9_2_1_3)
    
    if records_9_2_1_3.exists():
        record_9_2_1_3 = records_9_2_1_3.first()
        value_9_2_1_3_target = record_9_2_1_3.target_value
        print(f"\n📊 9.2.1.3 target value: {value_9_2_1_3_target}")
        
        # Calculate 9.2.1.3.2 target = 9.2.1.3 * 9.2.1.3.1%
        # 9.2.1.3.1% = 63% = 0.63
        calculated_target = value_9_2_1_3_target * (63 / 100)
        
        print(f"📐 Calculated 9.2.1.3.2 target = {value_9_2_1_3_target} * 63% = {calculated_target}")
        
        # Update 9.2.1.3.2
        code_9_2_1_3_2 = '9.2.1.3.2'
        records_9_2_1_3_2 = RenewableData.objects.filter(code=code_9_2_1_3_2)
        
        if records_9_2_1_3_2.exists():
            for record in records_9_2_1_3_2:
                old_status = record.status_value
                old_target = record.target_value
                old_formula = record.formula
                
                record.status_value = 0
                record.target_value = calculated_target
                record.formula = '9.2.1.3 * 9.2.1.3.1%'
                record.is_fixed = False  # This is a calculated value
                record.save()
                
                print(f"\n✓ Updated {code_9_2_1_3_2}: {record.name}")
                print(f"  Status: {old_status} → 0")
                print(f"  Target: {old_target} → {calculated_target}")
                print(f"  Formula: {old_formula} → 9.2.1.3 * 9.2.1.3.1%")
                print(f"  Is Fixed: True → False (calculated)")
        else:
            print(f"\n⚠ No records found for code: {code_9_2_1_3_2}")
    else:
        print(f"\n⚠ No records found for code: {code_9_2_1_3} - cannot calculate 9.2.1.3.2")
    
    print("\n" + "=" * 60)
    print("Update complete!")
    
    # Verify the updates
    print("\n\nVerifying updates:")
    print("=" * 60)
    
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
    update_9_2_1_3_values()
