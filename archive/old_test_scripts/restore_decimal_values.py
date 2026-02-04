import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Restore ONLY these specific biogas values to decimal format
# All other values in the system remain unchanged

# Restore 5.2 entry to decimal format
entry_52 = RenewableData.objects.get(code='5.2')
entry_52.status_value = 15.998  # restore to decimal
entry_52.target_value = 44.571  # restore to decimal
entry_52.save()
print('Restored 5.2: Status→15.998, Target→44.571')

# Restore 5.3 entry to decimal format  
entry_53 = RenewableData.objects.get(code='5.3')
entry_53.status_value = 4.558   # restore to decimal
entry_53.target_value = 12.762  # restore to decimal
entry_53.save()
print('Restored 5.3: Status→4.558, Target→12.762')

print('✅ Only specified biogas values restored to decimal format!')
print('All other system values remain unchanged.')