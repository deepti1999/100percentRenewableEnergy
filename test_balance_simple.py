"""
SIMPLE BALANCE TEST - Tests the balance_full_system function directly
===================================================================
Tests:
1. Balance completes within 90 seconds (no stuck/hang)  
2. End balance is achieved (both WS and Energy within tolerance)
3. Final 10.1 is correctly calculated following the chain

This test calls balance_full_system directly via HTTP, avoiding signal recursion.

Run: python3 test_balance_simple.py
"""
import os
import sys
import time
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client
from django.contrib.auth.models import User
from simulator.models import RenewableData
from simulator.ws_models import WSData
from calculation_engine.bilanz_engine import calculate_bilanz_data

# Configuration  
MAX_TIME_SECONDS = 90
WS_TOLERANCE = 10.0
ENERGY_TOLERANCE = 1.0

print("="*80)
print("SIMPLE BALANCE TEST (HTTP API)")
print("="*80)
print(f"Max time: {MAX_TIME_SECONDS}s | WS tol: {WS_TOLERANCE} | Energy tol: {ENERGY_TOLERANCE}")
print("="*80)

# Create test client
client = Client(enforce_csrf_checks=False)

# Get or create test user
user, created = User.objects.get_or_create(username='testuser')
if created:
    user.set_password('testpass')
    user.save()
    print("   Created new test user")
else:
    # Make sure password is set
    user.set_password('testpass')
    user.save()
    
login_success = client.login(username='testuser', password='testpass')
print(f"   Login success: {login_success}")

# Record initial state
print("\n📊 Initial State:")
r101 = RenewableData.objects.get(code='10.1')
initial_10_1 = r101.target_value
print(f"   10.1: {initial_10_1:.2f}")

row_366 = WSData.objects.get(tag_im_jahr=366)
initial_ws_balance = row_366.ladezustand_netto or 0
print(f"   WS Balance: {initial_ws_balance:.2f}")

bilanz_initial = calculate_bilanz_data()
initial_demand = bilanz_initial.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
initial_renewable = bilanz_initial.get("renewable_by_sector", {}).get("ziel", {}).get("gesamt", 0) or 0
initial_gap = initial_demand - initial_renewable
print(f"   Energy Gap: {initial_gap:.2f}")

# Test results
results = {
    "test1_no_hang": False,
    "test2_balanced": False,
    "test3_chain_correct": False,
    "duration": 0,
}

print("\n🔄 Calling /api/balance-full/...")
start = time.time()

try:
    # Simulator app is mounted at '' (root) in landuse_project/urls.py
    # So paths are /api/... not /simulator/api/...
    response = client.get('/bilanz/')  # First check if bilanz page is accessible
    print(f"   Bilanz page accessible: {response.status_code}")
    
    response = client.post(
        '/api/balance-full/',  # Correct path - simulator at root
        data=json.dumps({
            "driver": "solar",
            "max_iterations": 5,
            "energy_tolerance": ENERGY_TOLERANCE,
            "ws_tolerance": WS_TOLERANCE
        }),
        content_type='application/json'
    )
    
    duration = time.time() - start
    results["duration"] = duration
    
    print(f"\n   Response Status: {response.status_code}")
    print(f"   Duration: {duration:.1f}s")
    
    # TEST 1: Check if completed within timeout
    if response.status_code == 200 and duration < MAX_TIME_SECONDS:
        results["test1_no_hang"] = True
        print("   ✅ TEST 1 PASS: Completed within timeout")
    else:
        print(f"   ❌ TEST 1 FAIL: Status={response.status_code}, Duration={duration:.1f}s")
    
    # Parse response
    if response.status_code == 200:
        resp_data = response.json()
        print(f"\n   Response: {json.dumps(resp_data, indent=2)[:500]}...")
        
        status = resp_data.get('status', 'unknown')
        
        # TEST 2: Check if balanced
        ws_result = resp_data.get('ws_result', {})
        energy_result = resp_data.get('energy_result', {})
        
        final_ws_balance = ws_result.get('final_balance', 0)
        final_gap = energy_result.get('final_gap', 0)
        
        ws_ok = ws_result.get('is_balanced', False) or abs(final_ws_balance) <= WS_TOLERANCE
        energy_ok = energy_result.get('is_balanced', False) or abs(final_gap) <= ENERGY_TOLERANCE
        
        if ws_ok and energy_ok:
            results["test2_balanced"] = True
            print(f"   ✅ TEST 2 PASS: Balanced (WS={final_ws_balance:.2f}, Gap={final_gap:.2f})")
        else:
            print(f"   ❌ TEST 2 FAIL: Not balanced (WS={final_ws_balance:.2f}, Gap={final_gap:.2f})")
        
        # TEST 3: Verify chain - check if 10.1 matches final calculation
        r101.refresh_from_db()
        final_10_1 = r101.target_value
        
        bilanz_final = calculate_bilanz_data()
        computed_10_1 = bilanz_final.get("renewable_by_sector", {}).get("ziel", {}).get("gesamt", 0) or 0
        
        diff = abs(final_10_1 - computed_10_1)
        if diff < 10.0:  # Allow 10 GWh tolerance
            results["test3_chain_correct"] = True
            print(f"   ✅ TEST 3 PASS: Chain correct (10.1={final_10_1:.2f}, computed={computed_10_1:.2f})")
        else:
            print(f"   ❌ TEST 3 FAIL: Mismatch (10.1={final_10_1:.2f}, computed={computed_10_1:.2f})")
    
except Exception as e:
    duration = time.time() - start
    results["duration"] = duration
    print(f"\n   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Final summary
print("\n" + "="*80)
print("TEST RESULTS SUMMARY")
print("="*80)

print(f"\n✓ TEST 1 - No Hang (< {MAX_TIME_SECONDS}s): ", end="")
print("✅ PASS" if results["test1_no_hang"] else "❌ FAIL", f"({results['duration']:.1f}s)")

print(f"✓ TEST 2 - Balance Achieved: ", end="")
print("✅ PASS" if results["test2_balanced"] else "❌ FAIL")

print(f"✓ TEST 3 - Chain Correct: ", end="")
print("✅ PASS" if results["test3_chain_correct"] else "❌ FAIL")

all_passed = all([results["test1_no_hang"], results["test2_balanced"], results["test3_chain_correct"]])
print(f"\n{'✅ ALL TESTS PASSED!' if all_passed else '❌ SOME TESTS FAILED'}")
print("="*80)

sys.exit(0 if all_passed else 1)
