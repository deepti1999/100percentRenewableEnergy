#!/usr/bin/env python3
"""
Quick fix: Import WS constants without triggering signals
"""
import os, sys, django

# Disable signal loading temporarily
os.environ['DISABLE_SIGNALS'] = '1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

# Manually set up Django with minimal imports
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/Users/deeptimaheedharan/Desktop/total new try /db.sqlite3',
        }
    },
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'simulator',
    ],
)

django.setup()

from simulator.models import Formula

print("Importing WS constants directly into database...")

WS_CONSTANTS = [
    ('WS_ETA_STROM_GAS', '0.65', 'ws_constant', 'Wirkungsgrad Strom zu Gas'),
    ('WS_ETA_GAS_STROM', '0.60', 'ws_constant', 'Wirkungsgrad Gas zu Strom'),
    ('WS_ETA_SPEICHER', '0.90', 'ws_constant', 'Wirkungsgrad Speicher'),
    ('WS_ABREGELUNG_THRESHOLD', '0.0', 'ws_constant', 'Abregelung Threshold'),
]

created = 0
for key, expr, cat, desc in WS_CONSTANTS:
    obj, created_flag = Formula.objects.update_or_create(
        key=key,
        defaults={
            'expression': expr,
            'category': cat,
            'description': desc,
            'is_active': True,
        }
    )
    if created_flag:
        created += 1
        print(f"✅ Created: {key}")
    else:
        print(f"♻️  Updated: {key}")

print(f"\n✅ Imported {created} new WS constants")

# Now check verbrauch count
from simulator.models import VerbrauchData
count = VerbrauchData.objects.count()
print(f"✅ VerbrauchData entries: {count}")
