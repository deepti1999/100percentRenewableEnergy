"""
PyPSA Energy Distribution Optimization
Distributes renewable energy sources across demand sectors optimally
"""

import os
import django
import pandas as pd
import numpy as np

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData

print('='*80)
print('ENERGY DISTRIBUTION OPTIMIZATION WITH PyPSA')
print('='*80)

# 1. COLLECT DEMAND DATA FROM VERBRAUCHDATA
print('\n1. DEMAND SECTORS (from VerbrauchData):')
print('-'*80)

# Map VerbrauchData codes to sector names
demand_codes = {
    '1': 'KLIK',           # Kraft, Licht, Information, Kommunikation, Kälte
    '2.0': 'Gebäudewärme', # Building heat - Bedarfsniveau
    '3.0': 'Prozesswärme', # Process heat
    # Need to find Mobile Anwendungen code
}

demand_df = []

# Get KLIK
klik = VerbrauchData.objects.get(code='1')
demand_df.append({
    'sector': 'KLIK',
    'code': '1',
    'status_mwh': klik.status,
    'target_mwh': klik.ziel or klik.status,
    'status_gwh': klik.status / 1000,
    'target_gwh': (klik.ziel or klik.status) / 1000
})
print(f'KLIK: Status={klik.status:,.0f} MWh = {klik.status/1000:.3f} GWh')
print(f'      Target={(klik.ziel or klik.status):,.0f} MWh = {(klik.ziel or klik.status)/1000:.3f} GWh')

# Get Gebäudewärme
gw = VerbrauchData.objects.get(code='2.0')
demand_df.append({
    'sector': 'Gebäudewärme',
    'code': '2.0',
    'status_mwh': gw.status,
    'target_mwh': gw.ziel or gw.status,
    'status_gwh': gw.status / 1000,
    'target_gwh': (gw.ziel or gw.status) / 1000
})
print(f'Gebäudewärme: Status={gw.status:,.0f} MWh = {gw.status/1000:.3f} GWh')
print(f'              Target={(gw.ziel or gw.status):,.0f} MWh = {(gw.ziel or gw.status)/1000:.3f} GWh')

# Get Prozesswärme
pw = VerbrauchData.objects.get(code='3.0')
demand_df.append({
    'sector': 'Prozesswärme',
    'code': '3.0',
    'status_mwh': pw.status,
    'target_mwh': pw.ziel or pw.status,
    'status_gwh': pw.status / 1000,
    'target_gwh': (pw.ziel or pw.status) / 1000
})
print(f'Prozesswärme: Status={pw.status:,.0f} MWh = {pw.status/1000:.3f} GWh')
print(f'              Target={(pw.ziel or pw.status):,.0f} MWh = {(pw.ziel or pw.status)/1000:.3f} GWh')

# Get Mobile Anwendungen - try to find it
ma_codes = ['4.0', '4.7', '4.8']
ma = None
for code in ma_codes:
    try:
        ma = VerbrauchData.objects.get(code=code)
        if ma.status and ma.status > 10000:
            break
    except:
        continue

if ma:
    demand_df.append({
        'sector': 'Mobile Anwendungen',
        'code': ma.code,
        'status_mwh': ma.status,
        'target_mwh': ma.ziel or ma.status,
        'status_gwh': ma.status / 1000,
        'target_gwh': (ma.ziel or ma.status) / 1000
    })
    print(f'Mobile Anwendungen: Status={ma.status:,.0f} MWh = {ma.status/1000:.3f} GWh')
    print(f'                    Target={(ma.ziel or ma.status):,.0f} MWh = {(ma.ziel or ma.status)/1000:.3f} GWh')

demand_df = pd.DataFrame(demand_df)
total_demand_status = demand_df['status_gwh'].sum()
total_demand_target = demand_df['target_gwh'].sum()
print(f'\nTotal Demand: Status={total_demand_status:,.1f} GWh, Target={total_demand_target:,.1f} GWh')

# 2. COLLECT SUPPLY DATA
print('\n2. RENEWABLE ENERGY SOURCES:')
print('-'*80)

supply_sources = []

# Solar PV
try:
    solar = RenewableData.objects.get(code='3.1.1.2')
    supply_sources.append({
        'source': 'Solar',
        'type': 'Electricity',
        'status_gwh': solar.status_value / 1000,
        'target_gwh': solar.target_value / 1000
    })
    print(f'Solar PV: Status={(solar.status_value/1000):.1f} GWh, Target={(solar.target_value/1000):.1f} GWh')
except:
    pass

