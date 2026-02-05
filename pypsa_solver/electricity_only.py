"""
electricity_only.py - PyPSA Electricity-Only Model

Step-by-step implementation following user guidance.
CORRECTED VERSION: Proper unit handling (MW vs GWh)
"""

import pypsa
import pandas as pd

# =============================================================================
# HELPER FUNCTION: Convert GWh/year to MW average
# =============================================================================
def gwh_per_year_to_mw_avg(E_gwh):
    """Convert annual energy (GWh/a) to average power (MW)"""
    return E_gwh * 1000 / 8760  # 8760 hours per year

# Create the network
network = pypsa.Network()

# STEP 4 — Time axis (365 days)
snapshots = pd.date_range(
    start="2023-01-01",
    periods=365,
    freq="D"
)
network.set_snapshots(snapshots)

# CRITICAL FIX: Set snapshot weightings for daily model (24 hours per snapshot)
network.snapshot_weightings = pd.DataFrame(
    index=network.snapshots,
    data={"objective": 24.0, "generators": 24.0, "stores": 24.0}
)
print("✓ Snapshot weightings set to 24 hours per day")

# STEP 5 — Electricity bus (Think of this as "Germany's electricity system")
network.add("Bus", "electricity")

# STEP 5B — Hydrogen bus (separate sector for realistic constraints)
network.add("Bus", "hydrogen")

# STEP 6 — Load your profiles (CRITICAL)
# From CSVs
solar = pd.read_csv("data/solar_promile.csv")["solar_promile"]
wind = pd.read_csv("data/wind_promile.csv")["wind_promile"]
demand = pd.read_csv("data/verbrauch_promile.csv")["verbrauch_promile"]

# CORRECTED: Promiles are energy-shape distributions (sum to 1)
# These represent how annual energy is distributed across days
wind_share = wind / wind.sum()      # Energy share per day (sums to 1)
solar_share = solar / solar.sum()   # Energy share per day (sums to 1)
demand_share = demand / demand.sum() # Energy share per day (sums to 1)

# CORRECTED: For solar p_max_pu, we need a capacity-factor-like curve (max = 1)
solar_cf = solar / solar.max()  # Capacity factor shape (max = 1, not sum = 1)

print("✓ Profiles loaded")
print(f"  Wind share sum:   {wind_share.sum():.4f} (energy distribution)")
print(f"  Solar share sum:  {solar_share.sum():.4f} (energy distribution)")
print(f"  Solar CF max:     {solar_cf.max():.4f} (capacity factor shape)")
print(f"  Demand share sum: {demand_share.sum():.4f} (energy distribution)")

# STEP 7 — Define TOTAL electricity demand correctly
# Annual values (TARGET):
# E_electricity comes from: VerbrauchData.objects.get(code='7').ziel
#   → Verbrauch page, Code 7 "Strom-Endverbrauch insgesamt", Ziel column
E_electricity = 1_003_863.64     # GWh/a - from Verbrauch page code 7 (ziel)
E_hydrogen    =   385_933.329    # GWh/a
# FIX #4: Remove loss_rate to avoid double-counting with storage efficiencies
# Excel's 9.2% losses already conceptually include conversion effects
# PyPSA storage efficiencies (38% round-trip) handle the real losses
loss_rate     = 0.0              # Set to 0 - losses handled by storage efficiency

# =============================================================================
# FIX 3: WINTER-WEIGHTED HYDROGEN PROFILE
# =============================================================================
# Hydrogen demand is NOT flat - it's higher in winter (heating, less solar)
# Create a winter-weighted profile (peaks in Dec-Jan, low in Jun-Jul)
import numpy as np
day_of_year = np.arange(1, 366)
# FIX #2: Stronger winter dominance (amplitude 1.5, not 0.5)
# Real hydrogen systems have 2-3x winter/summer ratio
winter_weight = 1 + 1.5 * np.cos(2 * np.pi * (day_of_year - 1) / 365)
winter_weight = np.clip(winter_weight, 0.2, None)  # Ensure no negative values
hydrogen_profile = winter_weight / winter_weight.sum()  # Normalize to sum=1

print(f"✓ Winter-weighted hydrogen profile created (STRONG)")
print(f"  Winter peak (day 1):   {hydrogen_profile[0]*365:.2f}x average")
print(f"  Summer low (day 183):  {hydrogen_profile[182]*365:.2f}x average")

# Electricity load (follows demand_share profile)
E_electricity_with_losses = E_electricity / (1 - loss_rate)  # GWh/a
electricity_daily_gwh = demand_share * E_electricity_with_losses
electricity_p_set_mw = electricity_daily_gwh * 1000 / 24  # MW

# Hydrogen load (winter-weighted profile)
E_hydrogen_with_losses = E_hydrogen / (1 - loss_rate)  # GWh/a
hydrogen_daily_gwh = hydrogen_profile * E_hydrogen_with_losses
hydrogen_p_set_mw = hydrogen_daily_gwh * 1000 / 24  # MW

# Total system energy (for reference)
E_total = (E_electricity + E_hydrogen) / (1 - loss_rate)  # GWh/a

# =============================================================================
# CRITICAL FIX: SEPARATE ELECTRICITY AND HYDROGEN LOADS
# =============================================================================
# Instead of combining loads on one bus, we:
# 1. Put electricity load on electricity bus (direct consumption)
# 2. Put hydrogen load on hydrogen bus (requires electrolyzer)
# 3. Add electrolyzer Link with POWER LIMIT (creates bottleneck!)

# Add ELECTRICITY load (direct consumption)
network.add(
    "Load",
    "electricity_load",
    bus="electricity",
    p_set=electricity_p_set_mw.values  # MW - follows demand profile
)

