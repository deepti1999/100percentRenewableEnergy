import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Update 5.2 entry - remove decimal points
entry_52 = RenewableData.objects.get(code='5.2')
entry_52.status_value = 15998  # was 15.998
entry_52.target_value = 44571  # was 44.571
entry_52.save()
print('Updated 5.2: Status 15.998→15998, Target 44.571→44571')

# Update 5.3 entry - remove decimal points
entry_53 = RenewableData.objects.get(code='5.3')
entry_53.status_value = 4558   # was 4.558
entry_53.target_value = 12762  # was 12.762
entry_53.save()
print('Updated 5.3: Status 4.558→4558, Target 12.762→12762')

print('✅ All decimal points removed from biogas values!')
