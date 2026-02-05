"""
Debug script to check model parameters
"""
import pypsa
import pandas as pd
import numpy as np

# Load profiles
solar = pd.read_csv("data/solar_promile.csv")["solar_promile"]
wind = pd.read_csv("data/wind_promile.csv")["wind_promile"]
demand = pd.read_csv("data/verbrauch_promile.csv")["verbrauch_promile"]

wind_cf = wind / wind.max()
solar_cf = solar / solar.max()
demand_share = demand / demand.sum()

# Parameters
E_electricity = 1_003_863.64
E_hydrogen = 385_933.329
E_total = E_electricity + E_hydrogen  # No loss rate

E_wind = 706_236.566
E_water_geo = 50_000.0
E_bio = 30_000.0

# Winter H2 profile
day_of_year = np.arange(1, 366)
winter_weight = 1 + 1.5 * np.cos(2 * np.pi * (day_of_year - 1) / 365)
winter_weight = np.clip(winter_weight, 0.2, None)
hydrogen_profile = winter_weight / winter_weight.sum()

# Load profiles  
electricity_daily_gwh = demand_share * E_electricity
hydrogen_daily_gwh = hydrogen_profile * E_hydrogen
total_daily_gwh = electricity_daily_gwh + hydrogen_daily_gwh
total_p_set_mw = total_daily_gwh * 1000 / 24

print("Load check:")
print(f"  Total load: {total_p_set_mw.sum() * 24 / 1000:,.2f} GWh")
print(f"  Target E_total: {E_total:,.2f} GWh")

# Generator p_nom calculations
wind_p_nom_mw = E_wind * 1000 / (wind_cf.sum() * 24)
water_p_nom_mw = E_water_geo * 1000 / (365 * 24)
bio_p_nom_mw = E_bio * 1000 / (365 * 24)

print(f"\nGenerator p_nom (MW):")
print(f"  Wind:      {wind_p_nom_mw:,.0f} MW")
print(f"  Water:     {water_p_nom_mw:,.0f} MW")
print(f"  Bio:       {bio_p_nom_mw:,.0f} MW")

# Check energy from generators
wind_max_energy = wind_p_nom_mw * wind_cf.sum() * 24 / 1000
water_max_energy = water_p_nom_mw * 365 * 24 / 1000
bio_max_energy = bio_p_nom_mw * 365 * 24 / 1000

print(f"\nMax possible energy if fully dispatched (GWh):")
print(f"  Wind:      {wind_max_energy:,.0f} GWh (target: {E_wind:,.0f})")
print(f"  Water:     {water_max_energy:,.0f} GWh (target: {E_water_geo:,.0f})")
print(f"  Bio:       {bio_max_energy:,.0f} GWh (target: {E_bio:,.0f})")

# Solar residual needed
residual = E_total - E_wind - E_water_geo - E_bio
print(f"\nResidual for solar: {residual:,.0f} GWh")

# Check solar CF sum
print(f"\nSolar CF sum: {solar_cf.sum():.2f}")
print(f"Wind CF sum: {wind_cf.sum():.2f}")
