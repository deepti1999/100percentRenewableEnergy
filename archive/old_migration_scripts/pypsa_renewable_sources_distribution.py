"""
PyPSA: Distribute Renewable Energy SOURCES to Demand SECTORS
=============================================================
Takes renewable energy from sources (sections 1-9) and distributes
them proportionally to demand sectors (10.3, 10.4, 10.5, 10.6)

Formula: Allocation_sector = Total_Renewable_Sources × (Demand_sector / Total_Demand)
"""

import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('='*80)
print('RENEWABLE ENERGY SOURCES → SECTORS DISTRIBUTION (PyPSA)')
print('='*80)

# ============================================================================
# STEP 1: COLLECT RENEWABLE ENERGY SOURCES (Sections 1-9)
# ============================================================================
print('\n⚡ STEP 1: Renewable Energy SOURCES (Supply)')
print('-'*80)

# Define renewable source codes
renewable_sources = {
    # Section 1: Hydro
    '1.1.2.1.2': 'Laufwasser (Hydro)',
    
    # Section 2: Wind
    '2.1.1.2.2': 'Onshore Wind',
    '2.2.1.2.3': 'Offshore Wind',
    
    # Section 3: Solar
    '3.1.1.2': 'Solar PV',
    
    # Section 4: Biogenic fuels
    '4.3.1': 'Biogene Brennstoffe',
    '4.4.2': 'Fernwärme aus Biomasse',
    
    # Section 5: Biogas
    '5.4.2.2': 'Biogas Strom',
    '5.4.2.4': 'Biogas Wärme',
    
    # Section 7: Heat pumps / Ambient heat
    '7.1.2.2': 'Wärmepumpe Gebäude Strom',
    '7.1.4.2': 'Wärmepumpe Industrie Strom',
}

sources_df = []
total_sources_status = 0
total_sources_target = 0

print('Renewable Sources:')
for code, name in renewable_sources.items():
    try:
        item = RenewableData.objects.get(code=code)
        # Values are actually stored as MWh even though unit says GWh/a
        # So divide by 1000 to get actual GWh
        status_gwh = item.status_value / 1000
        target_gwh = item.target_value / 1000
        
        sources_df.append({
            'Code': code,
            'Source': name,
            'Status_GWh': status_gwh,
            'Target_GWh': target_gwh
        })
        total_sources_status += status_gwh
        total_sources_target += target_gwh
        print(f'  {name:40s}: Status={status_gwh:8.3f} GWh, Target={target_gwh:8.3f} GWh')
    except Exception as e:
        print(f'  {name:40s}: NOT FOUND')

print('-'*80)
print(f'  {"TOTAL RENEWABLE SOURCES":40s}: Status={total_sources_status:8.3f} GWh, Target={total_sources_target:8.3f} GWh')

sources_df = pd.DataFrame(sources_df)

# ============================================================================
# STEP 2: GET DEMAND SECTORS (Section 10)
# ============================================================================
print('\n📊 STEP 2: Demand SECTORS (Section 10)')
print('-'*80)

demand_sectors = {
    '10.3': 'KLIK',
    '10.4': 'Gebäudewärme',
    '10.5': 'Prozesswärme',
    '10.6': 'Mobile Anwendungen'
}

demand_df = []
total_demand_status = 0
total_demand_target = 0

print('Demand by Sector:')
for code, name in demand_sectors.items():
    item = RenewableData.objects.get(code=code)
    demand_df.append({
        'Code': code,
        'Sector': name,
        'Demand_Status_GWh': item.status_value,
        'Demand_Target_GWh': item.target_value
    })
    total_demand_status += item.status_value
    total_demand_target += item.target_value
    print(f'  {name:20s}: Status={item.status_value:8.3f} GWh, Target={item.target_value:8.3f} GWh')

print('-'*80)
print(f'  {"TOTAL DEMAND":20s}: Status={total_demand_status:8.3f} GWh, Target={total_demand_target:8.3f} GWh')

demand_df = pd.DataFrame(demand_df)

# Verify totals match
print(f'\n✅ Verification:')
print(f'  Total Sources Status: {total_sources_status:.3f} GWh')
print(f'  Total Demand Status:  {total_demand_status:.3f} GWh')
print(f'  Match: {abs(total_sources_status - total_demand_status) < 0.01}')
print(f'  Total Sources Target: {total_sources_target:.3f} GWh')
print(f'  Total Demand Target:  {total_demand_target:.3f} GWh')
print(f'  Match: {abs(total_sources_target - total_demand_target) < 0.01}')

# ============================================================================
# STEP 3: CALCULATE DEMAND SHARES
# ============================================================================
print('\n📈 STEP 3: Calculate Sector Demand Shares')
print('-'*80)

