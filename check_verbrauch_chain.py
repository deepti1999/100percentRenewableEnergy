#!/usr/bin/env python
"""
Check Verbrauch formulas and dependencies
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

# Check 2.6 formula
v26 = VerbrauchData.objects.get(code='2.6')
v27 = VerbrauchData.objects.get(code='2.7')
v270 = VerbrauchData.objects.filter(code='2.7.0').first()
v28 = VerbrauchData.objects.get(code='2.8')
v280 = VerbrauchData.objects.get(code='2.8.0')
v29 = VerbrauchData.objects.get(code='2.9')
v290 = VerbrauchData.objects.get(code='2.9.0')
v210 = VerbrauchData.objects.filter(code='2.10').first()

print('VERBRAUCH CALCULATION CHAIN:')
print('='*60)
print(f'2.6 (Endenergie):    Ziel = {v26.ziel}')
print(f'2.7 (Brennstoffe %): Ziel = {v27.ziel}')
if v270: print(f'2.7.0 (Brennstoffe): Ziel = {v270.ziel}')
print(f'2.8 (Waerme %):      Ziel = {v28.ziel}')
print(f'2.8.0 (Waerme):      Ziel = {v280.ziel}')
print(f'2.9 (Strom %):       Ziel = {v29.ziel}')
print(f'2.9.0 (Strom):       Ziel = {v290.ziel}')
if v210: print(f'2.10 (Total):        Ziel = {v210.ziel}')

# Verify the percentages add up
total_pct = float(v27.ziel or 0) + float(v28.ziel or 0) + float(v29.ziel or 0)
print(f'\nPercentages: 2.7 + 2.8 + 2.9 = {v27.ziel} + {v28.ziel} + {v29.ziel} = {total_pct}%')

# Verify the values add up
if v270:
    total_val = float(v270.ziel or 0) + float(v280.ziel or 0) + float(v290.ziel or 0)
    print(f'Values: 2.7.0 + 2.8.0 + 2.9.0 = {v270.ziel} + {v280.ziel} + {v290.ziel} = {total_val}')
    print(f'2.6 = {v26.ziel}')

# Check the formula for 2.8.0
print('\n' + '='*60)
print('KEY FORMULA: 2.8.0 = 2.6 x 2.8% / 100')
print('='*60)
calculated_280 = float(v26.ziel) * float(v28.ziel) / 100
print(f'2.6 x 2.8% / 100 = {v26.ziel} x {v28.ziel} / 100 = {calculated_280:.2f}')
print(f'Actual 2.8.0 = {v280.ziel}')