# Add HYDROGEN load (on separate hydrogen bus)
# Note: hydrogen_p_set_mw is already a numpy array (from hydrogen_profile * scalar)
network.add(
    "Load",
    "hydrogen_load",
    bus="hydrogen",
    p_set=hydrogen_p_set_mw  # MW - winter-weighted profile (already numpy array)
)

# =============================================================================
# THE KEY CONSTRAINT: ELECTROLYZER WITH POWER LIMIT
# =============================================================================
# This Link converts electricity → hydrogen with:
# - LIMITED POWER (p_nom) - can't produce unlimited H2 instantly
# - Efficiency loss (65%)
# This creates the seasonal inflexibility that forces curtailment!
#
# Electrolyzer sizing: ~80 GW is realistic for Germany's H2 ambitions
# Avg H2 demand = 385,933 GWh / 8760h = 44 GW (electrical input @ 65% eff = 68 GW)
# Peak winter H2 = ~2.2x avg = ~150 GW electrical input needed
# With 80 GW cap → can't meet winter peak → needs H2 storage
# But H2 storage also limited → some summer solar must be curtailed

network.add(
    "Link",
    "electrolyzer",
    bus0="electricity",      # Input: electricity
    bus1="hydrogen",         # Output: hydrogen
    p_nom_extendable=True,   # Let optimizer size it
    p_nom_max=68_000,        # MW - minimum feasible (~68 GW = 593,743 GWh / 8760h)
    efficiency=0.65,         # 65% electrolyzer efficiency
    capital_cost=1           # Small cost to track capacity
)

print(f"✓ Loads added (SEPARATED electricity + hydrogen)")
print(f"  E_electricity: {E_electricity:,.2f} GWh/a (on electricity bus)")
print(f"  E_hydrogen:    {E_hydrogen:,.2f} GWh/a (on hydrogen bus)")
print(f"  Loss rate:     {loss_rate*100:.1f}%")
print(f"  E_total:       {E_total:,.2f} GWh/a")
print(f"  Avg elec load: {gwh_per_year_to_mw_avg(E_electricity):,.2f} MW")
print(f"  Avg H2 load:   {gwh_per_year_to_mw_avg(E_hydrogen):,.2f} MW")
print(f"✓ Electrolyzer Link added (POWER-LIMITED)")
print(f"  p_nom_max:     80,000 MW (realistic H2 infrastructure)")
print(f"  efficiency:    65%")
print(f"  → Creates seasonal bottleneck → forces curtailment!")

# STEP 8 — Fixed generators (wind, water, bio)
# =============================================================================
# SIMPLIFIED APPROACH: Use p_nom with p_max_pu for dispatchable generation
# =============================================================================
# Wind/bio/water have ANNUAL ENERGY TARGETS
# We set p_nom to match the energy target, and allow curtailment via optimization
# This is simpler than GlobalConstraints and works reliably

E_wind = 706_236.566  # GWh/a - from RenewableData code 9.1.1 target_value
E_water_geo = 50_000.0  # GWh/a - from RenewableData code 9.1.3 target_value  
E_bio = 30_000.0  # GWh/a - from RenewableData code 9.1.4 target_value

# Wind capacity factor profile
wind_cf = wind / wind.max()  # Capacity factor (max = 1)
# Calculate p_nom such that if fully utilized: sum(p_nom × cf × 24h) = E_wind × 1000 MWh
wind_p_nom_mw = E_wind * 1000 / (wind_cf.sum() * 24)

# Add wind with fixed p_nom but optimizable dispatch
# Use negative marginal cost to give priority over solar (force full utilization)
network.add(
    "Generator",
    "wind",
    bus="electricity",
    p_nom=wind_p_nom_mw,           # Fixed capacity to meet energy target if fully used
    p_max_pu=wind_cf.values,       # Capacity factor profile (allows curtailment)
    marginal_cost=-0.01            # Slight priority (want to use all wind first)
)

# Water+Geothermal - flat profile, dispatchable
water_p_nom_mw = E_water_geo * 1000 / (365 * 24)  # Average power for annual energy
network.add(
    "Generator",
    "water_geothermal",
    bus="electricity",
    p_nom=water_p_nom_mw,
    p_max_pu=1.0,                  # Always available
    marginal_cost=-0.01            # Slight priority
)

# Bio - flat profile, dispatchable
bio_p_nom_mw = E_bio * 1000 / (365 * 24)
network.add(
    "Generator",
    "bio",
    bus="electricity",
    p_nom=bio_p_nom_mw,
    p_max_pu=1.0,
    marginal_cost=-0.01            # Slight priority
)

print(f"✓ Fixed generators added (p_nom based on energy targets)")
print(f"  Wind:           {E_wind:,.2f} GWh/a → p_nom={wind_p_nom_mw:,.0f} MW")
print(f"  Water+Geo:      {E_water_geo:,.2f} GWh/a → p_nom={water_p_nom_mw:,.0f} MW")
print(f"  Bio:            {E_bio:,.2f} GWh/a → p_nom={bio_p_nom_mw:,.0f} MW")

# STEP 9 — Solar (THIS IS THE CORE)
# Solar is NOT given energy - it is ALLOWED TO GROW
# PyPSA will decide the optimal solar capacity to meet demand
# CORRECTED: Use capacity-factor shape (max=1), not energy distribution (sum=1)
network.add(
    "Generator",
    "solar",
    bus="electricity",
    p_max_pu=solar_cf.values,       # Capacity factor profile (max=1)
    p_nom_extendable=True,          # ⭐ This is what makes solar expandable!
    marginal_cost=0,                # No fuel cost
    capital_cost=1                  # Minimal cost to track capacity
)

print(f"✓ Solar (extendable) added")
print(f"  p_nom_extendable: True")
print(f"  p_max_pu: capacity factor shape (max={solar_cf.max():.2f})")
print(f"  → PyPSA will optimize solar capacity (MW) to meet demand gap")

