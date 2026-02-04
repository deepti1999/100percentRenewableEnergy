#!/usr/bin/env python3
"""
Script to renumber VerbrauchData codes for MA Luftverkehr and subsequent sections.
Uses raw SQL to avoid triggering Django signals and cascading updates.
"""
import sqlite3

# Connect directly to SQLite database
db_path = '/Users/deeptimaheedharan/Desktop/anti gravity final fixes/db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('='*80)
print('STEP 1: Renumbering VerbrauchData codes using raw SQL')
print('='*80)

# Define the complete mapping of old -> new codes
# Must be done carefully to avoid conflicts - use TEMP codes first
# Process in reverse order (highest codes first to avoid conflicts)

# Phase 1: Move existing 7.x and 8 to TEMP_9.x and TEMP_10 (to make room)
phase1 = [
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_10' WHERE code = '8'", '8 -> TEMP_10'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_9.1.4' WHERE code = '7.1.4'", '7.1.4 -> TEMP_9.1.4'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_9.1.3' WHERE code = '7.1.3'", '7.1.3 -> TEMP_9.1.3'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_9.1.2' WHERE code = '7.1.2'", '7.1.2 -> TEMP_9.1.2'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_9.1.1' WHERE code = '7.1.1'", '7.1.1 -> TEMP_9.1.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_9.1' WHERE code = '7.1'", '7.1 -> TEMP_9.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_9' WHERE code = '7'", '7 -> TEMP_9'),
]

# Phase 2: Move existing 5 and 6 to TEMP_7 and TEMP_8
phase2 = [
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_8' WHERE code = '6'", '6 -> TEMP_8'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_7' WHERE code = '5'", '5 -> TEMP_7'),
]

# Phase 3: Move 4.3.x to TEMP_6.x (Endenergieverbrauch MA gesamt section)
phase3 = [
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_6.2' WHERE code = '4.3.6'", '4.3.6 -> TEMP_6.2'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_6.1.3' WHERE code = '4.3.5'", '4.3.5 -> TEMP_6.1.3'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_6.1.2' WHERE code = '4.3.4'", '4.3.4 -> TEMP_6.1.2'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_6.1.1' WHERE code = '4.3.3'", '4.3.3 -> TEMP_6.1.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_6.1' WHERE code = '4.3.2'", '4.3.2 -> TEMP_6.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_6.0' WHERE code = '4.3.1'", '4.3.1 -> TEMP_6.0'),
]

# Phase 4: Move 4.2.x to TEMP_5.x (MA Luftverkehr section)
phase4 = [
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_5.2.2' WHERE code = '4.2.5'", '4.2.5 -> TEMP_5.2.2'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_5.2.1' WHERE code = '4.2.4'", '4.2.4 -> TEMP_5.2.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_5.2' WHERE code = '4.2.3'", '4.2.3 -> TEMP_5.2'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_5.1' WHERE code = '4.2.2'", '4.2.2 -> TEMP_5.1'),
    ("UPDATE simulator_verbrauchdata SET code = 'TEMP_5.0' WHERE code = '4.2.1'", '4.2.1 -> TEMP_5.0'),
]

