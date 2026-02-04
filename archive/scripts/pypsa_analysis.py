"""
PyPSA Energy System Analysis
Analyzes renewable energy surplus and storage requirements
"""

import pypsa
import pandas as pd
import numpy as np
from pathlib import Path
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData


def generate_timeseries_csv(csv_path='pypsa_timeseries.csv', use_smard_data=True):
    """
    Generate hourly timeseries CSV from SMARD real data scaled to target demand
    """
    if use_smard_data:
        # Get target electricity demand from database (Ziel value)
        target_demand_mwh = VerbrauchData.objects.get(code='5').ziel
        target_demand_gwh = target_demand_mwh / 1000  # Convert to GWh
        
        # Load SMARD data
        smard_path = os.path.join(Path(__file__).parent.parent, 'data', 'Actual_generation_202302010000_202401010000_Hour.csv')
        
        # Read SMARD CSV with proper settings
        smard_df = pd.read_csv(smard_path, sep=';', thousands=',', decimal='.')
        
        # Parse dates (use Start date column)
        smard_df['time'] = pd.to_datetime(smard_df['Start date'], format='%b %d, %Y %I:%M %p')
        
        # Calculate SMARD total demand (all generation sources)
        smard_demand_mwh = (smard_df['Biomass [MWh] Calculated resolutions'] +
                           smard_df['Hydropower [MWh] Calculated resolutions'] +
                           smard_df['Wind offshore [MWh] Calculated resolutions'] +
                           smard_df['Wind onshore [MWh] Calculated resolutions'] +
                           smard_df['Photovoltaics [MWh] Calculated resolutions'] +
                           smard_df['Other renewable [MWh] Calculated resolutions'] +
                           smard_df['Nuclear [MWh] Calculated resolutions'] +
                           smard_df['Lignite [MWh] Calculated resolutions'] +
                           smard_df['Hard coal [MWh] Calculated resolutions'] +
                           smard_df['Fossil gas [MWh] Calculated resolutions'] +
                           smard_df['Other conventional [MWh] Calculated resolutions'])
        
        smard_total_demand_gwh = smard_demand_mwh.sum() / 1000
        
        # Calculate scaling factor to match target demand
        scale_factor = target_demand_gwh / smard_total_demand_gwh
        
        print(f"SMARD original demand: {smard_total_demand_gwh:,.1f} GWh")
        print(f"Target demand (Ziel):  {target_demand_gwh:,.1f} GWh")
        print(f"Scaling factor: {scale_factor:.4f}")
        
        # Extract renewable generation and scale to target (convert MWh to GWh)
        df = pd.DataFrame({
            'time': smard_df['time'],
            'solar_GWh': smard_df['Photovoltaics [MWh] Calculated resolutions'] / 1000 * scale_factor,
            'wind_GWh': (smard_df['Wind offshore [MWh] Calculated resolutions'] + 
                        smard_df['Wind onshore [MWh] Calculated resolutions']) / 1000 * scale_factor,
            'biomass_GWh': smard_df['Biomass [MWh] Calculated resolutions'] / 1000 * scale_factor,
            'water_GWh': smard_df['Hydropower [MWh] Calculated resolutions'] / 1000 * scale_factor,
            'demand_GWh': smard_demand_mwh / 1000 * scale_factor
        })
        
        print(f"\nScaled to target:")
        print(f"Loaded SMARD data: {len(df)} hours")
        print(f"Date range: {df['time'].min()} to {df['time'].max()}")
        print(f"Total Solar: {df['solar_GWh'].sum():.1f} GWh")
        print(f"Total Wind: {df['wind_GWh'].sum():.1f} GWh")
        print(f"Total Biomass: {df['biomass_GWh'].sum():.1f} GWh")
        print(f"Total Hydro: {df['water_GWh'].sum():.1f} GWh")
        print(f"Total Demand: {df['demand_GWh'].sum():.1f} GWh")
        
    else:
        # Fallback: Use synthetic profiles from database values
        solar_annual = RenewableData.objects.get(code='9.4.3.3').status_value
        wind_annual = RenewableData.objects.get(code='9.4.3.2').status_value
        biomass_annual = RenewableData.objects.get(code='4.3').status_value
        water_annual = RenewableData.objects.get(code='7.1').status_value
        demand_annual = VerbrauchData.objects.get(code='5').get_effective_value()
        
        # Convert to GWh
        solar_gwh = solar_annual / 1000
        wind_gwh = wind_annual / 1000
        biomass_gwh = biomass_annual / 1000
        water_gwh = water_annual / 1000
        demand_gwh = demand_annual / 1000
        
        # Create hourly timeseries (8760 hours in a year)
        hours = 8760
        dates = pd.date_range(start='2024-01-01', periods=hours, freq='h')
        hour_of_day = np.array([d.hour for d in dates])
        
        # Solar: peaks at noon, zero at night
        solar_profile = np.maximum(0, 1 - ((hour_of_day - 12) / 12) ** 2)
        solar_hourly = solar_profile * (solar_gwh / solar_profile.sum())
        
        # Wind: more variable
        wind_profile = 0.7 + 0.3 * ((hour_of_day - 12) / 12) ** 2
        wind_hourly = wind_profile * (wind_gwh / wind_profile.sum())
        
        # Biomass: constant baseload
        biomass_hourly = np.full(hours, biomass_gwh / hours)
        
        # Water/Hydro: constant
        water_hourly = np.full(hours, water_gwh / hours)
        
        # Demand: higher during day
        demand_profile = 0.6 + 0.4 * np.maximum(0, 1 - ((hour_of_day - 14) / 12) ** 2)
        demand_hourly = demand_profile * (demand_gwh / demand_profile.sum())
        
        # Create DataFrame
        df = pd.DataFrame({
            'time': dates,
            'solar_GWh': solar_hourly,
            'wind_GWh': wind_hourly,
            'biomass_GWh': biomass_hourly,
            'water_GWh': water_hourly,
            'demand_GWh': demand_hourly
        })
    
    df.to_csv(csv_path, index=False)
    return df