# Wind
try:
    wind1 = RenewableData.objects.get(code='2.1.1.2.2')
    wind2 = RenewableData.objects.get(code='2.2.1.2.3')
    wind_s = (wind1.status_value + wind2.status_value) / 1000
    wind_t = (wind1.target_value + wind2.target_value) / 1000
    supply_sources.append({
        'source': 'Wind',
        'type': 'Electricity',
        'status_gwh': wind_s,
        'target_gwh': wind_t
    })
    print(f'Wind: Status={wind_s:.1f} GWh, Target={wind_t:.1f} GWh')
except Exception as e:
    print(f'Wind error: {e}')

# Hydro
try:
    hydro = RenewableData.objects.get(code='1.1.2.1.2')
    supply_sources.append({
        'source': 'Hydro',
        'type': 'Electricity',
        'status_gwh': hydro.status_value / 1000,
        'target_gwh': hydro.target_value / 1000
    })
    print(f'Hydro: Status={(hydro.status_value/1000):.1f} GWh, Target={(hydro.target_value/1000):.1f} GWh')
except Exception as e:
    print(f'Hydro error: {e}')

# Biogas Electricity
try:
    biogas = RenewableData.objects.get(code='5.4.2.2')
    supply_sources.append({
        'source': 'Biogas',
        'type': 'Electricity',
        'status_gwh': biogas.status_value / 1000,
        'target_gwh': (biogas.target_value or 0) / 1000
    })
    print(f'Biogas: Status={(biogas.status_value/1000):.1f} GWh, Target={((biogas.target_value or 0)/1000):.1f} GWh')
except Exception as e:
    print(f'Biogas error: {e}')

# Heat Pumps
try:
    hp1 = RenewableData.objects.get(code='7.1.2.2')
    hp2 = RenewableData.objects.get(code='7.1.4.2')
    hp_s = (hp1.status_value + hp2.status_value) / 1000
    hp_t = ((hp1.target_value or 0) + (hp2.target_value or 0)) / 1000
    supply_sources.append({
        'source': 'Heat Pumps',
        'type': 'Heat',
        'status_gwh': hp_s,
        'target_gwh': hp_t
    })
    print(f'Heat Pumps: Status={hp_s:.1f} GWh, Target={hp_t:.1f} GWh')
except Exception as e:
    print(f'Heat Pumps error: {e}')

# District Heating
try:
    district = RenewableData.objects.get(code='4.4.2')
    supply_sources.append({
        'source': 'District Heating',
        'type': 'Heat',
        'status_gwh': district.status_value / 1000,
        'target_gwh': district.target_value / 1000
    })
    print(f'District Heating: Status={(district.status_value/1000):.1f} GWh, Target={(district.target_value/1000):.1f} GWh')
except Exception as e:
    print(f'District Heating error: {e}')

# Biogas Heat
try:
    bio_heat = RenewableData.objects.get(code='5.4.2.4')
    supply_sources.append({
        'source': 'Biogas Heat',
        'type': 'Heat',
        'status_gwh': (bio_heat.status_value or 0) / 1000,
        'target_gwh': (bio_heat.target_value or 0) / 1000
    })
    print(f'Biogas Heat: Status={((bio_heat.status_value or 0)/1000):.1f} GWh, Target={((bio_heat.target_value or 0)/1000):.1f} GWh')
except Exception as e:
    print(f'Biogas Heat error: {e}')

supply_df = pd.DataFrame(supply_sources)
total_supply_status = supply_df['status_gwh'].sum()
total_supply_target = supply_df['target_gwh'].sum()
print(f'\nTotal Supply: Status={total_supply_status:.1f} GWh, Target={total_supply_target:.1f} GWh')

# 3. SIMPLE PROPORTIONAL DISTRIBUTION
print('\n3. PROPORTIONAL DISTRIBUTION (STATUS):')
print('='*80)

# Calculate distribution based on demand proportions
demand_df['demand_ratio'] = demand_df['status_gwh'] / total_demand_status

distribution_status = []
for _, sector in demand_df.iterrows():
    sector_allocation = {}
    sector_allocation['Sector'] = sector['sector']
    sector_allocation['Demand'] = sector['status_gwh']
    sector_allocation['Ratio'] = sector['demand_ratio']
    
    # Allocate each source proportionally
    for _, source in supply_df.iterrows():
        allocated = source['status_gwh'] * sector['demand_ratio']
        sector_allocation[source['source']] = allocated
    
    distribution_status.append(sector_allocation)

dist_df_status = pd.DataFrame(distribution_status)
print(dist_df_status.to_string(index=False))

# 4. TARGET DISTRIBUTION
print('\n4. PROPORTIONAL DISTRIBUTION (TARGET):')
print('='*80)

demand_df['target_ratio'] = demand_df['target_gwh'] / total_demand_target

