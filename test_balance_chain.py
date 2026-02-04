"""
Test the Fixed Balance Button by calling functions directly (bypasses HTTP layer)
Chain: LandUse → Full Renewable → WS → 9.x/10.x Renewable
"""
import os
import sys

# Add testserver to ALLOWED_HOSTS before Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

# Patch ALLOWED_HOSTS for test
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from simulator.views import _balance_energy_core, _balance_ws_storage_core
from simulator.recalc_service import recalc_all_renewables_full
from simulator.ws_formula_service import recalculate_all_ws_data 
from simulator.models import RenewableData
from simulator.ws_models import WSData
from simulator.signals import get_ws_constants
from calculation_engine.bilanz_engine import calculate_bilanz_data

print("="*80)
print("TESTING FIXED BALANCE BUTTON (Direct Function Calls)")
print("Chain: LandUse → Full Renewable → WS → 9.x/10.x Renewable")
print("="*80)

WS_TOLERANCE = 10.0
ENERGY_TOLERANCE = 1.0
MAX_ITERATIONS = 5

print("\n🔄 Starting balance test...")

iteration_history = []
for i in range(MAX_ITERATIONS):
    print(f"\n--- Iteration {i+1}/{MAX_ITERATIONS} ---")
    
    # STEP 1: Balance Energy
    print("  [1] Balancing Energy...")
    energy_result = _balance_energy_core(driver="solar", energy_tolerance=ENERGY_TOLERANCE, max_iter=10)
    energy_balanced = energy_result.get("is_balanced", False)
    energy_gap = energy_result.get("final_gap", 0)
    print(f"      Energy: balanced={energy_balanced}, gap={energy_gap:.2f}")
    
    # FIRST RENEWABLE RECALC
    print("  [1b] Full Renewable recalc...")
    recalc_all_renewables_full(exclude_ws_dependent=False)
    
    # STEP 2: WS Recalc
    print("  [2] Recalculating WS...")
    recalculate_all_ws_data(num_passes=1)
    
    # STEP 3: Balance WS
    print("  [3] Balancing WS Storage...")
    ws_result = _balance_ws_storage_core(ws_tolerance=WS_TOLERANCE, max_iter=10)
    ws_balanced = ws_result.get("is_balanced", False)
    ws_balance = ws_result.get("final_balance", 0)
    print(f"      WS: balanced={ws_balanced}, ladezustand={ws_balance:.2f}")
    
    # STEP 4: Set FIXED values for 9.3.1 and 9.3.4
    print("  [4] Setting fixed values for 9.3.1 and 9.3.4...")
    
    RenewableData.objects.filter(code='9.3.4').update(target_value=189289)
    RenewableData.objects.filter(code='9.3.1').update(target_value=405047)
    print(f"      9.3.1=405047 (fixed), 9.3.4=189289 (fixed)")
    
    # SECOND RENEWABLE RECALC - 9.x + 10.x
    print("  [4b] Recalculating 9.x + 10.x sections...")
    recalc_all_renewables_full(exclude_ws_dependent=False)
    
    # STEP 5: Final verification
    print("  [5] Final verification...")
    row_366.refresh_from_db()
    final_ws = row_366.ladezustand_netto or 0
    ws_still_ok = abs(final_ws) <= WS_TOLERANCE
    
    bilanz = calculate_bilanz_data()
    demand = bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
    renewable = bilanz.get("renewable_by_sector", {}).get("ziel", {}).get("gesamt", 0) or 0
    final_gap = demand - renewable
    energy_still_ok = abs(final_gap) <= ENERGY_TOLERANCE
    
    print(f"      WS: {final_ws:.2f} (ok={ws_still_ok})")
    print(f"      Energy: gap={final_gap:.2f} (ok={energy_still_ok})")
    
    iteration_history.append({
        "iteration": i + 1,
        "ws": final_ws,
        "gap": final_gap,
        "ws_ok": ws_still_ok,
        "energy_ok": energy_still_ok,
    })
    
    if ws_still_ok and energy_still_ok:
        print(f"\n✅ FULLY BALANCED AND STABLE after {i+1} iterations!")
        break
    else:
        print("      ⚠️ Chain broke balance, continuing...")

else:
    print(f"\n⚠️ Max iterations reached")

print("\n" + "-"*40)
print("Iteration History:")
for h in iteration_history:
    print(f"  [{h['iteration']}] WS={h['ws']:.2f} (ok={h['ws_ok']}), Gap={h['gap']:.2f} (ok={h['energy_ok']})")

print("\n" + "="*80)
