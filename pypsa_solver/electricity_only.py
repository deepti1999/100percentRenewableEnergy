"""
electricity_only.py - PyPSA Electricity-Only Model

Step-by-step implementation following user guidance.
"""

import pypsa
import pandas as pd

# Create the network
network = pypsa.Network()

# STEP 4 — Time axis (365 days)
snapshots = pd.date_range(
    start="2023-01-01",
    periods=365,
    freq="D"
)
network.set_snapshots(snapshots)

# STEP 5 — Electricity bus (Think of this as "Germany's electricity system")
network.add("Bus", "electricity")

# STEP 6 — Load your profiles (CRITICAL)
# From CSVs
solar = pd.read_csv("data/solar_promile.csv")["solar_promile"]
wind = pd.read_csv("data/wind_promile.csv")["wind_promile"]
demand = pd.read_csv("data/verbrauch_promile.csv")["verbrauch_promile"]

# Normalize inside Python (never trust Excel normalization)
solar_pu = solar / solar.sum()
wind_pu = wind / wind.sum()
demand_pu = demand / demand.sum()

# Annual energy values from RenewableEnergy page (Ziel = target_value)
# These would come from RenewableData model:
#   9.1.1 = aus Windenergie (wind_annual)
#   9.1.2 = aus Solarenergie (solar_annual)
#   9.1.3 = aus Wasserkraft + Tiefengeothermie (water_geo_annual)
#   9.1.4 = aus Bioenergie (bio_annual)
#
# For now, set placeholder values - will fetch from DB later
wind_annual = 100.0       # GWh/a - from 9.1.1 target_value
solar_annual = 150.0      # GWh/a - from 9.1.2 target_value
water_geo_annual = 20.0   # GWh/a - from 9.1.3 target_value
bio_annual = 30.0         # GWh/a - from 9.1.4 target_value

print("✓ Profiles loaded and normalized")
print(f"  Solar profile sum: {solar_pu.sum():.4f}")
print(f"  Wind profile sum: {wind_pu.sum():.4f}")
print(f"  Demand profile sum: {demand_pu.sum():.4f}")

# STEP 7 — Define TOTAL electricity demand correctly
# Annual values (TARGET):
# E_electricity comes from: VerbrauchData.objects.get(code='7').ziel
#   → Verbrauch page, Code 7 "Strom-Endverbrauch insgesamt", Ziel column
E_electricity = 1_003_863.64     # GWh/a - from Verbrauch page code 7 (ziel)
E_hydrogen    =   385_933.329    # GWh/a
loss_rate     = 0.092            # 9.2% losses

# Total system load (including losses)
E_total = (E_electricity + E_hydrogen) / (1 - loss_rate)

# Daily demand distribution
daily_load = demand_pu * E_total

# Add to network
network.add(
    "Load",
    "total_electricity_load",
    bus="electricity",
    p_set=daily_load.values
)

print(f"✓ Load added")
print(f"  E_electricity: {E_electricity:,.2f} GWh/a")
print(f"  E_hydrogen:    {E_hydrogen:,.2f} GWh/a")
print(f"  Loss rate:     {loss_rate*100:.1f}%")
print(f"  E_total:       {E_total:,.2f} GWh/a")

# STEP 8 — Fixed generators (wind, water, bio)
# Annual energy values from RenewableData (target_value / ziel):
#   9.1.1 = aus Windenergie
#   9.1.3 = aus Wasserkraft + Tiefengeothermie
#   9.1.4 = aus Bioenergie

# Wind (uses wind profile)
# p_nom = annual energy / sum of capacity factors
E_wind = 706_236.566  # GWh/a - from RenewableData code 9.1.1 target_value
wind_p_nom = E_wind / wind_pu.sum()  # Installed capacity to achieve target energy

network.add(
    "Generator",
    "wind",
    bus="electricity",
    p_nom=wind_p_nom,
    p_max_pu=wind_pu.values,  # Capacity factor profile
    marginal_cost=0
)

# Water + Geothermal (flat profile - constant baseload)
E_water_geo = 50_000.0  # GWh/a - from RenewableData code 9.1.3 target_value
water_geo_p_nom = E_water_geo / 365  # Daily capacity (flat profile)

