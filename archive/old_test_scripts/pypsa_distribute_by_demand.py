"""
PyPSA: Distribute Renewable Energy Sources by Actual Demand
============================================================
Takes total renewable energy (10.1) and distributes to sectors
based on their actual demand share from VerbrauchData
"""

import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print('='*80)
print('RENEWABLE ENERGY DISTRIBUTION BY DEMAND SHARE')
print('='*80)

# ============================================================================
# STEP 1: CALCULATE TOTAL RENEWABLE ENERGY FROM SOURCES (Sections 1-9)
# ============================================================================
print('\n⚡ STEP 1: Calculate Total Renewable Energy from Sources')
print('-'*80)

# Main renewable source codes that contribute to final energy
renewable_sources = {
    '1.1.2.1.2': 'Laufwasser (Hydro)',
    '2.1.1.2.2': 'Onshore Wind',
    '2.2.1.2': 'Offshore Wind',
    '3.1.1.2': 'Solar PV',
    '4.4.2': 'Fernwärme aus Biomasse',
    '5.4.2.2': 'Biogas Strom',
    '7.1.2.2': 'Wärmepumpe Gebäude',
    '7.1.4.2': 'Wärmepumpe Industrie',
}

E_total_status = 0
E_total_target = 0

print('Renewable Sources:')
for code, name in renewable_sources.items():
    try:
        item = RenewableData.objects.get(code=code)
        # Values are stored as MWh, convert to GWh
        status_gwh = (item.status_value or 0) / 1000
        target_gwh = (item.target_value or 0) / 1000
        E_total_status += status_gwh
        E_total_target += target_gwh
        print(f'  {code:15s} {name:30s}: Status={status_gwh:8.3f} GWh, Target={target_gwh:8.3f} GWh')
    except Exception as e:
        print(f'  {code:15s} {name:30s}: NOT FOUND')

print('-'*80)
print(f'Total Renewable Energy from Sources:')
print(f'  Status: {E_total_status:.3f} GWh/a')
print(f'  Target: {E_total_target:.3f} GWh/a')

# ============================================================================
# STEP 2: GET ACTUAL DEMAND FROM VERBRAUCHDATA
# ============================================================================
print('\n📊 STEP 2: Actual Energy Demand by Sector (from VerbrauchData)')
print('-'*80)

# Get demand data
klik = VerbrauchData.objects.get(code='1')
gebaudewarme = VerbrauchData.objects.get(code='2.0')
prozesswarme = VerbrauchData.objects.get(code='3.0')
mobile_demand_gwh = 171.816  # Calculated: 1855.292 - 1683.476

# Build demand table
demand_data = [
    {'Sector': 'KLIK', 'Demand_GWh': klik.status / 1000},
    {'Sector': 'Gebäudewärme', 'Demand_GWh': gebaudewarme.status / 1000},
    {'Sector': 'Prozesswärme', 'Demand_GWh': prozesswarme.status / 1000},
    {'Sector': 'Mobile Anwendungen', 'Demand_GWh': mobile_demand_gwh}
]

demand_df = pd.DataFrame(demand_data)
D_total = demand_df['Demand_GWh'].sum()

print(f'{"Sector":<20s} | {"Demand (GWh)":<15s} | {"Share %":<10s}')
print('-'*50)
for idx, row in demand_df.iterrows():
    share = (row['Demand_GWh'] / D_total) * 100
    demand_df.at[idx, 'Share_%'] = share
    print(f"{row['Sector']:<20s} | {row['Demand_GWh']:>12.3f}    | {share:>8.1f}%")

print('-'*50)
print(f"{'TOTAL':<20s} | {D_total:>12.3f}    | {'100.0':>8s}%")

# ============================================================================
# STEP 3: DISTRIBUTE RENEWABLE ENERGY PROPORTIONALLY
# ============================================================================
print('\n🔄 STEP 3: Distribute Renewable Energy by Demand Share')
print('-'*80)

# Calculate allocation using formula: E_sector = E_total × (D_sector / D_total)
demand_df['Renewable_Status_GWh'] = demand_df['Demand_GWh'] / D_total * E_total_status
demand_df['Renewable_Target_GWh'] = demand_df['Demand_GWh'] / D_total * E_total_target

print('\nSTATUS Allocation:')
print(f'{"Sector":<20s} | {"Renewable (GWh)":<15s} | {"% of Total Renewable":<20s}')
print('-'*60)
for idx, row in demand_df.iterrows():
    pct = (row['Renewable_Status_GWh'] / E_total_status) * 100
    print(f"{row['Sector']:<20s} | {row['Renewable_Status_GWh']:>12.3f}    | {pct:>16.1f}%")

print('-'*60)
print(f"{'TOTAL':<20s} | {demand_df['Renewable_Status_GWh'].sum():>12.3f}    | {'100.0':>16s}%")

