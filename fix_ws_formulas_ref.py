"""
Fix WS Formulas - Remove 'ref_' prefix from expressions

The formulas were using ref_ausspeich_gas_366 but the context variables
are named ausspeich_gas_366 (without ref_ prefix).

This script removes the ref_ prefix so formulas work correctly.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.models import Formula
from django.db import transaction
from django.core.cache import cache

print("=" * 70)
print("FIXING WS FORMULAS - Removing 'ref_' prefix")
print("=" * 70)

with transaction.atomic():
    # Get all WS formulas with ref_ in expression
    formulas = Formula.objects.filter(category='ws', expression__icontains='ref_', is_active=True)
    
    updated_count = 0
    for f in formulas:
        old_expr = f.expression
        # Replace ref_ prefix with nothing - the variable names in context don't have ref_
        new_expr = old_expr.replace('ref_', '')
        
        if old_expr != new_expr:
            print(f"\nFixing {f.key}:")
            print(f"  OLD: {old_expr}")
            print(f"  NEW: {new_expr}")
            
            f.expression = new_expr
            f.save()
            
            # Clear cache for this formula
            cache.delete(f'formula_{f.key}')
            updated_count += 1

print(f"\n{'=' * 70}")
print(f"✅ Updated {updated_count} formulas")
print("=" * 70)

# Now trigger a full WS recalculation
print("\n🔄 Triggering WS recalculation...")
from simulator.ws_formula_service import recalculate_all_ws_data, get_ws_formula_evaluator

# Clear evaluator cache
evaluator = get_ws_formula_evaluator()
evaluator.clear_cache()

# Recalculate
stats = recalculate_all_ws_data(num_passes=3)
print(f"✅ WS Recalculation complete: {stats['updated']} updates, {stats['errors']} errors")
