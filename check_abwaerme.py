#!/usr/bin/env python3
"""Check Abwärme formula values"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from simulator.models import RenewableData

# Current (wrong) codes in bilanz_engine.py
current_codes = ['4.3.4.2', '4.4.1', '5.4.2.4', '6.1.3.2.4', '9.3.2.1']
# Correct codes per user requirement
correct_codes = ['4.3.3.4', '4.4.2', '5.4.2.4', '6.1.3.2.4']

print('=== STATUS VALUES ===')
print('Current formula codes in bilanz_engine.py:')
current_total = 0
for code in current_codes:
    try:
        r = RenewableData.objects.get(code=code)
        val = r.status_value if r.status_value else 0
        print(f'  {code}: status = {val:,.2f}')
        current_total += val
    except RenewableData.DoesNotExist:
        print(f'  {code}: NOT FOUND')
print(f'Current total: {current_total:,.2f}')

print()
print('Correct formula codes (user requirement):')
print('4.3.3.4 status + 4.4.2 status + 5.4.2.4 status + 6.1.3.2.4 status')
correct_total = 0
for code in correct_codes:
    try:
        r = RenewableData.objects.get(code=code)
        val = r.status_value if r.status_value else 0
        print(f'  {code}: status = {val:,.2f}')
        correct_total += val
    except RenewableData.DoesNotExist:
        print(f'  {code}: NOT FOUND')
print(f'Correct total: {correct_total:,.2f}')

print()
print('=== TARGET (ZIEL) VALUES ===')
print('Current formula codes in bilanz_engine.py:')
current_total_t = 0
for code in current_codes:
    try:
        r = RenewableData.objects.get(code=code)
        val = r.target_value if r.target_value else 0
        print(f'  {code}: target = {val:,.2f}')
        current_total_t += val
    except RenewableData.DoesNotExist:
        print(f'  {code}: NOT FOUND')
print(f'Current total: {current_total_t:,.2f}')

print()
print('Correct formula codes (user requirement):')
correct_total_t = 0
for code in correct_codes:
    try:
        r = RenewableData.objects.get(code=code)
        val = r.target_value if r.target_value else 0
        print(f'  {code}: target = {val:,.2f}')
        correct_total_t += val
    except RenewableData.DoesNotExist:
        print(f'  {code}: NOT FOUND')
print(f'Correct total: {correct_total_t:,.2f}')

print()
print('=== SUMMARY ===')
print(f'User sees: 55,974')
print(f'Current (status): {current_total:,.2f}')
print(f'Current (target): {current_total_t:,.2f}')
print(f'Correct (status): {correct_total:,.2f}')
print(f'Correct (target): {correct_total_t:,.2f}')
