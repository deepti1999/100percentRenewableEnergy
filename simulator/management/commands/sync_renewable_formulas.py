"""
Django Management Command: Sync Renewable Energy Formulas

This command syncs all formulas from renewable_energy_complete_formulas.py
to the database, ensuring the webapp uses the centralized formula definitions.

Usage:
    python manage.py sync_renewable_formulas
    python manage.py sync_renewable_formulas --verify-only
"""

from django.core.management.base import BaseCommand
from simulator.renewable_formulas import (
    sync_formulas_to_database,
    validate_formula_coverage,
    get_all_formula_codes,
    get_formula_for_code,
)


class Command(BaseCommand):
    help = 'Sync renewable energy formulas from renewable_energy_complete_formulas.py to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verify-only',
            action='store_true',
            help='Only verify formula coverage without updating',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        verify_only = options['verify_only']
        verbose = options['verbose']
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS('RENEWABLE ENERGY FORMULA SYNC'))
        self.stdout.write("=" * 80)
        
        # Validate coverage first
        self.stdout.write("\n📊 Validating formula coverage...")
        validation = validate_formula_coverage()
        
        self.stdout.write(f"\n  Total formulas in registry: {validation['total_registry']}")
        self.stdout.write(f"  Total codes in database: {validation['total_database']}")
        
        if validation['missing_in_db']:
            self.stdout.write(self.style.WARNING(
                f"\n  ⚠️  {len(validation['missing_in_db'])} codes in registry but not in database:"
            ))
            if verbose:
                for code in validation['missing_in_db'][:10]:  # Show first 10
                    self.stdout.write(f"    - {code}")
                if len(validation['missing_in_db']) > 10:
                    self.stdout.write(f"    ... and {len(validation['missing_in_db']) - 10} more")
        
        if validation['missing_in_registry']:
            self.stdout.write(self.style.WARNING(
                f"\n  ⚠️  {len(validation['missing_in_registry'])} codes in database but not in registry:"
            ))
            if verbose:
                for code in validation['missing_in_registry'][:10]:
                    self.stdout.write(f"    - {code}")
                if len(validation['missing_in_registry']) > 10:
                    self.stdout.write(f"    ... and {len(validation['missing_in_registry']) - 10} more")
        
        if validation['in_sync']:
            self.stdout.write(self.style.SUCCESS("\n  ✅ Registry and database are in sync!"))
        
        # If verify-only, stop here
        if verify_only:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("Verification complete (no changes made)")
            return
        
        # Sync formulas to database
        self.stdout.write("\n\n🔄 Syncing formulas to database...")
        stats = sync_formulas_to_database()
        
        self.stdout.write(f"\n  ✅ Updated: {stats['updated']}")
        self.stdout.write(f"  ⏭️  Skipped (no changes): {stats['skipped']}")
        
        if stats['errors']:
            self.stdout.write(self.style.WARNING(
                f"\n  ⚠️  Errors: {len(stats['errors'])}"
            ))
            if verbose:
                for error in stats['errors'][:10]:
                    self.stdout.write(f"    - {error}")
                if len(stats['errors']) > 10:
                    self.stdout.write(f"    ... and {len(stats['errors']) - 10} more errors")
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS('✅ Formula sync complete!'))
        self.stdout.write("=" * 80)
        
        # Show usage tip
        self.stdout.write("\n💡 Tip: The webapp will now use formulas from renewable_energy_complete_formulas.py")
        self.stdout.write("   Any changes to formulas in that file should be followed by running this command.\n")
