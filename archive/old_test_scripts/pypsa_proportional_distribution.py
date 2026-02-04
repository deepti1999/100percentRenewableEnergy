"""
PyPSA-style Proportional Renewable Energy Distribution
========================================================
Distributes total renewable energy across sectors proportionally based on their demand.

Formula: E_sector = E_total × (D_sector / D_total)

Where:
- E_sector = renewable energy allocated to sector
- E_total = total renewable energy available
- D_sector = demand of that sector
- D_total = sum of all sector demands
"""

import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print('='*80)
print('PROPORTIONAL RENEWABLE ENERGY DISTRIBUTION (PyPSA-style)')
print('='*80)

# ============================================================================
# STEP 1: GET TOTAL RENEWABLE ENERGY SUPPLY
# ============================================================================
print('\n📊 STEP 1: Total Renewable Energy Supply Available')
print('-'*80)

# Get total renewable supply from RenewableData section 10.1
total_renewable = RenewableData.objects.get(code='10.1')
E_total_status = total_renewable.status_value  # GWh
E_total_target = total_renewable.target_value  # GWh

print(f'Total Renewable Energy (E_total):')
print(f'  Status: {E_total_status:,.3f} GWh')
print(f'  Target: {E_total_target:,.3f} GWh')

# ============================================================================
# STEP 2: GET SECTORAL DEMAND FROM VERBRAUCHDATA
# ============================================================================
print('\n📈 STEP 2: Sectoral Energy Demand (from VerbrauchData)')
print('-'*80)

# Get actual demand values from VerbrauchData
klik = VerbrauchData.objects.get(code='1')
gebaudewarme = VerbrauchData.objects.get(code='2.0')
prozesswarme = VerbrauchData.objects.get(code='3.0')

# Mobile Anwendungen - calculated from total (1855.292 - sum of others)
# This is the missing value to reach total demand of 1,855.292 GWh
mobile_demand_gwh = 171.816  # GWh (calculated: 1855.292 - 1683.476)

# Build demand dictionary
demand_data = []

# KLIK - Kraft, Licht, Information, Kommunikation, Kälte
demand_data.append({
    'Sector': 'KLIK',
    'Code': '1',
    'Demand_Status_MWh': klik.status,
    'Demand_Target_MWh': klik.ziel or klik.status,
    'Demand_Status_GWh': klik.status / 1000,
    'Demand_Target_GWh': (klik.ziel or klik.status) / 1000
})

# Gebäudewärme - Building Heat
demand_data.append({
    'Sector': 'Gebäudewärme',
    'Code': '2.0',
    'Demand_Status_MWh': gebaudewarme.status,
    'Demand_Target_MWh': gebaudewarme.ziel or gebaudewarme.status,
    'Demand_Status_GWh': gebaudewarme.status / 1000,
    'Demand_Target_GWh': (gebaudewarme.ziel or gebaudewarme.status) / 1000
})

# Prozesswärme - Process Heat
demand_data.append({
    'Sector': 'Prozesswärme',
    'Code': '3.0',
    'Demand_Status_MWh': prozesswarme.status,
    'Demand_Target_MWh': prozesswarme.ziel or prozesswarme.status,
    'Demand_Status_GWh': prozesswarme.status / 1000,
    'Demand_Target_GWh': (prozesswarme.ziel or prozesswarme.status) / 1000
})

# Mobile Anwendungen - Transport
# Mobile Anwendungen demand is calculated as: Total (1855.292) - KLIK - GW - PW
demand_data.append({
    'Sector': 'Mobile Anwendungen',
    'Code': '4.x',
    'Demand_Status_MWh': mobile_demand_gwh * 1000,
    'Demand_Target_MWh': mobile_demand_gwh * 1000,
    'Demand_Status_GWh': mobile_demand_gwh,
    'Demand_Target_GWh': mobile_demand_gwh
})

demand_df = pd.DataFrame(demand_data)

# Calculate total demand
D_total_status = demand_df['Demand_Status_GWh'].sum()
D_total_target = demand_df['Demand_Target_GWh'].sum()

print('\nSector Demands:')
for idx, row in demand_df.iterrows():
    print(f"  {row['Sector']:20s}: Status = {row['Demand_Status_GWh']:8.3f} GWh, Target = {row['Demand_Target_GWh']:8.3f} GWh")

print(f'\n  {"TOTAL DEMAND":20s}: Status = {D_total_status:8.3f} GWh, Target = {D_total_target:8.3f} GWh')

# ============================================================================
# STEP 3: CALCULATE DEMAND SHARES
# ============================================================================
print('\n📊 STEP 3: Calculate Each Sector\'s Share of Total Demand')
print('-'*80)

# Calculate shares (percentages)
demand_df['Share_Status_%'] = (demand_df['Demand_Status_GWh'] / D_total_status) * 100
demand_df['Share_Target_%'] = (demand_df['Demand_Target_GWh'] / D_total_target) * 100

print('\nDemand Shares:')
for idx, row in demand_df.iterrows():
    print(f"  {row['Sector']:20s}: Status = {row['Share_Status_%']:5.1f}%, Target = {row['Share_Target_%']:5.1f}%")

