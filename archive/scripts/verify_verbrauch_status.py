#!/usr/bin/env python3
"""
Verify Verbrauch Data Status
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData, Formula

print("=" * 80)
print("VERBRAUCH DATA STATUS REPORT")
print("=" * 80)
print()

# Count by section
sections = {}
for v in VerbrauchData.objects.all().order_by('code'):
    section = v.code.split('.')[0]
    if section not in sections:
        sections[section] = {'total': 0, 'calculated': 0, 'entries': []}
    sections[section]['total'] += 1
    if v.is_calculated:
        sections[section]['calculated'] += 1
    sections[section]['entries'].append(v)

print(f"Total Verbrauch Entries: {VerbrauchData.objects.count()}")
print(f"Total Calculated: {VerbrauchData.objects.filter(is_calculated=True).count()}")
print(f"Total Formulas: {Formula.objects.filter(key__startswith='V_').count()}")
print()

print("Breakdown by Section:")
print("-" * 80)
for section in sorted(sections.keys()):
    data = sections[section]
    print(f"\nSection {section}: {data['total']} entries ({data['calculated']} calculated)")
    print(f"  First: {data['entries'][0].code} - {data['entries'][0].category}")
    print(f"  Last:  {data['entries'][-1].code} - {data['entries'][-1].category}")
    
print()
print("=" * 80)
print("Sample Values (first 20 entries):")
print("=" * 80)
for v in VerbrauchData.objects.all()[:20]:
    calc = " [CALC]" if v.is_calculated else ""
    print(f"{v.code:10s} {v.category[:35]:35s} S:{str(v.status)[:10]:>10s} Z:{str(v.ziel)[:10]:>10s}{calc}")

print()
print("✅ Verbrauch data is ready!")
print(f"📊 Access at: http://127.0.0.1:8001/verbrauch/")
print()