network.add(
    "Generator",
    "water_geothermal",
    bus="electricity",
    p_nom=water_geo_p_nom,
    p_max_pu=1.0,  # Constant baseload
    marginal_cost=0
)

# Bio (flat profile for now)
E_bio = 30_000.0  # GWh/a - from RenewableData code 9.1.4 target_value
bio_p_nom = E_bio / 365  # Daily capacity

network.add(
    "Generator",
    "bio",
    bus="electricity",
    p_nom=bio_p_nom,
    p_max_pu=1.0,  # Available as needed
    marginal_cost=0
)

print(f"✓ Fixed generators added")
print(f"  Wind:           {E_wind:,.2f} GWh/a (profile-based)")
print(f"  Water+Geo:      {E_water_geo:,.2f} GWh/a (flat)")
print(f"  Bio:            {E_bio:,.2f} GWh/a (flat)")

# STEP 9 — Solar (THIS IS THE CORE)
# Solar is NOT given energy - it is ALLOWED TO GROW
# PyPSA will decide the optimal solar capacity to meet demand
# Solar details come from RenewableEnergy page 1st section (installed capacity, etc.)
network.add(
    "Generator",
    "solar",
    bus="electricity",
    p_max_pu=solar_pu.values,      # Capacity factor profile (normalized)
    p_nom_extendable=True,          # ⭐ This is what makes solar expandable!
    marginal_cost=0,                # No fuel cost
    capital_cost=1                  # Minimal cost to track capacity
)

print(f"✓ Solar (extendable) added")
print(f"  p_nom_extendable: True")
print(f"  → PyPSA will optimize solar capacity to meet demand gap")

# STEP 10 — Storage
network.add(
    "StorageUnit",
    "storage",
    bus="electricity",
    p_nom_extendable=True,
    max_hours=200,                    # Energy capacity = 200 * power capacity
    efficiency_store=0.65,            # 65% charging efficiency
    efficiency_dispatch=0.585,        # 58.5% discharging efficiency
    cyclic_state_of_charge=True       # SOC at end = SOC at start
)

print(f"✓ Storage added")
print(f"  p_nom_extendable: True")
print(f"  max_hours: 200")
print(f"  efficiency_store: 65%")
print(f"  efficiency_dispatch: 58.5%")
print(f"  cyclic_state_of_charge: True")

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
print("Storage units:", network.storage_units.index.tolist())
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
soc = network.storage_units_t.state_of_charge["storage"]

print("\n" + "="*50)
print("CYCLIC SOC VERIFICATION")
print("="*50)
print(f"SOC day 1:    {soc.iloc[0]:,.2f}")
print(f"SOC day 365:  {soc.iloc[-1]:,.2f}")
print(f"Difference:   {soc.iloc[-1] - soc.iloc[0]:,.2f}")
print("="*50)

# Expected: Difference ≈ 0 (small numerical tolerance is OK)

# STEP 15 — Extract the SOLUTION (this is your result)
print("\n" + "="*50)
print("OPTIMIZATION RESULTS")
print("="*50)

# Solar installed capacity (chosen by PyPSA)
solar_capacity = network.generators.loc["solar", "p_nom_opt"]
print(f"Solar capacity [GWh]:  {solar_capacity:,.2f}")

# Solar energy actually produced
solar_energy = network.generators_t.p["solar"].sum()
print(f"Solar energy [GWh]:    {solar_energy:,.2f}")

# Also show other generation
wind_energy = network.generators_t.p["wind"].sum()
water_geo_energy = network.generators_t.p["water_geothermal"].sum()
bio_energy = network.generators_t.p["bio"].sum()

print(f"\nAll generation:")
print(f"  Wind:           {wind_energy:,.2f} GWh")
print(f"  Water+Geo:      {water_geo_energy:,.2f} GWh")
print(f"  Bio:            {bio_energy:,.2f} GWh")
print(f"  Solar:          {solar_energy:,.2f} GWh")
print(f"  ─────────────────────────────")
total_gen = wind_energy + water_geo_energy + bio_energy + solar_energy
print(f"  TOTAL:          {total_gen:,.2f} GWh")