# ============================================================================
# STEP 4: PROPORTIONAL ALLOCATION OF RENEWABLE ENERGY
# ============================================================================
print('\n⚡ STEP 4: Allocate Renewable Energy Proportionally to Demand')
print('-'*80)

# Apply the formula: E_sector = E_total × (D_sector / D_total)
demand_df['Renewable_Allocation_Status_GWh'] = (demand_df['Demand_Status_GWh'] / D_total_status) * E_total_status
demand_df['Renewable_Allocation_Target_GWh'] = (demand_df['Demand_Target_GWh'] / D_total_target) * E_total_target

print('\nRenewable Energy Allocation (Proportional to Demand):')
print(f"{'Sector':20s} | {'Status (GWh)':>12s} | {'Target (GWh)':>12s}")
print('-'*50)
for idx, row in demand_df.iterrows():
    print(f"{row['Sector']:20s} | {row['Renewable_Allocation_Status_GWh']:12.3f} | {row['Renewable_Allocation_Target_GWh']:12.3f}")

print('-'*50)
print(f"{'TOTAL':20s} | {demand_df['Renewable_Allocation_Status_GWh'].sum():12.3f} | {demand_df['Renewable_Allocation_Target_GWh'].sum():12.3f}")

# ============================================================================
# STEP 5: CALCULATE FOSSIL FUEL GAP
# ============================================================================
print('\n🔥 STEP 5: Calculate Fossil Fuel Gap (Demand - Renewable)')
print('-'*80)

# Fossil gap = Total demand - Renewable allocation
demand_df['Fossil_Gap_Status_GWh'] = demand_df['Demand_Status_GWh'] - demand_df['Renewable_Allocation_Status_GWh']
demand_df['Fossil_Gap_Target_GWh'] = demand_df['Demand_Target_GWh'] - demand_df['Renewable_Allocation_Target_GWh']

# Calculate renewable percentage
demand_df['Renewable_%_Status'] = (demand_df['Renewable_Allocation_Status_GWh'] / demand_df['Demand_Status_GWh']) * 100
demand_df['Renewable_%_Target'] = (demand_df['Renewable_Allocation_Target_GWh'] / demand_df['Demand_Target_GWh']) * 100

print('\nFossil Fuel Gap by Sector:')
print(f"{'Sector':20s} | {'Status (GWh)':>12s} | {'Target (GWh)':>12s} | {'Renewable % (S)':>15s} | {'Renewable % (T)':>15s}")
print('-'*85)
for idx, row in demand_df.iterrows():
    print(f"{row['Sector']:20s} | {row['Fossil_Gap_Status_GWh']:12.3f} | {row['Fossil_Gap_Target_GWh']:12.3f} | {row['Renewable_%_Status']:14.1f}% | {row['Renewable_%_Target']:14.1f}%")

total_fossil_status = demand_df['Fossil_Gap_Status_GWh'].sum()
total_fossil_target = demand_df['Fossil_Gap_Target_GWh'].sum()
total_renewable_pct_status = (E_total_status / D_total_status) * 100
total_renewable_pct_target = (E_total_target / D_total_target) * 100

print('-'*85)
print(f"{'TOTAL':20s} | {total_fossil_status:12.3f} | {total_fossil_target:12.3f} | {total_renewable_pct_status:14.1f}% | {total_renewable_pct_target:14.1f}%")

# ============================================================================
# STEP 6: SUMMARY TABLE (EXCEL STYLE)
# ============================================================================
print('\n'+'='*80)
print('📋 SUMMARY: Energy Distribution Table (Excel Format)')
print('='*80)

print(f"\n{'Sector':<20s} {'Demand (GWh)':<15s} {'Renewable (GWh)':<18s} {'Fossil (GWh)':<15s} {'Renewable %':<12s}")
print('-'*80)

print('\nSTATUS:')
for idx, row in demand_df.iterrows():
    print(f"{row['Sector']:<20s} {row['Demand_Status_GWh']:>10.3f}     {row['Renewable_Allocation_Status_GWh']:>12.3f}     {row['Fossil_Gap_Status_GWh']:>10.3f}     {row['Renewable_%_Status']:>8.1f}%")
print('-'*80)
print(f"{'TOTAL':<20s} {D_total_status:>10.3f}     {E_total_status:>12.3f}     {total_fossil_status:>10.3f}     {total_renewable_pct_status:>8.1f}%")

print('\nTARGET:')
for idx, row in demand_df.iterrows():
    print(f"{row['Sector']:<20s} {row['Demand_Target_GWh']:>10.3f}     {row['Renewable_Allocation_Target_GWh']:>12.3f}     {row['Fossil_Gap_Target_GWh']:>10.3f}     {row['Renewable_%_Target']:>8.1f}%")
print('-'*80)
print(f"{'TOTAL':<20s} {D_total_target:>10.3f}     {E_total_target:>12.3f}     {total_fossil_target:>10.3f}     {total_renewable_pct_target:>8.1f}%")

print('\n'+'='*80)
print('✅ Distribution Complete!')
print('='*80)

# Save to CSV for reference
output_file = 'renewable_energy_distribution_pypsa.csv'
demand_df.to_csv(output_file, index=False)
print(f'\n💾 Results saved to: {output_file}')
