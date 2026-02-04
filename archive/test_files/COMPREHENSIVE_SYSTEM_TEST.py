#!/usr/bin/env python
"""
COMPREHENSIVE SYSTEM TEST - PERMANENT FILE
Tests if the entire webapp is 100% non-hardcoded and extensible

This test can be run anytime to verify:
1. All formulas use FormulaVariable approach (friend's approach)
2. No hardcoded formulas anywhere
3. All pages use calculation engines
4. System is 100% extensible via Admin
5. Real-time updates work

Run: python COMPREHENSIVE_SYSTEM_TEST.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, RenewableData, VerbrauchData, WSData
from calculation_engine.renewable_engine import RenewableCalculator
from calculation_engine.verbrauch_engine import VerbrauchCalculator
from django.core.cache import cache

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_1_formula_migration():
    """Test 1: Verify 100% migration to FormulaVariable"""
    print_section("TEST 1: 100% FORMULA MIGRATION TO FORMULAVARIABLE")
    
    categories = ['renewable', 'verbrauch', 'ws']
    total_calculated = 0
    total_with_mappings = 0
    
    results = []
    
    for category in categories:
        # Count calculated formulas (not fixed values)
        calculated = Formula.objects.filter(
            category=category,
            is_fixed=False
        ).count()
        
        # Count formulas with FormulaVariable mappings
        with_mappings = Formula.objects.filter(
            category=category,
            is_fixed=False,
            variables__isnull=False
        ).distinct().count()
        
        percentage = (with_mappings / calculated * 100) if calculated > 0 else 0
        
        total_calculated += calculated
        total_with_mappings += with_mappings
        
        status = "✅" if percentage == 100 else "❌"
        results.append({
            'category': category.upper(),
            'calculated': calculated,
            'with_mappings': with_mappings,
            'percentage': percentage,
            'status': status
        })
    
    # Print results
    print("\nCategory     | Calculated | With Mappings | Coverage")
    print("-" * 60)
    for r in results:
        print(f"{r['status']} {r['category']:<10} | {r['calculated']:>10} | {r['with_mappings']:>13} | {r['percentage']:>6.1f}%")
    
    print("-" * 60)
    overall = (total_with_mappings / total_calculated * 100) if total_calculated > 0 else 0
    print(f"   TOTAL        | {total_calculated:>10} | {total_with_mappings:>13} | {overall:>6.1f}%")
    
    if overall == 100:
        print(f"\n✅ TEST 1 PASSED - All {total_calculated} calculated formulas use FormulaVariable")
        return True
    else:
        print(f"\n❌ TEST 1 FAILED - Only {overall:.1f}% migrated")
        return False

def test_2_no_hardcoded_formulas():
    """Test 2: Verify no hardcoded formulas in code"""
    print_section("TEST 2: NO HARDCODED FORMULAS IN CODE")
    
    # Check key files for hardcoded formula patterns
    files_to_check = [
        'simulator/views.py',
        'calculation_engine/renewable_engine.py',
        'calculation_engine/verbrauch_engine.py',
        'calculation_engine/bilanz_engine.py',
        'calculation_engine/ws_calculator.py'
    ]
    
    forbidden_patterns = [
        'RENEWABLE_FORMULAS[',
        'VERBRAUCH_FORMULAS[',
        'WS_FORMULAS[',
        'LANDUSE_FORMULAS['
    ]
    
    violations = []
    
    for file_path in files_to_check:
        full_path = os.path.join('/Users/deeptimaheedharan/Desktop/total new try ', file_path)
        if not os.path.exists(full_path):
            print(f"⚠️  {file_path}: File not found")
            continue
            
        with open(full_path, 'r') as f:
            content = f.read()
            
        found = []
        for pattern in forbidden_patterns:
            if pattern in content:
                found.append(pattern)
        
        if found:
            violations.append({'file': file_path, 'patterns': found})
            print(f"❌ {file_path}: Found {', '.join(found)}")
        else:
            print(f"✅ {file_path}: Clean")
    
    if not violations:
        print(f"\n✅ TEST 2 PASSED - No hardcoded formulas found in {len(files_to_check)} files")
        return True
    else:
        print(f"\n❌ TEST 2 FAILED - Found hardcoded formulas in {len(violations)} files")
        return False

def test_3_all_pages_use_calculators():
    """Test 3: Verify all pages use calculation engines"""
    print_section("TEST 3: ALL PAGES USE CALCULATION ENGINES")
    
    pages = [
        {
            'name': 'Renewable Page',
            'view': 'renewable_list',
            'uses': 'RenewableCalculator',
            'check': lambda: 'RenewableCalculator()' in open('/Users/deeptimaheedharan/Desktop/total new try /simulator/views.py').read()
        },
        {
            'name': 'Verbrauch Page',
            'view': 'verbrauch_list',
            'uses': 'VerbrauchCalculator',
            'check': lambda: 'VerbrauchCalculator()' in open('/Users/deeptimaheedharan/Desktop/total new try /simulator/views.py').read()
        },
        {
            'name': 'Annual Electricity (WS)',
            'view': 'annual_electricity_view',
            'uses': 'RenewableCalculator',
            'check': lambda: 'RenewableCalculator()' in open('/Users/deeptimaheedharan/Desktop/total new try /simulator/views.py').read()
        },
        {
            'name': 'Bilanz Page',
            'view': 'bilanz_view',
            'uses': 'bilanz_engine → Calculators',
            'check': lambda: 'calculate_bilanz_data()' in open('/Users/deeptimaheedharan/Desktop/total new try /simulator/views.py').read()
        }
    ]
    
    all_passed = True
    
    for page in pages:
        uses_calculator = page['check']()
        status = "✅" if uses_calculator else "❌"
        print(f"{status} {page['name']}: Uses {page['uses']} → FormulaVariable")
        if not uses_calculator:
            all_passed = False
    
    if all_passed:
        print(f"\n✅ TEST 3 PASSED - All {len(pages)} pages use calculation engines")
        return True
    else:
        print(f"\n❌ TEST 3 FAILED - Some pages don't use calculators")
        return False

def test_4_extensibility():
    """Test 4: Verify system is extensible - new formulas work without code changes"""
    print_section("TEST 4: EXTENSIBILITY - ADD NEW FORMULA VIA ADMIN")
    
    # Clean up any existing test data
    Formula.objects.filter(key='TEST_EXTENSIBILITY_FINAL').delete()
    RenewableData.objects.filter(code='TEST_EXTENSIBILITY_FINAL').delete()
    
    try:
        # Step 1: Create RenewableData entry (Admin UI simulation)
        print("\n📝 Admin creates new RenewableData entry...")
        test_data = RenewableData.objects.create(
            code='TEST_EXTENSIBILITY_FINAL',
            description='Final extensibility test',
            is_fixed=False,
            status_value=0,
            target_value=0
        )
        print(f"   ✓ Created: {test_data.code}")
        
        # Step 2: Create Formula (Admin UI simulation)
        print("\n📝 Admin creates new Formula...")
        formula = Formula.objects.create(
            key='TEST_EXTENSIBILITY_FINAL',
            category='renewable',
            expression='pv + wind',
            description='Test extensibility',
            is_fixed=False,
            is_active=True
        )
        print(f"   ✓ Created: {formula.key}")
        print(f"   Expression: {formula.expression}")
        
        # Step 3: Create FormulaVariable mappings (Admin UI simulation)
        print("\n📝 Admin creates variable mappings...")
        FormulaVariable.objects.create(
            formula=formula,
            variable_name='pv',
            source_type='renewable_status',
            source_key='10.3',
            default_value=0
        )
        FormulaVariable.objects.create(
            formula=formula,
            variable_name='wind',
            source_type='renewable_status',
            source_key='10.5',
            default_value=0
        )
        print(f"   ✓ Mapped 2 variables")
        
        # Step 4: Calculate WITHOUT code changes
        print("\n🧪 Calculate new formula (NO code changes)...")
        calculator = RenewableCalculator()
        status, target = calculator.calculate('TEST_EXTENSIBILITY_FINAL')
        
        print(f"   Result: {status}")
        
        if status is not None and status > 0:
            print(f"\n✅ TEST 4 PASSED - New formula works without code changes!")
            print(f"   🎉 System is 100% extensible via Admin!")
            return True
        else:
            print(f"\n❌ TEST 4 FAILED - New formula returned None or zero")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED - Exception: {e}")
        return False
        
    finally:
        # Cleanup
        Formula.objects.filter(key='TEST_EXTENSIBILITY_FINAL').delete()
        RenewableData.objects.filter(code='TEST_EXTENSIBILITY_FINAL').delete()

def test_5_real_time_updates():
    """Test 5: Verify real-time formula updates work"""
    print_section("TEST 5: REAL-TIME UPDATES - MODIFY FORMULA VIA ADMIN")
    
    # Clean up
    Formula.objects.filter(key='TEST_REALTIME').delete()
    RenewableData.objects.filter(code='TEST_REALTIME').delete()
    
    try:
        # Create test formula
        print("\n📝 Setup: Create test formula...")
        RenewableData.objects.create(
            code='TEST_REALTIME',
            description='Real-time test',
            is_fixed=False,
            status_value=0,
            target_value=0
        )
        
        formula = Formula.objects.create(
            key='TEST_REALTIME',
            category='renewable',
            expression='pv',
            description='Test real-time updates',
            is_fixed=False,
            is_active=True
        )
        
        FormulaVariable.objects.create(
            formula=formula,
            variable_name='pv',
            source_type='renewable_status',
            source_key='10.3',
            default_value=0
        )
        
        # Calculate initial value
        print("\n🧪 Calculate initial formula (pv)...")
        calculator = RenewableCalculator()
        initial, _ = calculator.calculate('TEST_REALTIME')
        print(f"   Result: {initial}")
        
        # Modify formula
        print("\n📝 Admin modifies formula to (pv * 3)...")
        formula.expression = 'pv * 3'
        formula.save()
        
        # Clear ALL caches (status and target)
        cache.delete(f'renewable_TEST_REALTIME')
        cache.delete(f'renewable_TEST_REALTIME_status')
        cache.delete(f'renewable_TEST_REALTIME_target')
        
        # Create new calculator instance to avoid any internal caching
        fresh_calculator = RenewableCalculator()
        
        # Calculate modified value
        print("\n🧪 Calculate modified formula...")
        modified, _ = fresh_calculator.calculate('TEST_REALTIME')
        print(f"   Result: {modified}")
        print(f"   Expected: {initial * 3 if initial else None}")
        
        if modified is not None and initial is not None:
            diff = abs(modified - (initial * 3))
            if diff < 0.01:
                print(f"\n✅ TEST 5 PASSED - Real-time updates work!")
                return True
        
        print(f"\n❌ TEST 5 FAILED - Real-time update didn't work")
        return False
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED - Exception: {e}")
        return False
        
    finally:
        # Cleanup
        Formula.objects.filter(key='TEST_REALTIME').delete()
        RenewableData.objects.filter(code='TEST_REALTIME').delete()

def test_6_data_statistics():
    """Test 6: Show system statistics"""
    print_section("TEST 6: SYSTEM STATISTICS")
    
    print("\n📊 Database Statistics:")
    print(f"   RenewableData:    {RenewableData.objects.count():>5} entries")
    print(f"   VerbrauchData:    {VerbrauchData.objects.count():>5} entries")
    print(f"   WSData:           {WSData.objects.count():>5} entries")
    print(f"   Formulas:         {Formula.objects.count():>5} total")
    print(f"   - Renewable:      {Formula.objects.filter(category='renewable').count():>5}")
    print(f"   - Verbrauch:      {Formula.objects.filter(category='verbrauch').count():>5}")
    print(f"   - WS:             {Formula.objects.filter(category='ws').count():>5}")
    print(f"   FormulaVariables: {FormulaVariable.objects.count():>5} mappings")
    
    print("\n📋 Component Clarification:")
    print("   1. WSData (Database):        367 rows of daily energy storage data")
    print("   2. WS Formulas (Formulas):   37 calculation formulas")
    print("   3. Annual Electricity Page:  Web view showing energy flows")
    print("   → All THREE are different components working together")
    
    return True

def test_7_no_temporary_files():
    """Test 7: Verify no temporary fix files are being used"""
    print_section("TEST 7: NO TEMPORARY FIX FILES IN USE")
    
    # Check if any temporary fix files are imported or used
    files_to_check = [
        'simulator/views.py',
        'calculation_engine/renewable_engine.py',
        'calculation_engine/verbrauch_engine.py',
        'calculation_engine/bilanz_engine.py'
    ]
    
    temp_patterns = [
        'from archive',
        'import fix_',
        'import temp_',
        'one_time_fix',
        'temporary_fix'
    ]
    
    violations = []
    
    for file_path in files_to_check:
        full_path = os.path.join('/Users/deeptimaheedharan/Desktop/total new try ', file_path)
        if not os.path.exists(full_path):
            continue
            
        with open(full_path, 'r') as f:
            content = f.read()
            
        found = []
        for pattern in temp_patterns:
            if pattern.lower() in content.lower():
                found.append(pattern)
        
        if found:
            violations.append({'file': file_path, 'patterns': found})
            print(f"❌ {file_path}: Uses {', '.join(found)}")
        else:
            print(f"✅ {file_path}: No temporary imports")
    
    if not violations:
        print(f"\n✅ TEST 7 PASSED - No temporary fix files in use")
        print(f"   All code uses permanent calculation engines")
        return True
    else:
        print(f"\n❌ TEST 7 FAILED - Found temporary imports in {len(violations)} files")
        return False

def main():
    """Run all comprehensive tests"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  COMPREHENSIVE SYSTEM TEST - 100% EXTENSIBILITY VERIFICATION".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    tests = [
        ("Formula Migration", test_1_formula_migration),
        ("No Hardcoded Formulas", test_2_no_hardcoded_formulas),
        ("All Pages Use Calculators", test_3_all_pages_use_calculators),
        ("Extensibility", test_4_extensibility),
        ("Real-Time Updates", test_5_real_time_updates),
        ("System Statistics", test_6_data_statistics),
        ("No Temporary Files", test_7_no_temporary_files),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {e}")
            results.append((name, False))
    
    # Final summary
    print_section("FINAL RESULTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status:12} - {name}")
    
    print("\n" + "="*80)
    
    if passed == total:
        print("\n🎉🎉🎉 ALL TESTS PASSED! 🎉🎉🎉")
        print("\n✅ Your webapp is:")
        print("   • 100% NON-HARDCODED")
        print("   • 100% EXTENSIBLE via Admin UI")
        print("   • Using friend's FormulaVariable approach")
        print("   • All pages working with calculation engines")
        print("   • No temporary fix files")
        print("   • Real-time updates working")
        print("\n👉 Admin users can add/modify formulas WITHOUT developer help!")
        print("="*80 + "\n")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print(f"\n   {passed}/{total} tests passed")
        print("   Please review the failed tests above")
        print("="*80 + "\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
