import csv
from django.core.management.base import BaseCommand
from simulator.models import VerbrauchData

class Command(BaseCommand):
    help = 'Load exact Gebäudewärme structure from CSV'

    def handle(self, *args, **options):
        # Path to the exact structure CSV
        csv_file_path = 'Gebaeudewaerme_exact_structure.csv'
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                created_count = 0
                
                for row in reader:
                    # Convert empty strings to None for numeric fields
                    status = float(row['status']) if row['status'] else None
                    ziel = float(row['ziel']) if row['ziel'] else None
                    is_calculated = bool(int(row['is_calculated'])) if row['is_calculated'] else False
                    user_percent = float(row['user_percent']) if row['user_percent'] else None
                    
                    # Create or update the record
                    verbrauch_item, created = VerbrauchData.objects.get_or_create(
                        code=row['code'],
                        defaults={
                            'category': row['category'],
                            'unit': row['unit'],
                            'status': status,
                            'ziel': ziel,
                            'is_calculated': is_calculated,
                            'user_percent': user_percent,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'✅ Created {row["code"]}: {row["category"]}')
                    else:
                        # Update existing record
                        verbrauch_item.category = row['category']
                        verbrauch_item.unit = row['unit']
                        verbrauch_item.status = status
                        verbrauch_item.ziel = ziel
                        verbrauch_item.is_calculated = is_calculated
                        verbrauch_item.user_percent = user_percent
                        verbrauch_item.save()
                        self.stdout.write(f'🔄 Updated {row["code"]}: {row["category"]}')
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed Gebäudewärme data: {created_count} new records')
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File {csv_file_path} not found. Make sure it exists in the project root.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading data: {str(e)}')
            )