import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse

# Check for LandUse 2.2.2
try:
    landuse_222 = LandUse.objects.get(code='2.2.2')
    print(f'Found LandUse 2.2.2: {landuse_222.name}')
    print(f'  Status: {landuse_222.status_ha} ha')
    print(f'  Target: {landuse_222.target_ha} ha')
except LandUse.DoesNotExist:
    print('LandUse 2.2.2 not found!')
    
# Show available 2.2.x entries
print('\nAvailable 2.2.x LandUse entries:')
landuse_22x = LandUse.objects.filter(code__startswith='2.2.').order_by('code')
for lu in landuse_22x:
    print(f'  {lu.code}: {lu.name} - Status: {lu.status_ha}, Target: {lu.target_ha}')