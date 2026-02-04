from django.core.management.base import BaseCommand
from simulator.models import VerbrauchData


class Command(BaseCommand):
    help = 'Update VerbrauchData to mark specific codes as calculated'
    
    def handle(self, *args, **options):
        # Codes that need to be calculated
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
        
        # Mark these codes as calculated
        updated_count = 0
        for code in calculated_codes:
            try:
                verbrauch_item = VerbrauchData.objects.get(code=code)
                verbrauch_item.is_calculated = True
                verbrauch_item.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Marked {code} as calculated')
                )
            except VerbrauchData.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Code {code} not found in database')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} items to be calculated')
        )