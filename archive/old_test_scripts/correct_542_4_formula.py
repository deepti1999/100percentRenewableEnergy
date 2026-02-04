import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Correct the formula for 5.4.2.4
entry = RenewableData.objects.get(code='5.4.2.4')
entry.formula = '5.4 * 5.4.2 / 100 * 5.4.2.3 / 100'
entry.save()
print('✅ Corrected 5.4.2.4 formula: 5.4 * 5.4.2% * 5.4.2.3%')