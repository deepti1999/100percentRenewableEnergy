from django.core.management.base import BaseCommand
import pandas as pd
from simulator.models import LandUse

class Command(BaseCommand):
    help = 'Import clean CSV data with proper parent relationships'

    def handle(self, *args, **options):
        # Clear existing data
        LandUse.objects.all().delete()
        self.stdout.write('🗑️  Cleared existing data.')
        
        # Load the clean CSV
        df = pd.read_csv("Flaechen_Daten_Clean.csv")
        self.stdout.write(f'📁 Loading {len(df)} rows from Flaechen_Daten_Clean.csv...')
        
        # First pass: Create all objects
        created_objects = {}
        for _, row in df.iterrows():
            code = str(row["Code"])
            landuse = LandUse.objects.create(
                code=code,
                name=row["Name"],
                status_ha=float(row["Status_ha"]) if pd.notna(row["Status_ha"]) else None,
                target_ha=float(row["Target_ha"]) if pd.notna(row["Target_ha"]) else None,
                quelle=row["Quelle"]
            )
            created_objects[code] = landuse
        
        # Second pass: Set parent relationships
        for _, row in df.iterrows():
            code = str(row["Code"])
            parent_code_raw = row["Parent_Code"]
            
            if pd.notna(parent_code_raw):
                parent_code = str(int(parent_code_raw)) if isinstance(parent_code_raw, float) else str(parent_code_raw)
                if parent_code in created_objects:
                    child = created_objects[code]
                    parent = created_objects[parent_code]
                    child.parent = parent
                    child.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully imported {LandUse.objects.count()} records from clean CSV!')
        )
        
        # Show some examples
        self.stdout.write('\n📊 Sample data with calculated percentages:')
        for code in ['1', '1.1', '2', '2.1']:
            try:
                lu = LandUse.objects.get(code=code)
                status_pct = f'{lu.status_percent}%' if lu.status_percent else '-'
                target_pct = f'{lu.target_percent}%' if lu.target_percent else '-'
                self.stdout.write(f'  {lu.code} - {lu.name}: Status {status_pct}, Target {target_pct}')
            except LandUse.DoesNotExist:
                pass