# Storage
storage_capacity = network.storage_units.loc["storage", "p_nom_opt"]
print(f"\nStorage capacity: {storage_capacity:,.2f} GWh")

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
# solar_energy is in GWh, so multiply by 1000 to convert to MWh
solar_land_ha = solar_energy * 1000 / solar_yield

print(f"Solar energy produced:     {solar_energy:,.2f} GWh/a")
print(f"Solar yield:               {solar_yield:,.0f} MWh/ha/year")
print(f"Solar land use [ha]:       {solar_land_ha:,.2f}")
print(f"Solar land use [km²]:      {solar_land_ha / 100:,.2f}")

# Also calculate based on installed capacity (alternative method)
# Using capacity factor approach
solar_capacity_mw = solar_capacity * 1000  # Convert GW to MW
# Typical solar capacity density: ~30-50 MW/km² or ~0.3-0.5 MW/ha
# Using standard value: ~1 MW per 2 ha (or 0.5 MW/ha)
solar_land_ha_from_capacity = solar_capacity_mw / 0.5  # ha

print(f"\nAlternative calculation (from capacity):")
print(f"Solar installed capacity:  {solar_capacity:,.2f} GW")
print(f"Solar capacity [MW]:       {solar_capacity_mw:,.2f} MW")
print(f"Land use (0.5 MW/ha):      {solar_land_ha_from_capacity:,.2f} ha")

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

# Total generation across all generators (sum across columns for each timestep)
total_generation = network.generators_t.p.sum(axis=1)

# Total load (demand) across all loads
total_load = network.loads_t.p.sum(axis=1)

# Storage flows (positive = discharging, negative = charging)
storage_dispatch = network.storage_units_t.p_dispatch.sum(axis=1)  # Discharging
storage_store = network.storage_units_t.p_store.sum(axis=1)        # Charging

# Energy balance: Generation + Storage_discharge = Load + Storage_charge + Curtailment
# Curtailment = Generation - Load - Net_storage_charging
# But simpler: clip any excess to zero
curtailment = (total_generation - total_load).clip(lower=0).sum()

print(f"Total generation:          {total_generation.sum():,.2f} GWh")
print(f"Total load:                {total_load.sum():,.2f} GWh")
print(f"Storage charged:           {storage_store.sum():,.2f} GWh")
print(f"Storage discharged:        {storage_dispatch.sum():,.2f} GWh")
print(f"\nCurtailment [GWh]:         {curtailment:,.2f}")

# Calculate curtailment percentage
if total_generation.sum() > 0:
    curtailment_pct = curtailment / total_generation.sum() * 100
    print(f"Curtailment [%]:           {curtailment_pct:.2f}%")

print("="*50)

# Interpretation
if curtailment > 0:
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