# Phase 5: Finalize all TEMP codes to final codes
phase5 = [
    # Section 5 (MA Luftverkehr)
    ("UPDATE simulator_verbrauchdata SET code = '5.0' WHERE code = 'TEMP_5.0'", 'TEMP_5.0 -> 5.0'),
    ("UPDATE simulator_verbrauchdata SET code = '5.1' WHERE code = 'TEMP_5.1'", 'TEMP_5.1 -> 5.1'),
    ("UPDATE simulator_verbrauchdata SET code = '5.2' WHERE code = 'TEMP_5.2'", 'TEMP_5.2 -> 5.2'),
    ("UPDATE simulator_verbrauchdata SET code = '5.2.1' WHERE code = 'TEMP_5.2.1'", 'TEMP_5.2.1 -> 5.2.1'),
    ("UPDATE simulator_verbrauchdata SET code = '5.2.2' WHERE code = 'TEMP_5.2.2'", 'TEMP_5.2.2 -> 5.2.2'),
    # Section 6 (Endenergieverbrauch MA gesamt)
    ("UPDATE simulator_verbrauchdata SET code = '6.0' WHERE code = 'TEMP_6.0'", 'TEMP_6.0 -> 6.0'),
    ("UPDATE simulator_verbrauchdata SET code = '6.1' WHERE code = 'TEMP_6.1'", 'TEMP_6.1 -> 6.1'),
    ("UPDATE simulator_verbrauchdata SET code = '6.1.1' WHERE code = 'TEMP_6.1.1'", 'TEMP_6.1.1 -> 6.1.1'),
    ("UPDATE simulator_verbrauchdata SET code = '6.1.2' WHERE code = 'TEMP_6.1.2'", 'TEMP_6.1.2 -> 6.1.2'),
    ("UPDATE simulator_verbrauchdata SET code = '6.1.3' WHERE code = 'TEMP_6.1.3'", 'TEMP_6.1.3 -> 6.1.3'),
    ("UPDATE simulator_verbrauchdata SET code = '6.2' WHERE code = 'TEMP_6.2'", 'TEMP_6.2 -> 6.2'),
    # Section 7 (was 5 - Strom-Endverbrauch)
    ("UPDATE simulator_verbrauchdata SET code = '7' WHERE code = 'TEMP_7'", 'TEMP_7 -> 7'),
    # Section 8 (was 6 - Endenergieverbrauch)
    ("UPDATE simulator_verbrauchdata SET code = '8' WHERE code = 'TEMP_8'", 'TEMP_8 -> 8'),
    # Section 9 (was 7 - Grundstoff-Synthetisierung)
    ("UPDATE simulator_verbrauchdata SET code = '9' WHERE code = 'TEMP_9'", 'TEMP_9 -> 9'),
    ("UPDATE simulator_verbrauchdata SET code = '9.1' WHERE code = 'TEMP_9.1'", 'TEMP_9.1 -> 9.1'),
    ("UPDATE simulator_verbrauchdata SET code = '9.1.1' WHERE code = 'TEMP_9.1.1'", 'TEMP_9.1.1 -> 9.1.1'),
    ("UPDATE simulator_verbrauchdata SET code = '9.1.2' WHERE code = 'TEMP_9.1.2'", 'TEMP_9.1.2 -> 9.1.2'),
    ("UPDATE simulator_verbrauchdata SET code = '9.1.3' WHERE code = 'TEMP_9.1.3'", 'TEMP_9.1.3 -> 9.1.3'),
    ("UPDATE simulator_verbrauchdata SET code = '9.1.4' WHERE code = 'TEMP_9.1.4'", 'TEMP_9.1.4 -> 9.1.4'),
    # Section 10 (was 8 - fossil)
    ("UPDATE simulator_verbrauchdata SET code = '10' WHERE code = 'TEMP_10'", 'TEMP_10 -> 10'),
]

# Execute all phases
all_phases = [
    ("Phase 1: Moving 7.x and 8 to TEMP_9.x and TEMP_10", phase1),
    ("Phase 2: Moving 5 and 6 to TEMP_7 and TEMP_8", phase2),
    ("Phase 3: Moving 4.3.x to TEMP_6.x", phase3),
    ("Phase 4: Moving 4.2.x to TEMP_5.x", phase4),
    ("Phase 5: Finalizing all TEMP codes", phase5),
]

for phase_name, updates in all_phases:
    print(f"\n{phase_name}")
    print("-" * 40)
    for sql, desc in updates:
        cursor.execute(sql)
        if cursor.rowcount > 0:
            print(f'  {desc}')
        else:
            print(f'  {desc} (no rows)')

conn.commit()
print('\n✅ VerbrauchData codes updated!')

print('\n' + '='*80)
print('STEP 2: Updating Formula expressions using raw SQL')
print('='*80)

# Get all formulas
cursor.execute("SELECT id, key, expression FROM simulator_formula")
formulas = cursor.fetchall()

# Define replacements using markers to prevent double-replacement
# Must process from most specific (longest) to least specific
# Use unique markers to avoid replacement conflicts

replacements = [
    # Section 4.3.x -> 6.x (Endenergieverbrauch MA)
    ('Verbrauch_4_3_6', '###V_6_2###'),       # 4.3.6 -> 6.2
    ('Verbrauch_4_3_5', '###V_6_1_3###'),     # 4.3.5 -> 6.1.3
    ('Verbrauch_4_3_4', '###V_6_1_2###'),     # 4.3.4 -> 6.1.2
    ('Verbrauch_4_3_3', '###V_6_1_1###'),     # 4.3.3 -> 6.1.1
    ('Verbrauch_4_3_2', '###V_6_1###'),       # 4.3.2 -> 6.1
    ('Verbrauch_4_3_1', '###V_6_0###'),       # 4.3.1 -> 6.0
    
    # Section 4.2.x -> 5.x (MA Luftverkehr)
    ('Verbrauch_4_2_5', '###V_5_2_2###'),     # 4.2.5 -> 5.2.2
    ('Verbrauch_4_2_4', '###V_5_2_1###'),     # 4.2.4 -> 5.2.1
    ('Verbrauch_4_2_3', '###V_5_2###'),       # 4.2.3 -> 5.2
    ('Verbrauch_4_2_2', '###V_5_1###'),       # 4.2.2 -> 5.1
    ('Verbrauch_4_2_1', '###V_5_0###'),       # 4.2.1 -> 5.0
    
    # Section 5 -> 7, 6 -> 8 (shift main sections)
    ('Verbrauch_6', '###V_8###'),             # 6 -> 8
    ('Verbrauch_5', '###V_7###'),             # 5 -> 7
]

