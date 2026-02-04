import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from simulator.models import VerbrauchData


class Command(BaseCommand):
    help = 'Load Verbrauch data from KLIK_Hierarchy_BlankForCalculated.csv'

    def handle(self, *args, **options):
        # Clear existing data
        VerbrauchData.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing VerbrauchData'))
        
        # Path to CSV file
        csv_file = os.path.join(settings.BASE_DIR, 'KLIK_Hierarchy_BlankForCalculated.csv')
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return
        
        # Load data from CSV
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            created_count = 0
            
            for row in reader:
                # Clean the data
                code = row['Code'].strip()
                category = row['Category'].strip().replace('"', '')  # Remove quotes
                unit = row['Unit'].strip()
                
                # Convert numeric fields
                status = None
                if row['Status'].strip():
                    try:
                        status = float(row['Status'].strip())
                    except ValueError:
                        pass
                
                ziel = None
                if row['Ziel'].strip():
                    try:
                        ziel = float(row['Ziel'].strip())
                    except ValueError:
                        pass
                
                # Create VerbrauchData object
                verbrauch_data = VerbrauchData.objects.create(
                    code=code,
                    category=category,
                    unit=unit,
                    status=status,
                    ziel=ziel
                )
                
                created_count += 1
                self.stdout.write(f'Created: {code} - {category}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {created_count} Verbrauch records')
        )