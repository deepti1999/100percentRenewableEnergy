import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def update_renewable_values():
    """
    Update renewable energy values for codes starting with 9.2.1
    """
    updates = [
        # code, status_value, target_value
        ('9.2.1.1.1', 0, 0),
        ('9.2.1.1.1.1', 0, 80),
        ('9.2.1.1.2', 0, 0),
        ('9.2.1.2', 0, 0),
        ('9.2.1.2.1', 0, 80),
        ('9.2.1.2.2', 0, 0),
        ('9.2.1.3', 0, 95330),
    ]
    
    print("Updating renewable energy values...")
    print("=" * 60)
    
    for code, status_val, target_val in updates:
        records = RenewableData.objects.filter(code=code)
        
        if records.exists():
            for record in records:
                old_status = record.status_value
                old_target = record.target_value
                
                record.status_value = status_val
                record.target_value = target_val
                record.save()
                
                print(f"\n✓ Updated {code}: {record.name}")
                print(f"  Status: {old_status} → {status_val}")
                print(f"  Target: {old_target} → {target_val}")
        else:
            print(f"\n⚠ No records found for code: {code}")
    
    print("\n" + "=" * 60)
    print("Update complete!")
    
    # Verify the updates
    print("\n\nVerifying updates:")
    print("=" * 60)
    for code, status_val, target_val in updates:
        records = RenewableData.objects.filter(code=code)
        for record in records:
            print(f"\n{code}: {record.name}")
            print(f"  Status: {record.status_value} (Expected: {status_val})")
            print(f"  Target: {record.target_value} (Expected: {target_val})")
            status_match = "✓" if record.status_value == status_val else "✗"
            target_match = "✓" if record.target_value == target_val else "✗"
            print(f"  Match: Status {status_match}, Target {target_match}")

if __name__ == '__main__':
    update_renewable_values()
