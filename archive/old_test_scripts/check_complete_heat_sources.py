import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('COMPLETE RENEWABLE HEAT SOURCES (from Excel):')
print('='*80)

# All heat sources from user's Excel breakdown
heat_sources = {
    '2.2.1.2.3': 'Solarthermie Gebäudewärme',
    '4.1.3.1': 'Solid biomass → Gebäudewärme (KEY MISSING 88 GWh!)',
    '4.1.3.2': 'Solid biomass → Prozesswärme',
    '4.4.2': 'Bio-waste district heat',
    '5.4.2.4': 'Biogas CHP heat',
    '6.1.2.4': 'Biodiesel CHP heat',
    '8.2': 'Geothermal',
    '7.1.2.3': 'Heat pump air',
    '7.1.4.3': 'Heat pump ground'
}

total_s = 0
total_t = 0

for code, name in heat_sources.items():
    item = RenewableData.objects.filter(code=code).first()
    if item:
        s = item.status_value or 0
        t = item.target_value or 0
        
        # Convert if > 1000 (MWh to GWh)
        if s > 1000:
            s = s / 1000
        if t > 1000:
            t = t / 1000
            
        total_s += s
        total_t += t
        print(f'{code:12s} {name:45s} S={s:8.3f} T={t:8.3f}')
    else:
        print(f'{code:12s} {name:45s} NOT FOUND')

print('='*80)
print(f'TOTAL RENEWABLE HEAT: Status={total_s:.3f} GWh, Target={total_t:.3f} GWh')
print(f'Expected from Excel:  Status=152.287 GWh, Target=615.217 GWh')
print(f'Difference:           Status={152.287 - total_s:.3f} GWh, Target={615.217 - total_t:.3f} GWh')

print('\n' + '='*80)
print('NOW RECALCULATE TOTAL RENEWABLE ENERGY WITH COMPLETE SOURCES:')
print('='*80)

# Electricity
elec_item = RenewableData.objects.filter(code='9.4.3.3').first()
elec_s = elec_item.status_value / 1000 if elec_item and elec_item.status_value else 0
elec_t = elec_item.target_value / 1000 if elec_item and elec_item.target_value else 0
print(f'Electricity (9.4.3.3): Status={elec_s:.3f} GWh, Target={elec_t:.3f} GWh')

print(f'\nHeat (all sources):    Status={total_s:.3f} GWh, Target={total_t:.3f} GWh')

# Fuels
fuel_sources = ['5.4.3', '5.4.4', '6.1.1.2', '6.2.2', '5.4.3.2', '5.4.4.2']
fuel_s = 0
fuel_t = 0
for code in fuel_sources:
    item = RenewableData.objects.filter(code=code).first()
    if item:
        s = item.status_value / 1000 if item.status_value and item.status_value > 1000 else (item.status_value or 0)
        t = item.target_value / 1000 if item.target_value and item.target_value > 1000 else (item.target_value or 0)
        fuel_s += s
        fuel_t += t

print(f'Fuels (biofuels):      Status={fuel_s:.3f} GWh, Target={fuel_t:.3f} GWh')

total_renewable_s = elec_s + total_s + fuel_s
total_renewable_t = elec_t + total_t + fuel_t

print('\n' + '='*80)
print(f'TOTAL RENEWABLE ENERGY (10.1):')
print(f'  Calculated: Status={total_renewable_s:.3f} GWh, Target={total_renewable_t:.3f} GWh')
print(f'  Expected:   Status=459.452 GWh, Target=1855.334 GWh')
print(f'  Difference: Status={459.452 - total_renewable_s:.3f} GWh, Target={1855.334 - total_renewable_t:.3f} GWh')
