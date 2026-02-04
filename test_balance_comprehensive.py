"""
COMPREHENSIVE BALANCE BUTTON TEST
==================================
Tests:
1. Balance completes within 90 seconds (no stuck/hang)
2. End balance is achieved (both WS and Energy within tolerance)
3. Final 10.1 is correctly calculated following the chain

Run: python3 test_balance_comprehensive.py
"""
import os
import sys
import time
import signal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.db import transaction
from simulator.models import RenewableData, LandUse
from simulator.ws_models import WSData
from simulator.signals import get_ws_constants
from simulator.recalc_service import recalc_all_renewables_full
from simulator.ws_formula_service import recalculate_all_ws_data
from calculation_engine.bilanz_engine import calculate_bilanz_data

# Configuration
MAX_TIME_SECONDS = 90  # 1.5 minutes
WS_TOLERANCE = 10.0    # GWh
ENERGY_TOLERANCE = 1.0 # GWh
MAX_ITERATIONS = 10

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Balance operation timed out!")

def run_balance_test():
    """
    Run the balance test with all 3 verification steps
    """
    print("="*80)
    print("COMPREHENSIVE BALANCE BUTTON TEST")
    print("="*80)
    print(f"Max time: {MAX_TIME_SECONDS}s | WS tol: {WS_TOLERANCE} | Energy tol: {ENERGY_TOLERANCE}")
    print("="*80)
    
    # Set up timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(MAX_TIME_SECONDS)
    
    start_time = time.time()
    test_results = {
        "test1_no_hang": False,
        "test2_balanced": False,
        "test3_chain_correct": False,
        "duration_seconds": 0,
        "iterations": 0,
        "final_ws_balance": None,
        "final_energy_gap": None,
        "final_10_1": None,
        "expected_10_1": None,
    }
    
    try:
        print("\n🔄 Starting balance process...")
        
        # Store initial 10.1 value for later comparison
        r101 = RenewableData.objects.get(code='10.1')
        initial_10_1 = r101.target_value
        print(f"   Initial 10.1: {initial_10_1:.2f}")
        
        # Get initial LU_2.1 (solar driver)
        lu_solar = LandUse.objects.get(code='LU_2.1')
        initial_lu_ha = lu_solar.target_ha
        print(f"   Initial LU_2.1: {initial_lu_ha:.2f} ha")
        
        # BALANCE LOOP
        iteration_history = []
        final_lu_ha = initial_lu_ha
        
        for iteration in range(MAX_ITERATIONS):
            print(f"\n--- Iteration {iteration+1}/{MAX_ITERATIONS} ---")
            elapsed = time.time() - start_time
            print(f"   Elapsed: {elapsed:.1f}s")
            
            # ============================================
            # STEP 1: Adjust LandUse (goal-seek for energy balance)
            # ============================================
            print("   [1] Adjusting LandUse for energy balance...")
            bilanz = calculate_bilanz_data()
            demand = bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
            
            # Get current 10.1
            r101.refresh_from_db()
            current_renewable = r101.target_value or 0
            energy_gap = demand - current_renewable
            
            # Simple proportional adjustment
            if abs(energy_gap) > ENERGY_TOLERANCE:
                adjustment_factor = 1 + (energy_gap / current_renewable * 0.5) if current_renewable else 1.1
                new_ha = final_lu_ha * adjustment_factor
                new_ha = max(0, new_ha)  # Don't go negative
                
                lu_solar.target_ha = new_ha
                lu_solar.save(skip_cascade=True)
                lu_solar._recalculate_renewable_dependents()
                final_lu_ha = new_ha
                print(f"       LU_2.1: {final_lu_ha:.2f} ha (gap={energy_gap:.2f})")
            
            # ============================================
            # STEP 2: FIRST RENEWABLE RECALC (full page)
            # ============================================
            print("   [2] Full renewable recalc (after LandUse)...")
            recalc_all_renewables_full(exclude_ws_dependent=False)
            
            # ============================================
            # STEP 3: WS recalculation
            # ============================================
            print("   [3] WS recalculation...")
            recalculate_all_ws_data(num_passes=1)
            
            # ============================================
            # STEP 4: Balance WS (adjust stromverbr)
            # ============================================
            print("   [4] Balancing WS Storage...")
            row_366 = WSData.objects.get(tag_im_jahr=366)
            ws_balance = row_366.ladezustand_netto or 0
            
            # Simple WS balance - adjust stromverbr proportionally
            if abs(ws_balance) > WS_TOLERANCE:
                current_stromverbr = row_366.stromverbr_raumwaerm_korr or 0
                # Increase stromverbr if storage is positive (too much energy stored)
                # Decrease if negative (not enough stored)
                adjustment = ws_balance * 0.5  # Damped adjustment
                new_stromverbr = current_stromverbr + adjustment
                new_stromverbr = max(0, new_stromverbr)
                WSData.objects.filter(tag_im_jahr=366).update(stromverbr_raumwaerm_korr=new_stromverbr)
                
                # Recalc WS with new stromverbr
                recalculate_all_ws_data(num_passes=1)
                row_366.refresh_from_db()
                ws_balance = row_366.ladezustand_netto or 0
                print(f"       WS balance: {ws_balance:.2f} (stromverbr={new_stromverbr:.2f})")
            
            # ============================================
            # STEP 5: Push WS → Renewable (9.3.1, 9.3.4)
            # ============================================
            print("   [5] Push WS → Renewable (9.3.1, 9.3.4)...")
            ws_consts = get_ws_constants()
            abregelung = row_366.abregelung_z or 0.0
            ely_surplus = (row_366.einspeich or 0.0) / ws_consts['ETA_STROM_GAS'] if ws_consts.get('ETA_STROM_GAS') else 0.0
            
            RenewableData.objects.filter(code='9.3.4').update(target_value=abregelung)
            RenewableData.objects.filter(code='9.3.1').update(target_value=ely_surplus)
            print(f"       9.3.1={ely_surplus:.2f}, 9.3.4={abregelung:.2f}")
            
            # ============================================
            # STEP 6: SECOND RENEWABLE RECALC (9.x + 10.x)
            # ============================================
            print("   [6] Second renewable recalc (9.x + 10.x)...")
            recalc_all_renewables_full(exclude_ws_dependent=False)
            
            # ============================================
            # STEP 7: Final verification
            # ============================================
            print("   [7] Verification...")
            row_366.refresh_from_db()
            r101.refresh_from_db()
            
            final_ws_balance = row_366.ladezustand_netto or 0
            final_10_1 = r101.target_value or 0
            
            bilanz_final = calculate_bilanz_data()
            final_demand = bilanz_final.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
            final_gap = final_demand - final_10_1
            
            ws_ok = abs(final_ws_balance) <= WS_TOLERANCE
            energy_ok = abs(final_gap) <= ENERGY_TOLERANCE
            
            print(f"       WS: {final_ws_balance:.2f} (ok={ws_ok})")
            print(f"       Energy: gap={final_gap:.2f} (ok={energy_ok})")
            print(f"       10.1: {final_10_1:.2f}")
            
            iteration_history.append({
                "iteration": iteration + 1,
                "ws_balance": final_ws_balance,
                "energy_gap": final_gap,
                "lu_ha": final_lu_ha,
                "val_10_1": final_10_1,
            })
            
            if ws_ok and energy_ok:
                print(f"\n✅ BALANCED after {iteration+1} iterations!")
                test_results["test2_balanced"] = True
                break
        
        # Cancel timeout
        signal.alarm(0)
        
        # Record results
        test_results["test1_no_hang"] = True
        test_results["duration_seconds"] = time.time() - start_time
        test_results["iterations"] = len(iteration_history)
        test_results["final_ws_balance"] = final_ws_balance
        test_results["final_energy_gap"] = final_gap
        test_results["final_10_1"] = final_10_1
        
        # ============================================
        # TEST 3: Verify chain correctness
        # ============================================
        print("\n" + "="*60)
        print("TEST 3: Verifying chain correctness (fresh 10.1 calculation)")
        print("="*60)
        
        # Force a fresh recalculation to verify the chain
        print("   Running fresh chain: LU → Renewable → WS → 9.3.x → Renewable...")
        
        # Step 1: Fresh renewable recalc
        recalc_all_renewables_full(exclude_ws_dependent=True)
        
        # Step 2: Fresh WS recalc
        recalculate_all_ws_data(num_passes=1)
        
        # Step 3: Push WS → 9.3.x
        row_366.refresh_from_db()
        abregelung = row_366.abregelung_z or 0.0
        ely_surplus = (row_366.einspeich or 0.0) / ws_consts['ETA_STROM_GAS'] if ws_consts.get('ETA_STROM_GAS') else 0.0
        RenewableData.objects.filter(code='9.3.4').update(target_value=abregelung)
        RenewableData.objects.filter(code='9.3.1').update(target_value=ely_surplus)
        
        # Step 4: Final renewable recalc
        recalc_all_renewables_full(exclude_ws_dependent=False)
        
        # Verify 10.1 is consistent
        r101.refresh_from_db()
        verified_10_1 = r101.target_value or 0
        test_results["expected_10_1"] = verified_10_1
        
        # Check if 10.1 is stable (same as what we got from balance)
        difference = abs(final_10_1 - verified_10_1)
        is_chain_correct = difference < 1.0  # Allow 1 GWh tolerance
        test_results["test3_chain_correct"] = is_chain_correct
        
        print(f"   Final 10.1 from balance: {final_10_1:.2f}")
        print(f"   Verified 10.1 from fresh chain: {verified_10_1:.2f}")
        print(f"   Difference: {difference:.2f}")
        print(f"   Chain correct: {is_chain_correct}")
        
    except TimeoutError as e:
        signal.alarm(0)
        test_results["duration_seconds"] = MAX_TIME_SECONDS
        print(f"\n❌ TIMEOUT: {e}")
        
    except Exception as e:
        signal.alarm(0)
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================
    # FINAL RESULTS
    # ============================================
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    print(f"\n✓ TEST 1 - No Hang (< {MAX_TIME_SECONDS}s): ", end="")
    if test_results["test1_no_hang"]:
        print(f"✅ PASS ({test_results['duration_seconds']:.1f}s)")
    else:
        print("❌ FAIL (Timed out)")
    
    print(f"✓ TEST 2 - Balance Achieved: ", end="")
    if test_results["test2_balanced"]:
        print(f"✅ PASS (WS={test_results['final_ws_balance']:.2f}, Gap={test_results['final_energy_gap']:.2f})")
    else:
        print(f"❌ FAIL (WS={test_results.get('final_ws_balance', 'N/A')}, Gap={test_results.get('final_energy_gap', 'N/A')})")
    
    print(f"✓ TEST 3 - Chain Correct: ", end="")
    if test_results["test3_chain_correct"]:
        print(f"✅ PASS (10.1 verified: {test_results['expected_10_1']:.2f})")
    else:
        print(f"❌ FAIL (Mismatch: {test_results.get('final_10_1', 'N/A')} vs {test_results.get('expected_10_1', 'N/A')})")
    
    all_passed = all([test_results["test1_no_hang"], test_results["test2_balanced"], test_results["test3_chain_correct"]])
    print(f"\n{'✅ ALL TESTS PASSED!' if all_passed else '❌ SOME TESTS FAILED'}")
    print("="*80)
    
    return test_results

if __name__ == "__main__":
    results = run_balance_test()
    sys.exit(0 if all([results["test1_no_hang"], results["test2_balanced"], results["test3_chain_correct"]]) else 1)
