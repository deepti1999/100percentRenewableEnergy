"""
Import LandUse calculation formulas into database.
Creates the three essential formulas for LandUse percentage calculations:
- LANDUSE_STATUS_PERCENT: Child status_ha ÷ parent status_ha × 100
- LANDUSE_TARGET_PERCENT: Child target_ha ÷ parent target_ha × 100  
- LANDUSE_CHANGE_RATIO: Target_ha ÷ status_ha

These formulas make LandUse calculations database-driven and extensible.
"""

from django.core.management.base import BaseCommand
from simulator.models import Formula, FormulaVariable
from django.db import transaction


class Command(BaseCommand):
    help = 'Import LandUse formulas into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing formulas',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('IMPORTING LANDUSE FORMULAS'))
        self.stdout.write('=' * 70)
        self.stdout.write('')

        # Define the three LandUse formulas
        formulas = {
            'LANDUSE_STATUS_PERCENT': {
                'expression': 'child_status / parent_status * 100',
                'description': 'Calculate status percentage: child status_ha ÷ parent status_ha × 100',
                'variables': [
                    {
                        'variable_name': 'child_status',
                        'source_type': 'landuse_status',
                        'source_key': 'CURRENT_ROW',  # Placeholder, will be set by view
                        'is_required': True,
                        'notes': 'Current LandUse row status_ha value'
                    },
                    {
                        'variable_name': 'parent_status',
                        'source_type': 'landuse_status',
                        'source_key': 'PARENT_ROW',  # Placeholder, will be set by view
                        'is_required': True,
                        'notes': 'Parent LandUse row status_ha value'
                    },
                ]
            },
            'LANDUSE_TARGET_PERCENT': {
                'expression': 'child_target / parent_target * 100',
                'description': 'Calculate target percentage: child target_ha ÷ parent target_ha × 100',
                'variables': [
                    {
                        'variable_name': 'child_target',
                        'source_type': 'landuse_target',
                        'source_key': 'CURRENT_ROW',  # Placeholder, will be set by view
                        'is_required': True,
                        'notes': 'Current LandUse row target_ha value'
                    },
                    {
                        'variable_name': 'parent_target',
                        'source_type': 'landuse_target',
                        'source_key': 'PARENT_ROW',  # Placeholder, will be set by view
                        'is_required': True,
                        'notes': 'Parent LandUse row target_ha value'
                    },
                ]
            },
            'LANDUSE_CHANGE_RATIO': {
                'expression': 'child_target / child_status',
                'description': 'Calculate change ratio: target_ha ÷ status_ha',
                'variables': [
                    {
                        'variable_name': 'child_target',
                        'source_type': 'landuse_target',
                        'source_key': 'CURRENT_ROW',  # Placeholder, will be set by view
                        'is_required': True,
                        'notes': 'Current LandUse row target_ha value'
                    },
                    {
                        'variable_name': 'child_status',
                        'source_type': 'landuse_status',
                        'source_key': 'CURRENT_ROW',  # Placeholder, will be set by view
                        'is_required': True,
                        'notes': 'Current LandUse row status_ha value'
                    },
                ]
            },
        }

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for key, data in formulas.items():
                expression = data['expression']
                description = data['description']
                variables = data['variables']

                # Check if formula exists
                existing = Formula.objects.filter(key=key, category='landuse').first()

                if existing and not force:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Skipped {key} (already exists, use --force to update)')
                    )
                    continue

                if existing:
                    # Update existing formula
                    existing.expression = expression
                    existing.description = description
                    existing.is_fixed = False
                    existing.is_active = True
                    existing.save()
                    
                    # Delete old variables and recreate
                    existing.variables.all().delete()
                    formula = existing
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Updated {key}'))
                else:
                    # Create new formula
                    formula = Formula.objects.create(
                        key=key,
                        expression=expression,
                        description=description,
                        category='landuse',
                        is_fixed=False,
                        is_active=True,
                        version=1,
                        validation_status='valid',
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created {key}'))

                # Create FormulaVariable entries
                for var_data in variables:
                    FormulaVariable.objects.create(
                        formula=formula,
                        variable_name=var_data['variable_name'],
                        source_type=var_data['source_type'],
                        source_key=var_data['source_key'],
                        is_required=var_data.get('is_required', True),
                        notes=var_data.get('notes', ''),
                    )
                    self.stdout.write(
                        f'    → Added variable: {var_data["variable_name"]} ({var_data["source_type"]})'
                    )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 70))
        self.stdout.write(self.style.SUCCESS('LandUse Formula Import Complete!'))
        self.stdout.write(self.style.SUCCESS(f'  Created:  {created_count} formulas'))
        self.stdout.write(self.style.SUCCESS(f'  Updated:  {updated_count} formulas'))
        if skipped_count:
            self.stdout.write(self.style.WARNING(f'  Skipped:  {skipped_count} formulas (use --force to update)'))
        self.stdout.write(self.style.SUCCESS(f'  Total:    {created_count + updated_count + skipped_count} formulas'))
        self.stdout.write(self.style.SUCCESS('═' * 70))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ LandUse formulas are now in the database!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Check Admin → Formulas → Filter by "landuse" category')
        self.stdout.write('  2. You should see: LANDUSE_STATUS_PERCENT, LANDUSE_TARGET_PERCENT, LANDUSE_CHANGE_RATIO')
        self.stdout.write('  3. Each formula has 2 FormulaVariable entries')
        self.stdout.write('  4. Update views.py to use these formulas instead of hardcoded math')
        self.stdout.write('')