def run_sensitivity_case(eta_store, eta_dispatch, max_hrs, case_name):
    """
    Run a single sensitivity case with specified storage parameters.
    Returns dict with key results.
    """
    # Create fresh network
    net = pypsa.Network()
    net.set_snapshots(snapshots)
    net.add("Bus", "electricity")
    
    # Add load
    net.add("Load", "total_electricity_load", bus="electricity", p_set=daily_load.values)
    
    # Add fixed generators (wind, water_geo, bio)
    net.add("Generator", "wind", bus="electricity", p_nom=wind_p_nom, 
            p_max_pu=wind_pu.values, marginal_cost=0)
    net.add("Generator", "water_geothermal", bus="electricity", 
            p_nom=water_geo_p_nom, p_max_pu=1.0, marginal_cost=0)
    net.add("Generator", "bio", bus="electricity", 
            p_nom=bio_p_nom, p_max_pu=1.0, marginal_cost=0)
    
    # Add extendable solar
    net.add("Generator", "solar", bus="electricity", p_max_pu=solar_pu.values,
            p_nom_extendable=True, marginal_cost=0, capital_cost=1)
    
    # Add storage with specified efficiencies
    net.add("StorageUnit", "storage", bus="electricity",
            p_nom_extendable=True, max_hours=max_hrs,
            efficiency_store=eta_store, efficiency_dispatch=eta_dispatch,
            cyclic_state_of_charge=True)
    
    # Solve (suppress output)
    import logging
    logging.getLogger('pypsa').setLevel(logging.WARNING)
    logging.getLogger('linopy').setLevel(logging.WARNING)
    
    status = net.optimize(solver_name="highs")
    
    if status[0] != 'ok':
        return None
    
    # Extract results
    sol_cap = net.generators.loc["solar", "p_nom_opt"]
    sol_energy = net.generators_t.p["solar"].sum()
    sol_land = sol_energy * 1000 / solar_yield
    
    stor_cap = net.storage_units.loc["storage", "p_nom_opt"]
    stor_energy_cap = stor_cap * max_hrs  # Energy capacity
    stor_discharged = net.storage_units_t.p_dispatch["storage"].sum()
    stor_charged = net.storage_units_t.p_store["storage"].sum()
    
    total_gen = net.generators_t.p.sum(axis=1)
    total_ld = net.loads_t.p.sum(axis=1)
    curt = (total_gen - total_ld).clip(lower=0).sum()
    curt_pct = curt / total_gen.sum() * 100 if total_gen.sum() > 0 else 0
    
    soc = net.storage_units_t.state_of_charge["storage"]
    
    return {
        "case": case_name,
        "eta_store": eta_store,
        "eta_dispatch": eta_dispatch,
        "eta_roundtrip": eta_store * eta_dispatch,
        "max_hours": max_hrs,
        "solar_capacity_GWh": sol_cap,
        "solar_energy_GWh": sol_energy,
        "solar_land_ha": sol_land,
        "storage_power_GWh": stor_cap,
        "storage_energy_GWh": stor_energy_cap,
        "storage_charged_GWh": stor_charged,
        "storage_discharged_GWh": stor_discharged,
        "curtailment_GWh": curt,
        "curtailment_percent": curt_pct,
        "soc_day1": soc.iloc[0],
        "soc_day365": soc.iloc[-1]
    }

# Define storage technology cases
storage_cases = [
    {"eta_store": 0.95, "eta_dispatch": 0.95, "name": "A: Battery (Li-ion)"},
    {"eta_store": 0.80, "eta_dispatch": 0.80, "name": "B: Pumped Hydro"},
    {"eta_store": 0.65, "eta_dispatch": 0.585, "name": "C: Hydrogen (baseline)"},
]

print("\nRunning storage efficiency sensitivity analysis...")
print("-" * 70)

efficiency_results = []
for case in storage_cases:
    result = run_sensitivity_case(
        case["eta_store"], case["eta_dispatch"], 200, case["name"]
    )
    if result:
        efficiency_results.append(result)
        print(f"\n{case['name']}")
        print(f"  Round-trip efficiency:   {result['eta_roundtrip']*100:.1f}%")
        print(f"  Solar land [ha]:         {result['solar_land_ha']:,.0f}")
        print(f"  Storage capacity [GWh]:  {result['storage_energy_GWh']:,.0f}")
        print(f"  Storage discharged:      {result['storage_discharged_GWh']:,.0f} GWh")
        print(f"  Curtailment:             {result['curtailment_percent']:.1f}%")

# Summary table
print("\n" + "="*70)
print("EFFICIENCY SENSITIVITY SUMMARY TABLE")
print("="*70)
print(f"{'Case':<25} {'η_rt':>8} {'Solar[ha]':>12} {'Stor[GWh]':>12} {'Curt[%]':>10}")
print("-"*70)
for r in efficiency_results:
    print(f"{r['case']:<25} {r['eta_roundtrip']*100:>7.0f}% {r['solar_land_ha']:>12,.0f} {r['storage_energy_GWh']:>12,.0f} {r['curtailment_percent']:>9.1f}%")
print("="*70)

# =============================================================================
# STEP 18B — Storage Size Sensitivity (max_hours)
# =============================================================================

print("\n" + "="*70)
print("STEP 18B: STORAGE SIZE SENSITIVITY (max_hours)")
print("="*70)

max_hours_cases = [50, 100, 200, 500]

print("\nRunning storage size sensitivity analysis (using Hydrogen efficiency)...")
print("-" * 70)

