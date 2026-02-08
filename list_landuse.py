#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()
from simulator.models import LandUse
for lu in LandUse.objects.all()[:20]:
    print(f'{lu.code}: {lu.target_ha}')
