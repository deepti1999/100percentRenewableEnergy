#!/usr/bin/env python3
"""Test balance_all API"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

import json
from django.test import Client
from simulator.models import WSData, LandUse

print('=== Before Balance All ===')
ws_366 = WSData.objects.get(tag_im_jahr=366)
lu_21 = LandUse.objects.get(code='LU_2.1')
print(f'LU_2.1 (Solar) target_ha = {lu_21.target_ha:,.2f}')
print(f'stromverbr_raumwaerm_korr = {ws_366.stromverbr_raumwaerm_korr:,.2f}')
print(f'ladezustand_netto = {ws_366.ladezustand_netto:,.2f}')

print()
print('=== Calling balance_all API ===')

# Create a test client with a logged in user
from django.contrib.auth.models import User
client = Client()
user = User.objects.filter(is_superuser=True).first()
if user:
    client.force_login(user)
    
    response = client.post('/api/balance-all/', 
        data=json.dumps({'driver': 'solar', 'tolerance': 1.0, 'ws_tolerance': 10.0}),
        content_type='application/json'
    )
    
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Response: {json.dumps(result, indent=2)}')
    
    print()
    print('=== After Balance All ===')
    ws_366 = WSData.objects.get(tag_im_jahr=366)
    lu_21 = LandUse.objects.get(code='LU_2.1')
    print(f'LU_2.1 (Solar) target_ha = {lu_21.target_ha:,.2f}')
    print(f'stromverbr_raumwaerm_korr = {ws_366.stromverbr_raumwaerm_korr:,.2f}')
    print(f'ladezustand_netto = {ws_366.ladezustand_netto:,.2f}')
else:
    print('ERROR: No superuser found')
