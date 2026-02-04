import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def update_grundstoff_values():
    """
    Update Grundstoff-Synthetisierung values to English format
    7.1 = 2337, 2337 (no decimals)
    7.1.2 = 197841, 104855 (no decimals)
    """
    
    updates = [
        {'code': '7.1', 'status': 2337, 'ziel': 2337},
        {'code': '7.1.2', 'status': 197841, 'ziel': 104855},
    ]
    
    print("Updating Grundstoff-Synthetisierung values to English format...")
    print("=" * 70)
    
    for update in updates:
        code = update['code']
        item = VerbrauchData.objects.filter(code=code).first()
        
        if item:
            old_status = item.status
            old_ziel = item.ziel
            
            item.status = update['status']
            item.ziel = update['ziel']
            item.save()
            
            print(f"\n✓ Updated {code}: {item.category}")
            print(f"  Status: {old_status} → {update['status']}")
            print(f"  Ziel: {old_ziel} → {update['ziel']}")
        else:
            print(f"\n✗ Not found: {code}")
    
    print("\n" + "=" * 70)
    print("Update complete!")
    
    # Test calculations
    print("\n\nTesting calculations with new values:")
    print("=" * 70)
    
    codes = ['7.1', '7.1.1', '7.1.2', '7.1.3', '7.1.4']
    
    for code in codes:
        item = VerbrauchData.objects.filter(code=code).first()
        if item:
            print(f"\n{code}: {item.category}")
            print(f"  Unit: {item.unit}")
            
            # Status
            if item.is_calculated and item.status_calculated:
                calc_status = item.calculate_value()
                print(f"  Status: {item.status} → Calculated: {calc_status}")
            else:
                print(f"  Status: {item.status}")
            
            # Ziel
            if item.is_calculated and item.ziel_calculated:
                calc_ziel = item.calculate_ziel_value()
                print(f"  Ziel: {item.ziel} → Calculated: {calc_ziel}")
            else:
                print(f"  Ziel: {item.ziel}")

if __name__ == '__main__':
    update_grundstoff_values()
