#!/usr/bin/env python

import os
import sys
import django

# Add the project root to sys.path
project_root = '/Users/deeptimaheedharan/Desktop/check'
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def update_biogene_brennstoffe_fluessig_units():
    """Update units for all biogene brennstoffe (flüssig) entries"""
    
    print("🚀 Updating units for Biogene Brennstoffe (flüssig) entries...")
    
    # Update units for all biogene brennstoffe (flüssig) entries
    unit_mapping = {
        '6': '',  # Main category, no unit
        '6.1': '',  # Biodiesel category, no unit  
        '6.1.1': 'ha',  # Anbaufläche Ölpflanzen für Biodiesel (ha)
        '6.1.1.1': 'MWh/ha/a',  # Biodiesel – Energieertrag (MWh/ha/a)
        '6.1.1.2': 'GWh/a',  # Biodiesel aus eigenem Anbau (GWh/a)
        '6.1.2': 'GWh/a',  # Biodiesel aus Import (+) / Export (-) (GWh/a)
        '6.1.3': 'GWh/a',  # Biodiesel Gesamtaufkommen (GWh/a)
        '6.1.3.1': '%',  # davon Einsatz für mobile Anwendungen (%)
        '6.1.3.1.1': 'GWh/a',  # Biokraftstoff (flüssig) (GWh/a)
        '6.1.3.2': '%',  # davon Einsatz für Verstromung (%)
        '6.1.3.2.1': '%',  # Nutzungsgrad Blockheizkraftwerk (%)
        '6.1.3.2.2': 'GWh/a',  # Bruttostromerzeugung (GWh/a)
        '6.1.3.2.3': '%',  # Nutzungsgrad KWK-Abwärme effektiv (%)
        '6.1.3.2.4': 'GWh/a',  # Gebäudewärme (Endenergie) (GWh/a)
        '6.2': '',  # Bioethanol category, no unit
        '6.2.1': 'ha',  # Anbaufläche Energiepflanzen für Bioethanol (ha)
        '6.2.1.1': 'MWh/ha/a',  # Bioethanol – Energieertrag (brutto) (MWh/ha/a)
        '6.2.1.2': 'GWh/a',  # Bioethanol aus eigenem Anbau (GWh/a)
        '6.2.2': 'GWh/a',  # Bioethanol aus Import (+) / Export (-) (GWh/a)
        '6.2.3': 'GWh/a',  # Bioethanol gesamt – Mobile Anwendungen (GWh/a)
    }
    
    updated_count = 0
    for code, unit in unit_mapping.items():
        try:
            entry = RenewableData.objects.get(code=code)
            entry.unit = unit
            entry.save()
            print(f'✅ Updated {code}: unit = "{unit}"')
            updated_count += 1
        except RenewableData.DoesNotExist:
            print(f'❌ Entry {code} not found')
    
    print(f'\n🎉 Updated {updated_count} entries with proper units')

if __name__ == '__main__':
    update_biogene_brennstoffe_fluessig_units()