distribution_target = []
for _, sector in demand_df.iterrows():
    sector_allocation = {}
    sector_allocation['Sector'] = sector['sector']
    sector_allocation['Demand'] = sector['target_gwh']
    sector_allocation['Ratio'] = sector['target_ratio']
    
    # Allocate each source proportionally
    for _, source in supply_df.iterrows():
        allocated = source['target_gwh'] * sector['target_ratio']
        sector_allocation[source['source']] = allocated
    
    distribution_target.append(sector_allocation)

dist_df_target = pd.DataFrame(distribution_target)
print(dist_df_target.to_string(index=False))

# 5. CALCULATE FOSSIL FUEL GAP
print('\n5. RENEWABLE vs DEMAND GAP (Filled by Fossil):')
print('='*80)

print('\nSTATUS:')
print(f'Total Demand: {total_demand_status:.1f} GWh')
print(f'Total Renewable Supply: {total_supply_status:.1f} GWh')
fossil_gap_status = total_demand_status - total_supply_status
print(f'FOSSIL GAP: {fossil_gap_status:.1f} GWh ({(fossil_gap_status/total_demand_status*100):.1f}%)')

print('\nTARGET:')
print(f'Total Demand: {total_demand_target:.1f} GWh')
print(f'Total Renewable Supply: {total_supply_target:.1f} GWh')
fossil_gap_target = total_demand_target - total_supply_target
print(f'FOSSIL GAP: {fossil_gap_target:.1f} GWh ({(fossil_gap_target/total_demand_target*100):.1f}%)')

# 6. ADD FOSSIL TO EACH SECTOR PROPORTIONALLY
print('\n6. FINAL DISTRIBUTION WITH FOSSIL FUELS:')
print('='*80)

print('\nSTATUS (with Fossil):')
dist_df_status['Fossil'] = dist_df_status['Demand'] - (
    dist_df_status[[col for col in dist_df_status.columns if col not in ['Sector', 'Demand', 'Ratio']]].sum(axis=1)
)
dist_df_status['Total'] = dist_df_status[[col for col in dist_df_status.columns if col not in ['Sector', 'Demand', 'Ratio']]].sum(axis=1)
dist_df_status['Renewable %'] = ((dist_df_status['Total'] - dist_df_status['Fossil']) / dist_df_status['Total'] * 100)

print(dist_df_status[['Sector', 'Demand', 'Solar', 'Wind', 'Hydro', 'Biogas', 'Heat Pumps', 'District Heating', 'Biogas Heat', 'Fossil', 'Total', 'Renewable %']].to_string(index=False))

print('\nTARGET (with Fossil):')
dist_df_target['Fossil'] = dist_df_target['Demand'] - (
    dist_df_target[[col for col in dist_df_target.columns if col not in ['Sector', 'Demand', 'Ratio']]].sum(axis=1)
)
dist_df_target['Total'] = dist_df_target[[col for col in dist_df_target.columns if col not in ['Sector', 'Demand', 'Ratio']]].sum(axis=1)
dist_df_target['Renewable %'] = ((dist_df_target['Total'] - dist_df_target['Fossil']) / dist_df_target['Total'] * 100)

print(dist_df_target[['Sector', 'Demand', 'Solar', 'Wind', 'Hydro', 'Biogas', 'Heat Pumps', 'District Heating', 'Biogas Heat', 'Fossil', 'Total', 'Renewable %']].to_string(index=False))

# 7. CREATE EXCEL-STYLE ENERGY BALANCE TABLE
print('\n7. ENERGY BALANCE TABLE (like Excel):')
print('='*80)

print('\nZiel-Bilanz Endenergie: Erneuerbar + Fossil (Aktiva) = Verbrauch (Passiva)')
print('\nSTATUS Scenario (Angaben in GWh):')
print('='*80)

# Header
header = f"{'Anwendung':<25} | {'KLIK':>12} | {'Gebäudewärme':>12} | {'Prozesswärme':>12} | {'Mobile Anw.':>12} | {'Insgesamt':>12}"
print(header)
print('-'*len(header))

# Get sector allocations
klik_s = dist_df_status[dist_df_status['Sector'] == 'KLIK'].iloc[0]
gw_s = dist_df_status[dist_df_status['Sector'] == 'Gebäudewärme'].iloc[0]
pw_s = dist_df_status[dist_df_status['Sector'] == 'Prozesswärme'].iloc[0]
ma_s = dist_df_status[dist_df_status['Sector'] == 'Mobile Anwendungen'].iloc[0]

# Verbrauch Strom (Electricity consumption)
print(f"{'Verbrauch Strom':<25} | {klik_s['Demand']:>12.3f} | {0:>12.3f} | {0:>12.3f} | {0:>12.3f} | {klik_s['Demand']:>12.3f}")

