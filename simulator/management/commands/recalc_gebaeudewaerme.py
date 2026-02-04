from django.core.management.base import BaseCommand

from simulator.gebaeudewaerme_recalculator import recalc_all_gebaeudewaerme


class Command(BaseCommand):
    help = "Recalculate all calculated GebaeudewaermeData rows."

    def handle(self, *args, **options):
        updated = recalc_all_gebaeudewaerme(trigger_code="management_command")
        self.stdout.write(
            self.style.WARNING(
                f"Gebaeudewaerme recalculation is deprecated; skipped (updated {len(updated)} rows)"
            )
        )
