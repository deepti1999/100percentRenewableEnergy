"""
Direct test of WS balance functionality - bypassing HTTP
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

print("="*80)
print("TESTING WS BALANCE WITH NEW FORMULAVARIABLE SYSTEM")
print("="*80)

from simulator.views import _balance_ws_storage_core
from simulator.ws_models import WSData

print("\n🧪 Test 1: Check current Row 366 values...")
try:
    row_366 = WSData.objects.get(tag_im_jahr=366)
    print(f"   stromverbr_raumwaerm_korr_366: {row_366.stromverbr_raumwaerm_korr:,.2f}")
    print(f"   ladezustand_netto_366: {row_366.ladezustand_netto:,.2f}")
    print("   ✅ Row 366 loaded")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n🧪 Test 2: Try simple WS balance (1 iteration)...")
try:
    result = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=1, num_passes=1)
    print(f"\n   Results:")
    print(f"   - is_balanced: {result.get('is_balanced')}")
    print(f"   - final_balance: {result.get('final_balance'):.2f}")
    print(f"   - final_stromverbr: {result.get('final_stromverbr'):.2f}")
    print(f"   - iterations: {result.get('iterations')}")
    print("   ✅ Balance function executed")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    print(f"\n   Traceback:")
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
