#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import LandUse, RenewableData, VerbrauchData

print("=== ADMIN PANEL FILTERING - ONLY FIXED VALUES SHOWN ===\n")

# Check LandUse (no calculated field, so all should show)
landuse_total = LandUse.objects.count()
print(f"LandUse:")
print(f"  Total items: {landuse_total}")
print(f"  All items shown in admin (no filtering needed)")

# Check RenewableData (filter by is_fixed=True)
renewable_total = RenewableData.objects.count()
renewable_fixed = RenewableData.objects.filter(is_fixed=True).count()
renewable_calculated = RenewableData.objects.filter(is_fixed=False).count()

print(f"\nRenewableData:")
print(f"  Total items in database: {renewable_total}")
print(f"  Fixed values (shown in admin): {renewable_fixed}")
print(f"  Calculated values (hidden from admin): {renewable_calculated}")

if renewable_calculated > 0:
    print("  Calculated items (hidden):")
    for item in RenewableData.objects.filter(is_fixed=False)[:10]:  # Show first 10
        print(f"    {item.code or 'No-Code'}: {item.name[:50]}...")

# Check VerbrauchData (filter by is_calculated=False)
verbrauch_total = VerbrauchData.objects.count()
verbrauch_fixed = VerbrauchData.objects.filter(is_calculated=False).count()
verbrauch_calculated = VerbrauchData.objects.filter(is_calculated=True).count()

print(f"\nVerbrauchData:")
print(f"  Total items in database: {verbrauch_total}")
print(f"  Fixed values (shown in admin): {verbrauch_fixed}")
print(f"  Calculated values (hidden from admin): {verbrauch_calculated}")

if verbrauch_calculated > 0:
    print("  Calculated items (hidden):")
    for item in VerbrauchData.objects.filter(is_calculated=True)[:10]:  # Show first 10
        print(f"    {item.code}: {item.category[:50]}...")

print(f"\n=== SUMMARY ===")
print(f"Total items that will appear in admin panel:")
print(f"  LandUse: {landuse_total}")
print(f"  RenewableData: {renewable_fixed}")
print(f"  VerbrauchData: {verbrauch_fixed}")
print(f"  TOTAL VISIBLE: {landuse_total + renewable_fixed + verbrauch_fixed}")

print(f"\nTotal calculated items hidden from admin:")
print(f"  RenewableData: {renewable_calculated}")
print(f"  VerbrauchData: {verbrauch_calculated}")
print(f"  TOTAL HIDDEN: {renewable_calculated + verbrauch_calculated}")