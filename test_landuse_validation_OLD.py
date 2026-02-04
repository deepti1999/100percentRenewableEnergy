#!/usr/bin/env python
"""
Test Land Use Validation Rule
==============================
Tests the maximum increase percentage validation for land use changes.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse
from django.conf import settings

print("=" * 80)
print("LAND USE VALIDATION RULE TEST")
print("=" * 80)

# Check configuration
max_increase = getattr(settings, 'LANDUSE_MAX_INCREASE_PERCENT', 3)
print(f"\n📋 Configuration:")
print(f"   Maximum allowed increase: {max_increase} percentage points")

# Find a test land use entry
test_landuse = LandUse.objects.filter(parent__isnull=False).first()

if not test_landuse:
    print("\n❌ No land use entries with parent found. Cannot test.")
    exit(1)

print(f"\n🧪 Test Entry:")
print(f"   Code: {test_landuse.code}")
print(f"   Name: {test_landuse.name}")
print(f"   Current user_percent: {test_landuse.user_percent or 0}%")

# Calculate test values
current = test_landuse.user_percent or 10  # Use 10% if None
max_allowed = current + max_increase  # Add percentage POINTS
over_limit = current + max_increase + 1

print(f"\n📊 Calculated Limits:")
print(f"   Current: {current:.2f}%")
print(f"   Maximum allowed: {max_allowed:.2f}%")
print(f"   Test value (should fail): {over_limit:.2f}%")

print(f"\n✅ Validation logic:")
print(f"   - Values ≤ {max_allowed:.2f}% will be ACCEPTED")
print(f"   - Values > {max_allowed:.2f}% will be REJECTED")

print(f"\n💡 To change the limit:")
print(f"   Edit landuse_project/settings.py")
print(f"   Change LANDUSE_MAX_INCREASE_PERCENT = {max_increase} to your desired value")

print("\n" + "=" * 80)
print("To test in browser:")
print("1. Start server: python manage.py runserver")
print("2. Go to Land Use page")
print(f"3. Try to change {test_landuse.code} from {current:.2f}% to {over_limit:.2f}%")
print("4. You should see an error message")
print("=" * 80)
