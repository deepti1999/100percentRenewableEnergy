import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print("=== Testing VerbrauchData Access ===\n")

# Test VerbrauchData directly
try:
    vd = VerbrauchData.objects.get(code='6')
    print(f"VerbrauchData code '6':")
    print(f"  status: {vd.status} (type: {type(vd.status)})")
    print(f"  ziel: {vd.ziel} (type: {type(vd.ziel)})")
except Exception as e:
    print(f"Error getting VerbrauchData: {e}")

print("\n=== Testing RenewableData Formula ===\n")

# Test renewable
try:
    renewable = RenewableData.objects.get(code='10.2.1')
    print(f"Renewable 10.2.1:")
    print(f"  Formula: '{renewable.formula}'")
    print(f"  is_fixed: {renewable.is_fixed}")
    
    # Test if formula starts correctly
    if renewable.formula:
        print(f"  Starts with 'VerbrauchData_': {renewable.formula.startswith('VerbrauchData_')}")
        if renewable.formula.startswith('VerbrauchData_'):
            verbrauch_code = renewable.formula.replace('VerbrauchData_', '')
            print(f"  Extracted code: '{verbrauch_code}'")
    
    print("\n=== Calling get_calculated_values() ===\n")
    calc_status, calc_target = renewable.get_calculated_values()
    print(f"  calc_status: {calc_status}")
    print(f"  calc_target: {calc_target}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
