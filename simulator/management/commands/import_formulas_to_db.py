"""
Management Command: Import Formulas to Database
===============================================

This command imports all formulas from renewable_energy_complete_formulas.py
into the database Formula model, making them editable via Admin UI.

USAGE:
    python manage.py import_formulas_to_db
    python manage.py import_formulas_to_db --force  # Overwrite existing formulas
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from simulator.models import Formula
import sys
import os


class Command(BaseCommand):
    help = 'Import formulas from Python files into database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing formulas',
        )
        parser.add_argument(
            '--category',
            type=str,
            default='renewable',
            help='Category to assign to formulas (default: renewable)',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        category = options['category']
        
        self.stdout.write(self.style.NOTICE('Starting formula import from Python files...'))
        
        try:
            # Add parent directory to path
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            
            # Import all formula sections
            from renewable_energy_complete_formulas import (
                SECTION_1_FORMULAS,
                SECTION_2_FORMULAS,
                SECTION_3_FORMULAS,
                SECTION_4_FORMULAS,
                SECTION_5_FORMULAS,
                SECTION_6_FORMULAS,
                SECTION_7_FORMULAS,
                SECTION_8_FORMULAS,
                SECTION_9_FORMULAS,
            )
            
            # Combine all sections
            all_formulas = {
                **SECTION_1_FORMULAS,
                **SECTION_2_FORMULAS,
                **SECTION_3_FORMULAS,
                **SECTION_4_FORMULAS,
                **SECTION_5_FORMULAS,
                **SECTION_6_FORMULAS,
                **SECTION_7_FORMULAS,
                **SECTION_8_FORMULAS,
                **SECTION_9_FORMULAS,
            }
            
            self.stdout.write(f'Found {len(all_formulas)} formulas in Python files')
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            with transaction.atomic():
                for code, formula_def in all_formulas.items():
                    expression = formula_def.get('formula')
                    description = formula_def.get('description', '')
                    name = formula_def.get('name', '')
                    is_fixed = formula_def.get('is_fixed', False)
                    
                    # Build full description from name and description
                    full_description = name
                    if description and description != name:
                        full_description = f"{name}\n{description}" if name else description
                    
                    # Check if formula exists
                    existing = Formula.objects.filter(key=code).first()
                    
                    if existing and not force:
                        skipped_count += 1
                        self.stdout.write(self.style.WARNING(f'  ⊗ Skipped {code} (already exists, use --force to overwrite)'))
                        continue
                    
                    if existing:
                        # Update existing formula
                        existing.expression = expression or ''
                        existing.description = full_description
                        existing.category = category
                        existing.is_fixed = is_fixed
                        existing.is_active = True
                        existing.validation_status = 'valid'
                        existing.save()
                        existing.increment_version()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Updated {code}'))
                    else:
                        # Create new formula
                        Formula.objects.create(
                            key=code,
                            expression=expression or '',
                            description=full_description,
                            category=category,
                            is_fixed=is_fixed,
                            is_active=True,
                            version=1,
                            validation_status='valid',
                        )
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {code}'))
            
            # Summary
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('═' * 60))
            self.stdout.write(self.style.SUCCESS(f'Formula Import Complete!'))
            self.stdout.write(self.style.SUCCESS(f'  Created:  {created_count}'))
            self.stdout.write(self.style.SUCCESS(f'  Updated:  {updated_count}'))
            if skipped_count:
                self.stdout.write(self.style.WARNING(f'  Skipped:  {skipped_count}'))
            self.stdout.write(self.style.SUCCESS(f'  Total:    {len(all_formulas)}'))
            self.stdout.write(self.style.SUCCESS('═' * 60))
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE('✓ Formulas are now editable in Django Admin'))
            self.stdout.write(self.style.NOTICE('  Navigate to: /admin/simulator/formula/'))
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error importing formula files: {e}'))
            self.stdout.write(self.style.ERROR('Make sure renewable_energy_complete_formulas.py exists'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
            import traceback
            traceback.print_exc()
            return
