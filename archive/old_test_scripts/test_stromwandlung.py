#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/Users/deeptimaheedharan/Desktop/check')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

def test_stromwandlung_formulas():
    print("=== Testing Stromwandlung Formula Calculations ===")
    
    # Verify 4.3.4 has correct values
    v434 = VerbrauchData.objects.get(code='4.3.4')
    print(f'4.3.4 Values: Status={v434.status}, Ziel={v434.ziel}')
    
    # Test the problematic codes
    codes = ['9.2.1.1.1', '9.2.1.1.2', '9.2.1.2']
    
    for code in codes:
        try:
            item = RenewableData.objects.get(code=code)
            print(f'\n--- {code}: {item.name} ---')
            print(f'Formula: {item.formula}')
            print(f'Is Fixed: {item.is_fixed}')
            print(f'Current: Status={item.status_value}, Target={item.target_value}')
            
            if not item.is_fixed and item.formula:
                calc_status, calc_target = item.get_calculated_values()
                print(f'Calculated: Status={calc_status}, Target={calc_target}')
                
                # Update values if calculated successfully
                if calc_status is not None:
                    item.status_value = calc_status
                if calc_target is not None:
                    item.target_value = calc_target
                item.save()
                print('Updated and saved!')
            else:
                print('No calculation needed (fixed value)')
                
        except Exception as e:
            print(f'Error with {code}: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_stromwandlung_formulas()