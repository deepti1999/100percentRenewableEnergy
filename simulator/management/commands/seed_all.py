"""
Management command to seed all initial data on Heroku.
Runs all the data import commands in the correct order.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seed all initial data (run after migrate on a fresh database)'

    def handle(self, *args, **options):
        commands_in_order = [
            ('import_clean', 'Land-use Flaechen data'),
            ('load_verbrauch_data', 'Verbrauch hierarchy data'),
            ('load_gebaeudewaerme_data', 'Gebaeudewaerme data'),
            ('load_exact_gebaeudewaerme', 'Exact Gebaeudewaerme structure'),
            ('load_endenergie_data', 'Endenergie data'),
            ('import_ws_constants', 'WS constants'),
            ('import_ws_formulas', 'WS formulas'),
            ('import_formulas_to_db', 'Formulas to DB'),
            ('sync_renewable_formulas', 'Renewable formulas'),
        ]

        for cmd_name, description in commands_in_order:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'Loading: {description} ({cmd_name})')
            self.stdout.write(f'{"="*60}')
            try:
                call_command(cmd_name)
                self.stdout.write(self.style.SUCCESS(f'✅ {description} loaded successfully'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  {description} skipped: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✅ All seed data loaded!'))