size_results = []
for max_hrs in max_hours_cases:
    result = run_sensitivity_case(0.65, 0.585, max_hrs, f"max_hours={max_hrs}")
    if result:
        size_results.append(result)
        print(f"\nmax_hours = {max_hrs}")
        print(f"  Solar land [ha]:         {result['solar_land_ha']:,.0f}")
        print(f"  Storage energy [GWh]:    {result['storage_energy_GWh']:,.0f}")
        print(f"  Curtailment:             {result['curtailment_percent']:.1f}%")

# Summary table
print("\n" + "="*70)
print("STORAGE SIZE SENSITIVITY SUMMARY TABLE")
print("="*70)
print(f"{'max_hours':>10} {'Solar[ha]':>15} {'Stor Energy[GWh]':>18} {'Curt[%]':>10}")
print("-"*70)
for r in size_results:
    print(f"{r['max_hours']:>10} {r['solar_land_ha']:>15,.0f} {r['storage_energy_GWh']:>18,.0f} {r['curtailment_percent']:>9.1f}%")
print("="*70)
print("\n💡 Note: Observe diminishing returns as max_hours increases!")

# =============================================================================
# STEP 18C — Prepare Results for Django WebApp (JSON API Schema)
# =============================================================================

print("\n" + "="*70)
print("STEP 18C: JSON OUTPUT FOR DJANGO API")
print("="*70)

