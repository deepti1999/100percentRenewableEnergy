#!/usr/bin/env python3
"""Balance Gebäudewärme by adjusting Tiefengeothermie (8.2) to exactly match demand."""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get demand
cursor.execute("SELECT ziel FROM simulator_verbrauchdata WHERE code = '2.10'")
demand = cursor.fetchone()[0]

# Get current 10.4 supply
cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '10.4'")
supply = cursor.fetchone()[0]

# Get current 8.2 
cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '8.2'")
current_82 = cursor.fetchone()[0]

print(f'Demand (2.10): {demand:,.2f} GWh/a')
print(f'Supply (10.4): {supply:,.2f} GWh/a')
print(f'Current Gap: {demand - supply:,.2f} GWh/a')
print(f'Current 8.2: {current_82:,.2f} GWh/a')
print()

# Adjust 8.2 to close the gap exactly
gap = demand - supply
new_82 = current_82 + gap

if gap < 0:
    print(f'GAP IS NEGATIVE (over-supplied) - reducing 8.2')
elif gap > 0:
    print(f'GAP IS POSITIVE (under-supplied) - increasing 8.2')
else:
    print('Gap is zero - perfectly balanced!')
    
print(f'New 8.2 value: {new_82:,.2f} GWh/a')

cursor.execute("UPDATE simulator_renewabledata SET target_value = ? WHERE code = '8.2'", (new_82,))
conn.commit()
print(f'✓ Updated 8.2 from {current_82:,.2f} to {new_82:,.2f} GWh/a')

conn.close()
print()
print('Now run recalculation...')
