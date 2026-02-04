import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Remove decimal points from ONLY these specific 4 biogas values
# All other values in the system keep their decimal points unchanged

# Update 5.2 entry - remove decimals from these specific numbers only
entry_52 = RenewableData.objects.get(code='5.2')
entry_52.status_value = 15998  # 15.998 → 15998 (remove decimal)
entry_52.target_value = 44571  # 44.571 → 44571 (remove decimal)
entry_52.save()
print('5.2: Removed decimals → Status=15998, Target=44571')

# Update 5.3 entry - remove decimals from these specific numbers only
entry_53 = RenewableData.objects.get(code='5.3')
entry_53.status_value = 4558   # 4.558 → 4558 (remove decimal)
entry_53.target_value = 12762  # 12.762 → 12762 (remove decimal)
entry_53.save()
print('5.3: Removed decimals → Status=4558, Target=12762')

print('✅ Decimal points removed from ONLY these 4 specific numbers!')
print('All other numbers in the system keep their decimal points unchanged.')