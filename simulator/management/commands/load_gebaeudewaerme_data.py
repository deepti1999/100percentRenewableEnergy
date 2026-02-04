import csv
import os
from django.core.management.base import BaseCommand
from simulator.models import GebaeudewaermeData


class Command(BaseCommand):
    help = 'Load building heat data from Gebaudewarme_fixed_values.csv'
    
    def handle(self, *args, **options):
        # CSV file path - corrected to point to the right location
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'Gebaudewarme_fixed_values.csv')
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file_path}')
            )
            return
        
        # Clear existing data
        GebaeudewaermeData.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing GebaeudewaermeData'))
        
        # Load data from CSV
        loaded_count = 0
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Clean and prepare data
                code = row['Code'].strip()
                category = row['Category'].strip()
                unit = row['Unit'].strip()
                
                # Parse numeric values
                status = None
                if row['Status'].strip():
                    try:
                        status = float(row['Status'].strip())
                    except ValueError:
                        self.stdout.write(
                            self.style.WARNING(f'Invalid status value for {code}: {row["Status"]}')
                        )
                
                ziel = None
                if row['Ziel'].strip():
                    try:
                        ziel = float(row['Ziel'].strip())
                    except ValueError:
                        self.stdout.write(
                            self.style.WARNING(f'Invalid ziel value for {code}: {row["Ziel"]}')
                        )
                
                formula = row['Formula'].strip() if row['Formula'].strip() else None
                
                # Determine if this item should be calculated
                is_calculated = bool(formula)  # If formula exists, it's calculated
                
                # Create database entry
                GebaeudewaermeData.objects.create(
                    code=code,
                    category=category,
                    unit=unit,
                    status=status,
                    ziel=ziel,
                    formula=formula,
                    is_calculated=is_calculated
                )
                
                loaded_count += 1
                self.stdout.write(f'Loaded: {code} - {category}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {loaded_count} building heat records')
        )
        
        # Show summary
        total_count = GebaeudewaermeData.objects.count()
        calculated_count = GebaeudewaermeData.objects.filter(is_calculated=True).count()
        fixed_count = total_count - calculated_count
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Summary: {total_count} total, {fixed_count} fixed values, {calculated_count} calculated values'
            )
        )