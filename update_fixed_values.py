"""
Update 9.3.1 and 9.3.4 to fixed values in the database.

9.3.1 (Nutzungsgrad Stromspeicherung) = 405047
9.3.4 (Abregelung von Wind-/Solarstrom) = 189289
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def update_fixed_values():
    """Update 9.3.1 and 9.3.4 to their fixed values."""
    
    # Fixed values
    FIXED_VALUES = {
        '9.3.1': 405047,
        '9.3.4': 189289
    }
    
    print("=" * 60)
    print("Updating 9.3.1 and 9.3.4 to fixed values")
    print("=" * 60)
    
    for code, fixed_value in FIXED_VALUES.items():
        try:
            item = RenewableData.objects.get(code=code)
            old_value = item.target_value
            old_is_fixed = item.is_fixed
            
            # Update to fixed value and mark as fixed
            item.target_value = fixed_value
            item.is_fixed = True  # Mark as fixed so it won't be recalculated
            
            # Skip cascade and signals to prevent recalculation
            item._skip_cascade = True
            item.save()
            
            # Verify the value was saved
            item.refresh_from_db()
            
            print(f"\n✓ {code}: {item.name}")
            print(f"  Old value: {old_value:,.3f}")
            print(f"  New value: {item.target_value:,}")
            print(f"  is_fixed: {old_is_fixed} → {item.is_fixed}")
            
        except RenewableData.DoesNotExist:
            print(f"\n✗ {code}: NOT FOUND in database")
        except Exception as e:
            print(f"\n✗ {code}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("Update complete!")
    print("=" * 60)

if __name__ == '__main__':
    update_fixed_values()
