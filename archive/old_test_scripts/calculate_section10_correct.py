"""
Calculate Section 10 - Endenergieangebot aus erneuerbaren Quellen
Based on Excel structure with correct renewable energy distribution
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('='*80)
print('CALCULATING SECTION 10 - RENEWABLE ENERGY SUPPLY')
print('='*80)

# ============================================================================
# STEP 1: Get renewable ELECTRICITY from Section 9.4.3.3
# ============================================================================
print('\nSTEP 1: Renewable Electricity Supply')
print('-'*80)

elec_item = RenewableData.objects.get(code='9.4.3.3')
elec_status = elec_item.status_value / 1000  # Convert MWh to GWh
elec_target = elec_item.target_value / 1000

print(f'Renewable electricity (9.4.3.3): Status={elec_status:.3f} GWh, Target={elec_target:.3f} GWh')

# ============================================================================
# STEP 2: Get renewable HEAT sources
# ============================================================================
print('\nSTEP 2: Renewable Heat Supply')
print('-'*80)

heat_sources = {
    '5.4.2.4': 'Biogas heat for buildings',
    '7.1.2.3': 'Heat pump air - heat gain',
    '7.1.4.3': 'Heat pump ground - heat gain', 
    '8.2': 'Deep geothermal heat',
    '4.4.2': 'District heating from biomass'
}

heat_status = 0
heat_target = 0

for code, name in heat_sources.items():
    try:
        item = RenewableData.objects.get(code=code)
        s = (item.status_value or 0) / 1000 if (item.status_value or 0) > 1000 else (item.status_value or 0)
        t = (item.target_value or 0) / 1000 if (item.target_value or 0) > 1000 else (item.target_value or 0)
        heat_status += s
        heat_target += t
        print(f'  {code}: {name:40s} S={s:8.3f} T={t:8.3f}')
    except:
        print(f'  {code}: {name:40s} NOT FOUND')

print(f'\nTotal Heat: Status={heat_status:.3f} GWh, Target={heat_target:.3f} GWh')

# ============================================================================
# STEP 3: Get renewable FUELS (biofuels)
# ============================================================================
print('\nSTEP 3: Renewable Fuels Supply')
print('-'*80)

fuel_sources = {
    '5.4.3': 'Biomethane for mobile',
    '5.4.4': 'Liquid biofuel for mobile',
    '6.1.1.2': 'Biodiesel from own cultivation',
    '6.2.2': 'Bioethanol',
    '5.4.3.2': 'Biomethane converted',
    '5.4.4.2': 'Liquid biofuel converted',
}

fuel_status = 0
fuel_target = 0

for code, name in fuel_sources.items():
    try:
        item = RenewableData.objects.get(code=code)
        s = (item.status_value or 0) / 1000 if (item.status_value or 0) > 1000 else (item.status_value or 0)
        t = (item.target_value or 0) / 1000 if (item.target_value or 0) > 1000 else (item.target_value or 0)
        fuel_status += s
        fuel_target += t
        print(f'  {code}: {name:40s} S={s:8.3f} T={t:8.3f}')
    except:
        pass

print(f'\nTotal Fuels: Status={fuel_status:.3f} GWh, Target={fuel_target:.3f} GWh')

# ============================================================================
# STEP 4: Calculate TOTAL RENEWABLE ENERGY (10.1)
# ============================================================================
print('\n' + '='*80)
print('TOTAL RENEWABLE ENERGY SUPPLY (10.1)')
print('='*80)

total_status = elec_status + heat_status + fuel_status
total_target = elec_target + heat_target + fuel_target

print(f'Electricity: Status={elec_status:8.3f} GWh, Target={elec_target:8.3f} GWh')
print(f'Heat:        Status={heat_status:8.3f} GWh, Target={heat_target:8.3f} GWh')
print(f'Fuels:       Status={fuel_status:8.3f} GWh, Target={fuel_target:8.3f} GWh')
print('-'*80)
print(f'TOTAL (10.1): Status={total_status:.3f} GWh, Target={total_target:.3f} GWh')
print()
print(f'Expected:     Status=459.452 GWh, Target=1855.334 GWh')
print(f'Difference:   Status={459.452 - total_status:.3f} GWh, Target={1855.334 - total_target:.3f} GWh')

# ============================================================================
# STEP 5: SAVE 10.1 to database
# ============================================================================
print('\nSaving 10.1 to database...')
item_10_1 = RenewableData.objects.get(code='10.1')
item_10_1.status_value = total_status
item_10_1.target_value = total_target
item_10_1.save()
print(f'Saved 10.1: Status={total_status:.3f}, Target={total_target:.3f}')

print('\n' + '='*80)
print('If difference is not zero, we need to find missing sources!')
print('='*80)
