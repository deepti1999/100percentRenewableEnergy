"""
Test full chain recalculation with new FormulaVariable system
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

print("="*80)
print("TESTING FULL CHAIN RECALC WITH NEW FORMULAVARIABLE SYSTEM")
print("="*80)

from simulator.recalc_service import full_chain_recalc
from simulator.ws_models import WSData

print("\n🧪 Test: Run full_chain_recalc...")
try:
    print("   Running full_chain_recalc()...")
    full_chain_recalc()
    print("   ✅ full_chain_recalc completed")
    
    # Check if formulas were applied correctly
    row_1 = WSData.objects.get(tag_im_jahr=1)
    print(f"\n   Row 1 values:")
    print(f"   - stromverbr: {row_1.stromverbr}")
    print(f"   - windstrom: {row_1.windstrom}")
    print(f"   - solarstrom: {row_1.solarstrom}")
    print(f"   - wind_solar_konstant: {row_1.wind_solar_konstant}")
    
    row_366 = WSData.objects.get(tag_im_jahr=366)
    print(f"\n   Row 366 values:")
    print(f"   - stromverbr: {row_366.stromverbr}")
    print(f"   - windstrom: {row_366.windstrom}")
    print(f"   - solarstrom: {row_366.solarstrom}")
    
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    print(f"\n   Traceback:")
    traceback.print_exc()

print("\n" + "="*80)