print('\nTARGET Allocation:')
print(f'{"Sector":<20s} | {"Renewable (GWh)":<15s} | {"% of Total Renewable":<20s}')
print('-'*60)
for idx, row in demand_df.iterrows():
    pct = (row['Renewable_Target_GWh'] / E_total_target) * 100
    print(f"{row['Sector']:<20s} | {row['Renewable_Target_GWh']:>12.3f}    | {pct:>16.1f}%")

print('-'*60)
print(f"{'TOTAL':<20s} | {demand_df['Renewable_Target_GWh'].sum():>12.3f}    | {'100.0':>16s}%")

# ============================================================================
# STEP 4: CALCULATE FOSSIL FUEL GAP
# ============================================================================
print('\n🔥 STEP 4: Fossil Fuel Gap (Demand - Renewable)')
print('-'*80)

demand_df['Fossil_Status_GWh'] = demand_df['Demand_GWh'] - demand_df['Renewable_Status_GWh']
demand_df['Fossil_Target_GWh'] = demand_df['Demand_GWh'] - demand_df['Renewable_Target_GWh']

demand_df['Renewable_%_Status'] = (demand_df['Renewable_Status_GWh'] / demand_df['Demand_GWh']) * 100
demand_df['Renewable_%_Target'] = (demand_df['Renewable_Target_GWh'] / demand_df['Demand_GWh']) * 100

print('\nSTATUS - Energy Mix by Sector:')
print(f'{"Sector":<20s} | {"Demand":>10s} | {"Renewable":>10s} | {"Fossil":>10s} | {"Renewable %":>12s}')
print('-'*75)
for idx, row in demand_df.iterrows():
    print(f"{row['Sector']:<20s} | {row['Demand_GWh']:>10.3f} | {row['Renewable_Status_GWh']:>10.3f} | {row['Fossil_Status_GWh']:>10.3f} | {row['Renewable_%_Status']:>11.1f}%")

total_fossil_status = demand_df['Fossil_Status_GWh'].sum()
renewable_pct_status = (E_total_status / D_total) * 100

print('-'*75)
print(f"{'TOTAL':<20s} | {D_total:>10.3f} | {E_total_status:>10.3f} | {total_fossil_status:>10.3f} | {renewable_pct_status:>11.1f}%")

print('\nTARGET - Energy Mix by Sector:')
print(f'{"Sector":<20s} | {"Demand":>10s} | {"Renewable":>10s} | {"Fossil":>10s} | {"Renewable %":>12s}')
print('-'*75)
for idx, row in demand_df.iterrows():
    print(f"{row['Sector']:<20s} | {row['Demand_GWh']:>10.3f} | {row['Renewable_Target_GWh']:>10.3f} | {row['Fossil_Target_GWh']:>10.3f} | {row['Renewable_%_Target']:>11.1f}%")

total_fossil_target = demand_df['Fossil_Target_GWh'].sum()
renewable_pct_target = (E_total_target / D_total) * 100

print('-'*75)
print(f"{'TOTAL':<20s} | {D_total:>10.3f} | {E_total_target:>10.3f} | {total_fossil_target:>10.3f} | {renewable_pct_target:>11.1f}%")

# ============================================================================
# STEP 5: SAVE RESULTS FOR SECTION 10
# ============================================================================
print('\n'+'='*80)
print('📋 GENERATED VALUES FOR SECTION 10 (to be updated in RenewableData)')
print('='*80)

print('\nSection 10.3 (KLIK):')
klik_row = demand_df[demand_df['Sector'] == 'KLIK'].iloc[0]
print(f'  Status: {klik_row["Renewable_Status_GWh"]:.3f} GWh')
print(f'  Target: {klik_row["Renewable_Target_GWh"]:.3f} GWh')

print('\nSection 10.4 (Gebäudewärme):')
gw_row = demand_df[demand_df['Sector'] == 'Gebäudewärme'].iloc[0]
print(f'  Status: {gw_row["Renewable_Status_GWh"]:.3f} GWh')
print(f'  Target: {gw_row["Renewable_Target_GWh"]:.3f} GWh')

print('\nSection 10.5 (Prozesswärme):')
pw_row = demand_df[demand_df['Sector'] == 'Prozesswärme'].iloc[0]
print(f'  Status: {pw_row["Renewable_Status_GWh"]:.3f} GWh')
print(f'  Target: {pw_row["Renewable_Target_GWh"]:.3f} GWh')

print('\nSection 10.6 (Mobile Anwendungen):')
ma_row = demand_df[demand_df['Sector'] == 'Mobile Anwendungen'].iloc[0]
print(f'  Status: {ma_row["Renewable_Status_GWh"]:.3f} GWh')
print(f'  Target: {ma_row["Renewable_Target_GWh"]:.3f} GWh')

print('\n'+'='*80)
print('✅ Distribution Complete!')
print('='*80)

# Save to CSV
demand_df.to_csv('renewable_energy_distribution_pypsa.csv', index=False)
print('\n💾 Results saved to: renewable_energy_distribution_pypsa.csv')
