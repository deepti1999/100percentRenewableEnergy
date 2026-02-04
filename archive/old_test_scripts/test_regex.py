#!/usr/bin/env python3
import re

def test_regex():
    formula = 'IF(Verbrauch_4.3.4 > Renewable_5.4.3.2; Verbrauch_4.3.4 - Renewable_5.4.3.2; 0)'
    print(f'Formula: {formula}')
    
    # Test new regex pattern
    code_pattern = r'(?<!Verbrauch_)(?<!Renewable_)\b\d+\.\d+(?:\.\d+)*\b'
    codes = re.findall(code_pattern, formula)
    print(f'Codes found: {codes}')
    
    # Test on true value expression
    true_expr = 'Verbrauch_4.3.4 - Renewable_5.4.3.2'
    true_codes = re.findall(code_pattern, true_expr)
    print(f'Codes in true expression: {true_codes}')
    
    # Test on a simple mathematical expression
    math_expr = '9.2.1.1.1 * 9.2.1.1.1.1 / 100'
    math_codes = re.findall(code_pattern, math_expr)
    print(f'Codes in math expression: {math_codes}')

if __name__ == '__main__':
    test_regex()