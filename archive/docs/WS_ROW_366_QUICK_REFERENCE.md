# WS Database Row 366 Update - Complete Guide

## Overview

This update changes how WS database row 366 (Column J: `stromverbr_raumwaerm_korr`) gets its value. Previously it was copied from RenewableData 9.4.3, but now it's calculated from the Annual Electricity Flow system.

## Quick Start

To update WS row 366 with the correct Annual Electricity value:

```bash
python3 link_ws_to_annual_electricity.py
```

To view the calculation breakdown:

```bash
python3 show_annual_electricity_summary.py
```

To verify the current value:

```bash
python3 verify_ws_366.py
```

## What Changed

### Before
- **Value Source**: Direct copy from RenewableData table (code 9.4.3)
- **Value**: 1,124,854.43 MWh
- **Logic**: Simple database reference
- **Script**: `link_ws_to_renewable.py` ⚠️ DEPRECATED

### After
- **Value Source**: Calculated from Annual Electricity Flow (T + O + S formula)
- **Value**: 1,234,056.40 MWh
- **Logic**: Complex renewable energy flow through electricity system
- **Script**: `link_ws_to_annual_electricity.py` ✅ ACTIVE

## The Calculation

```
Stromnetz zum Endverbrauch = T + O + S

Where:
  T = Rückverstromung (Reconversion)       = 263,120.55 MWh
  O = Direct renewable to grid             = 966,410.85 MWh  
  S = Biomass                              = 4,525.00 MWh
  ───────────────────────────────────────────────────────────
  Total                                    = 1,234,056.40 MWh
```

### Flow Through System

```
GENERATION SOURCES
├─ S: Biomass (4.4.1)                    =      4,525.00 MWh
├─ K: PV (1.1.2.1.2 + 1.2.1.2)          =  1,220,951.59 MWh
├─ J: Wind (2.1.1.2.2 + 2.2.1.2)        =    706,236.57 MWh
└─ L: Hydro+Geothermal (3.1.1.2)        =     19,492.52 MWh

M NODE (K + J + L)                       =  1,946,680.68 MWh
│
├─ Elektrolyse nach Angebot (9.2.1.5.2) =    385,933.82 MWh
│  └─ H₂ Production (65% Eta)            =    250,856.99 MWh
│
└─ N Node (M - Elektrolyse)              =  1,560,746.85 MWh
   │
   ├─ Q: Abregelung (9.3.4)              =    189,289.00 MWh (curtailed)
   │
   ├─ P: Elektrolyse Stromspeicher (9.3.1) = 405,047.00 MWh
   │  └─ U: Gasspeicher Strom (65% Eta)  =    263,280.55 MWh
   │     └─ T: Rückverstromung (U - 160) =    263,120.55 MWh → FINAL
   │
   └─ O: Direct to Grid                  =    966,410.85 MWh → FINAL

S: Biomass (from above)                  =      4,525.00 MWh → FINAL

FINAL: T + O + S                         =  1,234,056.40 MWh
```

## Files Reference

### Active Scripts

| File | Purpose | When to Use |
|------|---------|-------------|
| `link_ws_to_annual_electricity.py` | Update WS row 366 with Annual Electricity calculation | Run after updating renewable energy data |
| `show_annual_electricity_summary.py` | Display complete calculation breakdown | View all values and verify calculations |
| `verify_ws_366.py` | Check current WS row 366 value | Quick verification of database state |

### Documentation

| File | Purpose |
|------|---------|
| `WS_ROW_366_UPDATE_DOCUMENTATION.md` | Detailed technical documentation |
| `WS_ROW_366_QUICK_REFERENCE.md` | This quick reference guide |

### Deprecated Scripts

| File | Status | Notes |
|------|--------|-------|
| `link_ws_to_renewable.py` | ⚠️ DEPRECATED | Old method - kept for reference only |

## Web Interface

View the Annual Electricity Flow diagram with live calculations:
```
http://127.0.0.1:8000/annual-electricity/
```

The diagram shows:
- All generation sources (S, K, J, L)
- Flow through M and N nodes
- Electrolysis branches (nach Angebot and Stromspeicher)
- Storage and reconversion (P, U, T)
- Final grid supply (T + O + S)

## Database Schema

### WSData Table - Row 366
```python
tag_im_jahr: 366
datum_ref: "01.01.24"
stromverbr_raumwaerm_korr: 1,234,056.40  # Column J - Updated by script
```

This value represents the **annual electricity supply to end consumers** from all renewable sources after accounting for:
- Direct renewable flow to grid
- Storage and reconversion efficiency losses
- Curtailment (Abregelung)
- Biomass contribution

## Relationship to Daily Values

```
Daily Sum (Days 1-365):        1,124,854.43 MWh
Annual Reference (Row 366):    1,234,056.40 MWh
───────────────────────────────────────────────
Difference:                    +109,201.98 MWh (+9.71%)
```

The difference represents:
- ✅ Reconverted electricity from storage (T component)
- ✅ Optimized distribution through grid system
- ✅ System efficiency effects (storage/reconversion cycle)

## Integration Points

### 1. RenewableData Table
The calculation pulls target values from:
- 1.1.2.1.2, 1.2.1.2 (PV)
- 2.1.1.2.2, 2.2.1.2 (Wind)
- 3.1.1.2 (Hydro+Geothermal)
- 4.4.1 (Biomass)
- 9.2.1.5.2 (Elektrolyse nach Angebot)
- 9.3.1 (Elektrolyse Stromspeicher)
- 9.3.4 (Abregelung)

### 2. Annual Electricity View
The Django view at `simulator/views.py` function `annual_electricity_view()` uses identical calculation logic to populate the web diagram.

### 3. WSData Table
Row 366 stores the final calculated value, which is used as a reference for other WS calculations.

## Troubleshooting

### Value Doesn't Match
If the WS row 366 value doesn't match the calculation:
```bash
python3 link_ws_to_annual_electricity.py
```

### Check Calculation Components
View the detailed breakdown:
```bash
python3 show_annual_electricity_summary.py
```

### Verify Database State
Quick check of current values:
```bash
python3 verify_ws_366.py
```

### Web Diagram Not Updating
Restart Django server:
```bash
python3 manage.py runserver
```

## Best Practices

1. **After updating renewable data**: Always run `link_ws_to_annual_electricity.py`
2. **Before running WS calculations**: Verify row 366 is up to date
3. **For debugging**: Use `show_annual_electricity_summary.py` to see all components
4. **Regular validation**: Periodically run `verify_ws_366.py` to ensure consistency

## Notes

- The calculation uses **target values** (Ziel) from RenewableData, not status values
- Storage efficiency is fixed at **65%** for hydrogen production
- Reconversion subtracts **160 MWh** from gas storage
- The web diagram and database calculation use **identical logic**
- Values are in **MWh** (megawatt-hours)

## Support

For questions or issues:
1. Check `WS_ROW_366_UPDATE_DOCUMENTATION.md` for detailed technical info
2. Run `show_annual_electricity_summary.py` to see current state
3. Review the calculation flow diagram above
4. Verify RenewableData table has all required codes