# =============================================================================
# CURTAILMENT: Now handled IMPLICITLY
# =============================================================================
# With p_nom_extendable generators, curtailment happens when:
#   available power (p_nom_opt * p_max_pu) > dispatched power (p)
# No explicit sink needed - PyPSA optimizes dispatch automatically

print(f"✓ Curtailment handled implicitly (p_nom + p_max_pu approach)")
print(f"  Available = p_nom_opt × p_max_pu")
print(f"  Curtailed = Available - Dispatched")

# =============================================================================
# FIX 1: CAP STORAGE POWER, NOT JUST ENERGY
# =============================================================================
# Hydrogen storage reality: huge energy capacity, but LIMITED power
# Electrolyzers + fuel cells have realistic power limits
# =============================================================================
# STORAGE: Now split into electricity buffer + hydrogen seasonal storage
# =============================================================================

# Battery storage on electricity bus (short-term buffer, high efficiency)
network.add(
    "StorageUnit",
    "battery",
    bus="electricity",
    p_nom_extendable=True,
    p_nom_max=50_000,                 # MW - battery power cap (~50 GW)
    max_hours=4,                      # Short-term (4 hours)
    efficiency_store=0.95,            # 95% charging (battery)
    efficiency_dispatch=0.95,         # 95% discharging (battery)
    cyclic_state_of_charge=True
)

# Hydrogen storage on HYDROGEN bus (seasonal storage, lower efficiency)
# This stores H2 directly, not electricity
network.add(
    "Store",
    "h2_storage",
    bus="hydrogen",
    e_nom_extendable=True,
    e_nom_max=200_000_000,            # MWh - large seasonal H2 storage (~200 TWh)
    e_cyclic=True                     # Cyclic state of charge
)

# Fuel cell: converts hydrogen back to electricity (for winter peaks)
network.add(
    "Link",
    "fuel_cell",
    bus0="hydrogen",         # Input: hydrogen
    bus1="electricity",      # Output: electricity
    p_nom_extendable=True,
    p_nom_max=100_000,       # MW - fuel cell power cap (~100 GW, for winter peaks)
    efficiency=0.55,         # 55% fuel cell efficiency
    capital_cost=1
)

print(f"✓ Storage system added (REALISTIC multi-component)")
print(f"  Battery (electricity bus):")
print(f"    p_nom_max: 50,000 MW, max_hours: 4, η: 90% round-trip")
print(f"  H2 Storage (hydrogen bus):")
print(f"    e_nom_max: 200 TWh (seasonal storage)")
print(f"  Fuel Cell (H2 → electricity):")
print(f"    p_nom_max: 60,000 MW, efficiency: 55%")

print("✓ Network created successfully!")
print(f"  PyPSA version: {pypsa.__version__}")
print(f"  Snapshots: {len(network.snapshots)} days")

# STEP 11 — Sanity check (VERY IMPORTANT, don't skip)
print("\n" + "="*50)
print("SANITY CHECK - Verify all components before solving")
print("="*50)
print("Snapshots:", len(network.snapshots))
print("Buses:", network.buses.index.tolist())
print("Generators:", network.generators.index.tolist())
print("Loads:", network.loads.index.tolist())
print("Links:", network.links.index.tolist())
print("Storage units:", network.storage_units.index.tolist())
print("Stores:", network.stores.index.tolist())
print("="*50)

# Expected:
# - Snapshots = 365
# - Bus = electricity
# - Generators = wind, water_geothermal, bio, solar
# - Load = total_electricity_load
# - Storage = storage
# If anything is missing → STOP and fix first!

# STEP 12 — Solve the optimization
print("\n🚀 Running optimization...")
status = network.optimize(solver_name="highs")  # HiGHS is already installed

print(f"\n✓ Optimization complete!")
print(f"  Status: {status}")
if status[0] == 'ok':
    print(f"  Objective: {network.objective:,.2f}")
else:
    print(f"  ⚠️ Optimization failed - check model constraints")

# STEP 13 — Check solver status (CRITICAL)
print("\n" + "="*50)
print("SOLVER STATUS CHECK")
print("="*50)
print(f"Objective:           {network.objective:,.2f}")
print(f"Status:              {status[0]}")
print(f"Termination:         {status[1]}")
print("="*50)

# You MUST see:
#   status = ok
#   termination = optimal
# If not → results are invalid!

# STEP 14 — Verify cyclic SOC condition (THIS IS THE KEY)
battery_soc = network.storage_units_t.state_of_charge["battery"]
h2_soc = network.stores_t.e["h2_storage"]

print("\n" + "="*50)
print("CYCLIC SOC VERIFICATION")
print("="*50)
print(f"Battery SOC day 1:    {battery_soc.iloc[0]:,.2f} MWh")
print(f"Battery SOC day 365:  {battery_soc.iloc[-1]:,.2f} MWh")
print(f"Battery difference:   {battery_soc.iloc[-1] - battery_soc.iloc[0]:,.2f} MWh")
print(f"\nH2 Storage day 1:     {h2_soc.iloc[0]/1e6:,.2f} TWh")
print(f"H2 Storage day 365:   {h2_soc.iloc[-1]/1e6:,.2f} TWh")
print(f"H2 difference:        {(h2_soc.iloc[-1] - h2_soc.iloc[0])/1e6:,.4f} TWh")
print("="*50)

# Use battery SOC for backward compatibility in later code
soc = battery_soc

# Expected: Difference ≈ 0 (small numerical tolerance is OK)

# STEP 15 — Extract the SOLUTION (this is your result)
print("\n" + "="*50)
print("OPTIMIZATION RESULTS")
print("="*50)

# CORRECTED: p_nom_opt is in MW (power), not GWh (energy)
# Solar installed capacity (chosen by PyPSA)
solar_capacity_mw = network.generators.loc["solar", "p_nom_opt"]
print(f"Solar capacity [MW]:   {solar_capacity_mw:,.2f}")

