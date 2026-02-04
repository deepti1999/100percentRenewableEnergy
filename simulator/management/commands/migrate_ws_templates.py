"""
Management command to migrate WSFormulaTemplate entries to the unified Formula model.

Usage:
    python manage.py migrate_ws_templates

This creates corresponding Formula entries with category='ws' for each WSFormulaTemplate entry.
The ws_row_type field on Formula is used to distinguish between different row types.
"""
from django.core.management.base import BaseCommand, CommandError
from simulator.models import Formula
from simulator.ws_formula_template import WSFormulaTemplate


class Command(BaseCommand):
    help = 'Migrate WSFormulaTemplate entries to unified Formula model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually creating entries',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing Formula entries if they exist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        templates = WSFormulaTemplate.objects.filter(is_active=True)
        
        if not templates.exists():
            self.stdout.write(self.style.WARNING('No active WSFormulaTemplate entries found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {templates.count()} active WSFormulaTemplate entries'))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for template in templates:
            column_name = template.column_name.lower()
            display_name = template.display_name
            description = template.description or ''
            
            # Map template formulas to the Formula model with row type
            # Key format: WS_columnname_rowtype (to ensure uniqueness)
            formulas_to_create = []
            
            if template.formula_day_1:
                formulas_to_create.append({
                    'key': f'WS_{column_name}_day_1',
                    'ws_row_type': 'day_1',
                    'expression': template.formula_day_1,
                    'description': f'{display_name} - Day 1 formula'
                })
            
            if template.formula_days_2_365:
                formulas_to_create.append({
                    'key': f'WS_{column_name}_days_2_365',
                    'ws_row_type': 'days_2_365',
                    'expression': template.formula_days_2_365,
                    'description': f'{display_name} - Days 2-365 pattern formula'
                })
            
            if template.formula_row_366:
                formulas_to_create.append({
                    'key': f'WS_{column_name}_row_366',
                    'ws_row_type': 'row_366',
                    'expression': template.formula_row_366,
                    'description': f'{display_name} - Row 366 (annual summary)'
                })
            
            if template.formula_row_367:
                formulas_to_create.append({
                    'key': f'WS_{column_name}_row_367',
                    'ws_row_type': 'row_367',
                    'expression': template.formula_row_367,
                    'description': f'{display_name} - Row 367 (reference)'
                })
            
            if template.formula_row_368:
                formulas_to_create.append({
                    'key': f'WS_{column_name}_row_368',
                    'ws_row_type': 'row_368',
                    'expression': template.formula_row_368,
                    'description': f'{display_name} - Row 368+'
                })
            
            # Process custom row formulas
            if template.custom_row_formulas:
                for row_num, formula_expr in template.custom_row_formulas.items():
                    formulas_to_create.append({
                        'key': f'WS_{column_name}_{row_num}',
                        'ws_row_type': f'row_{row_num}',
                        'expression': formula_expr,
                        'description': f'{display_name} - Row {row_num}'
                    })
            
            for formula_data in formulas_to_create:
                key = formula_data['key']
                ws_row_type = formula_data['ws_row_type']
                
                # Check if formula exists
                existing = Formula.objects.filter(key=key, ws_row_type=ws_row_type).first()
                
                if existing:
                    if force:
                        if not dry_run:
                            existing.expression = formula_data['expression']
                            existing.description = formula_data['description']
                            existing.save()
                        self.stdout.write(f'  Updated: {key} ({ws_row_type})')
                        updated_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'  Skipped (exists): {key} ({ws_row_type})'))
                        skipped_count += 1
                else:
                    if not dry_run:
                        Formula.objects.create(
                            key=key,
                            expression=formula_data['expression'],
                            description=formula_data['description'],
                            category='ws',
                            ws_row_type=ws_row_type,
                            is_active=True,
                        )
                    self.stdout.write(self.style.SUCCESS(f'  Created: {key} ({ws_row_type})'))
                    created_count += 1
        
        # Summary
        self.stdout.write('')
        self.stdout.write('='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write('='*50)
