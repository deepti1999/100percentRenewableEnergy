#!/usr/bin/env python3
"""Check Gebäudewärme balance from Bilanz"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from calculation_engine.bilanz_engine import calculate_bilanz_data

data = calculate_bilanz_data()

print('=== GEBÄUDEWÄRME FROM BILANZ ===')
print()
print('VERBRAUCH (Demand):')
print(f'  Status: {data["verbrauch_gesamt"]["status"]["gebaeudewaerme"]:,.2f} GWh')
print(f'  Ziel:   {data["verbrauch_gesamt"]["ziel"]["gebaeudewaerme"]:,.2f} GWh')

print()
print('ERNEUERBAR (Renewable Production):')
print(f'  Status: {data["verbrauch_heat_renewable"]["status"]["gebaeudewaerme"]:,.2f} GWh')
print(f'  Ziel:   {data["verbrauch_heat_renewable"]["ziel"]["gebaeudewaerme"]:,.2f} GWh')

print()
print('ABWÄRME (Waste Heat):')
print(f'  Status: {data["verbrauch_heat_abwaerme"]["status"]["gebaeudewaerme"]:,.2f} GWh')
print(f'  Ziel:   {data["verbrauch_heat_abwaerme"]["ziel"]["gebaeudewaerme"]:,.2f} GWh')

print()
print('FOSSIL (Residual):')
print(f'  Status: {data["verbrauch_heat_fossil"]["status"]["gebaeudewaerme"]:,.2f} GWh')
print(f'  Ziel:   {data["verbrauch_heat_fossil"]["ziel"]["gebaeudewaerme"]:,.2f} GWh')

print()
print('=' * 60)
print('BALANCE CHECK')
print('=' * 60)
for col in ['status', 'ziel']:
    demand = data['verbrauch_gesamt'][col]['gebaeudewaerme']
    renewable = data['verbrauch_heat_renewable'][col]['gebaeudewaerme']
    abwaerme = data['verbrauch_heat_abwaerme'][col]['gebaeudewaerme']
    fossil = data['verbrauch_heat_fossil'][col]['gebaeudewaerme']
    total_supply = renewable + abwaerme + fossil
    
    print(f'\n{col.upper()}:')
    print(f'  Demand:            {demand:>15,.2f} GWh')
    print(f'  Renewable:         {renewable:>15,.2f} GWh')
    print(f'  Abwärme:           {abwaerme:>15,.2f} GWh')
    print(f'  Fossil:            {fossil:>15,.2f} GWh')
    print(f'  ----------------------------------------')
    print(f'  Total Supply:      {total_supply:>15,.2f} GWh')
    print(f'  Gap (Demand-Supply): {demand - total_supply:>13,.2f} GWh')
    
    if col == 'ziel':
        coverage_pct = ((renewable + abwaerme) / demand * 100) if demand > 0 else 0
        print(f'  Renewable+Abwärme Coverage: {coverage_pct:.1f}%')
