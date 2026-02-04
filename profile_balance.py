import os
import django
import time
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.views import _balance_energy_core, _balance_ws_storage_core
from simulator.recalc_service import unified_recalc_all
from calculation_engine.bilanz_engine import calculate_bilanz_data

def profile_balancing():
    print("Starting profile...")
    
    start_total = time.perf_counter()
    
    # 1. Profile Energy Balance Core
    print("\n--- Profiling _balance_energy_core (driver=solar, max_iter=5) ---")
    start = time.perf_counter()
    res_e = _balance_energy_core(driver="solar", energy_tolerance=1.0, max_iter=5, num_passes=1)
    end = time.perf_counter()
    print(f"Energy Balance Result: {res_e}")
    print(f"Duration: {end - start:.2f}s")
    
    # 2. Profile WS Storage Balance Core
    print("\n--- Profiling _balance_ws_storage_core (max_iter=5) ---")
    start = time.perf_counter()
    res_ws = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=5, num_passes=1)
    end = time.perf_counter()
    print(f"WS Balance Result: {res_ws}")
    print(f"Duration: {end - start:.2f}s")
    
    # 3. Profile unified_recalc_all
    print("\n--- Profiling unified_recalc_all ---")
    start = time.perf_counter()
    res_u = unified_recalc_all()
    end = time.perf_counter()
    print(f"Unified Recalc Duration: {end - start:.2f}s")

    end_total = time.perf_counter()
    print(f"\nTotal profiling time: {end_total - start_total:.2f}s")

if __name__ == "__main__":
    profile_balancing()
