import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def import_grundstoff_synthetisierung():
    """
    Import Grundstoff-Synthetisierung (Material Synthesis) hierarchy
    Category 7 in VerbrauchData
    
    Structure:
    7 - Grundstoff-Synthetisierung
        7.1 - Bedarfsniveau Grundstoffe (statisch) - kWh/a/Pers. - 2.337 / 2.337
            7.1.1 (*) - Zieleinfluss Kunststofferzeugung/Pers. - % - 100 / 53.0
            7.1.2 (=) - Bedarf an Grundstoffen - GWh/a - 197.841 / 104.855
            7.1.3 (*) - Anteil aus H2 synthetisierter Grundstoffe - % - 0 / 73.0
            7.1.4 (=) - Bedarf an synthetischen Grundstoffen - GWh/a - 0 / 76.545
    """
    
    data = [
        {
            'code': '7',
            'category': 'Grundstoff-Synthetisierung',
            'unit': '',
            'status': None,
            'ziel': None,
            'is_calculated': False,
            'status_calculated': False,
            'ziel_calculated': False,
        },
        {
            'code': '7.1',
            'category': 'Bedarfsniveau Grundstoffe (statisch)',
            'unit': 'kWh/a/Pers.',
            'status': 2.337,
            'ziel': 2.337,
            'is_calculated': False,
            'status_calculated': False,
            'ziel_calculated': False,
        },
        {
            'code': '7.1.1',
            'category': '* Zieleinfluss Kunststofferzeugung/Pers.',
            'unit': '%',
            'status': 100,
            'ziel': 53.0,
            'is_calculated': False,
            'status_calculated': False,
            'ziel_calculated': False,
        },
        {
            'code': '7.1.2',
            'category': '= Bedarf an Grundstoffen',
            'unit': 'GWh/a',
            'status': 197.841,
            'ziel': 104.855,
            'is_calculated': True,
            'status_calculated': True,
            'ziel_calculated': True,
        },
        {
            'code': '7.1.3',
            'category': '* Anteil aus H2 synthetisierter Grundstoffe',
            'unit': '%',
            'status': 0,
            'ziel': 73.0,
            'is_calculated': False,
            'status_calculated': False,
            'ziel_calculated': False,
        },
        {
            'code': '7.1.4',
            'category': '= Bedarf an synthetischen Grundstoffen',
            'unit': 'GWh/a',
            'status': 0,
            'ziel': 76.545,
            'is_calculated': True,
            'status_calculated': True,
            'ziel_calculated': True,
        },
    ]
    
    print("Importing Grundstoff-Synthetisierung hierarchy...")
    print("=" * 70)
    
    for item in data:
        code = item['code']
        
        # Check if already exists
        existing = VerbrauchData.objects.filter(code=code).first()
        
        if existing:
            # Update existing
            for key, value in item.items():
                setattr(existing, key, value)
            existing.save()
            print(f"✓ Updated: {code} - {item['category']}")
        else:
            # Create new
            VerbrauchData.objects.create(**item)
            print(f"✓ Created: {code} - {item['category']}")
        
        # Display values
        print(f"  Unit: {item['unit']}")
        print(f"  Status: {item['status']} | Ziel: {item['ziel']}")
        if item['is_calculated']:
            print(f"  [CALCULATED]")
        print()
    
    print("=" * 70)
    print("Import complete!")
    
    # Verify the hierarchy
    print("\nVerifying Grundstoff-Synthetisierung hierarchy:")
    print("=" * 70)
    
    records = VerbrauchData.objects.filter(code__startswith='7').order_by('code')
    for record in records:
        indent = "  " * record.get_hierarchy_level()
        calc_flag = " [CALC]" if record.is_calculated else ""
        print(f"{indent}{record.code}: {record.category}")
        print(f"{indent}  Unit: {record.unit} | Status: {record.status} | Ziel: {record.ziel}{calc_flag}")

if __name__ == '__main__':
    import_grundstoff_synthetisierung()