demand_df['Share_Status_%'] = (demand_df['Demand_Status_GWh'] / total_demand_status) * 100
demand_df['Share_Target_%'] = (demand_df['Demand_Target_GWh'] / total_demand_target) * 100

print('Demand Distribution:')
for idx, row in demand_df.iterrows():
    print(f"  {row['Sector']:20s}: Status={row['Share_Status_%']:5.1f}%, Target={row['Share_Target_%']:5.1f}%")

# ============================================================================
# STEP 4: DISTRIBUTE RENEWABLE SOURCES TO SECTORS
# ============================================================================
print('\n🔄 STEP 4: Proportional Distribution of Renewable Sources to Sectors')
print('-'*80)

# For each renewable source, distribute it to sectors based on demand share
distribution_status = []
distribution_target = []

print('\nSTATUS Distribution:')
print(f"{'Source':40s} | {'KLIK':>10s} | {'GW':>10s} | {'PW':>10s} | {'MA':>10s} | {'Total':>10s}")
print('-'*95)

for idx, source in sources_df.iterrows():
    row_status = {'Source': source['Source']}
    row_target = {'Source': source['Source']}
    
    total_check_status = 0
    total_check_target = 0
    
    for idx2, sector in demand_df.iterrows():
        # STATUS: Distribute source energy proportionally
        allocation_status = source['Status_GWh'] * (sector['Demand_Status_GWh'] / total_demand_status)
        row_status[sector['Sector']] = allocation_status
        total_check_status += allocation_status
        
        # TARGET: Distribute source energy proportionally
        allocation_target = source['Target_GWh'] * (sector['Demand_Target_GWh'] / total_demand_target)
        row_target[sector['Sector']] = allocation_target
        total_check_target += allocation_target
    
    row_status['Total'] = total_check_status
    row_target['Total'] = total_check_target
    
    distribution_status.append(row_status)
    distribution_target.append(row_target)
    
    # Print STATUS distribution for this source
    print(f"{source['Source']:40s} | {row_status['KLIK']:10.3f} | {row_status['Gebäudewärme']:10.3f} | {row_status['Prozesswärme']:10.3f} | {row_status['Mobile Anwendungen']:10.3f} | {row_status['Total']:10.3f}")

print('\nTARGET Distribution:')
print(f"{'Source':40s} | {'KLIK':>10s} | {'GW':>10s} | {'PW':>10s} | {'MA':>10s} | {'Total':>10s}")
print('-'*95)

for row_target in distribution_target:
    print(f"{row_target['Source']:40s} | {row_target['KLIK']:10.3f} | {row_target['Gebäudewärme']:10.3f} | {row_target['Prozesswärme']:10.3f} | {row_target['Mobile Anwendungen']:10.3f} | {row_target['Total']:10.3f}")

# ============================================================================
# STEP 5: SUMMARY - Total Renewable Energy by Sector
# ============================================================================
print('\n'+'='*80)
print('📋 SUMMARY: Total Renewable Energy Received by Each Sector')
print('='*80)

distribution_status_df = pd.DataFrame(distribution_status)
distribution_target_df = pd.DataFrame(distribution_target)

print('\nSTATUS:')
print(f"{'Sector':20s} | {'Total Renewable (GWh)':>20s}")
print('-'*45)
for sector_name in ['KLIK', 'Gebäudewärme', 'Prozesswärme', 'Mobile Anwendungen']:
    total = distribution_status_df[sector_name].sum()
    print(f"{sector_name:20s} | {total:20.3f}")
print('-'*45)
print(f"{'TOTAL':20s} | {distribution_status_df[['KLIK', 'Gebäudewärme', 'Prozesswärme', 'Mobile Anwendungen']].sum().sum():20.3f}")

print('\nTARGET:')
print(f"{'Sector':20s} | {'Total Renewable (GWh)':>20s}")
print('-'*45)
for sector_name in ['KLIK', 'Gebäudewärme', 'Prozesswärme', 'Mobile Anwendungen']:
    total = distribution_target_df[sector_name].sum()
    print(f"{sector_name:20s} | {total:20.3f}")
print('-'*45)
print(f"{'TOTAL':20s} | {distribution_target_df[['KLIK', 'Gebäudewärme', 'Prozesswärme', 'Mobile Anwendungen']].sum().sum():20.3f}")

print('\n'+'='*80)
print('✅ Distribution Complete!')
print('='*80)

# Save results
distribution_status_df.to_csv('renewable_sources_distribution_status.csv', index=False)
distribution_target_df.to_csv('renewable_sources_distribution_target.csv', index=False)
print('\n💾 Results saved to:')
print('   - renewable_sources_distribution_status.csv')
print('   - renewable_sources_distribution_target.csv')
