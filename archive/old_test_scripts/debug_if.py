#!/usr/bin/env python3
import os
import sys
import django
import re

# Add the project directory to the Python path
sys.path.insert(0, '/Users/deeptimaheedharan/Desktop/check')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

def debug_if_formula():
    formula = "IF(Verbrauch_4.3.4 > Renewable_5.4.3.2; Verbrauch_4.3.4 - Renewable_5.4.3.2; 0)"
    print(f"Formula: {formula}")
    
    # Test the regex pattern
    code_pattern = r'\b\d+\.\d+(?:\.\d+)*\b'
    codes = re.findall(code_pattern, formula)
    print(f"Codes found by regex: {codes}")
    
    # Test condition extraction
    if_pattern = r'IF\(([^;]+);([^;]+);([^)]+)\)'
    match = re.match(if_pattern, formula)
    
    if match:
        condition_str, true_value_str, false_value_str = match.groups()
        print(f"Condition: '{condition_str}'")
        print(f"True value: '{true_value_str}'")
        print(f"False value: '{false_value_str}'")
        
        # Test condition parsing
        if ' > ' in condition_str:
            left, right = condition_str.split(' > ', 1)
            print(f"Left: '{left.strip()}'")
            print(f"Right: '{right.strip()}'")
            
            # Test the references
            left_clean = left.strip()
            right_clean = right.strip()
            
            if left_clean.startswith('Verbrauch_'):
                code = left_clean.replace('Verbrauch_', '')
                print(f"Verbrauch code: '{code}'")
                
            if right_clean.startswith('Renewable_'):
                code = right_clean.replace('Renewable_', '')
                print(f"Renewable code: '{code}'")
        
        # Test true value expression  
        print(f"\nTrue value expression: '{true_value_str.strip()}'")
        true_codes = re.findall(code_pattern, true_value_str.strip())
        print(f"Codes in true value: {true_codes}")

if __name__ == '__main__':
    debug_if_formula()