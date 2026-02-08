#!/usr/bin/env python
"""Check current state of all values"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData, LandUse

print('CURRENT STATE:')
print('='*60)

# LandUse
lu21 = LandUse.objects.get(code='LU_2.1')
print(f'LU_2.1: {lu21.target_ha:,.2f} ha')

# Verbrauch
v26 = VerbrauchData.objects.get(code='2.6')
v28 = VerbrauchData.objects.get(code='2.8')
v280 = VerbrauchData.objects.get(code='2.8.0')
v29 = VerbrauchData.objects.get(code='2.9')
v290 = VerbrauchData.objects.get(code='2.9.0')

print(f'2.6 (Endenergie): {v26.ziel:,.2f} GWh')
print(f'2.8 (Waerme %): {v28.ziel:.6f}%')
print(f'2.8.0 (Waerme): {v280.ziel:,.2f} GWh')
print(f'2.9 (Strom %): {v29.ziel:.6f}%')
print(f'2.9.0 (Strom): {v290.ziel:,.2f} GWh')

# Renewable
r912 = RenewableData.objects.get(code='9.1.2')
r1042 = RenewableData.objects.get(code='10.4.2')
r1043 = RenewableData.objects.get(code='10.4.3')
r104 = RenewableData.objects.get(code='10.4')

print(f'')
print(f'9.1.2 (Solar): {r912.target_value:,.2f} GWh')
print(f'10.4.2 (Waerme Supply): {r1042.target_value:,.2f} GWh')
print(f'10.4.3 (Strom Supply): {r1043.target_value:,.2f} GWh')
print(f'10.4 (Total): {r104.target_value:,.2f} GWh')

print(f'')
print(f'GAPS:')
print(f'Heat Gap (10.4.2 - 2.8.0): {r1042.target_value - v280.ziel:,.2f} GWh')
print(f'Electricity Gap (10.4.3 - 2.9.0): {r1043.target_value - v290.ziel:,.2f} GWh')
