import csv
import os
from django.core.management.base import BaseCommand
from simulator.models import RenewableData
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load 10th hierarchy endenergie data from CSV file'

    def handle(self, *args, **options):
        csv_file_path = 'endenergieangebot.csv'
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file_path}')
            )
            return

        # Clear existing 10th hierarchy data
        RenewableData.objects.filter(code__startswith='10.').delete()
        self.stdout.write('Cleared existing 10th hierarchy data')

        created_count = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            # Skip the header row
            next(file)
            reader = csv.reader(file)
            
            for row in reader:
                if len(row) < 4:
                    continue
                    
                hierarchy_text = row[0].strip()
                status_str = row[1].strip() if row[1] else ''
                target_str = row[2].strip() if row[2] else ''
                formula_note = row[3].strip() if row[3] else ''
                
                # Skip empty rows or section headers
                if not hierarchy_text or not hierarchy_text.startswith('10.'):
                    continue
                
                # Extract code and name from hierarchy text
                if '(' in hierarchy_text and ')' in hierarchy_text:
                    # Format: "10.1 Name (Unit)"
                    parts = hierarchy_text.split(' ', 1)
                    code = parts[0]
                    name_with_unit = parts[1] if len(parts) > 1 else ''
                    
                    # Extract unit from parentheses
                    if '(' in name_with_unit and ')' in name_with_unit:
                        name = name_with_unit.split('(')[0].strip()
                        unit = name_with_unit.split('(')[1].split(')')[0].strip()
                    else:
                        name = name_with_unit
                        unit = ''
                else:
                    # Format: "10. Section Header"
                    parts = hierarchy_text.split(' ', 1)
                    code = parts[0].rstrip('.')
                    name = parts[1] if len(parts) > 1 else ''
                    unit = ''
                
                # Parse status and target values
                status_value = None
                target_value = None
                
                if status_str:
                    try:
                        # Handle German decimal format (comma as decimal separator)
                        status_str = status_str.replace(',', '.')
                        status_value = float(status_str)
                    except ValueError:
                        pass
                
                if target_str:
                    try:
                        # Handle German decimal format (comma as decimal separator)
                        target_str = target_str.replace(',', '.')
                        target_value = float(target_str)
                    except ValueError:
                        pass
                
                # Create RenewableData entry
                renewable_data = RenewableData.objects.create(
                    category='Endenergie',
                    subcategory='Erneuerbare Quellen',
                    code=code,
                    name=name,
                    description=hierarchy_text,
                    unit=unit,
                    status_value=status_value,
                    target_value=target_value,
                    formula=formula_note if formula_note else None
                )
                
                created_count += 1
                self.stdout.write(f'Created: {code} - {name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {created_count} endenergie records')
        )