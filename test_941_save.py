#!/usr/bin/env python3
"""Test that 9.4.1 ziel is saved to database after balance."""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.models import RenewableData
from simulator.ws_365_service import apply_balanced_landuse

# Check 9.4.1 before
r941_before = RenewableData.objects.get(code='9.4.1')
print(f"BEFORE: 9.4.1 target_value = {r941_before.target_value:,.2f}")

# Run balance
print("\n" + "="*50)
result = apply_balanced_landuse()
print("="*50 + "\n")

# Check 9.4.1 after
r941_after = RenewableData.objects.get(code='9.4.1')
print(f"AFTER: 9.4.1 target_value = {r941_after.target_value:,.2f}")
print(f"Annual electricity from result: {result['annual_electricity']:,.2f}")
print(f"\n✅ 9.4.1 ziel saved to database: {r941_after.target_value == result['annual_electricity']}")
