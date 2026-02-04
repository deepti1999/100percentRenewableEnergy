#!/usr/bin/env python3
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, Formula

ws_366 = WSData.objects.get(tag_im_jahr=366)
print("=== WS Row 366: STROMVERBR RAUMWAERM KORR ===")
print(f"stromverbr_raumwaerm_korr = {ws_366.stromverbr_raumwaerm_korr:,.2f}")
print()
print("=== Related Row 366 Values ===")
print(f"stromverbr (Column G) = {ws_366.stromverbr:,.2f}" if ws_366.stromverbr else "stromverbr = None")
print(f"davon_raumw_korr (Column H) = {ws_366.davon_raumw_korr:,.2f}" if ws_366.davon_raumw_korr else "davon_raumw_korr = None")
