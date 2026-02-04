#!/usr/bin/env python
"""
Cleanup Test Data - Remove TEST_EXTENSIBILITY
Run this to remove the test formula created by ULTIMATE_FINAL_TEST.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, RenewableData

print("🧹 Cleaning up test data...")

# Remove TEST_EXTENSIBILITY
deleted_formula = Formula.objects.filter(key='TEST_EXTENSIBILITY').delete()
deleted_data = RenewableData.objects.filter(code='TEST_EXTENSIBILITY').delete()

print(f"   ✓ Deleted Formula entries: {deleted_formula[0]}")
print(f"   ✓ Deleted RenewableData entries: {deleted_data[0]}")

# Also clean up any TEST_EXTENSIBILITY_FINAL or TEST_REALTIME if they exist
Formula.objects.filter(key__startswith='TEST_').delete()
RenewableData.objects.filter(code__startswith='TEST_').delete()

print("\n✅ Cleanup complete! All test formulas removed.")
print("   Your formula list is now clean.")
