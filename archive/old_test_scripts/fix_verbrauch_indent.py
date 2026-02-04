"""Fix indentation in verbrauch_calculations.py"""

# Read the backup file
with open('simulator/models_backup_verbrauch_refactor_20251112_004629.py', 'r') as f:
    lines = f.readlines()

# Line 643 (index 643): "    def calculate_value(self):\n"
# Line 644 (index 644): "        \"\"\"\\n"
# Extract from index 644 (line 645) to 1814

calculate_value_lines = lines[644:1814]

# Find calculate_ziel_value
for i in range(1810, 1820):
    if 'def calculate_ziel_value' in lines[i]:
        print(f"Found calculate_ziel_value at line {i+1} (index {i})")
        # Extract from next line (docstring)
        calculate_ziel_value_lines = lines[i+1:3215]
        break

# Remove first 4 spaces from each line (dedent by one level)
def dedent_4spaces(lines):
    result = []
    for line in lines:
        if line.startswith('        '):  # 8 spaces -> remove 4 to get 4
            result.append(line[4:])
        elif line.startswith('    '):  # 4 spaces -> remove all 4 (empty function level)
            result.append(line[4:])
        else:
            result.append(line)  # Keep empty lines as-is
    return result

calculate_value_dedented = dedent_4spaces(calculate_value_lines)
calculate_ziel_value_dedented = dedent_4spaces(calculate_ziel_value_lines)

# Create the new file
with open('simulator/verbrauch_calculations.py', 'w') as f:
    f.write('"""\n')
    f.write('VerbrauchData Calculation Methods\n')
    f.write('===================================\n')
    f.write('\n')
    f.write('This file contains the calculate_value() and calculate_ziel_value() methods\n')
    f.write('extracted from models.py to reduce file size.\n')
    f.write('\n')
    f.write('IMPORTANT: Do not modify without testing all calculations!\n')
    f.write('"""\n')
    f.write('\n')
    
    # Write calculate_value_method
    f.write('def calculate_value_method(self):\n')
    f.writelines(calculate_value_dedented)
    f.write('\n')
    
    # Write calculate_ziel_value_method  
    f.write('def calculate_ziel_value_method(self):\n')
    f.writelines(calculate_ziel_value_dedented)

print("✅ Fixed indentation in verbrauch_calculations.py")
