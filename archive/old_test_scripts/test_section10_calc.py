import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Test specific section 10 codes
test_codes = ['10.2', '10.2.1', '10.4.1.1', '10.4.1.3']

print("Testing Section 10 Calculations:\n")

for code in test_codes:
    renewable = RenewableData.objects.get(code=code)
    print(f"Code: {code}")
    print(f"  Name: {renewable.name}")
    print(f"  Formula: {renewable.formula}")
    print(f"  is_fixed: {renewable.is_fixed}")
    
    calc_status, calc_target = renewable.get_calculated_values()
    print(f"  Calculated Status: {calc_status}")
    print(f"  Calculated Target: {calc_target}")
    print()
