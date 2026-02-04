"""
Management Command: Check all formulas across all pages
"""

from django.core.management.base import BaseCommand
from simulator.models import RenewableData, VerbrauchData, LandUse, WSData, Formula
import os


class Command(BaseCommand):
    help = 'Check formula coverage for all pages'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('DATABASE FORMULA COVERAGE CHECK - ALL PAGES')
        self.stdout.write('=' * 70)

        # 1. RENEWABLE
        self.stdout.write('\n1. RENEWABLE ENERGY PAGE')
        self.stdout.write('-' * 70)
        renewable_calculated = RenewableData.objects.filter(is_calculated=True).order_by('code')
        renewable_missing = []
        for entry in renewable_calculated:
            formula = Formula.objects.filter(category='renewable', key=entry.code).first()
            if not formula:
                renewable_missing.append(entry.code)

        self.stdout.write(f'Total calculated entries: {renewable_calculated.count()}')
        self.stdout.write(f'Total formulas in DB: {Formula.objects.filter(category="renewable").count()}')
        if renewable_missing:
            self.stdout.write(self.style.ERROR(f'❌ Missing {len(renewable_missing)} formulas:'))
            for code in renewable_missing[:10]:
                self.stdout.write(f'   - {code}')
            if len(renewable_missing) > 10:
                self.stdout.write(f'   ... and {len(renewable_missing) - 10} more')
        else:
            self.stdout.write(self.style.SUCCESS('✅ All renewable calculated entries have formulas'))

        # 2. VERBRAUCH
        self.stdout.write('\n2. VERBRAUCH (CONSUMPTION) PAGE')
        self.stdout.write('-' * 70)
        verbrauch_calculated = VerbrauchData.objects.filter(is_calculated=True).order_by('code')
        verbrauch_missing = []
        for entry in verbrauch_calculated:
            formula_keys = [f'V_{entry.code}', f'VERBRAUCH_{entry.code.replace(".", "_")}']
            formula = Formula.objects.filter(category='verbrauch', key__in=formula_keys).first()
            if not formula:
                verbrauch_missing.append(entry.code)

        self.stdout.write(f'Total calculated entries: {verbrauch_calculated.count()}')
        self.stdout.write(f'Total formulas in DB: {Formula.objects.filter(category="verbrauch").count()}')
        if verbrauch_missing:
            self.stdout.write(self.style.ERROR(f'❌ Missing {len(verbrauch_missing)} formulas:'))
            for code in verbrauch_missing[:10]:
                self.stdout.write(f'   - {code}')
            if len(verbrauch_missing) > 10:
                self.stdout.write(f'   ... and {len(verbrauch_missing) - 10} more')
        else:
            self.stdout.write(self.style.SUCCESS('✅ All verbrauch calculated entries have formulas'))

        # 3. LANDUSE
        self.stdout.write('\n3. LANDUSE PAGE')
        self.stdout.write('-' * 70)
        landuse_calculated = LandUse.objects.filter(is_calculated=True).order_by('code')
        landuse_missing = []
        for entry in landuse_calculated:
            formula = Formula.objects.filter(category='landuse', key=entry.code).first()
            if not formula:
                landuse_missing.append(entry.code)

        self.stdout.write(f'Total calculated entries: {landuse_calculated.count()}')
        self.stdout.write(f'Total formulas in DB: {Formula.objects.filter(category="landuse").count()}')
        if landuse_missing:
            self.stdout.write(self.style.ERROR(f'❌ Missing {len(landuse_missing)} formulas:'))
            for code in landuse_missing[:10]:
                self.stdout.write(f'   - {code}')
            if len(landuse_missing) > 10:
                self.stdout.write(f'   ... and {len(landuse_missing) - 10} more')
        else:
            self.stdout.write(self.style.SUCCESS('✅ All landuse calculated entries have formulas'))

        # 4. WS
        self.stdout.write('\n4. WS (ENERGY STORAGE) PAGE')
        self.stdout.write('-' * 70)
        ws_formulas = Formula.objects.filter(category='ws')
        self.stdout.write(f'Total WS formulas in DB: {ws_formulas.count()}')
        if ws_formulas.count() > 0:
            self.stdout.write(self.style.SUCCESS('✅ WS formulas exist in database'))
            self.stdout.write(f'   Formula keys: {[f.key for f in ws_formulas[:5]]}...')
        else:
            self.stdout.write(self.style.ERROR('❌ No WS formulas in database'))

        # SUMMARY
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 70)
        total_missing = len(renewable_missing) + len(verbrauch_missing) + len(landuse_missing)
        if total_missing == 0 and ws_formulas.count() > 0:
            self.stdout.write(self.style.SUCCESS('✅ ALL PAGES: Complete formula coverage in database'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ TOTAL MISSING: {total_missing} formulas across all pages'))
            if renewable_missing:
                self.stdout.write(f'   - Renewable: {len(renewable_missing)} missing')
            if verbrauch_missing:
                self.stdout.write(f'   - Verbrauch: {len(verbrauch_missing)} missing')
            if landuse_missing:
                self.stdout.write(f'   - LandUse: {len(landuse_missing)} missing')
            if ws_formulas.count() == 0:
                self.stdout.write(f'   - WS: No formulas')

        self.stdout.write(f'\n📊 Total formulas in database: {Formula.objects.count()}')
        
        # Check management commands
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('PERMANENT IMPORT COMMANDS AVAILABLE')
        self.stdout.write('=' * 70)
        cmd_dir = 'simulator/management/commands'
        if os.path.exists(cmd_dir):
            commands = [f for f in os.listdir(cmd_dir) if f.startswith('import_') and f.endswith('.py')]
            self.stdout.write(f'\nFound {len(commands)} import commands:')
            for cmd in sorted(commands):
                self.stdout.write(self.style.SUCCESS(f'   ✓ {cmd}'))
            self.stdout.write('\n✅ Formulas can be permanently re-imported using these management commands')
            self.stdout.write('   Run: python manage.py <command_name>')
