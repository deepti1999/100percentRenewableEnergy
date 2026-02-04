from django.core.management.base import BaseCommand
import pandas as pd
from simulator.models import LandUse

class Command(BaseCommand):
    help = 'Import land use data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def clean_numeric_value(self, value):
        """Convert value to float, handling '-' and other non-numeric strings"""
        if pd.isna(value) or str(value).strip() in ['-', '']:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def find_parent_code(self, code):
        """Find parent code based on hierarchical structure"""
        if '.' not in code:
            return None  # Root level
        
        parts = code.split('.')
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return None

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # Clear existing data
        LandUse.objects.all().delete()
        self.stdout.write('Cleared existing data.')
        
        # Load CSV
        df = pd.read_csv(csv_file)
        self.stdout.write(f'Loading {len(df)} rows from {csv_file}...')
        
        # First pass: Create all objects without parent relationships
        created_objects = {}
        for _, row in df.iterrows():
            code = str(row["Code"])
            landuse = LandUse.objects.create(
                code=code,
                name=row["Flächenart / Energetische Nutzung"],
                status_ha=self.clean_numeric_value(row["Status (ha)"]),
                target_ha=self.clean_numeric_value(row["Ziel (ha)"]),
                quelle=row["Quelle"]
            )
            created_objects[code] = landuse
        
        # Second pass: Set up parent relationships
        for code, landuse in created_objects.items():
            parent_code = self.find_parent_code(code)
            if parent_code and parent_code in created_objects:
                landuse.parent = created_objects[parent_code]
                landuse.save()
        
        count = LandUse.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {count} records with hierarchical relationships!')
        )