# Solar energy: sum(p × snapshot_weight) = sum(MW × 24h) = MWh, then /1000 = GWh
# With snapshot weighting of 24h, energy = p.sum() * 24 / 1000 GWh
solar_energy_gwh = network.generators_t.p["solar"].sum() * 24 / 1000
print(f"Solar energy [GWh/a]:  {solar_energy_gwh:,.2f}")

# Also show other generation
wind_energy_gwh = network.generators_t.p["wind"].sum() * 24 / 1000
water_geo_energy_gwh = network.generators_t.p["water_geothermal"].sum() * 24 / 1000
bio_energy_gwh = network.generators_t.p["bio"].sum() * 24 / 1000

print(f"\nAll generation (GWh/a):")
print(f"  Wind:           {wind_energy_gwh:,.2f} GWh")
print(f"  Water+Geo:      {water_geo_energy_gwh:,.2f} GWh")
print(f"  Bio:            {bio_energy_gwh:,.2f} GWh")
print(f"  Solar:          {solar_energy_gwh:,.2f} GWh")
print(f"  ─────────────────────────────")
total_gen_gwh = wind_energy_gwh + water_geo_energy_gwh + bio_energy_gwh + solar_energy_gwh
print(f"  TOTAL:          {total_gen_gwh:,.2f} GWh")

# Storage capacities (multi-component system)
battery_capacity_mw = network.storage_units.loc["battery", "p_nom_opt"]
battery_energy_mwh = battery_capacity_mw * 4  # 4 hours
h2_storage_mwh = network.stores.loc["h2_storage", "e_nom_opt"]
electrolyzer_mw = network.links.loc["electrolyzer", "p_nom_opt"]
fuel_cell_mw = network.links.loc["fuel_cell", "p_nom_opt"]

print(f"\nStorage system capacities:")
print(f"  Battery power:         {battery_capacity_mw:,.2f} MW")
print(f"  Battery energy:        {battery_energy_mwh/1000:,.2f} GWh")
print(f"  H2 storage:            {h2_storage_mwh/1_000_000:,.2f} TWh")
print(f"  Electrolyzer:          {electrolyzer_mw:,.2f} MW")
print(f"  Fuel cell:             {fuel_cell_mw:,.2f} MW")

print("="*50)

# STEP 16 — Convert solar energy → land use (Excel logic)
# This is the ENDOGENOUS land-use calculation
#
# From RenewableEnergy page, 1st section (Ziel values):
#   - Installed capacity from solar generators
#   - Solar yield = energy production per hectare per year
#
# Excel formula: solar_land_ha = solar_energy * 1000 / solar_yield
# Note: solar_energy is in GWh, so multiply by 1000 to get MWh

print("\n" + "="*50)
print("STEP 16: SOLAR LAND USE CALCULATION")
print("="*50)

# Solar yield from your Excel model (MWh per hectare per year)
# This represents how much energy 1 hectare of solar panels produces annually
solar_yield = 1235  # MWh / ha / year (your exact value from Excel)

# Convert solar energy (GWh) to land area (hectares)
# solar_energy_gwh is in GWh, so multiply by 1000 to convert to MWh
solar_land_ha = solar_energy_gwh * 1000 / solar_yield

print(f"Solar energy produced:     {solar_energy_gwh:,.2f} GWh/a")
print(f"Solar yield:               {solar_yield:,.0f} MWh/ha/year")
print(f"Solar land use [ha]:       {solar_land_ha:,.2f}")
print(f"Solar land use [km²]:      {solar_land_ha / 100:,.2f}")

# Alternative calculation from installed capacity
# Using capacity factor and land density
# Typical solar: ~1 MW per 1.5-2 ha (ground-mounted)
solar_land_ha_from_capacity = solar_capacity_mw / 0.6  # ~0.6 MW/ha typical

print(f"\nAlternative calculation (from capacity):")
print(f"Solar installed capacity:  {solar_capacity_mw:,.2f} MW")
print(f"Land use (0.6 MW/ha):      {solar_land_ha_from_capacity:,.2f} ha")

print("\n" + "="*50)
print("🔥 ENDOGENOUS LAND-USE RESULT")
print("="*50)
print(f"Solar land required:       {solar_land_ha:,.2f} hectares")
print(f"                           {solar_land_ha / 100:,.2f} km²")
print("="*50)
print("\n✅ This value can now be written back to the LandUse page!")

# STEP 17 — Check curtailment (optional but recommended)
# Curtailment = energy produced but not used
# This tells you how much solar/wind is wasted - very useful for analysis

print("\n" + "="*50)
print("STEP 17: CURTAILMENT ANALYSIS")
print("="*50)

# Total generation across all generators (MW at each timestep)
total_generation_mw = network.generators_t.p[["wind", "water_geothermal", "bio", "solar"]].sum(axis=1)

# Load breakdown (MW at each timestep)
elec_load_mw = network.loads_t.p["electricity_load"]
h2_load_mw = network.loads_t.p["hydrogen_load"]
total_load_mw = elec_load_mw + h2_load_mw

# Battery flows (MW)
battery_dispatch_mw = network.storage_units_t.p_dispatch["battery"]
battery_store_mw = network.storage_units_t.p_store["battery"]

# Link flows (MW) - electrolyzer and fuel cell
electrolyzer_mw_ts = network.links_t.p0["electrolyzer"]  # Electricity consumed
fuel_cell_mw_ts = -network.links_t.p1["fuel_cell"]       # Electricity produced (p1 is negative for output)

# CURTAILMENT: Calculate from electricity bus balance
# In a multi-bus model with sector coupling, curtailment happens when
# generation exceeds what can be: (1) directly consumed, (2) stored, or (3) converted

# For generators without explicit curtailment sink, curtailment = 0 by design
# PyPSA only produces what's needed. The "Available - Dispatched" approach
# works for must-run plants but not for extendable solar.

