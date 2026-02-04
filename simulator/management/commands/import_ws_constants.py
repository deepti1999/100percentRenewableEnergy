"""
Management command to import WS efficiency constants to database
"""
from django.core.management.base import BaseCommand
from simulator.models import Formula, FormulaVariable


class Command(BaseCommand):
    help = 'Import WS efficiency constants as database formulas'

    def handle(self, *args, **options):
        constants = [
            {
                'key': 'WS_ETA_STROM_GAS',
                'expression': '0.65',
                'description': 'Power to Gas efficiency (Elektrolyse)',
                'category': 'ws_constant',
                'is_fixed': True,
            },
            {
                'key': 'WS_ETA_GAS_STROM',
                'expression': '0.585',
                'description': 'Gas to Power efficiency (Rückverstromung)',
                'category': 'ws_constant',
                'is_fixed': True,
            },
            {
                'key': 'WS_STORAGE_CAPACITY',
                'expression': '160',
                'description': 'Storage capacity offset value (160)',
                'category': 'ws_constant',
                'is_fixed': True,
            },
        ]

        for const in constants:
            formula, created = Formula.objects.update_or_create(
                key=const['key'],
                category=const['category'],
                defaults={
                    'expression': const['expression'],
                    'description': const['description'],
                    'is_fixed': const['is_fixed'],
                    'is_active': True,
                    'validation_status': 'valid',
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} WS constant: {const["key"]} = {const["expression"]}')
            )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully imported {len(constants)} WS constants to database'))
