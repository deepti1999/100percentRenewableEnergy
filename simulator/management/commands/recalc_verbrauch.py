from django.core.management.base import BaseCommand

from simulator.verbrauch_recalculator import recalc_all_verbrauch


class Command(BaseCommand):
    help = "Recalculate all calculated VerbrauchData rows in dependency order."

    def handle(self, *args, **options):
        updated = recalc_all_verbrauch(trigger_code="management_command")
        self.stdout.write(
            self.style.SUCCESS(f"Recalculated VerbrauchData rows: {len(updated)} updated")
        )
