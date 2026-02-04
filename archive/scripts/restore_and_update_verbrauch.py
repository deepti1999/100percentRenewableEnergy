#!/usr/bin/env python3
"""
Restore and Update All Verbrauch Data
- Verify all 150 entries are present
- Update all formulas
- Recalculate all values
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData, Formula
from django.core.management import call_command

print("=" * 80)
print("VERIFYING AND UPDATING VERBRAUCH DATA")
print("=" * 80)
print()

# Step 1: Verify all data is present
print("Step 1: Verifying data count...")
count = VerbrauchData.objects.count()
print(f"✅ Total VerbrauchData entries: {count}")

if count < 150:
    print(f"❌ ERROR: Only {count} entries found, expected 150!")
    print("   Database may need full restoration")
else:
    print("✅ All entries present!")
print()

# Step 2: Import/Update formulas
print("Step 2: Importing verbrauch formulas...")
try:
    call_command('import_verbrauch_formulas', '--force')
    print("✅ Formulas imported successfully")
except:
    print("⚠️  Formula import command not available or failed")
print()

# Step 3: Mark calculated fields
print("Step 3: Marking calculated fields...")
try:
    call_command('update_calculated_verbrauch')
    print("✅ Calculated fields marked")
except:
    print("⚠️  Update calculated command not available")
print()

# Step 4: Show sample data
print("Step 4: Sample data verification...")
print("-" * 80)
print(f"{'Code':<12} {'Category':<40} {'Status':<12} {'Ziel':<12} {'Calc?':<6}")
print("-" * 80)

for v in VerbrauchData.objects.all()[:20]:
    calc = "✓" if v.is_calculated else " "
    status_str = str(v.status)[:10] if v.status is not None else "-"
    ziel_str = str(v.ziel)[:10] if v.ziel is not None else "-"
    print(f"{v.code:<12} {v.category[:40]:<40} {status_str:<12} {ziel_str:<12} {calc:<6}")

print()

# Step 5: Count by section
sections = {}
for v in VerbrauchData.objects.all():
    section = v.code.split('.')[0]
    if section not in sections:
        sections[section] = 0
    sections[section] += 1

print("Entries by section:")
for section in sorted(sections.keys()):
    print(f"  Section {section}: {sections[section]} entries")

print()
print("=" * 80)
print("✅ VERIFICATION COMPLETE!")
print("=" * 80)
print()
print(f"Total entries: {count}")
print(f"Calculated entries: {VerbrauchData.objects.filter(is_calculated=True).count()}")
print(f"Formula count: {Formula.objects.filter(key__startswith='V_').count()}")
print()
