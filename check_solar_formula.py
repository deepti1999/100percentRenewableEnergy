"""
Check Solar Formula and Calculate Required Land Use
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()
from simulator.models import RenewableData, LandUse

print('=' * 70)
print('SOLAR FORMULA REVERSE ENGINEERING')
print('=' * 70)

# 9.1.2 = 1.1.2.1.2 (Dach) + 1.2.1.2 (Frei)
print('\n9.1.2 (Total Solar) = 1.1.2.1.2 (Dach) + 1.2.1.2 (Frei)')

# DACH (Rooftop)
print('\n--- DACH (Rooftop) ---')
print('Formula: 1.1.2.1.2 = (1.1 * 1.1.2.1% * 1.1.2.1.1) / 1000')

r_11 = RenewableData.objects.filter(code='1.1').first()
r_1121 = RenewableData.objects.filter(code='1.1.2.1').first()
r_11211 = RenewableData.objects.filter(code='1.1.2.1.1').first()
r_11212 = RenewableData.objects.filter(code='1.1.2.1.2').first()

dach_ha = r_11.target_value if r_11 else 0
anteil_strom = r_1121.target_value if r_1121 else 0
energieertrag_dach = r_11211.target_value if r_11211 else 0
dach_gwh = r_11212.target_value if r_11212 else 0

print(f'  1.1 (Solare Dachflächen ha): {dach_ha:,.0f}')
print(f'  1.1.2.1 (Anteil Strom %): {anteil_strom}')
print(f'  1.1.2.1.1 (Energieertrag MWh/ha/a): {energieertrag_dach}')
print(f'  1.1.2.1.2 (Dach Result GWh): {dach_gwh:,.0f}')

# FREI (Ground-mounted)
print('\n--- FREI (Ground-mounted) ---')
print('Formula: 1.2.1.2 = (2.1 * 1.2.1.1) / 1000')

lu_21 = LandUse.objects.filter(code='2.1').first()
r_1211 = RenewableData.objects.filter(code='1.2.1.1').first()
r_1212 = RenewableData.objects.filter(code='1.2.1.2').first()

frei_ha = lu_21.ziel if lu_21 else 0
energieertrag_frei = r_1211.target_value if r_1211 else 0
frei_gwh = r_1212.target_value if r_1212 else 0

print(f'  2.1 (Solar Freiflächen ha): {frei_ha:,.0f}')
print(f'  1.2.1.1 (Energieertrag MWh/ha/a): {energieertrag_frei}')
print(f'  1.2.1.2 (Frei Result GWh): {frei_gwh:,.0f}')

# Total
print('\n--- CURRENT TOTAL ---')
r_912 = RenewableData.objects.filter(code='9.1.2').first()
current_solar = r_912.target_value if r_912 else 0
print(f'  1.1.2.1.2 (Dach): {dach_gwh:,.0f} GWh')
print(f'  1.2.1.2 (Frei): {frei_gwh:,.0f} GWh')
print(f'  9.1.2 (Total): {current_solar:,.0f} GWh')

# =============================================================================
# REVERSE ENGINEERING: Calculate Land Use for Optimal Solar
# =============================================================================
print('\n' + '=' * 70)
print('REVERSE ENGINEERING FOR OPTIMAL SOLAR')
print('=' * 70)

# Optimal Solar from Goal Seek
optimal_solar = 1_201_527  # GWh

print(f'\n   Target Solar (from Goal Seek): {optimal_solar:,.0f} GWh')
print(f'   Current Solar: {current_solar:,.0f} GWh')
print(f'   Difference: {optimal_solar - current_solar:,.0f} GWh')

# Option 1: Keep Dach fixed, adjust only Frei
print('\n--- OPTION 1: Adjust Freiflächen only (keep Dach fixed) ---')
needed_frei_gwh = optimal_solar - dach_gwh
print(f'   Current Dach: {dach_gwh:,.0f} GWh (fixed)')
print(f'   Needed Frei: {needed_frei_gwh:,.0f} GWh')

# Reverse: ha = (GWh * 1000) / Energieertrag
if energieertrag_frei > 0:
    needed_frei_ha = (needed_frei_gwh * 1000) / energieertrag_frei
    print(f'   Energieertrag: {energieertrag_frei} MWh/ha/a')
    print(f'   Required Freiflächen: {needed_frei_ha:,.0f} ha')
    print(f'   Current Freiflächen: {frei_ha:,.0f} ha')
    if frei_ha > 0:
        print(f'   Change: {needed_frei_ha - frei_ha:,.0f} ha ({((needed_frei_ha/frei_ha)-1)*100:+.1f}%)')
    else:
        print(f'   Change: {needed_frei_ha:,.0f} ha (from 0)')

# Option 2: Adjust both proportionally
print('\n--- OPTION 2: Adjust both proportionally ---')
if current_solar > 0:
    ratio = optimal_solar / current_solar
    new_dach_gwh = dach_gwh * ratio
    new_frei_gwh = frei_gwh * ratio
    
    print(f'   Scale factor: {ratio:.4f}')
    print(f'   New Dach: {new_dach_gwh:,.0f} GWh')
    print(f'   New Frei: {new_frei_gwh:,.0f} GWh')
    
    # Reverse for land use
    if anteil_strom > 0 and energieertrag_dach > 0:
        new_dach_ha = (new_dach_gwh * 1000) / ((anteil_strom / 100) * energieertrag_dach)
        print(f'   Required Dachflächen: {new_dach_ha:,.0f} ha (current: {dach_ha:,.0f})')
    
    if energieertrag_frei > 0:
        new_frei_ha = (new_frei_gwh * 1000) / energieertrag_frei
        print(f'   Required Freiflächen: {new_frei_ha:,.0f} ha (current: {frei_ha:,.0f})')

print('\n' + '=' * 70)
print('SUMMARY')
print('=' * 70)
print(f'\n   To achieve {optimal_solar:,.0f} GWh Solar:')
print(f'   Option 1: Set Freiflächen (2.1) to {needed_frei_ha:,.0f} ha')
if 'new_frei_ha' in dir():
    print(f'   Option 2: Scale proportionally to Frei={new_frei_ha:,.0f} ha, Dach={new_dach_ha:,.0f} ha')
