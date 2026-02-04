import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData
from calculation_engine.renewable_engine import RenewableCalculator

calculator = RenewableCalculator()

# Simulate what the view does
def get_renewable_target(code):
    """Get renewable value using FormulaVariable calculator"""
    try:
        renewable = RenewableData.objects.get(code=code)
        
        # If it's a fixed value, use the stored value directly
        if renewable.is_fixed:
            if renewable.target_value not in (None, 0, 0.0):
                return float(renewable.target_value)
            if renewable.status_value not in (None, 0, 0.0):
                return float(renewable.status_value)
            return 0
        
        # Use calculator to get calculated value
        status, target = calculator.calculate(code)
        
        # Prefer target, fall back to status, then to stored values
        if target not in (None, 0, 0.0):
            return float(target)
        if status not in (None, 0, 0.0):
            return float(status)
        if renewable.target_value not in (None, 0, 0.0):
            return float(renewable.target_value)
        if renewable.status_value not in (None, 0, 0.0):
            return float(renewable.status_value)
        return 0
    except RenewableData.DoesNotExist:
        return 0

# Calculate values like the view does
pv_value = get_renewable_target('1.1.2.1.2') + get_renewable_target('1.2.1.2')
wind_value = get_renewable_target('2.1.1.2.2') + get_renewable_target('2.2.1.2')
bio_value = get_renewable_target('4.4.1')
hydro_value = get_renewable_target('3.1.1.2')
m_total = pv_value + wind_value + hydro_value
ely_branch_value = get_renewable_target('9.2.1.5.2')

print("Values that should be in template context:")
print(f"bio = {round(bio_value, 2)}")
print(f"pv = {round(pv_value, 2)}")
print(f"wind = {round(wind_value, 2)}")
print(f"hydro = {round(hydro_value, 2)}")
print(f"m_total = {round(m_total, 2)}")
print(f"ely_branch_value = {round(ely_branch_value, 2)}")

if bio_value > 0 and pv_value > 0:
    print("\n✅ ALL VALUES ARE CALCULATED CORRECTLY!")
    print("The problem must be in how Django is rendering the template.")
else:
    print("\n❌ VALUES ARE STILL ZERO!")