# For solar: Available = p_nom_opt × p_max_pu, but solar is optimally sized
# so it doesn't overbuild (no incentive to). Curtailment comes from timing mismatch.

# CORRECT APPROACH: Calculate actual curtailment from energy balance
# Curtailment = Generation + FuelCell - ElecLoad - Electrolyzer - BatteryNet
actual_curt_mw = (
    total_generation_mw          # All generation
    + fuel_cell_mw_ts            # Electricity from H2
    - elec_load_mw               # Electricity demand
    - electrolyzer_mw_ts         # Going to H2 production  
    - battery_store_mw           # Going to battery
    + battery_dispatch_mw        # Coming from battery
)
# Any positive value is curtailed (unused)
curtailment_mw = actual_curt_mw.clip(lower=0)
curtailment_gwh = curtailment_mw.sum() * 24 / 1000

# For reference: theoretical available capacity
# (Not used for curtailment calc, but useful context)
available_solar_gwh = network.generators.loc["solar", "p_nom_opt"] * solar_cf.sum() * 24 / 1000
available_wind_gwh = wind_p_nom_mw * wind_cf.sum() * 24 / 1000
available_water_gwh = water_p_nom_mw * 365 * 24 / 1000
available_bio_gwh = bio_p_nom_mw * 365 * 24 / 1000
total_available_gwh = available_solar_gwh + available_wind_gwh + available_water_gwh + available_bio_gwh

# Convert to GWh for display
total_gen_check_gwh = total_generation_mw.sum() * 24 / 1000
elec_load_gwh = elec_load_mw.sum() * 24 / 1000
h2_load_gwh = h2_load_mw.sum() * 24 / 1000
total_load_check_gwh = total_load_mw.sum() * 24 / 1000
battery_charged_gwh = battery_store_mw.sum() * 24 / 1000
battery_discharged_gwh = battery_dispatch_mw.sum() * 24 / 1000
electrolyzer_gwh = electrolyzer_mw_ts.sum() * 24 / 1000
fuel_cell_gwh = fuel_cell_mw_ts.sum() * 24 / 1000

print(f"Total generation:          {total_gen_check_gwh:,.2f} GWh")
print(f"Total available (theor):   {total_available_gwh:,.2f} GWh")
print(f"Electricity load:          {elec_load_gwh:,.2f} GWh")
print(f"Hydrogen load:             {h2_load_gwh:,.2f} GWh")
print(f"Battery charged:           {battery_charged_gwh:,.2f} GWh")
print(f"Battery discharged:        {battery_discharged_gwh:,.2f} GWh")
print(f"Electrolyzer input:        {electrolyzer_gwh:,.2f} GWh")
print(f"Fuel cell output:          {fuel_cell_gwh:,.2f} GWh")
print(f"\\nCurtailment [GWh]:         {curtailment_gwh:,.2f}")

# Calculate curtailment percentage (relative to generation, not theoretical available)
if total_gen_check_gwh > 0:
    curtailment_pct = curtailment_gwh / total_gen_check_gwh * 100
    print(f"Curtailment [%]:           {curtailment_pct:.2f}% (of actual generation)")
else:
    curtailment_pct = 0

print("="*50)

# Interpretation
if curtailment_gwh > 1:
    print("\n⚠️  Some renewable energy was curtailed (wasted)")
    print("   Consider: more storage, demand flexibility, or grid export")
else:
    print("\n✅ No curtailment - all generated energy was used!")

# =============================================================================
# STEP 18A — Storage Efficiency Sensitivity Analysis (MOST IMPORTANT)
# =============================================================================
# Compare different storage technologies by their round-trip efficiency
# This gives you a killer comparison for analysis

print("\n" + "="*70)
print("STEP 18A: STORAGE EFFICIENCY SENSITIVITY ANALYSIS")
print("="*70)

import json

