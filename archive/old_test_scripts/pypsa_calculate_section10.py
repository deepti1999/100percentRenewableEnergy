"""
PyPSA: Calculate Section 10 by distributing renewable sources
"""
import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print('='*80)
print('CALCULATING SECTION 10 - RENEWABLE ENERGY DISTRIBUTION')
print('='*80)

# ============================================================================
# STEP 1: SUM ALL RENEWABLE SOURCES (Target = 459.452 Status, 1855.334 Target)
# ============================================================================
print('\nSTEP 1: Sum all renewable energy sources from sections 1-9')
print('-'*80)

# These are the FINAL renewable energy outputs that contribute to section 10
renewable_sources = {
    '9.4.3.3': 'Final electricity supply from renewables',  # Main electricity
    '5.4.2.4': 'Biogas heat for buildings',
    '5.4.3': 'Biomethane for mobile applications',
    '5.4.4': 'Liquid biofuel for mobile applications',
    '6.1.1.2': 'Biodiesel from own cultivation',
    '6.2.2': 'Bioethanol import/export',
    '7.1.2.3': 'Heat pump heat gain from air (buildings)',
    '7.1.4.3': 'Heat pump heat gain from ground (industry)',
    '8.2': 'Deep geothermal building heat',
}

E_total_status = 0
E_total_target = 0

print('Renewable Sources:')
for code, name in renewable_sources.items():
    try:
        item = RenewableData.objects.get(code=code)
        status_val = item.status_value or 0
        target_val = item.target_value or 0
        E_total_status += status_val
        E_total_target += target_val
        print(f'  {code:12s} {name:45s}: Status={status_val:8.3f} Target={target_val:8.3f}')
    except:
        print(f'  {code:12s} {name:45s}: NOT FOUND')

print('-'*80)
print(f'TOTAL RENEWABLE ENERGY: Status={E_total_status:8.3f} GWh, Target={E_total_target:8.3f} GWh')

# ============================================================================
# STEP 2: GET DEMAND FROM VERBRAUCHDATA
# ============================================================================
print('\nSTEP 2: Get demand from VerbrauchData')
print('-'*80)

klik = VerbrauchData.objects.get(code='1')
gebaudewarme = VerbrauchData.objects.get(code='2.0')
prozesswarme = VerbrauchData.objects.get(code='3.0')
mobile_demand_gwh = 171.816  # Calculated

demand_data = [
    {'code': '10.3', 'sector': 'KLIK', 'demand_gwh': klik.status / 1000},
    {'code': '10.4', 'sector': 'Gebäudewärme', 'demand_gwh': gebaudewarme.status / 1000},
    {'code': '10.5', 'sector': 'Prozesswärme', 'demand_gwh': prozesswarme.status / 1000},
    {'code': '10.6', 'sector': 'Mobile Anwendungen', 'demand_gwh': mobile_demand_gwh}
]

demand_df = pd.DataFrame(demand_data)
D_total = demand_df['demand_gwh'].sum()

print(f'{"Sector":<20s} {"Demand (GWh)":<15s} {"Share %":<10s}')
print('-'*50)
for idx, row in demand_df.iterrows():
    share = (row['demand_gwh'] / D_total) * 100
    demand_df.at[idx, 'share_pct'] = share
    print(f"{row['sector']:<20s} {row['demand_gwh']:>12.3f}    {share:>8.1f}%")

print('-'*50)
print(f"{'TOTAL':<20s} {D_total:>12.3f}    {'100.0':>8s}%")

# ============================================================================
# STEP 3: DISTRIBUTE PROPORTIONALLY
# ============================================================================
print('\nSTEP 3: Distribute renewable energy proportionally')
print('-'*80)

demand_df['renewable_status'] = demand_df['demand_gwh'] / D_total * E_total_status
demand_df['renewable_target'] = demand_df['demand_gwh'] / D_total * E_total_target

print(f'{"Code":<8s} {"Sector":<20s} {"Status (GWh)":<15s} {"Target (GWh)":<15s}')
print('-'*60)
for idx, row in demand_df.iterrows():
    print(f"{row['code']:<8s} {row['sector']:<20s} {row['renewable_status']:>12.3f}    {row['renewable_target']:>12.3f}")

# ============================================================================
# STEP 4: SAVE TO DATABASE
# ============================================================================
print('\nSTEP 4: Saving results to database')
print('-'*80)

for idx, row in demand_df.iterrows():
    item = RenewableData.objects.get(code=row['code'])
    item.status_value = row['renewable_status']
    item.target_value = row['renewable_target']
    item.save()
    print(f"Saved {row['code']}: Status={row['renewable_status']:.3f}, Target={row['renewable_target']:.3f}")

# Calculate and save 10.1 (total)
total_10_1 = RenewableData.objects.get(code='10.1')
total_10_1.status_value = E_total_status
total_10_1.target_value = E_total_target
total_10_1.save()
print(f"Saved 10.1: Status={E_total_status:.3f}, Target={E_total_target:.3f}")

print('\n' + '='*80)
print('CALCULATION COMPLETE!')
print('='*80)
print(f'\nTotal renewable energy distributed: Status={E_total_status:.3f} GWh, Target={E_total_target:.3f} GWh')
print(f'Total demand: {D_total:.3f} GWh')
print(f'Renewable coverage: Status={E_total_status/D_total*100:.1f}%, Target={E_total_target/D_total*100:.1f}%')
