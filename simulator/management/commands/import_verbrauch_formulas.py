"""
Management Command: Import Verbrauch Formulas to Database
=========================================================

This command imports Verbrauch formulas into the database with proper
cleaning and formatting.

USAGE:
    python manage.py import_verbrauch_formulas
    python manage.py import_verbrauch_formulas --force  # Overwrite existing
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from simulator.models import Formula
import re


# Manually curated Verbrauch formulas (cleaned from extraction)
# Keys prefixed with V_ to avoid conflicts with renewable formulas
VERBRAUCH_FORMULAS = {
    # KLIK (Electricity consumption - Section 1)
    'V_1.1.1.1': {
        'formula': 'Verbrauch_1.1 * Verbrauch_1.1.1 / 100',
        'description': 'KLIK Grundversorgung = Base * Percent',
    },
    'V_1.1.1.3': {
        'formula': 'Verbrauch_1.1.1.1 * Verbrauch_1.1.1.2 / 100',
        'description': 'KLIK Sub-calculation',
    },
    'V_1.2.1': {
        'formula': 'Verbrauch_1.1 * Verbrauch_1.2 / 100',
        'description': 'KLIK calculation 1.2.1',
    },
    'V_1.2.3': {
        'formula': 'Verbrauch_1.2.1 * Verbrauch_1.2.2 / 100',
        'description': 'KLIK calculation 1.2.3',
    },
    'V_1.2.5': {
        'formula': 'Verbrauch_1.2.3 * Verbrauch_1.2.4 / 100',
        'description': 'KLIK calculation 1.2.5',
    },
    'V_1.3.1': {
        'formula': 'Verbrauch_1.1 * Verbrauch_1.3 / 100',
        'description': 'KLIK calculation 1.3.1',
    },
    'V_1.3.3': {
        'formula': 'Verbrauch_1.3.1 * Verbrauch_1.3.2 / 100',
        'description': 'KLIK calculation 1.3.3',
    },
    'V_1.3.5': {
        'formula': 'Verbrauch_1.3.3 * Verbrauch_1.3.4 / 100',
        'description': 'KLIK calculation 1.3.5',
    },
    'V_1.4': {
        'formula': 'Verbrauch_1.1.1.3 + Verbrauch_1.2.5 + Verbrauch_1.3.5',
        'description': 'KLIK total electricity',
    },
    
    # Gebäudewärme (Building heat - Section 2)
    'V_2.1.0': {
        'formula': 'Verbrauch_2.0 * Verbrauch_2.1 / 100',
        'description': 'Building heat - Residential',
    },
    'V_2.1.9': {
        'formula': 'Verbrauch_2.1.0 * Verbrauch_2.1.2 / 100',
        'description': 'Building heat with development factor',
    },
    'V_2.2.0': {
        'formula': 'Verbrauch_2.0 * Verbrauch_2.2 / 100',
        'description': 'Building heat - Commercial',
    },
    'V_2.2.9': {
        'formula': 'Verbrauch_2.2.0 * Verbrauch_2.2.1 / 100',
        'description': 'Commercial building heat',
    },
    'V_2.3': {
        'formula': 'Verbrauch_2.1.9 + Verbrauch_2.2.9',
        'description': 'Total building heat demand',
    },
    'V_2.4.0': {
        'formula': 'Verbrauch_2.3 * Verbrauch_2.4 / 100',
        'description': 'Space heating portion',
    },
    'V_2.4.7': {
        'formula': 'Verbrauch_2.4.5 * Verbrauch_2.4.2 / 100',
        'description': 'Renovation impact',
    },
    'V_2.4.9': {
        'formula': 'Verbrauch_2.4.0 * (100 + Verbrauch_2.4.7) / 100',
        'description': 'Adjusted space heating',
    },
    'V_2.5.0': {
        'formula': 'Verbrauch_2.3 * Verbrauch_2.5 / 100',
        'description': 'Hot water portion',
    },
    'V_2.5.2': {
        'formula': 'Verbrauch_2.5.0 * Verbrauch_2.5.1 / 100',
        'description': 'Hot water adjusted',
    },
    'V_2.6': {
        'formula': 'Verbrauch_2.4.9 + Verbrauch_2.5.2',
        'description': 'Total building energy demand',
    },
    'V_2.7.0': {
        'formula': 'Verbrauch_2.6 * Verbrauch_2.7 / 100',
        'description': 'Final energy consumption',
    },
    'V_2.8.0': {
        'formula': 'Verbrauch_2.6 * Verbrauch_2.8 / 100',
        'description': 'Energy source 2.8',
    },
    'V_2.9.0': {
        'formula': 'Verbrauch_2.6 * Verbrauch_2.9 / 100',
        'description': 'Energy source 2.9',
    },
    'V_2.10': {
        'formula': 'Verbrauch_2.9.0 + Verbrauch_2.8.0 + Verbrauch_2.7.0',
        'description': 'Total building energy',
    },
    
    # Prozesswärme (Process heat - Section 3)
    'V_3.1.0': {
        'formula': 'Verbrauch_3.0 * Verbrauch_3.1 / 100',
        'description': 'Process heat base',
    },
    'V_3.1.2': {
        'formula': 'Verbrauch_3.1.0 * Verbrauch_3.1.1 / 100',
        'description': 'Process heat calculation',
    },
    'V_3.2.0': {
        'formula': 'Verbrauch_3.0 * Verbrauch_3.2 / 100',
        'description': 'Process heat type 2',
    },
    'V_3.2.1.5': {
        'formula': 'Verbrauch_3.2.0 * Verbrauch_3.2.1 / 100',
        'description': 'Process heat subtype',
    },
    'V_3.2.3': {
        'formula': 'Verbrauch_3.2.0 * Verbrauch_3.2.2 / 100',
        'description': 'Process heat adjusted',
    },
    'V_3.3': {
        'formula': 'Verbrauch_3.2.3 + Verbrauch_3.1.2',
        'description': 'Total process heat',
    },
    'V_3.4.0': {
        'formula': 'Verbrauch_3.3 * Verbrauch_3.4 / 100',
        'description': 'Process energy source 1',
    },
    'V_3.5.0': {
        'formula': 'Verbrauch_3.3 * Verbrauch_3.5 / 100',
        'description': 'Process energy source 2',
    },
    'V_3.6.0': {
        'formula': 'Verbrauch_3.3 * Verbrauch_3.6 / 100',
        'description': 'Process energy source 3',
    },
    'V_3.7': {
        'formula': 'Verbrauch_3.6.0 + Verbrauch_3.5.0 + Verbrauch_3.4.0',
        'description': 'Total process energy',
    },
    
    # Mobile Anwendungen (Transport - Section 4)
    'V_4.1.1.2': {
        'formula': 'Verbrauch_4.1 * Verbrauch_4.1.1 / 100 * Verbrauch_4.1.1.1 / 100',
        'description': 'Transport calculation',
    },
    'V_4.1.2.2': {
        'formula': 'Verbrauch_4.1.2.1 / 100 * Verbrauch_4.1.2 / 100 * Verbrauch_4.1',
        'description': 'Transport subtype',
    },
    'V_4.2.3': {
        'formula': 'Verbrauch_4.2.1 * Verbrauch_4.2.2 / 100',
        'description': 'Other transport',
    },
    'V_4.2.5': {
        'formula': 'Verbrauch_4.2.3 * Verbrauch_4.2.4 / 100',
        'description': 'Transport adjusted',
    },
    'V_4.3.1': {
        'formula': 'Verbrauch_4.3.2 + Verbrauch_4.3.6',
        'description': 'Total transport energy',
    },
    'V_4.1': {
        'formula': 'Verbrauch_4.1.1 + Verbrauch_4.1.2',
        'description': 'Transport category sum',
    },
    'V_4.0': {
        'formula': 'Verbrauch_4.1 + Verbrauch_4.2',
        'description': 'All transport',
    },
    
    # Totals (Sections 5, 6)
    'V_5': {
        'formula': 'Verbrauch_4.3.6 + Verbrauch_3.6.0 + Verbrauch_2.9.0 + Verbrauch_1.4',
        'description': 'Total final energy (Status)',
    },
    'V_6': {
        'formula': 'Verbrauch_4.3.1 + Verbrauch_3.7 + Verbrauch_2.10 + Verbrauch_1.4',
        'description': 'Total energy supply (Status)',
    },
}


class Command(BaseCommand):
    help = 'Import Verbrauch formulas into database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing formulas',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(self.style.NOTICE('Starting Verbrauch formula import...'))
        self.stdout.write('')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for code, formula_def in VERBRAUCH_FORMULAS.items():
                expression = formula_def.get('formula', '')
                description = formula_def.get('description', '')
                
                # Check if formula exists
                existing = Formula.objects.filter(key=code, category='verbrauch').first()
                
                if existing and not force:
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f'  ⊗ Skipped {code} (already exists)'))
                    continue
                
                if existing:
                    # Update existing
                    existing.expression = expression
                    existing.description = description
                    existing.is_active = True
                    existing.validation_status = 'valid'
                    existing.save()
                    existing.increment_version()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Updated {code}'))
                else:
                    # Create new
                    Formula.objects.create(
                        key=code,
                        expression=expression,
                        description=description,
                        category='verbrauch',
                        is_fixed=False,
                        is_active=True,
                        version=1,
                        validation_status='valid',
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created {code}'))
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS(f'Verbrauch Formula Import Complete!'))
        self.stdout.write(self.style.SUCCESS(f'  Created:  {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Updated:  {updated_count}'))
        if skipped_count:
            self.stdout.write(self.style.WARNING(f'  Skipped:  {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Total:    {len(VERBRAUCH_FORMULAS)}'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('✓ Verbrauch formulas now editable in Django Admin'))
        self.stdout.write(self.style.NOTICE('  Navigate to: /admin/simulator/formula/?category__exact=verbrauch'))
