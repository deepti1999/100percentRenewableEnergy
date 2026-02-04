import os
import django
import math
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.ws_models import WSData
from simulator.ws_formula_template import WSFormulaTemplate
from simulator.ws_formula_service import get_ws_formula_evaluator, recalculate_all_ws_data

def verify_ws_system():
    print("=" * 60)
    print("🔍 WS FORMULA VERIFICATION SYSTEM")
    print("=" * 60)

    # 1. Check for active templates
    templates = WSFormulaTemplate.objects.filter(is_active=True).order_by('priority')
    print(f"\n[1] Checking WSFormulaTemplate: {templates.count()} active templates found.")
    
    if templates.count() == 0:
        print("❌ ERROR: No active WSFormulaTemplates found. Recalculation will not work.")
        return

    # 2. Syntax check for all formulas
    print("\n[2] Performing syntax check on all active formulas...")
    evaluator = get_ws_formula_evaluator()
    evaluator.load_ws_data()
    evaluator.calculate_sums()
    
    syntax_errors = 0
    for t in templates:
        for tag in [1, 2, 366, 367, 368]:
            formula = t.get_formula_for_row(tag)
            if formula:
                try:
                    # Simple transform and eval check (dry run)
                    python_formula = evaluator._transform_formula(formula, tag)
                    # We won't actually eval here because it needs full context, 
                    # but we can check if it transforms without error
                    pass
                except Exception as e:
                    print(f"  ❌ Syntax Error in {t.column_name} (Row {tag}): {e}")
                    syntax_errors += 1
    
    if syntax_errors == 0:
        print("  ✅ All formulas passed basic syntax transformation.")
    else:
        print(f"  ⚠️ Found {syntax_errors} syntax-related issues.")

    # 3. Run full recalculation
    print("\n[3] Running full 3-pass recalculation...")
    try:
        stats = recalculate_all_ws_data(num_passes=3)
        print(f"  ✅ Recalculation complete: {stats['updated']} updates, {stats['errors']} errors.")
    except Exception as e:
        print(f"  ❌ Recalculation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Data validation
    print("\n[4] Validating WSData for consistency...")
    rows = WSData.objects.all().order_by('tag_im_jahr')
    
    issues = []
    for row in rows:
        # Check for NaN or Inf
        for field in evaluator._get_numeric_fields():
            val = getattr(row, field)
            if val is not None:
                if math.isnan(val):
                    issues.append(f"Day {row.tag_im_jahr}: {field} is NaN")
                elif math.isinf(val):
                    issues.append(f"Day {row.tag_im_jahr}: {field} is Inf")
    
    # Check Row 366 specifics (Annual Sums)
    try:
        row_366 = WSData.objects.get(tag_im_jahr=366)
        if abs(row_366.ladezustand_netto) > 1000: # Arbitrary large value check
             print(f"  ⚠️ Warning: Row 366 ladezustand_netto is quite large: {row_366.ladezustand_netto:.2f}")
    except WSData.DoesNotExist:
        issues.append("Row 366 is missing from database!")

    if not issues:
        print("  ✅ No NaN/Inf or missing critical rows found.")
    else:
        print(f"  ❌ Found {len(issues)} data issues:")
        for issue in issues[:10]: # Show first 10
            print(f"    - {issue}")
        if len(issues) > 10:
            print(f"    ... and {len(issues) - 10} more.")

    # 5. Dependency check (Priority order)
    print("\n[5] Dependency validation...")
    # This is harder to automate perfectly without a full graph, 
    # but we can check if priority numbers are spaced out.
    priorities = [t.priority for t in templates]
    unique_priorities = sorted(list(set(priorities)))
    print(f"  Distinct priorities: {unique_priorities}")
    if len(unique_priorities) < len(templates) / 2:
        print("  ⚠️ Warning: Many templates share the same priority. Interdependent formulas might need multiple passes to converge.")

    print("\n" + "=" * 60)
    print("🏁 VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    verify_ws_system()
