#!/bin/bash
# Delete all legacy hardcoded formula files

echo "Deleting legacy hardcoded files..."

# Legacy renewable formula files
rm -f simulator/renewable_formulas.py
rm -f renewable_energy_complete_formulas.py

# Legacy verbrauch calculation file
rm -f simulator/verbrauch_calculations.py.DEPRECATED_NOT_USED

# Legacy WS engine (if it has hardcoded math)
# Keep ws_engine.py but we'll fix it to be DB-only

echo "✅ Legacy files deleted"
echo "Remaining files to fix:"
echo "  - calculation_engine/renewable_engine.py (duplicate class)"
echo "  - calculation_engine/bilanz_engine.py (silent fallbacks)"
echo "  - simulator/views.py (fallback to stored values)"
echo "  - simulator/models.py (get_calculated_values fallbacks)"
