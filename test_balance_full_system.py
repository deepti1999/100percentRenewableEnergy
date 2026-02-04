#!/usr/bin/env python
"""
Test the complete balance system with new FormulaVariable-based WS calculations.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData, Formula, FormulaVariable
from simulator.views import final_balance
from django.test import RequestFactory

def test_balance_system():
    """Test the complete balance workflow."""
    print("=" * 80)
    print("TESTING BALANCE SYSTEM WITH FORMULAVARIABLE-BASED WS CALCULATIONS")
    print("=" * 80)
    
    # 1. Check database state
    print("\n1. DATABASE STATE CHECK:")
    ws_rows = WSData.objects.all().count()
    ws_formulas = Formula.objects.filter(category='ws', is_active=True).count()
    ws_vars = FormulaVariable.objects.filter(formula__category='ws').count()
    
    print(f"   ✓ WS rows: {ws_rows}")
    print(f"   ✓ WS formulas: {ws_formulas}")
    print(f"   ✓ WS formula variables: {ws_vars}")
    
    if ws_formulas == 0:
        print("   ❌ No WS formulas found in database!")
        return False
    
    # 2. Test formula loading with FormulaVariable
    print("\n2. FORMULA LOADING TEST:")
    try:
        test_formula = Formula.objects.prefetch_related('variables').get(
            key='WS_STROMVERBR',
            is_active=True,
            category='ws'
        )
        print(f"   ✓ Formula '{test_formula.key}' loaded successfully")
        print(f"   ✓ Expression: {test_formula.expression}")
        print(f"   ✓ Variables: {test_formula.variables.count()}")
        for var in test_formula.variables.all():
            print(f"     - {var.variable_name}: {var.source_type}.{var.source_key}")
    except Exception as e:
        print(f"   ❌ Failed to load formula: {e}")
        return False
    
    # 3. Check row 1-365 state before balance
    print("\n3. PRE-BALANCE STATE:")
    row_1 = WSData.objects.get(tag_im_jahr=1)
    row_365 = WSData.objects.get(tag_im_jahr=365)
    print(f"   Row 1 stromverbr: {row_1.stromverbr}")
    print(f"   Row 1 ladezustand_netto: {row_1.ladezustand_netto}")
    print(f"   Row 365 ladezustand_netto: {row_365.ladezustand_netto}")
    
    # 4. Test balance function
    print("\n4. RUNNING BALANCE:")
    try:
        factory = RequestFactory()
        request = factory.post('/balance/')
        request.POST = {'csrfmiddlewaretoken': 'test'}
        
        # Add required middleware/attributes
        from django.contrib.auth.models import AnonymousUser
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.messages.middleware import MessageMiddleware
        
        request.user = AnonymousUser()
        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
        
        response = final_balance(request)
        print(f"   ✓ Balance completed with status: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Balance failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Check row state after balance
    print("\n5. POST-BALANCE STATE:")
    row_1 = WSData.objects.get(tag_im_jahr=1)
    row_365 = WSData.objects.get(tag_im_jahr=365)
    print(f"   Row 1 stromverbr: {row_1.stromverbr}")
    print(f"   Row 1 ladezustand_netto: {row_1.ladezustand_netto}")
    print(f"   Row 365 ladezustand_netto: {row_365.ladezustand_netto}")
    
    # Check if balance improved
    if abs(row_365.ladezustand_netto or 0) < 10:
        print(f"   ✅ BALANCE ACHIEVED! Final gap: {row_365.ladezustand_netto:.2f} GWh")
    else:
        print(f"   ⚠️ Balance incomplete. Final gap: {row_365.ladezustand_netto:.2f} GWh")
    
    print("\n" + "=" * 80)
    print("✅ BALANCE SYSTEM TEST COMPLETED")
    print("=" * 80)
    return True

if __name__ == '__main__':
    test_balance_system()