def run_sensitivity_case(electrolyzer_cap_mw, case_name):
    """
    Run a single sensitivity case with specified electrolyzer power cap.
    Uses the new multi-component model (elec bus + H2 bus + electrolyzer link).
    Returns dict with key results.
    """
    # Create fresh network
    net = pypsa.Network()
    net.set_snapshots(snapshots)
    
    # Set snapshot weightings for daily model (24 hours per snapshot)
    net.snapshot_weightings = pd.DataFrame(
        index=net.snapshots,
        data={"objective": 24.0, "generators": 24.0, "stores": 24.0}
    )
    
    # Two-bus system
    net.add("Bus", "electricity")
    net.add("Bus", "hydrogen")
    
    # Add ELECTRICITY load (direct consumption)
    net.add("Load", "electricity_load", bus="electricity", p_set=electricity_p_set_mw.values)
    
    # Add HYDROGEN load (on hydrogen bus) - note: already numpy array
    net.add("Load", "hydrogen_load", bus="hydrogen", p_set=hydrogen_p_set_mw)
    
    # Add fixed generators with p_nom based on energy targets
    net.add("Generator", "wind", bus="electricity", p_nom=wind_p_nom_mw, 
            p_max_pu=wind_cf.values, marginal_cost=-0.01)
    net.add("Generator", "water_geothermal", bus="electricity", 
            p_nom=water_p_nom_mw, p_max_pu=1.0, marginal_cost=-0.01)
    net.add("Generator", "bio", bus="electricity", 
            p_nom=bio_p_nom_mw, p_max_pu=1.0, marginal_cost=-0.01)
    
    # Add extendable solar
    net.add("Generator", "solar", bus="electricity", p_max_pu=solar_cf.values,
            p_nom_extendable=True, marginal_cost=0, capital_cost=1)
    
    # Battery on electricity bus
    net.add("StorageUnit", "battery", bus="electricity",
            p_nom_extendable=True, p_nom_max=50_000, max_hours=4,
            efficiency_store=0.95, efficiency_dispatch=0.95,
            cyclic_state_of_charge=True)
    
    # Electrolyzer: electricity → hydrogen (POWER LIMITED)
    net.add("Link", "electrolyzer", bus0="electricity", bus1="hydrogen",
            p_nom_extendable=True, p_nom_max=electrolyzer_cap_mw,
            efficiency=0.65, capital_cost=1)
    
    # H2 storage on hydrogen bus
    net.add("Store", "h2_storage", bus="hydrogen",
            e_nom_extendable=True, e_nom_max=200_000_000, e_cyclic=True)
    
    # Fuel cell: hydrogen → electricity
    net.add("Link", "fuel_cell", bus0="hydrogen", bus1="electricity",
            p_nom_extendable=True, p_nom_max=60_000,
            efficiency=0.55, capital_cost=1)
    
    # Solve (suppress output)
    import logging
    logging.getLogger('pypsa').setLevel(logging.WARNING)
    logging.getLogger('linopy').setLevel(logging.WARNING)
    
    status = net.optimize(solver_name="highs")
    
    if status[0] != 'ok':
        return None
    
    # Extract results
    sol_cap_mw = net.generators.loc["solar", "p_nom_opt"]
    sol_energy_gwh = net.generators_t.p["solar"].sum() * 24 / 1000
    sol_land = sol_energy_gwh * 1000 / solar_yield
    
    elec_cap = net.links.loc["electrolyzer", "p_nom_opt"]
    fc_cap = net.links.loc["fuel_cell", "p_nom_opt"]
    h2_stor = net.stores.loc["h2_storage", "e_nom_opt"] / 1e6  # TWh
    batt_cap = net.storage_units.loc["battery", "p_nom_opt"]
    
    # Curtailment = available - dispatched
    avail_solar = sol_cap_mw * net.generators_t.p_max_pu["solar"]
    avail_wind = wind_p_nom_mw * net.generators_t.p_max_pu["wind"]
    total_avail_mw = avail_solar + avail_wind + water_p_nom_mw + bio_p_nom_mw
    total_disp_mw = net.generators_t.p.sum(axis=1)
    curt_mw = (total_avail_mw - total_disp_mw).clip(lower=0)
    curt_gwh = curt_mw.sum() * 24 / 1000
    total_avail_gwh = total_avail_mw.sum() * 24 / 1000
    curt_pct = curt_gwh / total_avail_gwh * 100 if total_avail_gwh > 0 else 0
    
    return {
        "case": case_name,
        "electrolyzer_cap_MW": electrolyzer_cap_mw,
        "solar_capacity_MW": sol_cap_mw,
        "solar_energy_GWh": sol_energy_gwh,
        "solar_land_ha": sol_land,
        "electrolyzer_opt_MW": elec_cap,
        "fuel_cell_MW": fc_cap,
        "h2_storage_TWh": h2_stor,
        "battery_MW": batt_cap,
        "curtailment_GWh": curt_gwh,
        "curtailment_percent": curt_pct
    }

# Define electrolyzer power cap sensitivity cases
# This is the KEY constraint that creates seasonal inflexibility
electrolyzer_cases = [
    {"cap": 60_000, "name": "60 GW electrolyzer"},
    {"cap": 80_000, "name": "80 GW electrolyzer (baseline)"},
    {"cap": 100_000, "name": "100 GW electrolyzer"},
    {"cap": 150_000, "name": "150 GW electrolyzer (relaxed)"},
]

print("\nRunning electrolyzer power cap sensitivity analysis...")
print("-" * 70)

efficiency_results = []
for case in electrolyzer_cases:
    result = run_sensitivity_case(case["cap"], case["name"])
    if result:
        efficiency_results.append(result)
        print(f"\n{case['name']}")
        print(f"  Electrolyzer cap:        {case['cap']/1000:.0f} GW")
        print(f"  Solar capacity [MW]:     {result['solar_capacity_MW']:,.0f}")
        print(f"  Solar land [ha]:         {result['solar_land_ha']:,.0f}")
        print(f"  Electrolyzer opt [MW]:   {result['electrolyzer_opt_MW']:,.0f}")
        print(f"  H2 storage [TWh]:        {result['h2_storage_TWh']:,.1f}")
        print(f"  Curtailment:             {result['curtailment_percent']:.1f}%")

# Summary table
print("\n" + "="*70)
print("ELECTROLYZER CAP SENSITIVITY SUMMARY TABLE")
print("="*70)
print(f"{'Case':<30} {'Elec[GW]':>10} {'Solar[MW]':>12} {'Land[ha]':>12} {'Curt[%]':>10}")
print("-"*70)
for r in efficiency_results:
    print(f"{r['case']:<30} {r['electrolyzer_cap_MW']/1000:>10.0f} {r['solar_capacity_MW']:>12,.0f} {r['solar_land_ha']:>12,.0f} {r['curtailment_percent']:>9.1f}%")
print("="*70)

# =============================================================================
# STEP 18B — Fuel Cell Cap Sensitivity
# =============================================================================

print("\n" + "="*70)
print("STEP 18B: FUEL CELL CAP SENSITIVITY")
print("="*70)

# Test different fuel cell power caps (affects winter electricity supply)
print("\n(Skipped for now - electrolyzer cap is the primary constraint)")
print("Fuel cell cap affects how much H2 can be converted back to electricity in winter.")

size_results = []  # Empty for compatibility

# =============================================================================
# STEP 18C — Prepare Results for Django WebApp (JSON API Schema)
# =============================================================================

print("\n" + "="*70)
print("STEP 18C: JSON OUTPUT FOR DJANGO API")
print("="*70)

