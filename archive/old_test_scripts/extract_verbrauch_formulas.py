#!/usr/bin/env python3
"""
Extract all VerbrauchData formulas from models.py and create verbrauch_formulas.py
This preserves all formulas exactly as they are - just moving them to a separate file.
"""

import re

def extract_formulas():
    """Extract all formulas from calculate_value() and calculate_ziel_value()"""
    
    with open('simulator/models.py', 'r') as f:
        content = f.read()
    
    # Find the calculate_value() method
    status_match = re.search(
        r'def calculate_value\(self\):.*?(?=\n    def |\nclass |\Z)',
        content,
        re.DOTALL
    )
    
    # Find the calculate_ziel_value() method
    ziel_match = re.search(
        r'def calculate_ziel_value\(self\):.*?(?=\n    def |\nclass |\Z)',
        content,
        re.DOTALL
    )
    
    if not status_match or not ziel_match:
        print("ERROR: Could not find calculate methods")
        return
    
    status_code = status_match.group(0)
    ziel_code = ziel_match.group(0)
    
    # Extract formula comments (# CODE = FORMULA)
    status_formulas = {}
    ziel_formulas = {}
    
    # Parse status formulas
    code_blocks = re.findall(
        r'elif self\.code == "([^"]+)":\s*\n\s*# ([^\n]+)',
        status_code
    )
    
    for code, formula in code_blocks:
        status_formulas[code] = formula.strip()
    
    # Parse ziel formulas
    code_blocks = re.findall(
        r'elif self\.code == "([^"]+)":\s*\n\s*# ([^\n]+)',
        ziel_code
    )
    
    for code, formula in code_blocks:
        ziel_formulas[code] = formula.strip()
    
    print(f"Extracted {len(status_formulas)} status formulas")
    print(f"Extracted {len(ziel_formulas)} ziel formulas")
    
    # Get unique codes
    all_codes = sorted(set(list(status_formulas.keys()) + list(ziel_formulas.keys())))
    print(f"Total unique codes: {len(all_codes)}")
    
    # Create the formula file
    create_formula_file(all_codes, status_formulas, ziel_formulas)

def create_formula_file(codes, status_formulas, ziel_formulas):
    """Create verbrauch_formulas.py with all formulas"""
    
    output = '''#!/usr/bin/env python3
"""
VERBRAUCH DATA FORMULAS
========================

This file contains ALL formulas for VerbrauchData calculations.
Extracted from models.py to reduce file size and improve maintainability.

Each formula is preserved EXACTLY as it was in the original code.

DO NOT MODIFY without testing all calculations!
"""

# All formulas organized by code
VERBRAUCH_FORMULAS = {
'''
    
    for code in codes:
        status_formula = status_formulas.get(code, 'None')
        ziel_formula = ziel_formulas.get(code, 'None')
        
        output += f'''    '{code}': {{
        'status_formula': "{status_formula}",
        'ziel_formula': "{ziel_formula}",
    }},
'''
    
    output += '''}

# Total formulas: ''' + str(len(codes)) + '''

def get_formula(code, field='status'):
    """Get formula for a specific code and field"""
    if code in VERBRAUCH_FORMULAS:
        key = f'{field}_formula'
        return VERBRAUCH_FORMULAS[code].get(key)
    return None
'''
    
    with open('verbrauch_formulas.py', 'w') as f:
        f.write(output)
    
    print(f"\n✅ Created verbrauch_formulas.py with {len(codes)} formulas")

if __name__ == '__main__':
    extract_formulas()
