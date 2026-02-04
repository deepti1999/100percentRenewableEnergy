#!/usr/bin/env python
"""
STEP 2: Migrate Verbrauch formulas to FormulaVariable approach
This script creates FormulaVariable mappings for all 92 Verbrauch formulas
"""
import os
import sys
import django
import re

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, VerbrauchData

def migrate_verbrauch_formulas():
    """Migrate all Verbrauch formulas to use FormulaVariable mappings"""
    
    print("=" * 70)
    print("STEP 2: Migrating Verbrauch Formulas to FormulaVariable")
    print("=" * 70)
    print()
    
    # Get all verbrauch formulas
    formulas = Formula.objects.filter(category='verbrauch', is_fixed=False).order_by('key')
    total_formulas = formulas.count()
    
    print(f"Found {total_formulas} Verbrauch formulas to migrate")
    print()
    
    success_count = 0
    failed_count = 0
    failed_formulas = []
    
    for formula in formulas:
        try:
            # Skip if already has mappings
            existing_mappings = FormulaVariable.objects.filter(formula=formula).count()
            if existing_mappings > 0:
                print(f"✓ {formula.key:15} - Already has {existing_mappings} mappings (SKIP)")
                success_count += 1
                continue
            
            # Extract variable names from expression
            # Verbrauch uses: Verbrauch_1.1, Verbrauch_2.3.4 (capital V with dots)
            # Others use: renewable_10_3, landuse_2_1 (lowercase with underscores)
            verbrauch_vars = set(re.findall(r'\bVerbrauch_[\d.]+\b', formula.expression))
            landuse_vars = set(re.findall(r'\blanduse_[\d_]+\b', formula.expression))
            renewable_vars = set(re.findall(r'\brenewable_[\d_]+\b', formula.expression))
            variables = verbrauch_vars | landuse_vars | renewable_vars
            
            if not variables:
                print(f"⚠ {formula.key:15} - No variables found in: {formula.expression[:60]}")
                failed_count += 1
                failed_formulas.append((formula.key, "No variables found"))
                continue
            
            # Create FormulaVariable mapping for each variable
            mappings_created = 0
            for var in sorted(variables):
                # Determine source type and key from variable name
                # Examples:
                #   Verbrauch_1.1.1 → source_type='verbrauch_status', source_key='1.1.1'
                #   landuse_2_1 → source_type='landuse_status', source_key='2.1'
                #   renewable_10_3 → source_type='renewable_status', source_key='10.3'
                
                # Verbrauch uses capital V with dots: Verbrauch_1.1.1
                # Others use lowercase with underscores: renewable_10_3
                if var.startswith('Verbrauch_'):
                    prefix = 'verbrauch'
                    code_part = var.replace('Verbrauch_', '')  # Already has dots
                elif var.startswith('landuse_'):
                    prefix = 'landuse'
                    code_part = var.replace('landuse_', '').replace('_', '.')
                elif var.startswith('renewable_'):
                    prefix = 'renewable'
                    code_part = var.replace('renewable_', '').replace('_', '.')
                else:
                    print(f"  ⚠ Unknown variable format: {var}")
                    continue
                
                # Determine source_type based on prefix
                # For Verbrauch formulas, default to status values
                if prefix == 'verbrauch':
                    source_type = 'verbrauch_status'
                elif prefix == 'landuse':
                    source_type = 'landuse_status'
                elif prefix == 'renewable':
                    source_type = 'renewable_status'
                else:
                    print(f"  ⚠ Unknown prefix: {prefix}")
                    continue
                
                # Create the mapping
                FormulaVariable.objects.create(
                    formula=formula,
                    variable_name=var,
                    source_type=source_type,
                    source_key=code_part
                )
                mappings_created += 1
            
            print(f"✓ {formula.key:15} - Created {mappings_created} mappings")
            success_count += 1
            
        except Exception as e:
            print(f"✗ {formula.key:15} - ERROR: {str(e)}")
            failed_count += 1
            failed_formulas.append((formula.key, str(e)))
    
    # Summary
    print()
    print("=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Total formulas: {total_formulas}")
    print(f"Successful: {success_count} ({success_count/total_formulas*100:.1f}%)")
    print(f"Failed: {failed_count}")
    print()
    
    if failed_formulas:
        print("Failed formulas:")
        for key, reason in failed_formulas:
            print(f"  - {key}: {reason}")
        print()
    
    # Count total mappings created
    total_mappings = FormulaVariable.objects.filter(formula__category='verbrauch').count()
    print(f"Total FormulaVariable mappings for Verbrauch: {total_mappings}")
    print()
    print("✅ Migration complete!")
    print()

if __name__ == '__main__':
    migrate_verbrauch_formulas()