# Marker to final conversions
marker_to_final = {
    '###V_6_2###': 'Verbrauch_6_2',
    '###V_6_1_3###': 'Verbrauch_6_1_3',
    '###V_6_1_2###': 'Verbrauch_6_1_2',
    '###V_6_1_1###': 'Verbrauch_6_1_1',
    '###V_6_1###': 'Verbrauch_6_1',
    '###V_6_0###': 'Verbrauch_6_0',
    '###V_5_2_2###': 'Verbrauch_5_2_2',
    '###V_5_2_1###': 'Verbrauch_5_2_1',
    '###V_5_2###': 'Verbrauch_5_2',
    '###V_5_1###': 'Verbrauch_5_1',
    '###V_5_0###': 'Verbrauch_5_0',
    '###V_8###': 'Verbrauch_8',
    '###V_7###': 'Verbrauch_7',
}

updated_count = 0
for formula_id, key, expression in formulas:
    if not expression:
        continue
        
    new_expr = expression
    
    # First pass: Replace with markers
    for old_pattern, marker in replacements:
        new_expr = new_expr.replace(old_pattern, marker)
    
    # Second pass: Replace markers with final values
    for marker, final_value in marker_to_final.items():
        new_expr = new_expr.replace(marker, final_value)
    
    # If changed, update
    if new_expr != expression:
        print(f'Key: {key}')
        print(f'  OLD: {expression[:80]}...' if len(expression) > 80 else f'  OLD: {expression}')
        print(f'  NEW: {new_expr[:80]}...' if len(new_expr) > 80 else f'  NEW: {new_expr}')
        cursor.execute("UPDATE simulator_formula SET expression = ? WHERE id = ?", (new_expr, formula_id))
        updated_count += 1

conn.commit()
print(f'\n✅ Updated {updated_count} formulas!')

print('\n' + '='*80)
print('STEP 3: Updating Formula keys')  
print('='*80)

# Update formula keys that reference old codes
key_updates = [
    # 4.2.x -> 5.x
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.2.5', '5.2.2') WHERE key LIKE '%4.2.5%'", '4.2.5 -> 5.2.2'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.2.4', '5.2.1') WHERE key LIKE '%4.2.4%'", '4.2.4 -> 5.2.1'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.2.3', '5.2') WHERE key LIKE '%4.2.3%'", '4.2.3 -> 5.2'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.2.2', '5.1') WHERE key LIKE '%4.2.2%'", '4.2.2 -> 5.1'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.2.1', '5.0') WHERE key LIKE '%4.2.1%'", '4.2.1 -> 5.0'),
    # 4.3.x -> 6.x
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.3.6', '6.2') WHERE key LIKE '%4.3.6%'", '4.3.6 -> 6.2'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.3.5', '6.1.3') WHERE key LIKE '%4.3.5%'", '4.3.5 -> 6.1.3'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.3.4', '6.1.2') WHERE key LIKE '%4.3.4%'", '4.3.4 -> 6.1.2'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.3.3', '6.1.1') WHERE key LIKE '%4.3.3%'", '4.3.3 -> 6.1.1'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.3.2', '6.1') WHERE key LIKE '%4.3.2%'", '4.3.2 -> 6.1'),
    ("UPDATE simulator_formula SET key = REPLACE(key, '4.3.1', '6.0') WHERE key LIKE '%4.3.1%'", '4.3.1 -> 6.0'),
]

for sql, desc in key_updates:
    cursor.execute(sql)
    if cursor.rowcount > 0:
        print(f'  {desc} ({cursor.rowcount} keys)')

conn.commit()

print('\n' + '='*80)
print('VERIFICATION - VerbrauchData codes in sections 4-10:')
print('='*80)
cursor.execute("SELECT code, category FROM simulator_verbrauchdata WHERE code LIKE '4.%' OR code LIKE '5%' OR code LIKE '6%' OR code LIKE '7%' OR code LIKE '8%' OR code LIKE '9%' OR code = '10' ORDER BY code")
for row in cursor.fetchall():
    print(f'  {row[0]:12} | {row[1][:50]}')

conn.close()
print('\n' + '='*80)
print('DONE! All changes committed to database.')
print('Refresh the Verbrauch page to see the new numbering.')
print('='*80)