def run_pypsa_analysis(csv_path='pypsa_timeseries.csv'):
    """
    Run PyPSA linear optimal power flow analysis
    Returns results dictionary with surplus, generation, and storage data
    """
    # Load data
    data = pd.read_csv(csv_path, parse_dates=["time"])
    data = data.set_index("time")
    
    # Create PyPSA network
    n = pypsa.Network()
    
    # Add time snapshots
    n.set_snapshots(data.index)
    
    # Add electricity bus
    n.add("Bus", "electricity")
    
    # Add demand as load
    n.add("Load", "demand",
          bus="electricity",
          p_set=data["demand_GWh"])
    
    # Add renewable generators
    # Solar
    if data["solar_GWh"].max() > 0:
        n.add("Generator", "solar",
              bus="electricity",
              p_max_pu=data["solar_GWh"] / data["solar_GWh"].max(),
              p_nom=data["solar_GWh"].max(),
              capital_cost=0,
              marginal_cost=0)
    
    # Wind
    if data["wind_GWh"].max() > 0:
        n.add("Generator", "wind",
              bus="electricity",
              p_max_pu=data["wind_GWh"] / data["wind_GWh"].max(),
              p_nom=data["wind_GWh"].max(),
              capital_cost=0,
              marginal_cost=0)
    
    # Biomass
    if data["biomass_GWh"].max() > 0:
        n.add("Generator", "biomass",
              bus="electricity",
              p_max_pu=data["biomass_GWh"] / data["biomass_GWh"].max(),
              p_nom=data["biomass_GWh"].max(),
              capital_cost=0,
              marginal_cost=0)
    
    # Water/Hydro
    if data["water_GWh"].max() > 0:
        n.add("Generator", "water",
              bus="electricity",
              p_max_pu=data["water_GWh"] / data["water_GWh"].max(),
              p_nom=data["water_GWh"].max(),
              capital_cost=0,
              marginal_cost=0)
    
    # Add storage unit (battery)
    n.add("StorageUnit", "battery",
          bus="electricity",
          p_nom=1e6,  # Large capacity
          max_hours=1000,
          efficiency_store=0.65,
          efficiency_dispatch=0.9,
          capital_cost=0,
          marginal_cost=0)
    
    # Run linear optimal power flow
    try:
        n.optimize()
    except Exception as e:
        print(f"Optimization error: {e}")
        # Fallback if optimization fails
        pass
    
    # Extract results
    generation = n.generators_t.p.sum(axis=1) if len(n.generators_t.p.columns) > 0 else pd.Series(0, index=data.index)
    
    # Get load data
    if "demand" in n.loads_t.p.columns:
        load = n.loads_t.p["demand"]
    elif len(n.loads_t.p.columns) > 0:
        load = n.loads_t.p.iloc[:, 0]
    else:
        load = data["demand_GWh"]
    
    storage_charge = n.storage_units_t.p.get("battery", pd.Series(0, index=data.index)) if hasattr(n.storage_units_t, 'p') else pd.Series(0, index=data.index)
    
    # Storage state of charge (energy stored over time)
    if hasattr(n.storage_units_t, 'state_of_charge') and "battery" in n.storage_units_t.state_of_charge.columns:
        storage_soc = n.storage_units_t.state_of_charge["battery"]
    else:
        storage_soc = pd.Series(0, index=data.index)
    
    # Calculate surplus (generation exceeding demand before storage)
    surplus = (generation - load).clip(lower=0)
    total_surplus_gwh = surplus.sum()
    
    # Calculate deficit (demand exceeding generation)
    deficit = (load - generation).clip(lower=0)
    total_deficit_gwh = deficit.sum()
    
    # Storage statistics
    storage_charging = storage_charge.clip(lower=0).sum()  # Positive = charging
    storage_discharging = (-storage_charge).clip(lower=0).sum()  # Negative = discharging
    max_storage_level = storage_soc.max()
    
    # Calculate statistics
    total_generation_gwh = generation.sum()
    total_demand_gwh = load.sum()
    renewable_share = (total_generation_gwh / total_demand_gwh * 100) if total_demand_gwh > 0 else 0
    
    # Sample data for visualization (every 24 hours = daily averages)
    sample_rate = 24
    sampled_indices = list(range(0, len(data), sample_rate))
    
    results = {
        'total_surplus_gwh': total_surplus_gwh,
        'total_deficit_gwh': total_deficit_gwh,
        'total_generation_gwh': total_generation_gwh,
        'total_demand_gwh': total_demand_gwh,
        'renewable_share_percent': renewable_share,
        'storage_charging_gwh': storage_charging,
        'storage_discharging_gwh': storage_discharging,
        'max_storage_level_gwh': max_storage_level,
        # Send only sampled data (365 days instead of 8760 hours)
        'generation_timeseries': [generation.iloc[i] for i in sampled_indices],
        'demand_timeseries': [load.iloc[i] for i in sampled_indices],
        'surplus_timeseries': [surplus.iloc[i] for i in sampled_indices],
        'timestamps': [str(data.index[i])[:10] for i in sampled_indices],  # Just dates
    }
    
    # Add generator breakdown
    if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p') and len(n.generators_t.p.columns) > 0:
        for gen_name in n.generators_t.p.columns:
            results[f'{gen_name}_timeseries'] = n.generators_t.p[gen_name].to_dict()
            results[f'{gen_name}_total_gwh'] = n.generators_t.p[gen_name].sum()
    else:
        # Fallback: use input data
        results['solar_total_gwh'] = data['solar_GWh'].sum()
        results['wind_total_gwh'] = data['wind_GWh'].sum()
        results['biomass_total_gwh'] = data['biomass_GWh'].sum()
        results['water_total_gwh'] = data['water_GWh'].sum()
        results['solar_timeseries'] = data['solar_GWh'].to_dict()
        results['wind_timeseries'] = data['wind_GWh'].to_dict()
        results['biomass_timeseries'] = data['biomass_GWh'].to_dict()
        results['water_timeseries'] = data['water_GWh'].to_dict()
    
    return results


