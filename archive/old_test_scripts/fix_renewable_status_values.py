"""
Fix status values for RenewableData entries that show "-" instead of calculated values.

The issue: These entries have formulas but status_value was set to 0.0 or None incorrectly.
Solution: Manually recalculate using direct formula evaluation without loading all data.
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Manually calculate for these specific codes
def manual_calculate(code):
    """Manually calculate status and target values"""
    entry = RenewableData.objects.get(code=code)
    formula = entry.formula
    
    if not formula:
        return None, None
    
    print(f"\nProcessing {code}: {formula}")
    
    # Get the parts of the formula
    parts = formula.replace(' ', '').split('/')
    
    try:
        if code == '9.2.1.5.2':
            # 9.2.1.5 / 9.2.1.5.1 * 100
            val_9_2_1_5 = RenewableData.objects.get(code='9.2.1.5')
            val_9_2_1_5_1 = RenewableData.objects.get(code='9.2.1.5.1')
            
            # For status: if either is None, result is None. If both exist (including 0.0), calculate
            if val_9_2_1_5.status_value is not None and val_9_2_1_5_1.status_value is not None:
                if val_9_2_1_5_1.status_value != 0:
                    status = (val_9_2_1_5.status_value / val_9_2_1_5_1.status_value) * 100
                else:
                    status = 0.0  # Division by zero for status -> 0
            else:
                status = None
                
            # For target: same logic
            if val_9_2_1_5.target_value is not None and val_9_2_1_5_1.target_value is not None:
                if val_9_2_1_5_1.target_value != 0:
                    target = (val_9_2_1_5.target_value / val_9_2_1_5_1.target_value) * 100
                else:
                    target = 0.0
            else:
                target = None
                
            return status, target
            
        elif code == '9.2.1.5.2.1':
            # 9.2.1.5.2 - 9.2.1.5.2.2
            val_9_2_1_5_2 = RenewableData.objects.get(code='9.2.1.5.2')
            val_9_2_1_5_2_2 = RenewableData.objects.get(code='9.2.1.5.2.2')
            
            # For subtraction, if both values exist (including 0.0), calculate
            if val_9_2_1_5_2.status_value is not None and val_9_2_1_5_2_2.status_value is not None:
                status = val_9_2_1_5_2.status_value - val_9_2_1_5_2_2.status_value
            else:
                status = None
                
            if val_9_2_1_5_2.target_value is not None and val_9_2_1_5_2_2.target_value is not None:
                target = val_9_2_1_5_2.target_value - val_9_2_1_5_2_2.target_value
            else:
                target = None
                
            return status, target
            
        elif code == '9.4.1':
            # 9.2 - 9.2.1.5.2.1 - 9.3.1 + 9.3.1.2 - 9.3.4
            codes_to_get = {
                '9.2': +1,
                '9.2.1.5.2.1': -1,
                '9.3.1': -1,
                '9.3.1.2': +1,
                '9.3.4': -1
            }
            
            status = 0.0
            target = 0.0
            status_has_any = False
            target_has_any = False
            
            for c, sign in codes_to_get.items():
                val = RenewableData.objects.get(code=c)
                if val.status_value is not None:
                    status += sign * val.status_value
                    status_has_any = True
                    
                if val.target_value is not None:
                    target += sign * val.target_value
                    target_has_any = True
                    
            return (status if status_has_any else None), (target if target_has_any else None)
            
        elif code == '9.4.3':
            # 9.4.1 + 9.4.2
            val_9_4_1 = RenewableData.objects.get(code='9.4.1')
            val_9_4_2 = RenewableData.objects.get(code='9.4.2')
            
            # For addition, if both exist (including 0.0), calculate
            if val_9_4_1.status_value is not None and val_9_4_2.status_value is not None:
                status = val_9_4_1.status_value + val_9_4_2.status_value
            else:
                status = None
                
            if val_9_4_1.target_value is not None and val_9_4_2.target_value is not None:
                target = val_9_4_1.target_value + val_9_4_2.target_value
            else:
                target = None
                
            return status, target
            
        elif code == '9.4.3.2':
            # 9.4.3 * 9.4.3.1 / 100
            val_9_4_3 = RenewableData.objects.get(code='9.4.3')
            val_9_4_3_1 = RenewableData.objects.get(code='9.4.3.1')
            
            # For multiplication, if both exist (including 0.0), calculate
            if val_9_4_3.status_value is not None and val_9_4_3_1.status_value is not None:
                status = (val_9_4_3.status_value * val_9_4_3_1.status_value) / 100
            else:
                status = None
                
            if val_9_4_3.target_value is not None and val_9_4_3_1.target_value is not None:
                target = (val_9_4_3.target_value * val_9_4_3_1.target_value) / 100
            else:
                target = None
                
            return status, target
            
        elif code == '9.4.3.3':
            # 9.4.3 - 9.4.3.2
            val_9_4_3 = RenewableData.objects.get(code='9.4.3')
            val_9_4_3_2 = RenewableData.objects.get(code='9.4.3.2')
            
            # For subtraction, if both exist (including 0.0), calculate
            if val_9_4_3.status_value is not None and val_9_4_3_2.status_value is not None:
                status = val_9_4_3.status_value - val_9_4_3_2.status_value
            else:
                status = None
                
            if val_9_4_3.target_value is not None and val_9_4_3_2.target_value is not None:
                target = val_9_4_3.target_value - val_9_4_3_2.target_value
            else:
                target = None
                
            return status, target
            
    except Exception as e:
        print(f"Error calculating {code}: {e}")
        return None, None
    
    return None, None


# Fix the entries in order (dependencies first)
codes_to_fix = ['9.2.1.5.2', '9.2.1.5.2.1', '9.4.1', '9.4.3', '9.4.3.2', '9.4.3.3']

print("=" * 60)
print("Fixing RenewableData status values")
print("=" * 60)

for code in codes_to_fix:
    entry = RenewableData.objects.get(code=code)
    print(f"\n{code}:")
    print(f"  Current: status={entry.status_value}, target={entry.target_value}")
    
    status, target = manual_calculate(code)
    print(f"  Calculated: status={status}, target={target}")
    
    if status is not None or target is not None:
        entry.status_value = status
        entry.target_value = target
        entry.save(update_fields=['status_value', 'target_value', 'updated_at'])
        print(f"  ✅ Updated!")
    else:
        print(f"  ⚠️  Could not calculate - dependencies missing")

print("\n" + "=" * 60)
print("Verification")
print("=" * 60)

for code in codes_to_fix:
    entry = RenewableData.objects.get(code=code)
    print(f"{code}: status={entry.status_value}, target={entry.target_value}")

print("\n✅ Done!")
