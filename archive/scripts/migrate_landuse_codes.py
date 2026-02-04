"""
Migration script to add LU_ prefix to all LandUse codes
This prevents collision with RenewableData codes in lookup tables

Before: LandUse code = "2.1"
After:  LandUse code = "LU_2.1"

This script:
1. Updates all LandUse.code values with LU_ prefix
2. Updates all formulas in RenewableData that reference LandUse codes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse, RenewableData

def migrate_landuse_codes():
    """Add LU_ prefix to all LandUse codes"""
    print("=" * 60)
    print("MIGRATING LANDUSE CODES")
    print("=" * 60)
    
    # Step 1: Collect all current LandUse codes
    landuse_mapping = {}  # old_code -> new_code
    all_landuse = LandUse.objects.all().order_by('code')
    
    print(f"\n📊 Found {all_landuse.count()} LandUse records")
    print("\nCodes to migrate:")
    for lu in all_landuse:
        old_code = lu.code
        # Only add prefix if it doesn't already have it
        if not old_code.startswith('LU_'):
            new_code = f"LU_{old_code}"
            landuse_mapping[old_code] = new_code
            print(f"  {old_code} → {new_code}")
        else:
            print(f"  {old_code} (already has prefix, skipping)")
    
    # Step 2: Update all LandUse codes
    print("\n" + "=" * 60)
    print("STEP 1: Updating LandUse codes")
    print("=" * 60)
    
    updated_count = 0
    for lu in all_landuse:
        old_code = lu.code
        new_code = landuse_mapping[old_code]
        lu.code = new_code
        lu.save(skip_cascade=True)  # Skip cascade during migration
        updated_count += 1
        print(f"✅ Updated: {old_code} → {new_code}")
    
    print(f"\n✅ Updated {updated_count} LandUse codes")
    
    # Step 3: Update RenewableData formulas that reference LandUse
    print("\n" + "=" * 60)
    print("STEP 2: Updating RenewableData formulas")
    print("=" * 60)
    
    renewable_items = RenewableData.objects.filter(formula__isnull=False)
    formula_updated_count = 0
    
    for item in renewable_items:
        if item.formula and 'LandUse_' in item.formula:
            old_formula = item.formula
            new_formula = old_formula
            
            # Replace each LandUse reference
            # Pattern: LandUse_X.X → LandUse_LU_X.X
            for old_code, new_code in landuse_mapping.items():
                old_ref = f"LandUse_{old_code}"
                new_ref = f"LandUse_{new_code}"
                new_formula = new_formula.replace(old_ref, new_ref)
            
            if new_formula != old_formula:
                item.formula = new_formula
                item.save(skip_cascade=True)
                formula_updated_count += 1
                print(f"✅ {item.code}: {old_formula} → {new_formula}")
    
    print(f"\n✅ Updated {formula_updated_count} RenewableData formulas")
    
    # Step 4: Verification
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    # Check LandUse codes
    non_prefixed = LandUse.objects.exclude(code__startswith='LU_')
    if non_prefixed.exists():
        print(f"⚠️  WARNING: {non_prefixed.count()} LandUse records without LU_ prefix:")
        for lu in non_prefixed:
            print(f"   - {lu.code}")
    else:
        print("✅ All LandUse codes have LU_ prefix")
    
    # Check for any remaining old LandUse references in formulas
    old_refs_found = []
    for item in RenewableData.objects.filter(formula__isnull=False):
        if item.formula and 'LandUse_' in item.formula:
            # Check if any old code patterns exist
            for old_code in landuse_mapping.keys():
                if f"LandUse_{old_code}" in item.formula and old_code not in ['LU_']:
                    old_refs_found.append((item.code, item.formula))
                    break
    
    if old_refs_found:
        print(f"\n⚠️  WARNING: {len(old_refs_found)} formulas still have old LandUse references:")
        for code, formula in old_refs_found:
            print(f"   - {code}: {formula}")
    else:
        print("✅ All formulas updated correctly")
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  ✅ {updated_count} LandUse codes updated")
    print(f"  ✅ {formula_updated_count} RenewableData formulas updated")
    print("\nNext steps:")
    print("  1. Test LandUse cascade updates")
    print("  2. Verify calculations work correctly")
    print("  3. Update any hardcoded LandUse references in views.py")

if __name__ == '__main__':
    migrate_landuse_codes()