if __name__ == "__main__":
    # Test the analysis
    print("=" * 80)
    print("PyPSA ENERGY SYSTEM ANALYSIS")
    print("=" * 80)
    print("\nGenerating timeseries from database...")
    df = generate_timeseries_csv()
    print(f"✅ Generated {len(df)} hourly records")
    
    print("\nRunning PyPSA linear optimal power flow (LOPF)...")
    results = run_pypsa_analysis()
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print(f"\n📊 GENERATION & DEMAND:")
    print(f"  Total Generation:     {results['total_generation_gwh']:>12,.0f} GWh/year")
    print(f"  Total Demand:         {results['total_demand_gwh']:>12,.0f} GWh/year")
    print(f"  Renewable Share:      {results['renewable_share_percent']:>12.1f} %")
    
    print(f"\n⚡ SURPLUS & DEFICIT:")
    print(f"  Total Surplus:        {results['total_surplus_gwh']:>12,.0f} GWh/year")
    print(f"  Total Deficit:        {results['total_deficit_gwh']:>12,.0f} GWh/year")
    
    print(f"\n🔋 STORAGE STATISTICS:")
    print(f"  Energy Charged:       {results['storage_charging_gwh']:>12,.0f} GWh/year")
    print(f"  Energy Discharged:    {results['storage_discharging_gwh']:>12,.0f} GWh/year")
    print(f"  Max Storage Level:    {results['max_storage_level_gwh']:>12,.0f} GWh")
    
    print(f"\n☀️ GENERATION BREAKDOWN:")
    if 'solar_total_gwh' in results:
        print(f"  Solar:                {results['solar_total_gwh']:>12,.1f} GWh/year")
    if 'wind_total_gwh' in results:
        print(f"  Wind:                 {results['wind_total_gwh']:>12,.1f} GWh/year")
    if 'biomass_total_gwh' in results:
        print(f"  Biomass:              {results['biomass_total_gwh']:>12,.1f} GWh/year")
    if 'water_total_gwh' in results:
        print(f"  Water/Hydro:          {results['water_total_gwh']:>12,.1f} GWh/year")
    
    print("\n" + "=" * 80)
    print(f"\n💡 KEY INSIGHT:")
    print(f"   Total surplus electricity: {results['total_surplus_gwh']:,.0f} GWh/year")
    print(f"   This is the excess renewable energy available after meeting demand")
    print(f"   and accounting for storage efficiency (65% charge / 90% discharge).")
    print("\n" + "=" * 80)
