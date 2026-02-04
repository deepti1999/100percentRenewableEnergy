from django.core.management.base import BaseCommand
from simulator.models import VerbrauchData


class Command(BaseCommand):
    help = 'Clear status and ziel values for calculated items in VerbrauchData'
    
    def handle(self, *args, **options):
        # Codes that need to be calculated (should have empty values in DB)
        calculated_codes = [
            '1.1.1.1',
            '1.1.1.3', 
            '1.2.1',
            '1.2.3',
            '1.2.5',
            '1.3.1',
            '1.3.3',
            '1.3.5',
            '1.4'
        ]
        
        # Clear values for these codes
        updated_count = 0
        for code in calculated_codes:
            try:
                verbrauch_item = VerbrauchData.objects.get(code=code)
                
                # Clear status and ziel values, keep only the structure
                old_status = verbrauch_item.status
                old_ziel = verbrauch_item.ziel
                
                verbrauch_item.status = None
                verbrauch_item.ziel = None
                verbrauch_item.is_calculated = True  # Ensure it's marked as calculated
                verbrauch_item.save()
                
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Cleared {code}: Status {old_status} → None, Ziel {old_ziel} → None'
                    )
                )
            except VerbrauchData.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Code {code} not found in database')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleared values for {updated_count} calculated items')
        )
        
        # Show summary of remaining fixed values
        fixed_items = VerbrauchData.objects.filter(is_calculated=False)
        self.stdout.write(
            self.style.SUCCESS(f'Fixed items with values: {fixed_items.count()}')
        )