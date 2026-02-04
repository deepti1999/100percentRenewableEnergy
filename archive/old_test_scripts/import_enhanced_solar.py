#!/usr/bin/env python
import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def import_enhanced_solar_data():
    """
    Import solar energy data from the enhanced CSV with Target, Fixed?, Formula, and Parent columns
    """
    # Read the CSV file
    df = pd.read_csv('solar_energy.csv')
    
    print(f"Reading {len(df)} rows from solar_energy.csv")
    print(f"Columns: {list(df.columns)}")
    
    # Clear existing solar data
    deleted_count = RenewableData.objects.filter(category='Solar').count()
    RenewableData.objects.filter(category='Solar').delete()
    print(f"Deleted {deleted_count} existing Solar records")
    
    # Process each row
    created_count = 0
    for index, row in df.iterrows():
        # Handle NaN values
        def clean_value(val):
            if pd.isna(val) or val == '' or val == 'nan':
                return None
            return val
        
        # Extract subcategory from name structure
        subcategory = None
        if 'Dachflächen' in str(row['Name']):
            subcategory = 'Dachflächen'
        elif 'Freiflächen' in str(row['Name']):
            subcategory = 'Freiflächen'
        elif 'Solarthermie' in str(row['Name']):
            subcategory = 'Solarthermie'
        elif 'Solarstrom' in str(row['Name']):
            subcategory = 'Solarstrom'
        
        # Parse Fixed? column - convert YES/NO to boolean
        is_fixed = True  # default
        fixed_str = clean_value(row.get('Fixed?'))
        if fixed_str:
            is_fixed = str(fixed_str).upper() == 'YES'
        
        # Parse target value - handle special case where target references another code
        target_val = clean_value(row.get('Target'))
        if target_val == '1.1':  # Special case where target references parent
            target_val = None
        elif target_val and isinstance(target_val, str) and '.' in target_val:
            try:
                target_val = float(target_val)
            except ValueError:
                target_val = None
        
        # Create the record
        renewable_data = RenewableData.objects.create(
            category='Solar',
            subcategory=subcategory,
            code=clean_value(row['Code']),
            name=row['Name'],
            unit=clean_value(row['Unit']) or '-',
            status_value=clean_value(row.get('Fixed Value')),
            target_value=target_val,
            formula=clean_value(row.get('Formula')),
            is_fixed=is_fixed,
            parent_code=clean_value(row.get('Parent')),
            source='solar_energy.csv'
        )
        
        created_count += 1
        print(f"Created: {renewable_data.code} - {renewable_data.name}")
    
    print(f"\nSuccessfully imported {created_count} renewable energy records")
    
    # Display summary
    print("\n=== IMPORT SUMMARY ===")
    total_records = RenewableData.objects.filter(category='Solar').count()
    fixed_records = RenewableData.objects.filter(category='Solar', is_fixed=True).count()
    calculated_records = RenewableData.objects.filter(category='Solar', is_fixed=False).count()
    records_with_targets = RenewableData.objects.filter(category='Solar', target_value__isnull=False).count()
    records_with_formulas = RenewableData.objects.filter(category='Solar', formula__isnull=False).count()
    
    print(f"Total Solar records: {total_records}")
    print(f"Fixed values: {fixed_records}")
    print(f"Calculated values: {calculated_records}")
    print(f"Records with targets: {records_with_targets}")
    print(f"Records with formulas: {records_with_formulas}")
    
    # Show sample records
    print("\n=== SAMPLE RECORDS ===")
    sample_records = RenewableData.objects.filter(category='Solar')[:5]
    for record in sample_records:
        print(f"Code: {record.code}")
        print(f"  Name: {record.name}")
        print(f"  Status: {record.status_value} | Target: {record.target_value}")
        print(f"  Fixed: {record.is_fixed} | Formula: {record.formula}")
        print(f"  Parent: {record.parent_code}")
        print()

if __name__ == '__main__':
    import_enhanced_solar_data()