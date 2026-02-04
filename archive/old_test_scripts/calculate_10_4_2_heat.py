"""
Calculate 10.4.2 - Gebäudewärme davon Wärme (Building Heat from Renewable Sources)

STATUS (66.958 GWh):
- Solarthermie Gebäudewärme: 8.449
- WP-Luft Wärmgewinn: 16.080
- WP-Erd/Wasser Wärmgewinn: 8.137
- Biogas-KWK Gebäudewärme: 19.432
- Biodiesel-KWK Gebäudewärme: 0.117
- Tiefengeothermie Gebäudewärme: 1.797
- Biogene Brennstoffe fest - Wärmenetze GW: 3.034
- Biogener Abfall - Wärmenetze GW: 9.913

ZIEL (527.536 GWh):
- Solarthermie Gebäudewärme: 11.515
- WP-Luft Wärmgewinn: 401.438
- WP-Erd/Wasser Wärmgewinn: 41.229
- Biogas-KWK Gebäudewärme: 0
- Biodiesel-KWK Gebäudewärme: 0
- Tiefengeothermie Gebäudewärme: 12.000
- Biogene Brennstoffe fest - Wärmenetze GW: 0
- Biogener Abfall - Wärmenetze GW: 9.913
- Langzeitspeicher KWK-Abwärme: 51.441
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('='*80)
print('CALCULATING 10.4.2 - Gebäudewärme davon Wärme')
print('='*80)

# Need to find the correct codes by searching
heat_components = {}

print('\nSearching for codes...\n')

# 1. Solarthermie Gebäudewärme (Status: 8.449, Ziel: 11.515)
print('1. Solarthermie Gebäudewärme:')
solar = RenewableData.objects.filter(code='1.1.1.1.2').first()
if solar:
    # Use get_calculated_values() since this has a formula
    if not solar.is_fixed and solar.formula:
        s, t = solar.get_calculated_values()
        # Convert MWh to GWh
        if s and s > 1000:
            s = s / 1000
        else:
            s = s or 0
        if t and t > 1000:
            t = t / 1000
        else:
            t = t or 0
    else:
        s = solar.status_value or 0
        t = solar.target_value or 0
        if s > 1000:
            s = s / 1000
        if t > 1000:
            t = t / 1000
    print(f'   1.1.1.1.2       {solar.name[:50]:50s} S={s:.3f} T={t:.3f}')
    heat_components['solar'] = ('1.1.1.1.2', s, t)
    if s < 1:
        print(f'   ⚠ Calculated from formula: {solar.formula}')

# 2. Heat Pumps (Status: 16.080 + 8.137, Ziel: 401.438 + 41.229)
print('\n2. Heat Pumps - Wärmgewinn (renewable heat extraction):')
hp_air = RenewableData.objects.filter(code='7.1.2.3').first()
if hp_air:
    s = hp_air.status_value or 0
    t = hp_air.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    print(f'   7.1.2.3         {hp_air.name[:50]:50s} S={s:.3f} T={t:.3f}')
    heat_components['hp_air'] = ('7.1.2.3', s, t)

hp_ground = RenewableData.objects.filter(code='7.1.4.3').first()
if hp_ground:
    s = hp_ground.status_value or 0
    t = hp_ground.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    print(f'   7.1.4.3         {hp_ground.name[:50]:50s} S={s:.3f} T={t:.3f}')
    heat_components['hp_ground'] = ('7.1.4.3', s, t)

# 3. Biogas CHP heat (Status: 19.432, Ziel: 0)
print('\n3. Biogas-KWK Gebäudewärme:')
biogas = RenewableData.objects.filter(code='5.4.2.4').first()
if biogas:
    s = biogas.status_value or 0
    t = biogas.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    print(f'   5.4.2.4         {biogas.name[:50]:50s} S={s:.3f} T={t:.3f}')
    heat_components['biogas'] = ('5.4.2.4', s, t)

# 4. Biodiesel CHP heat (Status: 0.117, Ziel: 0)
print('\n4. Biodiesel-KWK Gebäudewärme:')
biodiesel = RenewableData.objects.filter(code='6.1.3.2.4').first()
if biodiesel:
    s = biodiesel.status_value or 0  # Already in MWh
    t = biodiesel.target_value or 0
    # Biodiesel is stored in MWh not GWh
    if s < 1000:
        s_gwh = s / 1000  # Convert MWh to GWh
    else:
        s_gwh = s / 1000
    if t < 1000:
        t_gwh = t / 1000
    else:
        t_gwh = t / 1000
    print(f'   6.1.3.2.4       {biodiesel.name[:50]:50s} S={s_gwh:.3f} T={t_gwh:.3f}')
    heat_components['biodiesel'] = ('6.1.3.2.4', s_gwh, t_gwh)
    print(f'   (Raw DB value: {s:.1f} MWh = {s_gwh:.3f} GWh, Excel: 0.117 GWh)')

# 5. Geothermal (Status: 1.797, Ziel: 12.000)
print('\n5. Tiefengeothermie Gebäudewärme:')
geo = RenewableData.objects.filter(code='8.2').first()
if geo:
    s = geo.status_value or 0
    t = geo.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    print(f'   8.2             {geo.name[:50]:50s} S={s:.3f} T={t:.3f}')
    heat_components['geo'] = ('8.2', s, t)

# 6. Biomass district heat (Status: 3.034, Ziel: 0)
print('\n6. Biogene Brennstoffe fest - Wärmenetze GW:')
# Need to find 3.034 - could be 4.3.4.2 or calculated field
# For now, skip this as DB shows 0
print('   ⚠ Excel shows 3.034 GWh but DB shows 0 in 4.3.4.2 and 4.3.3.4')
print('   This value might be calculated or missing from import')

# 7. Bio waste district heat (Status: 9.913, Ziel: 9.913)
print('\n7. Biogener Abfall - Wärmenetze GW:')
bio_waste = RenewableData.objects.filter(code='4.4.2').first()
if bio_waste:
    s = bio_waste.status_value or 0
    t = bio_waste.target_value or 0
    if s > 1000:
        s = s / 1000
    if t > 1000:
        t = t / 1000
    print(f'   4.4.2           {bio_waste.name[:50]:50s} S={s:.3f} T={t:.3f}')
    heat_components['bio_waste'] = ('4.4.2', s, t)

# 8. Langzeitspeicher KWK (Ziel only: 51.441)
print('\n8. Langzeitspeicher KWK-Abwärme (only in Ziel):')
storage_codes = ['9.3.2.1', '9.4.2.1']
for code in storage_codes:
    item = RenewableData.objects.filter(code=code).first()
    if item:
        s = item.status_value or 0
        t = item.target_value or 0
        if s > 1000:
            s = s / 1000
        if t > 1000:
            t = t / 1000
        print(f'   {code:15s} {item.name[:50]:50s} S={s:.3f} T={t:.3f}')
        if 50 < t < 55:
            heat_components['storage'] = (code, s, t)
            print('   ✓ FOUND!')

# Calculate totals
print('\n' + '='*80)
print('SUMMARY:')
print('='*80)

total_status = 0
total_ziel = 0

for name, (code, s, t) in heat_components.items():
    print(f'{name:20s} {code:15s} S={s:8.3f} T={t:8.3f}')
    total_status += s
    total_ziel += t

print('='*80)
print(f'TOTAL 10.4.2:                        S={total_status:8.3f} T={total_ziel:8.3f}')
print(f'Expected from Excel:                 S=  66.958 T= 527.536')
print(f'Difference:                          S={66.958 - total_status:8.3f} T={527.536 - total_ziel:8.3f}')

# Save to database
print('\n' + '='*80)
if abs(total_ziel - 527.536) < 1:
    print('✓ TARGET VALUE MATCHES!')
    item_10_4_2 = RenewableData.objects.filter(code='10.4.2').first()
    if item_10_4_2:
        # Save with current values (Status incomplete due to missing data)
        item_10_4_2.status_value = total_status * 1000  # Convert to MWh
        item_10_4_2.target_value = total_ziel * 1000
        item_10_4_2.save()
        print(f'✓ Saved 10.4.2 to database: S={total_status:.3f} GWh, T={total_ziel:.3f} GWh')
        print('\n⚠ NOTE: Status value is incomplete due to missing database values:')
        print('  - 1.1.1.1.2 Solar thermal Status is None (should be 8.449 GWh)')
        print('  - 4.3.4.2 Biomass district heat is 0 (should be 3.034 GWh)')
        print(f'  - Total missing: ~{66.958 - total_status:.3f} GWh')
    else:
        print('\n✗ Code 10.4.2 not found in database')
else:
    print('\n✗ Target value does not match expected - NOT saving to database')
    print('   Need to find missing codes!')

print('\n' + '='*80)
print('FORMULA FOR 10.4.2 - Gebäudewärme davon Wärme:')
print('='*80)
print('10.4.2 = 1.1.1.1.2 (solar thermal)')
print('       + 7.1.2.3 (heat pump air)')
print('       + 7.1.4.3 (heat pump ground)')
print('       + 5.4.2.4 (biogas CHP heat)')
print('       + 6.1.3.2.4 (biodiesel CHP heat)')
print('       + 8.2 (geothermal)')
print('       + [4.3.4.2 or 4.3.3.4] (biomass district heat) - MISSING DATA')
print('       + 4.4.2 (bio waste district heat)')
print('       + 9.3.2.1 (seasonal storage CHP heat - Target only)')
