#!/usr/bin/env python3
"""
Script to renumber VerbrauchData codes and update Formula references.
Uses raw SQL to avoid triggering Django signals and cascading updates.
"""
import sqlite3
import re

# Connect directly to SQLite database
db_path = '/Users/deeptimaheedharan/Desktop/anti gravity final fixes/db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*80)
print('STEP 1: Renumbering VerbrauchData codes using raw SQL')
print('='*80)

# Update VerbrauchData codes using temp codes to avoid conflicts
# Must be done in two passes: first to temp, then to final

# Pass 1: Rename to temp codes (deepest first)
temp_updates = [
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_1.1.3' WHERE code = '1.1.1.3'", '1.1.1.3 -> TEMP_1.1.3'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_1.1.2' WHERE code = '1.1.1.2'", '1.1.1.2 -> TEMP_1.1.2'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_1.1.1' WHERE code = '1.1.1.1'", '1.1.1.1 -> TEMP_1.1.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_1.1' WHERE code = '1.1.1'", '1.1.1 -> TEMP_1.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_1.0' WHERE code = '1.1'", '1.1 -> TEMP_1.0'),
]

for sql, desc in temp_updates:
    cursor.execute(sql)
    if cursor.rowcount > 0:
        print(f'  {desc}')

# Pass 2: Rename from temp to final codes
final_updates = [
    ("UPDATE simulator_verbrauchdata SET code = '1.0' WHERE code = 'TEMP_1.0'", 'TEMP_1.0 -> 1.0'),
    ("UPDATE simulator_verbrauchdata SET code = '1.1' WHERE code = 'TEMP_1.1'", 'TEMP_1.1 -> 1.1'),
    ("UPDATE simulator_verbrauchdata SET code = '1.1.1' WHERE code = 'TEMP_1.1.1'", 'TEMP_1.1.1 -> 1.1.1'),
    ("UPDATE simulator_verbrauchdata SET code = '1.1.2' WHERE code = 'TEMP_1.1.2'", 'TEMP_1.1.2 -> 1.1.2'),
    ("UPDATE simulator_verbrauchdata SET code = '1.1.3' WHERE code = 'TEMP_1.1.3'", 'TEMP_1.1.3 -> 1.1.3'),
]

for sql, desc in final_updates:
    cursor.execute(sql)
    if cursor.rowcount > 0:
        print(f'  {desc}')

conn.commit()
print('VerbrauchData codes updated!')

print()
print('='*80)
print('STEP 2: Updating Formula expressions using raw SQL')
print('='*80)

# Get all formulas
cursor.execute("SELECT id, key, expression FROM simulator_formula")
formulas = cursor.fetchall()

# Define replacements - use markers to prevent double-replacement
# Replace in a single pass with unique markers first
replacements = [
    # From most specific (longest) to least specific
    # Pattern -> Replacement
    ('Verbrauch_1_1_1_3', '###V_1_1_3###'),     # 1.1.1.3 -> 1.1.3
    ('Verbrauch_1_1_1_2', '###V_1_1_2###'),     # 1.1.1.2 -> 1.1.2
    ('Verbrauch_1_1_1_1', '###V_1_1_1###'),     # 1.1.1.1 -> 1.1.1
    ('Verbrauch_1_1_1', '###V_1_1###'),         # 1.1.1 -> 1.1 (davon Haushalte)
    ('Verbrauch_1_1', '###V_1_0###'),           # 1.1 -> 1.0 (Bedarfsniveau)
]

# Marker to final conversions
marker_to_final = {
    '###V_1_1_3###': 'Verbrauch_1_1_3',
    '###V_1_1_2###': 'Verbrauch_1_1_2',
    '###V_1_1_1###': 'Verbrauch_1_1_1',
    '###V_1_1###': 'Verbrauch_1_1',
    '###V_1_0###': 'Verbrauch_1_0',
}

updated_count = 0
for formula_id, key, expression in formulas:
    if not expression:
        continue
        
    new_expr = expression
    
    # First pass: Replace with markers (avoids double-replace)
    for old_pattern, marker in replacements:
        new_expr = new_expr.replace(old_pattern, marker)
    
    # Second pass: Replace markers with final values
    for marker, final_value in marker_to_final.items():
        new_expr = new_expr.replace(marker, final_value)
    
    # If changed, update
    if new_expr != expression:
        print(f'Key: {key}')
        print(f'  OLD: {expression}')
        print(f'  NEW: {new_expr}')
        cursor.execute("UPDATE simulator_formula SET expression = ? WHERE id = ?", (new_expr, formula_id))
        updated_count += 1

conn.commit()
print()
print(f'Updated {updated_count} formulas!')

print()
print('='*80)
print('STEP 3: Updating Formula keys')
print('='*80)

key_updates = [
    ("UPDATE simulator_formula SET key = 'V_1.1.3' WHERE key = 'V_1.1.1.3'", 'V_1.1.1.3 -> V_1.1.3'),
    ("UPDATE simulator_formula SET key = 'V_1.1.3_ziel' WHERE key = 'V_1.1.1.3_ziel'", 'V_1.1.1.3_ziel -> V_1.1.3_ziel'),
    ("UPDATE simulator_formula SET key = 'V_1.1.1' WHERE key = 'V_1.1.1.1'", 'V_1.1.1.1 -> V_1.1.1'),
    ("UPDATE simulator_formula SET key = 'V_1.1.1_ziel' WHERE key = 'V_1.1.1.1_ziel'", 'V_1.1.1.1_ziel -> V_1.1.1_ziel'),
    ("UPDATE simulator_formula SET key = 'V_1_1_3_ziel' WHERE key = 'V_1_1_1_3_ziel'", 'V_1_1_1_3_ziel -> V_1_1_3_ziel'),
]

for sql, desc in key_updates:
    cursor.execute(sql)
    if cursor.rowcount > 0:
        print(f'  {desc}')

conn.commit()

print()
print('='*80)
print('VERIFICATION - VerbrauchData codes in section 1:')
print('='*80)
cursor.execute("SELECT code, category FROM simulator_verbrauchdata WHERE code LIKE '1%' ORDER BY code")
for row in cursor.fetchall()[:12]:
    print(f'  {row[0]:12} | {row[1]}')

conn.close()
print()
print('DONE! All changes committed to database.')
print('Refresh the Verbrauch page to see the new numbering.')