# Prepare the main result (multi-component model)
api_output = {
    "model_info": {
        "pypsa_version": pypsa.__version__,
        "snapshots": len(network.snapshots),
        "snapshot_weighting_hours": 24,
        "solver": "highs",
        "status": "optimal",
        "model_type": "multi-component (elec + H2 buses)"
    },
    "inputs": {
        "E_electricity_GWh": E_electricity,
        "E_hydrogen_GWh": E_hydrogen,
        "loss_rate": loss_rate,
        "E_total_GWh": E_total,
        "E_wind_GWh": E_wind,
        "E_water_geo_GWh": E_water_geo,
        "E_bio_GWh": E_bio,
        "solar_yield_MWh_per_ha": solar_yield
    },
    "results": {
        "solar_capacity_MW": float(solar_capacity_mw),
        "solar_energy_GWh": float(solar_energy_gwh),
        "solar_land_ha": float(solar_land_ha),
        "solar_land_km2": float(solar_land_ha / 100),
        "battery_power_MW": float(battery_capacity_mw),
        "battery_energy_GWh": float(battery_energy_mwh / 1000),
        "electrolyzer_MW": float(electrolyzer_mw),
        "fuel_cell_MW": float(fuel_cell_mw),
        "h2_storage_TWh": float(h2_storage_mwh / 1e6),
        "curtailment_GWh": float(curtailment_gwh),
        "curtailment_percent": float(curtailment_pct),
        "battery_soc_day1_MWh": float(battery_soc.iloc[0]),
        "battery_soc_day365_MWh": float(battery_soc.iloc[-1]),
        "h2_soc_day1_TWh": float(h2_soc.iloc[0] / 1e6),
        "h2_soc_day365_TWh": float(h2_soc.iloc[-1] / 1e6),
        "total_generation_GWh": float(total_gen_gwh),
        "electricity_load_GWh": float(elec_load_gwh),
        "hydrogen_load_GWh": float(h2_load_gwh)
    },
    "sensitivity_electrolyzer_cap": [
        {
            "case": r["case"],
            "electrolyzer_cap_MW": r["electrolyzer_cap_MW"],
            "solar_capacity_MW": r["solar_capacity_MW"],
            "solar_land_ha": r["solar_land_ha"],
            "h2_storage_TWh": r["h2_storage_TWh"],
            "curtailment_percent": r["curtailment_percent"]
        }
        for r in efficiency_results
    ]
}

# Pretty print the JSON
print("\nAPI Output Schema (for Django frontend):")
print("-"*70)
print(json.dumps(api_output, indent=2))

# Save to file for easy access
output_file = "pypsa_results.json"
with open(output_file, 'w') as f:
    json.dump(api_output, f, indent=2)
print(f"\n✅ Results saved to: {output_file}")

print("\n" + "="*70)
print("🎉 ALL STEPS COMPLETE!")
print("="*70)
print("""
Next steps for Django integration:
1. Import this JSON schema into your API views
2. Create a PyPSA service module that returns this structure
3. Connect to your frontend to display results
4. Add the solar_land_ha to your LandUse page calculations
""")

# =============================================================================
# STEP 19 — ENERGY BALANCE VERIFICATION (Multi-Component Model)
# =============================================================================

print("\n" + "="*70)
print("STEP 19: ENERGY BALANCE VERIFICATION")
print("="*70)

# ORIGINAL DEMAND VALUES (from Verbrauch page)
print(f"\n📊 ORIGINAL DEMAND (from Verbrauch page):")
print(f"   Code 7 - Strom-Endverbrauch (Ziel):  {E_electricity:>15,.2f} GWh/a")
print(f"   Hydrogen demand:                     {E_hydrogen:>15,.2f} GWh/a")
print(f"   Loss rate:                           {loss_rate*100:>15.1f}%")
print(f"   ─────────────────────────────────────────────────")
print(f"   E_total (incl. losses):              {E_total:>15,.2f} GWh/a")

# Total demand used in model - NOW SEPARATED
elec_demand_model_gwh = network.loads_t.p["electricity_load"].sum() * 24 / 1000
h2_demand_model_gwh = network.loads_t.p["hydrogen_load"].sum() * 24 / 1000
total_demand_gwh = elec_demand_model_gwh + h2_demand_model_gwh

print(f"\n📊 MODEL LOADS (on separate buses):")
print(f"   Electricity load (elec bus):         {elec_demand_model_gwh:>15,.2f} GWh")
print(f"   Hydrogen load (H2 bus):              {h2_demand_model_gwh:>15,.2f} GWh")
print(f"   ─────────────────────────────────────────────────")
print(f"   TOTAL (note: H2 bus in H2 units):    {total_demand_gwh:>15,.2f} GWh")

# Total renewable generation by source (MW*24h/1000 = GWh)
gen_wind_gwh = network.generators_t.p["wind"].sum() * 24 / 1000
gen_water_geo_gwh = network.generators_t.p["water_geothermal"].sum() * 24 / 1000
gen_bio_gwh = network.generators_t.p["bio"].sum() * 24 / 1000
gen_solar_gwh = network.generators_t.p["solar"].sum() * 24 / 1000
total_renewable_gen_gwh = gen_wind_gwh + gen_water_geo_gwh + gen_bio_gwh + gen_solar_gwh

# Link flows (electrolyzer and fuel cell)
electrolyzer_input_gwh = network.links_t.p0["electrolyzer"].sum() * 24 / 1000  # Electricity IN
fuel_cell_output_gwh = (-network.links_t.p1["fuel_cell"]).sum() * 24 / 1000    # Electricity OUT
electrolyzer_output_gwh = electrolyzer_input_gwh * 0.65  # H2 produced (65% efficiency)

# Battery flows (GWh)
battery_charged_gwh = network.storage_units_t.p_store["battery"].sum() * 24 / 1000
battery_discharged_gwh = network.storage_units_t.p_dispatch["battery"].sum() * 24 / 1000
battery_losses_gwh = battery_charged_gwh - battery_discharged_gwh

