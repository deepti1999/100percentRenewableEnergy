"""
Rollback script - removes all LU_ prefixes from LandUse codes
Returns codes to original numeric format (e.g., LU_LU_2.1 → 2.1)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse, RenewableData

def rollback_landuse_codes():
    print("=" * 60)
    print("ROLLING BACK LANDUSE CODES TO ORIGINAL")
    print("=" * 60)
    
    # Step 1: Remove all LU_ prefixes from LandUse
    all_landuse = LandUse.objects.all().order_by('code')
    
    for lu in all_landuse:
        old_code = lu.code
        # Remove all LU_ prefixes
        new_code = old_code.replace('LU_', '')
        
        if new_code != old_code:
            lu.code = new_code
            lu.save(skip_cascade=True)
            print(f"✅ {old_code} → {new_code}")
    
    # Step 2: Update RenewableData formulas
    print("\nUpdating RenewableData formulas...")
    for item in RenewableData.objects.filter(formula__isnull=False):
        if item.formula and 'LandUse_LU_' in item.formula:
            old_formula = item.formula
            new_formula = old_formula.replace('LandUse_LU_', 'LandUse_')
            item.formula = new_formula
            item.save(skip_cascade=True)
            print(f"✅ {item.code}: {old_formula} → {new_formula}")
    
    print("\n✅ Rollback complete!")

if __name__ == '__main__':
    rollback_landuse_codes()
