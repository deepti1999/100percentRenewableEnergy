import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, Formula
from simulator.formula_service import evaluate_with_mappings
from django.db import connection

# Force fresh DB connection
connection.close()
connection.connect()

print('=== Recalculating ALL RenewableData values ===')

# Get all renewable data sorted by code (to process in dependency order)
all_rd = list(RenewableData.objects.all().order_by('code'))
print(f'Total RenewableData entries: {len(all_rd)}')

# We need to recalculate multiple times because of dependencies
# (formula A depends on formula B which depends on formula C)
for round_num in range(5):  # 5 rounds should be enough for any dependency chain
    print(f'\n--- Round {round_num + 1} ---')
    changes = 0
    
    for rd in all_rd:
        # Status formula - key is the code (e.g. "10.1")
        try:
            status_val, _ = evaluate_with_mappings(rd.code, 'renewable')
            if status_val is not None and status_val != rd.status_value:
                print(f'{rd.code} status: {rd.status_value} -> {status_val}')
                rd.status_value = status_val
                changes += 1
        except Exception as e:
            if 'DoesNotExist' not in str(e):
                print(f'Error calculating status for {rd.code}: {e}')
        
        # Ziel formula - key is code + "_ziel" (e.g. "10.1_ziel")
        try:
            _, target_val = evaluate_with_mappings(f'{rd.code}_ziel', 'renewable')
            if target_val is not None and target_val != rd.target_value:
                print(f'{rd.code} target: {rd.target_value} -> {target_val}')
                rd.target_value = target_val
                changes += 1
        except Exception as e:
            if 'DoesNotExist' not in str(e):
                print(f'Error calculating target for {rd.code}: {e}')
        
        rd.save()
    
    print(f'Changes in round {round_num + 1}: {changes}')
    if changes == 0:
        print('No more changes, stopping.')
        break

print('\n=== Sample results ===')
rd_10_1 = RenewableData.objects.get(code='10.1')
print(f'10.1: status={rd_10_1.status_value}, target={rd_10_1.target_value}')

rd_1_1 = RenewableData.objects.get(code='1.1')
print(f'1.1: status={rd_1_1.status_value}, target={rd_1_1.target_value}')

rd_1_2 = RenewableData.objects.get(code='1.2')
print(f'1.2: status={rd_1_2.status_value}, target={rd_1_2.target_value}')
