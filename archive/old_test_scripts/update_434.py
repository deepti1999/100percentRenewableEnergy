#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/Users/deeptimaheedharan/Desktop/check')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def update_434():
    try:
        # Update 4.3.4 values to match webapp
        item_434 = VerbrauchData.objects.get(code='4.3.4')
        print(f'Current 4.3.4: Status={item_434.status}, Ziel={item_434.ziel}')
        
        item_434.status = 611057.0
        item_434.ziel = 91607.2
        item_434.save()
        
        print(f'Updated 4.3.4: Status={item_434.status}, Ziel={item_434.ziel}')
        print('Success!')
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    update_434()