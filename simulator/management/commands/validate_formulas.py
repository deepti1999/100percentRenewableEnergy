"""
Management Command: Validate All Formulas
=========================================

This command validates all formulas in the database and provides
a detailed report of validation results.

USAGE:
    python manage.py validate_formulas
    python manage.py validate_formulas --fix  # Auto-fix simple issues
    python manage.py validate_formulas --category renewable
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from simulator.models import Formula
from simulator.formula_validators import FormulaValidator


class Command(BaseCommand):
    help = 'Validate all formulas in the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Only validate formulas in this category',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Auto-fix simple issues (experimental)',
        )
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Include inactive formulas',
        )
    
    def handle(self, *args, **options):
        category = options.get('category')
        fix_issues = options.get('fix')
        include_inactive = options.get('inactive')
        
        self.stdout.write(self.style.NOTICE('🔍 Validating formulas...'))
        self.stdout.write('')
        
        # Get formulas to validate
        queryset = Formula.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)
        
        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No formulas found'))
            return
        
        self.stdout.write(f'Validating {total} formulas...')
        self.stdout.write('─' * 60)
        
        valid_count = 0
        warning_count = 0
        invalid_count = 0
        fixed_count = 0
        
        for formula in queryset:
            # Validate using the model method
            is_valid = formula.validate_expression()
            
            status_icon = '✓' if formula.validation_status == 'valid' else '⚠' if formula.validation_status == 'warning' else '✗'
            status_color = self.style.SUCCESS if formula.validation_status == 'valid' else self.style.WARNING if formula.validation_status == 'warning' else self.style.ERROR
            
            # Display result
            self.stdout.write(
                status_color(f'{status_icon} {formula.key:20s} [{formula.validation_status.upper():8s}]')
            )
            
            # Show validation messages if any issues
            if formula.validation_message and (formula.validation_status != 'valid' or include_inactive):
                for line in formula.validation_message.split('\n'):
                    if line.strip():
                        self.stdout.write(f'   {line}')
            
            # Count by status
            if formula.validation_status == 'valid':
                valid_count += 1
            elif formula.validation_status == 'warning':
                warning_count += 1
            else:
                invalid_count += 1
        
        # Summary
        self.stdout.write('')
        self.stdout.write('═' * 60)
        self.stdout.write(self.style.NOTICE('Validation Summary'))
        self.stdout.write('═' * 60)
        
        total_checked = valid_count + warning_count + invalid_count
        
        if valid_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Valid:    {valid_count:3d} ({valid_count*100//total_checked:3d}%)'))
        if warning_count > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠ Warnings: {warning_count:3d} ({warning_count*100//total_checked:3d}%)'))
        if invalid_count > 0:
            self.stdout.write(self.style.ERROR(f'  ✗ Invalid:  {invalid_count:3d} ({invalid_count*100//total_checked:3d}%)'))
        
        self.stdout.write('─' * 60)
        self.stdout.write(self.style.NOTICE(f'  Total:     {total_checked:3d}'))
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  Fixed:     {fixed_count:3d}'))
        
        self.stdout.write('═' * 60)
        
        # Final status
        if invalid_count == 0 and warning_count == 0:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ All formulas are valid!'))
        elif invalid_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ {invalid_count} formula(s) have errors that need attention'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'⚠️  {warning_count} formula(s) have warnings'))
