"""
List Formulas Command - View all formulas in database
=====================================================

Usage:
    python manage.py list_formulas
    python manage.py list_formulas --category renewable
    python manage.py list_formulas --search "1.1.2"
"""

from django.core.management.base import BaseCommand
from simulator.models import Formula


class Command(BaseCommand):
    help = 'List all formulas in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Filter by category (renewable, verbrauch, ws)',
        )
        parser.add_argument(
            '--search',
            type=str,
            help='Search in key or description',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of results (default: 50)',
        )

    def handle(self, *args, **options):
        category = options.get('category')
        search = options.get('search')
        limit = options.get('limit')
        
        self.stdout.write("=" * 90)
        self.stdout.write(self.style.SUCCESS("FORMULAS IN DATABASE"))
        self.stdout.write("=" * 90)
        
        # Build query
        formulas = Formula.objects.all()
        
        if category:
            formulas = formulas.filter(category=category)
            self.stdout.write(f"\n📂 Category: {category}")
        
        if search:
            formulas = formulas.filter(key__icontains=search)
            self.stdout.write(f"🔍 Search: {search}")
        
        total = formulas.count()
        formulas = formulas.order_by('key')[:limit]
        
        self.stdout.write(f"\n📊 Found {total} formulas")
        if total > limit:
            self.stdout.write(f"   Showing first {limit} (use --limit to see more)")
        
        self.stdout.write("\n" + "-" * 90)
        
        for formula in formulas:
            self.stdout.write(f"\n🔑 Key: {self.style.WARNING(formula.key)}")
            
            if formula.expression:
                expr = formula.expression[:80] + "..." if len(formula.expression) > 80 else formula.expression
                self.stdout.write(f"   Expression: {expr}")
            else:
                self.stdout.write(f"   Expression: {self.style.ERROR('(empty - fixed value)')}")
            
            if formula.description:
                desc = formula.description.split('\n')[0][:70]
                self.stdout.write(f"   Description: {desc}")
            
            self.stdout.write(f"   Category: {formula.category} | Fixed: {formula.is_fixed} | Active: {formula.is_active}")
        
        self.stdout.write("\n" + "=" * 90)
        
        # Show category breakdown
        self.stdout.write("\n📊 BREAKDOWN BY CATEGORY:")
        renewable_count = Formula.objects.filter(category='renewable').count()
        verbrauch_count = Formula.objects.filter(category='verbrauch').count()
        ws_count = Formula.objects.filter(category='ws').count()
        
        self.stdout.write(f"   Renewable: {renewable_count}")
        self.stdout.write(f"   Verbrauch: {verbrauch_count}")
        self.stdout.write(f"   WS:        {ws_count}")
        self.stdout.write(f"   ───────────────")
        self.stdout.write(f"   TOTAL:     {renewable_count + verbrauch_count + ws_count}")
        
        self.stdout.write("\n💡 TIP: Use Django Admin for better browsing:")
        self.stdout.write("   http://127.0.0.1:8000/admin/simulator/formula/")
        self.stdout.write("")
