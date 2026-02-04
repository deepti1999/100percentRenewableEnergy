#!/usr/bin/env python3
"""Test WS balance"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.views import _balance_ws_storage_core
from simulator.models import WSData

print('=== Before Balance ===')
ws_366 = WSData.objects.get(tag_im_jahr=366)
print(f'stromverbr_raumwaerm_korr = {ws_366.stromverbr_raumwaerm_korr:,.2f}')
print(f'ladezustand_netto = {ws_366.ladezustand_netto:,.2f}')

print()
print('=== Running WS Balance ===')
result = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=20, num_passes=1)
print()
print(f'Result: is_balanced={result["is_balanced"]}, iterations={result["iterations"]}')
print(f'  final_stromverbr = {result["final_stromverbr"]:,.2f}')
print(f'  final_balance = {result["final_balance"]:,.2f}')

print()
print('=== After Balance ===')
ws_366 = WSData.objects.get(tag_im_jahr=366)
print(f'stromverbr_raumwaerm_korr = {ws_366.stromverbr_raumwaerm_korr:,.2f}')
print(f'ladezustand_netto = {ws_366.ladezustand_netto:,.2f}')
