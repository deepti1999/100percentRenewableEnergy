"""
Complete cascade recalculation for all dependent values.
This script properly handles the dependency chain when LandUse changes.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, Formula, FormulaVariable
from simulator.formula_service import evaluate_with_mappings
from django.db import connection
from collections import defaultdict

def build_dependency_graph():
    """
    Build a graph of formula dependencies.
    Returns: dict mapping renewable_code -> set of codes it depends on
    """
    dependencies = defaultdict(set)
    
    for fv in FormulaVariable.objects.filter(
        formula__category='renewable',
        source_type__in=['renewable_status', 'renewable_target']
    ).select_related('formula'):
        # This formula depends on source_key
        formula_code = fv.formula.key.replace('_ziel_target', '').replace('_ziel', '')
        dependencies[formula_code].add(fv.source_key)
    
    return dependencies

def topological_sort(dependencies):
    """
    Return codes in order that respects dependencies (dependents come after dependencies).
    """
    # Build reverse graph - what depends on each code
    reverse_deps = defaultdict(set)
    all_codes = set(dependencies.keys())
    
    for code, deps in dependencies.items():
        all_codes.update(deps)
        for dep in deps:
            reverse_deps[dep].add(code)
    
    # Kahn's algorithm for topological sort
    in_degree = {code: len(dependencies.get(code, set())) for code in all_codes}
    
    # Start with nodes that have no dependencies
    queue = [code for code, degree in in_degree.items() if degree == 0]
    sorted_codes = []
    
    while queue:
        code = queue.pop(0)
        sorted_codes.append(code)
        
        for dependent in reverse_deps.get(code, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # Add any codes not in the sorted list (may have cycles)
    remaining = [c for c in all_codes if c not in sorted_codes]
    sorted_codes.extend(remaining)
    
    return sorted_codes

def recalculate_all_renewable_cascade():
    """
    Recalculate all RenewableData in dependency order.
    """
    # Force fresh DB connection
    connection.close()
    connection.connect()
    
    print('=== Building dependency graph ===')
    dependencies = build_dependency_graph()
    
    print('=== Topological sorting ===')
    sorted_codes = topological_sort(dependencies)
    
    print(f'=== Recalculating {len(sorted_codes)} codes in dependency order ===')
    
    updated = 0
    errors = 0
    
    for code in sorted_codes:
        rd = RenewableData.objects.filter(code=code).first()
        if not rd:
            continue
        
        status_changed = False
        target_changed = False
        
        # Calculate status value
        try:
            status_result, _ = evaluate_with_mappings(code, 'renewable')
            if status_result is not None and status_result != rd.status_value:
                rd.status_value = status_result
                status_changed = True
        except Exception as e:
            if 'DoesNotExist' not in str(e):
                print(f'  Error calculating status for {code}: {e}')
                errors += 1
        
        # Calculate target value - try multiple key formats
        for key_format in [f'{code}_ziel_target', f'{code}_ziel']:
            try:
                _, target_result = evaluate_with_mappings(key_format, 'renewable')
                if target_result is not None and target_result != rd.target_value:
                    rd.target_value = target_result
                    target_changed = True
                break
            except Exception:
                continue
        
        if status_changed or target_changed:
            rd.save()
            updated += 1
            if status_changed:
                print(f'  {code} status -> {rd.status_value}')
            if target_changed:
                print(f'  {code} target -> {rd.target_value}')
    
    print(f'\n=== Complete: Updated {updated} entries, {errors} errors ===')
    return updated, errors

if __name__ == '__main__':
    recalculate_all_renewable_cascade()
    
    # Verify results
    print('\n=== Verification ===')
    rd_10_1 = RenewableData.objects.get(code='10.1')
    print(f'10.1: status={rd_10_1.status_value}, target={rd_10_1.target_value}')
    print(f'  Different values: {rd_10_1.status_value != rd_10_1.target_value}')
