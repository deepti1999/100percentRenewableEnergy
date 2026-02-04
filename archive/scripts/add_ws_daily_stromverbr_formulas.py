#!/usr/bin/env python
"""
Add daily WS formulas for stromverbr_raumwaerm_korr that reference row 366.
This enables the WS Balance goal_seek to work correctly.

Formula pattern:
stromverbr_raumwaerm_korr_N = stromverbr_raumwaerm_korr_366 * (davon_raumw_korr_N / davon_raumw_korr_366)

This distributes the row 366 value proportionally across days based on daily heating demand.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula

def add_ws_daily_stromverbr_formulas():
    """Add formulas for daily stromverbr_raumwaerm_korr (rows 1-365)"""
    
    created_count = 0
    updated_count = 0
    
    print("Adding daily WS stromverbr_raumwaerm_korr formulas...")
    
    for day in range(1, 366):  # Days 1-365
        key = f'WS_STROMVERBR_RAUMWAERM_KORR_{day}'
        
        # Formula: Daily stromverbr = (row 366 stromverbr) * (daily davon / row 366 davon)
        # This ensures when row 366 changes, all daily values recalculate proportionally
        expression = f'stromverbr_raumwaerm_korr_366 * (davon_raumw_korr_{day} / davon_raumw_korr_366)'
        
        formula, created = Formula.objects.update_or_create(
            key=key,
            defaults={
                'category': 'ws',
                'expression': expression,
                'description': f'Daily stromverbr for WS day {day} - references row 366 for goal_seek',
                'is_active': True,
            }
        )
        
        if created:
            created_count += 1
            print(f'✅ Created: {key}')
        else:
            updated_count += 1
            print(f'♻️  Updated: {key}')
    
    print(f'\n✅ Done! Created: {created_count}, Updated: {updated_count}')
    print(f'Total formulas: {created_count + updated_count}')
    print('\n⚠️  Now run recalculate_ws_data() to apply these formulas!')

if __name__ == '__main__':
    add_ws_daily_stromverbr_formulas()
