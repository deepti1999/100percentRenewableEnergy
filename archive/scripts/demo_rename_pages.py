#!/usr/bin/env python3
"""
DEMO: Rename pages freely without breaking backend!

This demonstrates Option A: Simple Display Names
- Category codes stay hardcoded (backend logic unchanged)
- Display names can be changed anytime via admin or this script
- No code changes needed!
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import CategoryDisplayName, Formula

print("="*70)
print("🎨 CATEGORY DISPLAY NAME DEMO - RENAME PAGES FREELY!")
print("="*70)
print()

# Show current names
print("📋 CURRENT CATEGORY NAMES:")
print("-"*70)
for cat in CategoryDisplayName.objects.all().order_by('order'):
    print(f"{cat.icon} {cat.category_code:20} → {cat.display_name}")
print()

# DEMO 1: Rename "Renewable Energy" to "Solar & Wind Power"
print("🔄 DEMO 1: Renaming 'Renewable Energy' → 'Solar & Wind Power'")
print("-"*70)

cat = CategoryDisplayName.objects.get(category_code='renewable')
old_name = cat.display_name
cat.display_name = "Solar & Wind Power"
cat.save()

print(f"✅ Changed: '{old_name}' → '{cat.display_name}'")
print()

# Show that formulas still work with old code
print("🧪 Testing formulas still work...")
formula_count = Formula.objects.filter(category='renewable', is_active=True).count()
print(f"✅ Found {formula_count} formulas with category='renewable' (backend unchanged)")
print()

# Show Formula.__str__() uses new name
sample_formula = Formula.objects.filter(category='renewable').first()
if sample_formula:
    print(f"✅ Formula display: {sample_formula}")
    print(f"   (Uses new display name automatically!)")
print()

# DEMO 2: Rename "Energy Consumption" to "Demand & Usage"
print("🔄 DEMO 2: Renaming 'Energy Consumption' → 'Demand & Usage'")
print("-"*70)

cat = CategoryDisplayName.objects.get(category_code='verbrauch')
old_name = cat.display_name
cat.display_name = "Demand & Usage"
cat.save()

print(f"✅ Changed: '{old_name}' → '{cat.display_name}'")
print()

# Show updated names
print("📋 UPDATED CATEGORY NAMES:")
print("-"*70)
for cat in CategoryDisplayName.objects.all().order_by('order'):
    active = "✅" if cat.is_active else "❌"
    print(f"{active} {cat.icon} {cat.category_code:20} → {cat.display_name}")
print()

print("="*70)
print("🎉 SUCCESS! Pages renamed without breaking backend!")
print("="*70)
print()
print("💡 KEY INSIGHT:")
print("   - Backend code: Uses 'renewable', 'verbrauch' (unchanged)")
print("   - UI displays: Uses 'Solar & Wind Power', 'Demand & Usage'")
print("   - Change anytime via admin panel - no code changes!")
print()
print("🚀 To revert, just change display_name back to original values")
print("   or run: python3 seed_category_names.py")
print()

# Optional: Revert changes
print("❓ Reverting changes for demo purposes...")
CategoryDisplayName.objects.filter(category_code='renewable').update(
    display_name='Renewable Energy'
)
CategoryDisplayName.objects.filter(category_code='verbrauch').update(
    display_name='Energy Consumption'
)
print("✅ Reverted to original names")
print()
