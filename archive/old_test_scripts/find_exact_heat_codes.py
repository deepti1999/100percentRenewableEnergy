import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('FINDING EXACT CODES FOR 10.4.2 - Gebäudewärme davon Wärme')
print('='*80)
print('Target: 66.958 GWh (Status)\n')

# Search for Solarthermie Gebäudewärme (8.449 GWh)
print('1. Solarthermie Gebäudewärme (target: 8.449 GWh):')
solar_items = RenewableData.objects.filter(code__startswith='3.').order_by('code')
for item in solar_items:
    s = item.status_value or 0
    t = item.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    name_lower = item.name.lower()
    if ('gebäude' in name_lower or 'gw' in name_lower) and ('wärme' in name_lower or 'endenergie' in name_lower):
        if 7 < s < 10:  # Looking for ~8.449
            print(f'   {item.code:15s} {item.name[:50]:50s} S={s:.3f} T={t:.3f} ✓')
        else:
            print(f'   {item.code:15s} {item.name[:50]:50s} S={s:.3f} T={t:.3f}')

# Heat pumps (we already know these)
print('\n2. Heat Pumps (target: 16.080 + 8.137 = 24.217 GWh):')
hp_air = RenewableData.objects.filter(code='7.1.2.3').first()
if hp_air:
    s = hp_air.status_value / 1000 if hp_air.status_value > 1000 else hp_air.status_value
    t = hp_air.target_value / 1000 if hp_air.target_value > 1000 else hp_air.target_value
    print(f'   7.1.2.3         {hp_air.name[:50]:50s} S={s:.3f} T={t:.3f}')

hp_ground = RenewableData.objects.filter(code='7.1.4.3').first()
if hp_ground:
    s = hp_ground.status_value / 1000 if hp_ground.status_value > 1000 else hp_ground.status_value
    t = hp_ground.target_value / 1000 if hp_ground.target_value > 1000 else hp_ground.target_value
    print(f'   7.1.4.3         {hp_ground.name[:50]:50s} S={s:.3f} T={t:.3f}')

# Biogas CHP heat
print('\n3. Biogas-KWK Gebäudewärme (target: 19.432 GWh):')
biogas = RenewableData.objects.filter(code='5.4.2.4').first()
if biogas:
    s = biogas.status_value / 1000 if biogas.status_value > 1000 else biogas.status_value
    t = biogas.target_value / 1000 if biogas.target_value > 1000 else biogas.target_value
    print(f'   5.4.2.4         {biogas.name[:50]:50s} S={s:.3f} T={t:.3f}')

# Biodiesel CHP heat (0.117 GWh)
print('\n4. Biodiesel-KWK Gebäudewärme (target: 0.117 GWh):')
# Search in section 6 for biodiesel heat
biodiesel_items = RenewableData.objects.filter(code__startswith='6.').order_by('code')
for item in biodiesel_items:
    s = item.status_value or 0
    t = item.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    name_lower = item.name.lower()
    if ('gebäude' in name_lower or 'gw' in name_lower) and ('wärme' in name_lower or 'endenergie' in name_lower):
        if 0.1 < s < 0.2:  # Looking for ~0.117
            print(f'   {item.code:15s} {item.name[:50]:50s} S={s:.3f} T={t:.3f} ✓')
        else:
            print(f'   {item.code:15s} {item.name[:50]:50s} S={s:.3f} T={t:.3f}')

# Geothermal
print('\n5. Tiefengeothermie Gebäudewärme (target: 1.797 GWh):')
geo = RenewableData.objects.filter(code='8.2').first()
if geo:
    s = geo.status_value / 1000 if geo.status_value > 1000 else geo.status_value
    t = geo.target_value / 1000 if geo.target_value > 1000 else geo.target_value
    print(f'   8.2             {geo.name[:50]:50s} S={s:.3f} T={t:.3f}')

# Biomass district heat (3.034 GWh)
print('\n6. Biogene Brennstoffe fest - Wärmenetze GW (target: 3.034 GWh):')
biomass_items = RenewableData.objects.filter(code__startswith='4.').order_by('code')
for item in biomass_items:
    s = item.status_value or 0
    t = item.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    name_lower = item.name.lower()
    if ('wärmenetz' in name_lower or 'netz' in name_lower) and ('gw' in name_lower or 'endenergie' in name_lower):
        if 2 < s < 5:  # Looking for ~3.034
            print(f'   {item.code:15s} {item.name[:50]:50s} S={s:.3f} T={t:.3f} ✓')
        elif s > 0.1:
            print(f'   {item.code:15s} {item.name[:50]:50s} S={s:.3f} T={t:.3f}')

# Bio waste district heat
print('\n7. Biogener Abfall - Wärmenetze GW (target: 9.913 GWh):')
print(f'   4.4.2           Wärmenetze GW (already found)          S=9.913 T=9.913')

print('\n' + '='*80)
print('SUMMARY OF CODES TO USE FOR 10.4.2:')
print('='*80)