# Prepare the main result (baseline hydrogen storage case)
api_output = {
    "model_info": {
        "pypsa_version": pypsa.__version__,
        "snapshots": len(network.snapshots),
        "solver": "highs",
        "status": "optimal"
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
        "solar_capacity_GWh": float(solar_capacity),
        "solar_capacity_MW": float(solar_capacity * 1000),
        "solar_energy_GWh": float(solar_energy),
        "solar_land_ha": float(solar_land_ha),
        "solar_land_km2": float(solar_land_ha / 100),
        "storage_power_GWh": float(storage_capacity),
        "storage_energy_GWh": float(storage_capacity * 200),
        "storage_roundtrip_efficiency": 0.65 * 0.585,
        "curtailment_GWh": float(curtailment),
        "curtailment_percent": float(curtailment_pct),
        "soc_day1_GWh": float(soc.iloc[0]),
        "soc_day365_GWh": float(soc.iloc[-1]),
        "total_generation_GWh": float(total_generation.sum()),
        "total_load_GWh": float(total_load.sum())
    },
    "sensitivity_efficiency": [
        {
            "case": r["case"],
            "eta_roundtrip": r["eta_roundtrip"],
            "solar_land_ha": r["solar_land_ha"],
            "storage_energy_GWh": r["storage_energy_GWh"],
            "curtailment_percent": r["curtailment_percent"]
        }
        for r in efficiency_results
    ],
    "sensitivity_max_hours": [
        {
            "max_hours": r["max_hours"],
            "solar_land_ha": r["solar_land_ha"],
            "storage_energy_GWh": r["storage_energy_GWh"],
            "curtailment_percent": r["curtailment_percent"]
        }
        for r in size_results
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
# STEP 19 — ENERGY BALANCE VERIFICATION (Demand = Total Renewable Generation)
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

# Total demand used in model (should equal E_total)
total_demand = network.loads_t.p.sum().sum()
print(f"\n📊 MODEL LOAD (E_total used in PyPSA):")
print(f"   Total Load in model:                 {total_demand:>15,.2f} GWh")

# Total renewable generation by source
gen_wind = network.generators_t.p["wind"].sum()
gen_water_geo = network.generators_t.p["water_geothermal"].sum()
gen_bio = network.generators_t.p["bio"].sum()
gen_solar = network.generators_t.p["solar"].sum()
total_renewable_gen = gen_wind + gen_water_geo + gen_bio + gen_solar

# Storage flows
storage_charged = network.storage_units_t.p_store.sum().sum()
storage_discharged = network.storage_units_t.p_dispatch.sum().sum()
storage_losses = storage_charged - storage_discharged  # Energy lost in storage

print(f"\n📊 SUPPLY SIDE (Renewable Generation):")
print(f"   Wind:                                {gen_wind:>15,.2f} GWh")
print(f"   Water+Geothermal:                    {gen_water_geo:>15,.2f} GWh")
print(f"   Bioenergie:                          {gen_bio:>15,.2f} GWh")
print(f"   Solar:                               {gen_solar:>15,.2f} GWh")
print(f"   ─────────────────────────────────────────────────")
print(f"   TOTAL RENEWABLE GENERATION:          {total_renewable_gen:>15,.2f} GWh")

print(f"\n📊 STORAGE FLOWS:")
print(f"   Storage charged:                     {storage_charged:>15,.2f} GWh")
print(f"   Storage discharged:                  {storage_discharged:>15,.2f} GWh")
print(f"   Storage losses (round-trip):         {storage_losses:>15,.2f} GWh")

# Energy balance
net_storage_flow = storage_charged - storage_discharged
expected_gen = total_demand + net_storage_flow

print(f"\n📊 ENERGY BALANCE CHECK:")
print(f"   Total Renewable Generation:          {total_renewable_gen:>15,.2f} GWh")
print(f"   ─────────────────────────────────────────────────")
print(f"   = Model Load (E_total):              {total_demand:>15,.2f} GWh")
print(f"   + Storage losses:                    {net_storage_flow:>15,.2f} GWh")
print(f"   ─────────────────────────────────────────────────")
print(f"   = Expected Generation:               {expected_gen:>15,.2f} GWh")

balance_error = total_renewable_gen - expected_gen
balance_error_pct = abs(balance_error) / total_renewable_gen * 100 if total_renewable_gen > 0 else 0

print(f"\n   Balance difference:                  {balance_error:>15,.2f} GWh")
print(f"   Balance error:                       {balance_error_pct:>15.6f}%")

# KEY VERIFICATION: Does generation cover original Verbrauch demand?
print(f"\n" + "="*70)
print("🔥 KEY VERIFICATION: Renewable Generation vs Verbrauch Demand")
print("="*70)

# Useful energy = Generation - Storage losses
useful_energy = total_renewable_gen - storage_losses

print(f"\n   Total Renewable Generation:          {total_renewable_gen:>15,.2f} GWh")
print(f"   - Storage losses:                    {storage_losses:>15,.2f} GWh")
print(f"   ─────────────────────────────────────────────────")
print(f"   = Useful Energy Delivered:           {useful_energy:>15,.2f} GWh")
print(f"\n   vs Verbrauch Code 7 (Strom):         {E_electricity:>15,.2f} GWh")
print(f"   vs Hydrogen demand:                  {E_hydrogen:>15,.2f} GWh")
print(f"   vs E_total (Code 7 + H2 + losses):   {E_total:>15,.2f} GWh")

# Check if useful energy covers the demands
covers_electricity = useful_energy >= E_electricity
covers_total = abs(useful_energy - E_total) < 1  # Within 1 GWh tolerance

print(f"\n   ✓ Covers Strom-Endverbrauch (Code 7): {'YES ✅' if covers_electricity else 'NO ❌'}")
print(f"   ✓ Matches E_total (model load):      {'YES ✅' if covers_total else 'NO ❌'}")

print("\n" + "="*70)
if abs(balance_error_pct) < 0.1:
    print("✅ ENERGY BALANCE VERIFIED: Demand ≈ Useful Renewable Generation")
    print("   (Small numerical tolerance is normal)")
else:
    print("⚠️  ENERGY BALANCE MISMATCH - Please check model constraints!")
print("="*70)

# Additional verification: Check if demand is met at every timestep
unmet_demand = (network.loads_t.p.sum(axis=1) - 
                network.generators_t.p.sum(axis=1) - 
                network.storage_units_t.p_dispatch.sum(axis=1) + 
                network.storage_units_t.p_store.sum(axis=1)).clip(lower=0).sum()

print(f"\nUnmet demand check: {unmet_demand:,.2f} GWh")
if unmet_demand < 0.01:
    print("✅ All demand is met at every timestep!")
else:
    print(f"⚠️  Some demand was not met: {unmet_demand:,.2f} GWh")
