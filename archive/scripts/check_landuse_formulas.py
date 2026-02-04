#!/usr/bin/env python
"""
Quick test to verify LandUse formulas exist and are visible in admin.
Run this after running: python manage.py import_landuse_formulas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable

print("=" * 80)
print("LANDUSE FORMULA CHECK")
print("=" * 80)
print()

# Check if formulas exist
landuse_formulas = Formula.objects.filter(category='landuse').order_by('key')
count = landuse_formulas.count()

if count == 0:
    print("❌ NO LANDUSE FORMULAS FOUND!")
    print()
    print("Run this command first:")
    print("  python manage.py import_landuse_formulas")
    print()
else:
    print(f"✅ Found {count} LandUse formulas in database:")
    print()
    
    for formula in landuse_formulas:
        print(f"Formula: {formula.key}")
        print(f"  Category: {formula.category}")
        print(f"  Expression: {formula.expression}")
        print(f"  Description: {formula.description}")
        print(f"  Active: {formula.is_active}")
        print(f"  Fixed: {formula.is_fixed}")
        
        # Check variables
        variables = formula.variables.all()
        print(f"  Variables ({variables.count()}):")
        for var in variables:
            print(f"    - {var.variable_name}: {var.source_type} → {var.source_key}")
        print()

print("=" * 80)
print("HOW TO VIEW IN ADMIN:")
print("=" * 80)
print()
print("1. Go to: http://localhost:8000/admin/simulator/formula/")
print("2. In the right sidebar, click 'Category' filter")
print("3. Select 'landuse'")
print("4. You should see all formulas listed above")
print()
print("If you don't see them in admin but they appear here,")
print("try clearing your browser cache or opening in incognito mode.")
print()
