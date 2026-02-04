#!/usr/bin/env python3
"""
Test script to verify Bilanz calculations and display
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'energy_app.settings')
django.setup()

from simulator.models import VerbrauchData, RenewableData

print("=" * 80)
print("BILANZ TEST - Checking Data Availability")
print("=" * 80)

# Check if we have VerbrauchData
print("\n📊 VerbrauchData entries:")
verbrauch_count = VerbrauchData.objects.count()
print(f"Total entries: {verbrauch_count}")

if verbrauch_count > 0:
    print("\nSample entries:")
    for item in VerbrauchData.objects.all()[:10]:
        print(f"  {item.code}: {item.category} - Status: {item.status}, Ziel: {item.ziel}")
        
# Check specific codes used in bilanz_view
print("\n🔍 Checking specific codes used in Bilanz view:")
codes_to_check = ['1.4', '2.9.0', '3.6.0', '4.3.6']
for code in codes_to_check:
    try:
        item = VerbrauchData.objects.get(code=code)
        print(f"  ✓ {code}: {item.category} - Status: {item.status}, Ziel: {item.ziel}")
    except VerbrauchData.DoesNotExist:
        print(f"  ✗ {code}: NOT FOUND")

# Check RenewableData
print("\n🌱 RenewableData entries:")
renewable_count = RenewableData.objects.count()
print(f"Total entries: {renewable_count}")

if renewable_count > 0:
    print("\nChecking specific renewable codes:")
    renewable_codes = ['10.2', '10.7', '10.7.1', '10.7.2', '10.7.3', '10.4.2', '10.5.2']
    for code in renewable_codes:
        try:
            item = RenewableData.objects.get(code=code)
            print(f"  ✓ {code}: {item.name} - Status: {item.status_value}, Target: {item.target_value}")
        except RenewableData.DoesNotExist:
            print(f"  ✗ {code}: NOT FOUND")

print("\n" + "=" * 80)
print("Test complete! Check above for any missing codes (marked with ✗)")
print("=" * 80)
print("\n💡 To view the Bilanz page, visit: http://127.0.0.1:8000/simulator/bilanz/")
