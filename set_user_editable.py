#!/usr/bin/env python3
"""
Set User Editable Flag for VerbrauchData
=========================================

This script allows you to easily set which VerbrauchData fields
should be editable by users in the frontend.

Usage:
    python set_user_editable.py <code> [true|false]
    
Examples:
    python set_user_editable.py 2.1.1 true   # Make 2.1.1 editable
    python set_user_editable.py 2.1.1 false  # Make 2.1.1 non-editable
    python set_user_editable.py list         # List all editable fields
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData


def list_editable():
    """List all fields that are currently user_editable"""
    items = VerbrauchData.objects.filter(user_editable=True).order_by('code')
    
    print("\n" + "=" * 80)
    print("USER-EDITABLE VERBRAUCH FIELDS")
    print("=" * 80)
    print(f"{'Code':<10} {'Unit':<15} {'Category':<50}")
    print("-" * 80)
    
    for item in items:
        category = item.category[:47] + "..." if len(item.category) > 50 else item.category
        print(f"{item.code:<10} {item.unit:<15} {category:<50}")
    
    print("-" * 80)
    print(f"Total: {items.count()} editable fields")
    print("=" * 80)


def set_editable(code, value):
    """Set user_editable flag for a specific code"""
    try:
        item = VerbrauchData.objects.get(code=code)
        old_value = item.user_editable
        item.user_editable = value
        item.save()
        
        status = "✅ ENABLED" if value else "❌ DISABLED"
        print(f"\n{status} user editing for {code}")
        print(f"   Code: {code}")
        print(f"   Category: {item.category}")
        print(f"   Unit: {item.unit}")
        print(f"   Previous: {'Editable' if old_value else 'Not editable'}")
        print(f"   Current:  {'Editable' if value else 'Not editable'}")
        print(f"\n✓ Users can {'now' if value else 'no longer'} edit this field in the frontend.")
        
    except VerbrauchData.DoesNotExist:
        print(f"\n❌ ERROR: Code '{code}' not found in VerbrauchData")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_editable()
    elif len(sys.argv) == 3:
        code = sys.argv[1]
        value_str = sys.argv[2].lower()
        
        if value_str not in ['true', 'false', '1', '0', 'yes', 'no']:
            print(f"❌ ERROR: Value must be 'true' or 'false', got '{value_str}'")
            sys.exit(1)
        
        value = value_str in ['true', '1', 'yes']
        set_editable(code, value)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
