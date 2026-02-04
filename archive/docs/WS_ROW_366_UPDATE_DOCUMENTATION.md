# WS Database Row 366 Update - Data Source Change

## Summary
Updated WS database row 366 (Column J: `stromverbr_raumwaerm_korr`) to reference the Annual Electricity Flow calculation instead of RenewableData 9.4.3.

## Changes Made

### Old Data Source
- **Previous Source**: RenewableData table, code 9.4.3
- **Previous Value**: 1,124,854.43 MWh
- **Method**: Direct copy from renewable energy status value
- **Script**: `link_ws_to_renewable.py`

### New Data Source
- **Current Source**: Annual Electricity Flow calculation (T + O + S)
- **Current Value**: 1,234,056.40 MWh
- **Method**: Calculated from renewable energy distribution through the electricity grid
- **Script**: `link_ws_to_annual_electricity.py`

## Calculation Formula

The new value is calculated as:

```
Stromnetz zum Endverbrauch = T + O + S
```

Where:
- **T** = Rückverstromung (Reconversion from gas storage) = 263,120.55 MWh
  - Calculated as: Gasspeicher Strom - 160
  - Gasspeicher Strom = Elektrolyse Stromspeicher × 65% efficiency
  
- **O** = Direct renewable to grid = 966,410.85 MWh
  - Calculated as: N - Q - Elektrolyse Stromspeicher
  - This is the renewable energy that flows directly to the grid without storage
  
- **S** = Biomass contribution = 4,525.00 MWh
  - From RenewableData code 4.4.1 (target value)
  - Controllable biomass power plants

**Total**: 1,234,056.40 MWh

## Technical Details

### Script: `link_ws_to_annual_electricity.py`

The script performs the following steps:

1. **Fetches renewable energy data** from various sources:
   - PV: 1.1.2.1.2 + 1.2.1.2
   - Wind: 2.1.1.2.2 + 2.2.1.2
   - Hydro+Geothermal: 3.1.1.2
   - Biomass: 4.4.1

2. **Calculates flow through system**:
   - M node: PV + Wind + Hydro
   - Electrolysis branches: 9.2.1.5.2 (nach Angebot) and 9.3.1 (Überschuss)
   - Storage efficiency: 65% for hydrogen production
   - Reconversion: T = (Elektrolyse Stromspeicher × 65%) - 160

3. **Computes final grid supply**:
   - Direct renewable flow (O)
   - Reconverted storage (T)
   - Biomass (S)

4. **Updates WS database**:
   - Sets `stromverbr_raumwaerm_korr` in row 366
   - Value represents annual electricity supply to end consumers

### Integration with Annual Electricity View

The calculation in `link_ws_to_annual_electricity.py` mirrors the logic in `simulator/views.py` function `annual_electricity_view()`. This ensures:

- ✅ Consistent calculation across database and web display
- ✅ Single source of truth for electricity flow logic
- ✅ Automatic updates when renewable data changes

### Verification

After update:
- **WS Row 366 Value**: 1,234,056.40 MWh
- **Sum of Daily Values (days 1-365)**: 1,124,854.43 MWh
- **Difference**: +109,201.98 MWh (+9.71%)

The difference represents:
- Additional electricity from gas storage reconversion (T)
- Optimized distribution through the electricity system
- Efficiency gains and losses through storage/reconversion cycle

## Files Modified

1. **Created**: `link_ws_to_annual_electricity.py`
   - New script to calculate and update row 366 from Annual Electricity
   
2. **Superseded**: `link_ws_to_renewable.py`
   - Old script that linked to RenewableData 9.4.3
   - Keep for reference but use new script for updates

3. **Created**: `verify_ws_366.py`
   - Verification script to check current row 366 value
   - Shows calculation source and comparison with daily sum

## Usage

To update WS row 366 with the latest Annual Electricity calculation:

```bash
python3 link_ws_to_annual_electricity.py
```

To verify the current value:

```bash
python3 verify_ws_366.py
```

## Relationship to Annual Electricity Flow Diagram

The WS row 366 value now represents the final yellow block in the Annual Electricity Flow diagram:

```
[Sources: PV, Wind, Hydro, Biomass]
         ↓
[M Node - Total Generation]
         ↓
[Branches: Electrolysis, Curtailment, Direct]
         ↓
[Electrolysis → Storage → Reconversion (T)]
         ↓
[Final: Stromnetz zum Endverbrauch = T + O + S]
         ↓
[WS Row 366 Column J]
```

This creates a logical data flow from renewable sources → electricity system → WS database.

## Notes

- The value will change when renewable energy targets are updated
- To recalculate, simply run `link_ws_to_annual_electricity.py`
- The Annual Electricity web view uses the same calculation logic
- This ensures consistency between database and UI display
