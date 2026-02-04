"""
CHAIN STABILITY TEST
====================
Tests that after balance, if we run the full chain again:
  LandUse → Renewable → WS → 9.3.x → 10.1
The 10.1 value should NOT change.
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'landuse_project.settings'
import django
django.setup()

from simulator.models import RenewableData, LandUse
from simulator.ws_models import WSData
from simulator.recalc_service import recalc_all_renewables_full
from simulator.ws_formula_service import recalculate_all_ws_data
from simulator.signals import get_ws_constants
from calculation_engine.bilanz_engine import calculate_bilanz_data

print('='*70)
print('CHAIN STABILITY TEST')
print('Testing: After balance, does full chain produce same 10.1?')
print('='*70)

# 1. Get current values BEFORE any chain run
lu = LandUse.objects.get(code='LU_2.1')
r101 = RenewableData.objects.get(code='10.1')
row_366 = WSData.objects.get(tag_im_jahr=366)

print(f'\n📊 BEFORE CHAIN (current state after balance):')
print(f'   LU_2.1 (Solar ha): {lu.target_ha:.2f}')
print(f'   10.1 (Renewable Total): {r101.target_value:.2f}')
print(f'   WS ladezustand_netto: {row_366.ladezustand_netto:.6f}')

current_10_1 = r101.target_value

# 2. RUN FULL CHAIN: LandUse → Renewable → WS → 9.3.x → 10.x
print(f'\n🔄 Running FULL CHAIN (simulating Save Values)...')
print(f'   Step 1: Full Renewable recalc (from LandUse)...')
recalc_all_renewables_full(exclude_ws_dependent=True)

print(f'   Step 2: WS recalc...')
recalculate_all_ws_data(num_passes=1)

print(f'   Step 3: Push WS → 9.3.1, 9.3.4...')
row_366.refresh_from_db()
ws_consts = get_ws_constants()
abregelung = row_366.abregelung_z or 0.0
ely_surplus = (row_366.einspeich or 0.0) / ws_consts['ETA_STROM_GAS'] if ws_consts.get('ETA_STROM_GAS') else 0.0
RenewableData.objects.filter(code='9.3.4').update(target_value=abregelung)
RenewableData.objects.filter(code='9.3.1').update(target_value=ely_surplus)
print(f'      9.3.1={ely_surplus:.2f}, 9.3.4={abregelung:.2f}')

print(f'   Step 4: Recalc 9.x + 10.x...')
recalc_all_renewables_full(exclude_ws_dependent=False)

# 3. Get values AFTER chain run
r101.refresh_from_db()
row_366.refresh_from_db()
after_10_1 = r101.target_value
after_ws = row_366.ladezustand_netto or 0

bilanz = calculate_bilanz_data()
demand = bilanz.get('verbrauch_gesamt', {}).get('ziel', {}).get('gesamt', 0) or 0
renewable = bilanz.get('renewable_by_sector', {}).get('ziel', {}).get('gesamt', 0) or 0
gap = demand - renewable

print(f'\n📊 AFTER CHAIN:')
print(f'   10.1: {after_10_1:.2f}')
print(f'   WS ladezustand_netto: {after_ws:.6f}')
print(f'   Energy demand: {demand:.2f}')
print(f'   Energy renewable: {renewable:.2f}')
print(f'   Energy gap: {gap:.2f}')

# 4. VERIFY STABILITY
diff = abs(after_10_1 - current_10_1)
is_stable = diff < 1.0  # Allow 1 GWh tolerance

print(f'\n🔍 STABILITY CHECK:')
print(f'   10.1 before chain: {current_10_1:.2f}')
print(f'   10.1 after chain:  {after_10_1:.2f}')
print(f'   Difference: {diff:.6f} GWh')
print(f'   Is stable (diff < 1 GWh): {is_stable}')

if is_stable and abs(after_ws) < 10.0 and abs(gap) < 1.0:
    print(f'\n✅ CHAIN STABILITY VERIFIED!')
    print(f'   - 10.1 unchanged after full chain run')
    print(f'   - WS still balanced')
    print(f'   - Energy still balanced')
else:
    print(f'\n❌ CHAIN NOT STABLE!')
    print(f'   10.1 changed by {diff:.2f} GWh')

print('='*70)