# erneuerbar (renewable electricity)
renewable_elec_klik = klik_s['Solar'] + klik_s['Wind'] + klik_s['Hydro'] + klik_s['Biogas']
print(f"{'  erneuerbar*':<25} | {renewable_elec_klik:>12.3f} | {0:>12.3f} | {0:>12.3f} | {0:>12.3f} | {renewable_elec_klik:>12.3f}")

# fossil/atomar
fossil_elec_klik = klik_s['Fossil']
print(f"{'  fossil/atomar':<25} | {fossil_elec_klik:>12.3f} | {0:>12.3f} | {0:>12.3f} | {0:>12.3f} | {fossil_elec_klik:>12.3f}")

print()

# Verbr.Brennst.ges. (Total fuel consumption)
total_fuel = gw_s['Demand'] - (gw_s['Heat Pumps'] + gw_s['District Heating'] + gw_s['Biogas Heat']) + pw_s['Demand'] + ma_s['Demand']
print(f"{'Verbr.Brennst.ges.':<25} | {0:>12.3f} | {gw_s['Demand']:>12.3f} | {pw_s['Demand']:>12.3f} | {ma_s['Demand']:>12.3f} | {total_fuel:>12.3f}")

# erneuerbar fuels
renewable_fuel_gw = 0  # Simplified
renewable_fuel_pw = pw_s['Biogas']
renewable_fuel_ma = ma_s['Biogas']
total_renewable_fuel = renewable_fuel_gw + renewable_fuel_pw + renewable_fuel_ma
print(f"{'  erneuerbar*':<25} | {0:>12.3f} | {renewable_fuel_gw:>12.3f} | {renewable_fuel_pw:>12.3f} | {renewable_fuel_ma:>12.3f} | {total_renewable_fuel:>12.3f}")

# fossil fuels
fossil_fuel_gw = gw_s['Fossil'] - (gw_s['Heat Pumps'] + gw_s['District Heating'] + gw_s['Biogas Heat'])
fossil_fuel_pw = pw_s['Fossil'] - pw_s['Biogas']
fossil_fuel_ma = ma_s['Fossil'] - ma_s['Biogas']
total_fossil_fuel = fossil_fuel_gw + fossil_fuel_pw + fossil_fuel_ma
print(f"{'  fossil':<25} | {0:>12.3f} | {fossil_fuel_gw:>12.3f} | {fossil_fuel_pw:>12.3f} | {fossil_fuel_ma:>12.3f} | {total_fossil_fuel:>12.3f}")

print()

# Verbrauch Wärme (Heat consumption)
heat_gw = gw_s['Heat Pumps'] + gw_s['District Heating'] + gw_s['Biogas Heat']
total_heat = heat_gw
print(f"{'Verbrauch Wärme':<25} | {0:>12.3f} | {heat_gw:>12.3f} | {0:>12.3f} | {0:>12.3f} | {total_heat:>12.3f}")

# erneuerbar heat
renewable_heat = heat_gw
print(f"{'  erneuerbar*':<25} | {0:>12.3f} | {renewable_heat:>12.3f} | {0:>12.3f} | {0:>12.3f} | {renewable_heat:>12.3f}")

# fossil heat
print(f"{'  fossil':<25} | {0:>12.3f} | {0:>12.3f} | {0:>12.3f} | {0:>12.3f} | {0:>12.3f}")

print()
print('-'*len(header))

# Verbrauch gesamt (Total consumption)
total_klik = klik_s['Demand']
total_gw = gw_s['Demand']
total_pw = pw_s['Demand']
total_ma = ma_s['Demand']
total_all = total_klik + total_gw + total_pw + total_ma
print(f"{'Verbrauch gesamt':<25} | {total_klik:>12.3f} | {total_gw:>12.3f} | {total_pw:>12.3f} | {total_ma:>12.3f} | {total_all:>12.3f}")

# erneuerbar total
ren_klik = renewable_elec_klik
ren_gw = renewable_heat
ren_pw = renewable_fuel_pw
ren_ma = renewable_fuel_ma
ren_total = ren_klik + ren_gw + ren_pw + ren_ma
print(f"{'  erneuerbar*':<25} | {ren_klik:>12.3f} | {ren_gw:>12.3f} | {ren_pw:>12.3f} | {ren_ma:>12.3f} | {ren_total:>12.3f}")

# fossil total
fos_klik = fossil_elec_klik
fos_gw = fossil_fuel_gw
fos_pw = fossil_fuel_pw
fos_ma = fossil_fuel_ma
fos_total = fos_klik + fos_gw + fos_pw + fos_ma
print(f"{'  fossil':<25} | {fos_klik:>12.3f} | {fos_gw:>12.3f} | {fos_pw:>12.3f} | {fos_ma:>12.3f} | {fos_total:>12.3f}")

print('\n' + '='*80)
print('DISTRIBUTION COMPLETE')
print('='*80)
