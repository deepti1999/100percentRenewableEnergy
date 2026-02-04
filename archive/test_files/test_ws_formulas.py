"""
Test WS Formula Resolution
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, RenewableData, VerbrauchData
from simulator.formula_service import evaluate_with_mappings

print("="*80)
print("TESTING WS FORMULA RESOLUTION")
print("="*80)

# Test Row 366 reference calculations
print("\n1. Testing Row 366 Reference Formulas...")
print("-" * 80)

# Test davon_raumw_korr_366 = V_2_9_2_ziel * (V_2_4_ziel / 100)
print("\nTesting WS_DAVON_RAUMW_KORR_366:")
try:
    v_292 = VerbrauchData.objects.filter(code='2.9.2').first()
    v_24 = VerbrauchData.objects.filter(code='2.4').first()
    
    if v_292 and v_24:
        print(f"  Verbrauch 2.9.2.ziel = {v_292.ziel}")
        print(f"  Verbrauch 2.4.ziel = {v_24.ziel}")
        expected = v_292.ziel * (v_24.ziel / 100) if v_24.ziel else 0
        print(f"  Expected: {expected}")
        
        status, target = evaluate_with_mappings('WS_DAVON_RAUMW_KORR_366', category='ws')
        print(f"  Formula Result: {target}")
        print(f"  ✓ Match!" if abs(target - expected) < 0.01 else f"  ✗ Mismatch!")
    else:
        print("  ⚠ Verbrauch data not found")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test renewable references
print("\nTesting WS_REF_PV (1.1.2.1.2 + 1.2.1.2):")
try:
    r1 = RenewableData.objects.filter(code='1.1.2.1.2').first()
    r2 = RenewableData.objects.filter(code='1.2.1.2').first()
    
    if r1 and r2:
        print(f"  Renewable 1.1.2.1.2.target = {r1.target_value}")
        print(f"  Renewable 1.2.1.2.target = {r2.target_value}")
        expected = (r1.target_value or 0) + (r2.target_value or 0)
        print(f"  Expected: {expected}")
        
        status, target = evaluate_with_mappings('WS_REF_PV', category='ws')
        print(f"  Formula Result: {target}")
        print(f"  ✓ Match!" if abs(target - expected) < 0.01 else f"  ✗ Mismatch!")
    else:
        print("  ⚠ Renewable data not found")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\nTesting WS_REF_WIND (2.1.1.2.2 + 2.2.1.2):")
try:
    r1 = RenewableData.objects.filter(code='2.1.1.2.2').first()
    r2 = RenewableData.objects.filter(code='2.2.1.2').first()
    
    if r1 and r2:
        print(f"  Renewable 2.1.1.2.2.target = {r1.target_value}")
        print(f"  Renewable 2.2.1.2.target = {r2.target_value}")
        expected = (r1.target_value or 0) + (r2.target_value or 0)
        print(f"  Expected: {expected}")
        
        status, target = evaluate_with_mappings('WS_REF_WIND', category='ws')
        print(f"  Formula Result: {target}")
        print(f"  ✓ Match!" if abs(target - expected) < 0.01 else f"  ✗ Mismatch!")
    else:
        print("  ⚠ Renewable data not found")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test cascading formulas
print("\n2. Testing Cascading Formulas...")
print("-" * 80)

print("\nTesting WS_REF_TOTAL_GEN (PV + Wind + Hydro):")
try:
    status, target = evaluate_with_mappings('WS_REF_TOTAL_GEN', category='ws')
    print(f"  Formula Result: {target}")
    if target > 0:
        print(f"  ✓ Calculated successfully!")
    else:
        print(f"  ⚠ Zero result - check input data")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\nTesting WS_STROMVERBR_RAUMWAERM_KORR_366 (Final grid supply):")
try:
    status, target = evaluate_with_mappings('WS_STROMVERBR_RAUMWAERM_KORR_366', category='ws')
    print(f"  Formula Result: {target}")
    if target != 0:
        print(f"  ✓ Calculated successfully!")
    else:
        print(f"  ⚠ Zero result - check input data")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*80)
print("✅ WS Formula System Test Complete")
print("="*80)
print("\nNOTE: WS daily formulas require WS-specific context (ws_current_row, ws_sum, etc.)")
print("These will be provided by the WS calculation engine during actual calculation.")
