#!/usr/bin/env python3
"""Update Tiefengeothermie (8.2) to close the Gebäudewärme gap exactly."""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get current gap
cursor.execute("SELECT ziel FROM simulator_verbrauchdata WHERE code = '2.10'")
demand = cursor.fetchone()[0]

cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '10.4'")
supply = cursor.fetchone()[0]

gap = demand - supply
print(f'Current Gap: {gap:.2f} GWh/a')

# Get current 8.2 value
cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '8.2'")
current_82 = cursor.fetchone()[0]
print(f'Current 8.2 (Tiefengeothermie): {current_82:.2f} GWh/a')

# Calculate new value
new_82 = current_82 + gap
print(f'New 8.2 value needed: {new_82:.2f} GWh/a')

# Update 8.2
cursor.execute("UPDATE simulator_renewabledata SET target_value = ? WHERE code = '8.2'", (new_82,))
conn.commit()
print()
print(f'✓ Updated 8.2 Tiefengeothermie from {current_82:.2f} to {new_82:.2f} GWh/a')

conn.close()
print()
print('Now run recalculation to update 10.4.2 and 10.4...')
