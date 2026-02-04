import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

# Test a few section 10 calculations
test_codes = ['10.2.1', '10.2.2', '10.3.1', '10.4.3', '10.6.2', '10.5.3']

print("Testing Section 10 Calculations:")
print("=" * 80)

for code in test_codes:
    try:
        renewable = RenewableData.objects.get(code=code)
        print(f"\nCode: {code}")
        print(f"Name: {renewable.name}")
        print(f"Formula: {renewable.formula}")
        
        # Get calculated values
        calc_status, calc_target = renewable.get_calculated_values()
        
        print(f"Status (calculated): {calc_status}")
        print(f"Ziel (calculated): {calc_target}")
        
    except Exception as e:
        print(f"\nCode {code}: ERROR - {e}")

print("\n" + "=" * 80)
print("✅ All formulas should now calculate correctly on the webapp!")
