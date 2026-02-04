#!/usr/bin/env python3
"""
Import script for Biogas data from CSV file
Adds Biogas entries (5.x codes) to the RenewableData model
"""

import os
import sys
import csv
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

def import_biogas_data():
    """Import biogas data from CSV file"""
    csv_file_path = os.path.join(project_dir, 'biogas_full_hierarchy.csv')
    
    print(f"Importing Biogas data from: {csv_file_path}")
    
    # Clear existing biogas entries (codes starting with 5)
    deleted_count = RenewableData.objects.filter(code__startswith='5').count()
    RenewableData.objects.filter(code__startswith='5').delete()
    print(f"Deleted {deleted_count} existing biogas entries")
    
    imported_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                code = row['Code'].strip()
                parameter = row['Parameter'].strip()
                entry_type = row['Type'].strip()
                status = row['Status'].strip()
                target = row['Ziel'].strip()
                
                # Determine unit based on parameter description
                unit = ""
                if "MWh/ha/a" in parameter:
                    unit = "MWh/ha/a"
                elif "GWh/a" in parameter:
                    unit = "GWh/a"
                elif "%" in parameter:
                    unit = "%"
                elif "ha" in parameter:
                    unit = "ha"
                
                # Convert status and target values
                status_value = None
                target_value = None
                formula = None
                
                if status:
                    try:
                        status_value = float(status)
                    except ValueError:
                        pass
                
                if target:
                    try:
                        target_value = float(target)
                    except ValueError:
                        pass
                
                # Set formula field for calculated entries
                if entry_type.lower() == 'calculated':
                    formula = f"CALCULATED_{code}"
                
                # Create the RenewableData entry
                renewable_entry = RenewableData.objects.create(
                    code=code,
                    description=parameter,
                    status_value=status_value,
                    target_value=target_value,
                    unit=unit,
                    formula=formula,
                    category="Biogas"
                )
                
                imported_count += 1
                print(f"Imported: {code} - {parameter}")
        
        print(f"\n✅ Successfully imported {imported_count} biogas entries!")
        
        # Print summary
        print("\n📊 Summary of imported entries:")
        biogas_entries = RenewableData.objects.filter(code__startswith='5').order_by('code')
        for entry in biogas_entries:
            formula_info = f", Formula: {entry.formula}" if entry.formula else ""
            print(f"  {entry.code}: {entry.description} (Status: {entry.status_value}, Target: {entry.target_value}){formula_info}")
            
    except FileNotFoundError:
        print(f"❌ Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        print(f"❌ Error importing data: {e}")

if __name__ == "__main__":
    import_biogas_data()