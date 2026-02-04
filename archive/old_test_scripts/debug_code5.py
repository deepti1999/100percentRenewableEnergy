import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()
from simulator.models import VerbrauchData, RenewableData

print("Searching for code with value ~2089000")
for v in VerbrauchData.objects.all():
    eff_status = v.get_effective_value()
    if eff_status and 2088000 < eff_status < 2090000:
        print(f'VerbrauchData code {v.code}: status={eff_status}, ziel={v.get_effective_ziel_value()}')

for r in RenewableData.objects.all():
    s, t = r.get_calculated_values()
    if s and 2088000 < s < 2090000:
        print(f'RenewableData code {r.code}: status={s}, target={t}')
