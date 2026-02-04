#!/usr/bin/env python3
"""
Seed default CategoryDisplayName values.
Run this once after migration to populate default display names.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import CategoryDisplayName

# Default category display names
CATEGORIES = [
    {
        'category_code': 'renewable',
        'display_name': 'Renewable Energy',
        'description': 'Renewable energy sources including wind, solar, biomass, etc.',
        'icon': '🌱',
        'order': 1,
    },
    {
        'category_code': 'verbrauch',
        'display_name': 'Energy Consumption',
        'description': 'Energy consumption by sector (households, industry, transport, etc.)',
        'icon': '⚡',
        'order': 2,
    },
    {
        'category_code': 'ws',
        'display_name': 'Energy Storage (WS)',
        'description': 'Daily energy storage calculations (Wärmespeicher)',
        'icon': '🔋',
        'order': 3,
    },
    {
        'category_code': 'bilanz',
        'display_name': 'Energy Balance',
        'description': 'Energy balance sheet (supply vs demand)',
        'icon': '⚖️',
        'order': 4,
    },
    {
        'category_code': 'landuse',
        'display_name': 'Land Use',
        'description': 'Land use data and calculations',
        'icon': '🗺️',
        'order': 5,
    },
    {
        'category_code': 'ws_constant',
        'display_name': 'WS Constants',
        'description': 'Constants used in WS calculations (efficiency factors, etc.)',
        'icon': '🔢',
        'order': 10,
    },
    {
        'category_code': 'bilanz_constant',
        'display_name': 'Bilanz Constants',
        'description': 'Constants used in Bilanz calculations',
        'icon': '🔢',
        'order': 11,
    },
    {
        'category_code': 'other',
        'display_name': 'Other',
        'description': 'Other formulas and calculations',
        'icon': '📊',
        'order': 99,
    },
]

print("Seeding CategoryDisplayName entries...")
print("-" * 60)

created = 0
updated = 0

for cat_data in CATEGORIES:
    obj, created_flag = CategoryDisplayName.objects.update_or_create(
        category_code=cat_data['category_code'],
        defaults={
            'display_name': cat_data['display_name'],
            'description': cat_data['description'],
            'icon': cat_data['icon'],
            'order': cat_data['order'],
            'is_active': True,
        }
    )
    
    if created_flag:
        created += 1
        print(f"✅ Created: {obj.category_code} → {obj.display_name}")
    else:
        updated += 1
        print(f"♻️  Updated: {obj.category_code} → {obj.display_name}")

print("-" * 60)
print(f"✅ Done! Created: {created}, Updated: {updated}")
print()
print("Now you can:")
print("  1. Rename categories via admin panel")
print("  2. Change 'Renewable Energy' → 'Solar & Wind Power'")
print("  3. Backend code keeps working!")
print()