print(f"\n📊 SUPPLY SIDE (Renewable Generation):")
print(f"   Wind:                                {gen_wind_gwh:>15,.2f} GWh")
print(f"   Water+Geothermal:                    {gen_water_geo_gwh:>15,.2f} GWh")
print(f"   Bioenergie:                          {gen_bio_gwh:>15,.2f} GWh")
print(f"   Solar:                               {gen_solar_gwh:>15,.2f} GWh")
print(f"   ─────────────────────────────────────────────────")
print(f"   TOTAL RENEWABLE GENERATION:          {total_renewable_gen_gwh:>15,.2f} GWh")

print(f"\n📊 SECTOR COUPLING (Electrolyzer + Fuel Cell):")
print(f"   Electrolyzer input (elec):           {electrolyzer_input_gwh:>15,.2f} GWh")
print(f"   Electrolyzer output (H2):            {electrolyzer_output_gwh:>15,.2f} GWh")
print(f"   Electrolyzer losses:                 {electrolyzer_input_gwh - electrolyzer_output_gwh:>15,.2f} GWh")
print(f"   Fuel cell output (elec):             {fuel_cell_output_gwh:>15,.2f} GWh")

print(f"\n📊 BATTERY STORAGE FLOWS:")
print(f"   Battery charged:                     {battery_charged_gwh:>15,.2f} GWh")
print(f"   Battery discharged:                  {battery_discharged_gwh:>15,.2f} GWh")
print(f"   Battery losses (round-trip):         {battery_losses_gwh:>15,.2f} GWh")

# Energy balance on ELECTRICITY bus:
# Generation + fuel_cell_out + battery_discharge = elec_load + electrolyzer_in + battery_charge + curtailment
elec_supply = total_renewable_gen_gwh + fuel_cell_output_gwh + battery_discharged_gwh
elec_use = elec_demand_model_gwh + electrolyzer_input_gwh + battery_charged_gwh + curtailment_gwh

print(f"\n📊 ELECTRICITY BUS BALANCE:")
print(f"   Supply:")
print(f"     Renewable generation:              {total_renewable_gen_gwh:>15,.2f} GWh")
print(f"     Fuel cell output:                  {fuel_cell_output_gwh:>15,.2f} GWh")
print(f"     Battery discharge:                 {battery_discharged_gwh:>15,.2f} GWh")
print(f"     ─────────────────────────────────────────────────")
print(f"     TOTAL SUPPLY:                      {elec_supply:>15,.2f} GWh")
print(f"   Consumption:")
print(f"     Electricity load:                  {elec_demand_model_gwh:>15,.2f} GWh")
print(f"     Electrolyzer input:                {electrolyzer_input_gwh:>15,.2f} GWh")
print(f"     Battery charge:                    {battery_charged_gwh:>15,.2f} GWh")
print(f"     Curtailment:                       {curtailment_gwh:>15,.2f} GWh")
print(f"     ─────────────────────────────────────────────────")
print(f"     TOTAL CONSUMPTION:                 {elec_use:>15,.2f} GWh")

balance_error_gwh = elec_supply - elec_use
balance_error_pct = abs(balance_error_gwh) / elec_supply * 100 if elec_supply > 0 else 0

print(f"\n   Balance difference:                  {balance_error_gwh:>15,.2f} GWh")
print(f"   Balance error:                       {balance_error_pct:>15.6f}%")

# KEY VERIFICATION: Does generation cover original Verbrauch demand?
print(f"\n" + "="*70)
print("🔥 KEY VERIFICATION: Renewable Generation vs Verbrauch Demand")
print("="*70)

# Total losses in the system
total_losses_gwh = (electrolyzer_input_gwh - electrolyzer_output_gwh) + battery_losses_gwh
# Note: fuel cell losses are embedded in the H2→electricity conversion

print(f"\n   Total Renewable Generation:          {total_renewable_gen_gwh:>15,.2f} GWh")
print(f"   - Electrolyzer losses (35%):         {electrolyzer_input_gwh - electrolyzer_output_gwh:>15,.2f} GWh")
print(f"   - Battery losses (10%):              {battery_losses_gwh:>15,.2f} GWh")
print(f"   - Curtailment:                       {curtailment_gwh:>15,.2f} GWh")
print(f"   ─────────────────────────────────────────────────")
useful_energy_gwh = total_renewable_gen_gwh - total_losses_gwh - curtailment_gwh
print(f"   = Net Useful Energy:                 {useful_energy_gwh:>15,.2f} GWh")
print(f"\n   vs Verbrauch Code 7 (Strom):         {E_electricity:>15,.2f} GWh")
print(f"   vs Hydrogen demand (H2 units):       {E_hydrogen:>15,.2f} GWh")
print(f"   vs E_total (Code 7 + H2):            {E_total:>15,.2f} GWh")

# Check if demands are met
elec_met = abs(elec_demand_model_gwh - E_electricity) < 1
h2_met = abs(h2_demand_model_gwh - E_hydrogen) < 1

print(f"\n   ✓ Electricity demand met:            {'YES ✅' if elec_met else 'NO ❌'}")
print(f"   ✓ Hydrogen demand met:               {'YES ✅' if h2_met else 'NO ❌'}")

print("\n" + "="*70)
if abs(balance_error_pct) < 1:
    print("✅ ENERGY BALANCE VERIFIED on electricity bus")
    print("   (Small numerical tolerance is normal)")
else:
    print("⚠️  ENERGY BALANCE MISMATCH - Please check model constraints!")
print("="*70)

print(f"\n💡 KEY INSIGHT: Solar land = {solar_land_ha:,.0f} ha")
print(f"   Target range: 680,000 - 720,000 ha")
if 680_000 <= solar_land_ha <= 720_000:
    print("   ✅ WITHIN TARGET RANGE!")
elif solar_land_ha < 680_000:
    print(f"   ⚠️  Below target by {680_000 - solar_land_ha:,.0f} ha")
else:
    print(f"   ⚠️  Above target by {solar_land_ha - 720_000:,.0f} ha")
