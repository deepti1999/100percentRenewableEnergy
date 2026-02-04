from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import pandas as pd
import os
from .models import (
    LandUse, RenewableData, VerbrauchData, CalculationRun, CategoryDisplayName, Formula
)
from .recalc_service import run_full_recalc, recalc_all_renewables_full, unified_recalc_all
from simulator.verbrauch_recalculator import recalc_all_verbrauch
from simulator.ws_models import WSData
from simulator.goal_seek import goal_seek
from simulator.signals import compute_ws_diagram_reference, recalculate_ws_data, get_ws_constants
from calculation_engine.bilanz_engine import calculate_bilanz_data, get_renewable_value
from simulator.ws_formula_service import recalculate_all_ws_data

# =============================================================================
# FORMULA SOURCES - 100% DATABASE DRIVEN
# =============================================================================
# RENEWABLE: calculation_engine/renewable_engine.py (reads from Formula model)
# VERBRAUCH: calculation_engine/verbrauch_engine.py (reads from Formula model)
# LANDUSE: formula_service.py (reads from Formula model)
#
# All formulas stored in database (Formula model), editable via Admin UI.
# To update formulas:
#   1. Go to Django Admin → Formulas
#   2. Edit formula expression
#   3. Save → Changes apply immediately
#
# Models use get_calculated_values() / calculate_value() which read formulas
# from database and evaluate them dynamically with current data.
# NO hardcoded fallbacks - 100% extensible!
# =============================================================================

def landing_page(request):
    """Landing page for 100ProSim application"""
    return render(request, 'simulator/landing_page.html')

def user_guide(request):
    """Static quick-start guide with visual pointers to key pages"""
    return render(request, 'simulator/guide.html')

def test_storage(request):
    """Test page for localStorage debugging"""
    return render(request, 'simulator/test_storage.html')

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('simulator:main_simulation')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'simulator/login.html', {'form': form})

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('simulator:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'simulator/register.html', {'form': form})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('simulator:landing_page')

@login_required
def main_simulation(request):
    """Main simulation dashboard with sidebar navigation"""
    context = {
        'current_section': 'dashboard',
        'total_landuse_records': LandUse.objects.count(),
        'total_renewable_records': RenewableData.objects.count(),
    }
    return render(request, 'simulator/main_simulation.html', context)


@login_required
def user_manual(request):
    """User manual page with step-by-step guide and screenshots"""
    context = {
        'current_section': 'user_manual',
    }
    return render(request, 'simulator/user_manual.html', context)


def get_landuse_data():
    """Get LandUse data formatted for calculations"""
    data = {}
    landuse_items = LandUse.objects.all()
    
    for landuse in landuse_items:
        if landuse.status_ha is not None:
            data[landuse.code] = float(landuse.status_ha)
    
    # Store original 3.1 value before water mapping overwrites it
    if "3.1" in data:
        data["ORIGINAL_3.1"] = data["3.1"]
    
    # Apply water mapping: 3.1 → 0 (for water calculations)
    if "0" in data and "3.1" in data:
        data["3.1"] = data["0"]  # Water uses total land area
    
    return data

def calculate_percentages(landuse):
    """
    Calculate percentages and ratios dynamically.
    Uses database formulas when available (extensible), with safe fallback to direct calculation.
    """
    from simulator.models import Formula
    
    data = {
        'landuse': landuse,
        'status_percent': None,
        'target_percent': None,
        'change_ratio': None,
    }
    
    # Calculate status percentage (child/parent)
    if landuse.parent and landuse.parent.status_ha and landuse.status_ha and landuse.parent.status_ha > 0:
        try:
            # Try to use database formula if available
            formula = Formula.objects.filter(key='LANDUSE_STATUS_PERCENT', category='landuse', is_active=True).first()
            if formula:
                # Use formula expression from database
                context = {
                    'child_status': landuse.status_ha,
                    'parent_status': landuse.parent.status_ha,
                }
                # Direct evaluation using formula expression
                result = eval(formula.expression, {"__builtins__": {}}, context)
                data['status_percent'] = round(result, 1)
            else:
                # Fallback: Direct calculation
                data['status_percent'] = round((landuse.status_ha / landuse.parent.status_ha) * 100, 1)
        except Exception as e:
            # Fallback on any error
            data['status_percent'] = round((landuse.status_ha / landuse.parent.status_ha) * 100, 1)
    
    # Calculate target percentage (child/parent)
    if landuse.parent and landuse.parent.target_ha and landuse.target_ha and landuse.parent.target_ha > 0:
        try:
            # Try to use database formula if available
            formula = Formula.objects.filter(key='LANDUSE_TARGET_PERCENT', category='landuse', is_active=True).first()
            if formula:
                # Use formula expression from database
                context = {
                    'child_target': landuse.target_ha,
                    'parent_target': landuse.parent.target_ha,
                }
                # Direct evaluation using formula expression
                result = eval(formula.expression, {"__builtins__": {}}, context)
                data['target_percent'] = round(result, 1)
            else:
                # Fallback: Direct calculation
                data['target_percent'] = round((landuse.target_ha / landuse.parent.target_ha) * 100, 1)
        except Exception as e:
            # Fallback on any error
            data['target_percent'] = round((landuse.target_ha / landuse.parent.target_ha) * 100, 1)
    
    # Calculate change ratio (target/status)
    if landuse.status_ha and landuse.target_ha and landuse.status_ha > 0:
        try:
            # Try to use database formula if available
            formula = Formula.objects.filter(key='LANDUSE_CHANGE_RATIO', category='landuse', is_active=True).first()
            if formula:
                # Use formula expression from database
                context = {
                    'child_status': landuse.status_ha,
                    'child_target': landuse.target_ha,
                }
                # Direct evaluation using formula expression
                result = eval(formula.expression, {"__builtins__": {}}, context)
                data['change_ratio'] = round(result, 2)
            else:
                # Fallback: Direct calculation
                data['change_ratio'] = round(landuse.target_ha / landuse.status_ha, 2)
        except Exception as e:
            # Fallback on any error
            data['change_ratio'] = round(landuse.target_ha / landuse.status_ha, 2)
    
    return data

@login_required
def landuse_list(request):
    """Display all land use data with calculations done in web app"""
    landuses = LandUse.objects.all().order_by('code')
    latest_run = CalculationRun.objects.first()
    
    # Add calculations for each record (web app layer, not database)
    landuse_data = []
    for landuse in landuses:
        landuse_data.append(calculate_percentages(landuse))
    
    context = {
        'landuse_data': landuse_data,
        'total_count': landuses.count(),
        'current_section': 'landuse',
        'latest_run': latest_run,
    }
    return render(request, 'simulator/landuse_list.html', context)

@login_required
def landuse_detail(request, pk):
    """Display detailed view of a specific land use item"""
    landuse = LandUse.objects.get(pk=pk)
    data = calculate_percentages(landuse)
    
    # Also get children with calculations
    children_data = []
    for child in landuse.children.all():
        children_data.append(calculate_percentages(child))
    
    context = {
        'data': data,
        'children_data': children_data,
    }
    return render(request, 'simulator/landuse_detail.html', context)

def natural_sort_key(code):
    """
    Create a natural sorting key for codes like 1, 2, 3, ... 9, 10, 10.1, etc.
    Converts "10.1.2" to [10, 1, 2] for proper numerical sorting
    """
    import re
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(code))]

@login_required
def renewable_list(request):
    """Display all renewable energy data with hierarchical structure - using stored values for speed"""
    
    # Get all renewables from database - use stored values for fast page load
    renewables = list(RenewableData.objects.all())
    latest_run = CalculationRun.objects.first()
    run_id = request.GET.get("run_id")
    
    # Sort using natural sorting to get proper order: 1, 2, 3, ... 9, 10, 10.1
    renewables.sort(key=lambda x: natural_sort_key(x.code))
    
    # Preload formula keys to show which rows are calculated (for UI display only)
    formula_keys = set(
        Formula.objects.filter(category='renewable', is_active=True)
        .values_list('key', flat=True)
    )

    # Build hierarchical data structure for template
    hierarchical_data = []
    data_groups = {}
    
    for renewable in renewables:
        # Calculate hierarchy level based on code depth
        code_parts = renewable.code.split('.')
        hierarchy_level = len(code_parts)
        
        # Check if this row has formulas (for UI display only)
        has_status_formula = renewable.code in formula_keys
        has_target_formula = any(
            key in formula_keys
            for key in (f"{renewable.code}_target", f"{renewable.code}_ziel_target", f"{renewable.code}_ziel")
        )
        is_calculated = has_status_formula or has_target_formula

        # USE STORED VALUES for fast page load
        # Calculations are done by recalc buttons, not on page load
        display_value = renewable.status_value
        display_target = renewable.target_value
        
        # Build item for template
        item = {
            'code': renewable.code,
            'name': renewable.name,
            'unit': renewable.unit,
            'hierarchy_level': hierarchy_level,
            'display_value': display_value,
            'display_target': display_target,
            'calculated_value': display_value if is_calculated else None,
            'is_fixed': renewable.is_fixed,
            'parent_code': '.'.join(code_parts[:-1]) if len(code_parts) > 1 else None,
            'formula': renewable.formula,
            'landuse_source': renewable.landuse_code if hasattr(renewable, 'landuse_code') else None,
            'landuse_code': renewable.landuse_code if hasattr(renewable, 'landuse_code') else None,
        }
        hierarchical_data.append(item)
        
        # Group by category for summary
        category = code_parts[0]
        if category not in data_groups:
            data_groups[category] = []
        data_groups[category].append(renewable)
    
    context = {
        'hierarchical_data': hierarchical_data,
        'data_groups': data_groups,
        'total_count': len(renewables),
        'title': CategoryDisplayName.get_display_name('renewable'),  # Dynamic!
        'latest_run': latest_run,
        'run_id': run_id,
    }
    
    return render(request, 'simulator/renewable_list.html', context)

@login_required
def annual_electricity_view(request):
    """Annual electricity section using DB-driven formulas (category='annual')."""
    ws_consts = get_ws_constants()
    # NOTE: Auto-recalculation removed for faster page load.
    # Use "Recalculate WS Data" button on Renewable page or "Balance WS Storage" button here.
    diagram = compute_ws_diagram_reference()
    
    pv_value = diagram.get('pv_value', 0.0)
    wind_value = diagram.get('wind_value', 0.0)
    bio_value = diagram.get('bio_value', 0.0)
    hydro_value = diagram.get('hydro_value', 0.0)
    m_total = diagram.get('m_total', 0.0)
    ely_branch_value = diagram.get('ely_branch_value', 0.0)
    n_value = diagram.get('n_value', 0.0)
    n_input_branch = diagram.get('n_input_branch', 0.0)
    n_output_branch = diagram.get('n_output_branch', 0.0)
    gas_storage = diagram.get('gas_storage', 0.0)
    t_value = diagram.get('t_value', 0.0)
    t_output = diagram.get('t_output', 0.0)
    n_to_right = diagram.get('n_to_right', 0.0)
    final_stromnetz = diagram.get('final_stromnetz', 0.0)
    h2_offer = diagram.get('h2_offer', 0.0)
    h2_surplus = diagram.get('h2_surplus', 0.0)
    solarstrom_366 = diagram.get('solarstrom_366', 0.0)
    windstrom_366 = diagram.get('windstrom_366', 0.0)
    sonst_kraft_konstant_366 = diagram.get('sonst_kraft_konstant_366', 0.0)

    context = {
        'current_section': 'annual_electricity', 
        'title': 'Annual Electricity Analysis',
        'bio': round(bio_value, 2),
        'pv': round(pv_value, 2),
        'wind': round(wind_value, 2),
        'hydro': round(hydro_value, 2),
        'm_total': round(m_total, 2),
        'ely_branch_value': round(ely_branch_value, 2),
        'ely_offer': round(ely_branch_value, 2),
        'gasspeicher_direkt': round(ely_branch_value * ws_consts['ETA_STROM_GAS'], 2),
        'n_value': round(n_value, 2),
        'q_abregelung': round(diagram.get('q_abregelung', n_input_branch), 2),
        'n_input_branch': round(n_input_branch, 2),
        'n_output_branch': round(n_output_branch, 2),
        'ely_surplus': round(n_output_branch, 2),
        'n_to_right': round(n_to_right, 2),
        'h2_offer': round(h2_offer, 2),
        'h2_surplus': round(h2_surplus, 2),
        'gas_storage': round(gas_storage, 2),
        't_value': round(t_value, 2),
        't_output': round(t_output, 2),
        'final_stromnetz': round(final_stromnetz, 2),
        'n_input': round(n_input_branch, 2),
        'n_output': round(n_output_branch, 2),
        'h2_to_reconv': round(t_value, 2),
        'reconversion': round(t_output, 2),
        'final_consumption': round(final_stromnetz, 2),
        'ely_branch_value': round(ely_branch_value, 2),
        'solarstrom_366': round(solarstrom_366, 2),
        'windstrom_366': round(windstrom_366, 2),
        'sonst_kraft_konstant_366': round(sonst_kraft_konstant_366, 2),
    }
    
    return render(request, 'simulator/annual_electricity.html', context)

@login_required 
def cockpit_view(request):
    """
    Cockpit dashboard with dynamic bar charts showing energy balance by sector.
    All data comes from bilanz_engine calculation module.
    """
    # Import the bilanz calculation engine
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from calculation_engine.bilanz_engine import calculate_bilanz_data
    
    try:
        # Get all bilanz data from the calculation engine (fully dynamic)
        bilanz_data = calculate_bilanz_data()
        
        # Helper function to safely get nested values
        def safe_get(data, *keys, default=0):
            """Safely traverse nested dictionary"""
            try:
                result = data
                for key in keys:
                    result = result[key]
                return result if result is not None else default
            except (KeyError, TypeError):
                return default
        
        # Extract and flatten data for template
        context = {
            'current_section': 'cockpit',
            
            # STATUS VALUES (current)
            # Total consumption by sector
            'verbrauch_endenergie_gesamt': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'gesamt'),
            'verbrauch_endenergie_klik': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'kraft_licht'),
            'verbrauch_endenergie_gebaeudewaerme': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'gebaeudewaerme'),
            'verbrauch_endenergie_prozesswaerme': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'prozesswaerme'),
            'verbrauch_endenergie_mobile': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'mobile'),
            
            # Electricity (Strom)
            'strom_total': safe_get(bilanz_data, 'verbrauch_strom', 'status', 'gesamt'),
            'strom_renewable': safe_get(bilanz_data, 'verbrauch_strom_renewable', 'status', 'gesamt'),
            'strom_fossil': safe_get(bilanz_data, 'verbrauch_strom_fossil', 'status', 'gesamt'),
            
            # Fuels (Brennstoffe)
            'brennstoffe_total': safe_get(bilanz_data, 'verbrauch_fuels', 'status', 'gesamt'),
            'brennstoffe_renewable': safe_get(bilanz_data, 'verbrauch_fuels_renewable', 'status', 'gesamt'),
            'brennstoffe_fossil': safe_get(bilanz_data, 'verbrauch_fuels_fossil', 'status', 'gesamt'),
            
            # Fuel type breakdown
            'brennstoffe_gaseous': safe_get(bilanz_data, 'fuels_breakdown', 'status', 'gaseous'),
            'brennstoffe_liquid': safe_get(bilanz_data, 'fuels_breakdown', 'status', 'liquid'),
            'brennstoffe_solid': safe_get(bilanz_data, 'fuels_breakdown', 'status', 'solid'),
            
            # Heat (Wärme)
            'waerme_total': safe_get(bilanz_data, 'verbrauch_heat', 'status', 'gesamt'),
            'waerme_renewable': safe_get(bilanz_data, 'verbrauch_heat_renewable', 'status', 'gesamt'),
            'waerme_fossil': safe_get(bilanz_data, 'verbrauch_heat_fossil', 'status', 'gesamt'),

            # Precise Renewable by Sector (Status)
            'renewable_klik': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'kraft_licht'),
            'renewable_gebaeudewaerme': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'gebaeudewaerme'),
            'renewable_prozesswaerme': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'prozesswaerme'),
            'renewable_mobile': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'mobile'),
            
            # ZIEL VALUES (target)
            # Total consumption by sector
            'verbrauch_endenergie_gesamt_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'gesamt'),
            'verbrauch_endenergie_klik_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'kraft_licht'),
            'verbrauch_endenergie_gebaeudewaerme_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'gebaeudewaerme'),
            'verbrauch_endenergie_prozesswaerme_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'prozesswaerme'),
            'verbrauch_endenergie_mobile_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'mobile'),
            
            # Electricity (Strom) - Ziel
            'strom_total_ziel': safe_get(bilanz_data, 'verbrauch_strom', 'ziel', 'gesamt'),
            'strom_renewable_ziel': safe_get(bilanz_data, 'verbrauch_strom_renewable', 'ziel', 'gesamt'),
            'strom_fossil_ziel': safe_get(bilanz_data, 'verbrauch_strom_fossil', 'ziel', 'gesamt'),
            
            # Fuels (Brennstoffe) - Ziel
            'brennstoffe_total_ziel': safe_get(bilanz_data, 'verbrauch_fuels', 'ziel', 'gesamt'),
            'brennstoffe_renewable_ziel': safe_get(bilanz_data, 'verbrauch_fuels_renewable', 'ziel', 'gesamt'),
            'brennstoffe_fossil_ziel': safe_get(bilanz_data, 'verbrauch_fuels_fossil', 'ziel', 'gesamt'),
            
            # Fuel type breakdown - Ziel
            'brennstoffe_gaseous_ziel': safe_get(bilanz_data, 'fuels_breakdown', 'ziel', 'gaseous'),
            'brennstoffe_liquid_ziel': safe_get(bilanz_data, 'fuels_breakdown', 'ziel', 'liquid'),
            'brennstoffe_solid_ziel': safe_get(bilanz_data, 'fuels_breakdown', 'ziel', 'solid'),
            
            # Heat (Wärme) - Ziel
            'waerme_total_ziel': safe_get(bilanz_data, 'verbrauch_heat', 'ziel', 'gesamt'),
            'waerme_renewable_ziel': safe_get(bilanz_data, 'verbrauch_heat_renewable', 'ziel', 'gesamt'),
            'waerme_fossil_ziel': safe_get(bilanz_data, 'verbrauch_heat_fossil', 'ziel', 'gesamt'),

            # Precise Renewable by Sector (Ziel)
            'renewable_klik_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'kraft_licht'),
            'renewable_gebaeudewaerme_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'gebaeudewaerme'),
            'renewable_prozesswaerme_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'prozesswaerme'),
            'renewable_mobile_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'mobile'),
        }
        
        return render(request, 'simulator/cockpit.html', context)
        
    except Exception as e:
        # If there's any error, return error page with details
        import traceback
        return render(request, 'simulator/cockpit.html', {
            'current_section': 'cockpit',
            'error': str(e),
            'traceback': traceback.format_exc(),
            # Default zero values for all fields
            'verbrauch_endenergie_gesamt': 0,
            'verbrauch_endenergie_klik': 0,
            'verbrauch_endenergie_gebaeudewaerme': 0,
            'verbrauch_endenergie_prozesswaerme': 0,
            'verbrauch_endenergie_mobile': 0,
            'strom_total': 0,
            'strom_renewable': 0,
            'strom_fossil': 0,
            'brennstoffe_total': 0,
            'brennstoffe_renewable': 0,
            'brennstoffe_fossil': 0,
            'brennstoffe_gaseous': 0,
            'brennstoffe_liquid': 0,
            'brennstoffe_solid': 0,
            'waerme_total': 0,
            'waerme_renewable': 0,
            'waerme_fossil': 0,
            'verbrauch_endenergie_gesamt_ziel': 0,
            'verbrauch_endenergie_klik_ziel': 0,
            'verbrauch_endenergie_gebaeudewaerme_ziel': 0,
            'verbrauch_endenergie_prozesswaerme_ziel': 0,
            'verbrauch_endenergie_mobile_ziel': 0,
            'strom_total_ziel': 0,
            'strom_renewable_ziel': 0,
            'strom_fossil_ziel': 0,
            'brennstoffe_total_ziel': 0,
            'brennstoffe_renewable_ziel': 0,
            'brennstoffe_fossil_ziel': 0,
            'brennstoffe_gaseous_ziel': 0,
            'brennstoffe_liquid_ziel': 0,
            'brennstoffe_solid_ziel': 0,
            'waerme_total_ziel': 0,
            'waerme_renewable_ziel': 0,
            'waerme_fossil_ziel': 0,
        })


def cockpit_view_old(request):
    """OLD VERSION - kept for reference"""
    import json
    
    # Helper function to get values with fallback
    def safe_get_values(obj, is_renewable=False):
        """Get status and target values safely"""
        try:
            if is_renewable:
                status, target = obj.get_calculated_values()
                return (status or 0, target or 0)
            else:
                # Get all energy types
                status_strom = obj.get_effective_strom_value()
                status_gas = obj.get_effective_brennstoffe_gasfoermig_value()
                status_liquid = obj.get_effective_brennstoffe_fluessig_value()
                status_solid = obj.get_effective_brennstoffe_fest_value()
                status_heat = obj.get_effective_waerme_value()
                
                target_strom = obj.get_effective_strom_ziel_value()
                target_gas = obj.get_effective_brennstoffe_gasfoermig_ziel_value()
                target_liquid = obj.get_effective_brennstoffe_fluessig_ziel_value()
                target_solid = obj.get_effective_brennstoffe_fest_ziel_value()
                target_heat = obj.get_effective_waerme_ziel_value()
                
                status_total = status_strom + status_gas + status_liquid + status_solid + status_heat
                target_total = target_strom + target_gas + target_liquid + target_solid + target_heat
                
                return (status_total, target_total)
        except Exception as e:
            print(f"Error in safe_get_values: {e}")
            return (0, 0)
    
    # Get Verbrauch data by category
    categories_data = {
        'status': {},
        'ziel': {}
    }
    
    # KLIK (Kraft/Licht/Kälte)
    try:
        klik = VerbrauchData.objects.get(code='1.4')
        klik_s, klik_t = safe_get_values(klik)
        categories_data['status']['KLIK'] = klik_s
        categories_data['ziel']['KLIK'] = klik_t
    except Exception as e:
        print(f"KLIK error: {e}")
        categories_data['status']['KLIK'] = 0
        categories_data['ziel']['KLIK'] = 0
    
    # Gebäudewärme
    try:
        gw = VerbrauchData.objects.get(code='2.9.0')
        gw_s, gw_t = safe_get_values(gw)
        categories_data['status']['Gebäudewärme'] = gw_s
        categories_data['ziel']['Gebäudewärme'] = gw_t
    except Exception as e:
        print(f"Gebäudewärme error: {e}")
        categories_data['status']['Gebäudewärme'] = 0
        categories_data['ziel']['Gebäudewärme'] = 0
    
    # Prozesswärme
    try:
        pw = VerbrauchData.objects.get(code='3.6.0')
        pw_s, pw_t = safe_get_values(pw)
        categories_data['status']['Prozesswärme'] = pw_s
        categories_data['ziel']['Prozesswärme'] = pw_t
    except Exception as e:
        print(f"Prozesswärme error: {e}")
        categories_data['status']['Prozesswärme'] = 0
        categories_data['ziel']['Prozesswärme'] = 0
    
    # Mobile Anwendungen
    try:
        mobile = VerbrauchData.objects.get(code='4.3.6')
        mobile_s, mobile_t = safe_get_values(mobile)
        categories_data['status']['Mobile'] = mobile_s
        categories_data['ziel']['Mobile'] = mobile_t
    except Exception as e:
        print(f"Mobile error: {e}")
        categories_data['status']['Mobile'] = 0
        categories_data['ziel']['Mobile'] = 0
    
    # Get renewable data
    try:
        renewable = RenewableData.objects.get(code='10')
        ren_s, ren_t = safe_get_values(renewable, is_renewable=True)
        categories_data['status']['Erneuerbar'] = ren_s
        categories_data['ziel']['Erneuerbar'] = ren_t
    except Exception as e:
        print(f"Renewable error: {e}")
        categories_data['status']['Erneuerbar'] = 0
        categories_data['ziel']['Erneuerbar'] = 0
    
    # Calculate totals
    total_verbrauch_status = sum([v for k, v in categories_data['status'].items() if k != 'Erneuerbar'])
    total_verbrauch_ziel = sum([v for k, v in categories_data['ziel'].items() if k != 'Erneuerbar'])
    
    # Add fossil for comparison
    categories_data['status']['Fossil'] = total_verbrauch_status - categories_data['status']['Erneuerbar']
    categories_data['ziel']['Fossil'] = total_verbrauch_ziel - categories_data['ziel']['Erneuerbar']
    
    context = {
        'current_section': 'cockpit',
        'title': 'Energieverbrauch Dashboard',
        'graph_data': categories_data,
        'graph_data_json': json.dumps(categories_data)
    }
    return render(request, 'simulator/cockpit.html', context)

@login_required
@login_required
@require_http_methods(["POST"])
def update_user_percent(request):
    """API endpoint to save user percentage input for land use data"""
    try:
        data = json.loads(request.body)
        code = data.get('code')
        user_percent = data.get('user_percent')
        
        if not code:
            return JsonResponse({'success': False, 'error': 'Code is required'})
            
        # Get the land use record (with parent for target calc)
        landuse = get_object_or_404(LandUse.objects.select_related('parent'), code=code)

        # Update user_percent (allow None/empty for clearing)
        if user_percent == '' or user_percent is None:
            landuse.user_percent = None
        else:
            try:
                percent_val = float(user_percent)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid percentage value'})

            # ===================================================================
            # VALIDATION: Prevent excessive land use increases (percentage points)
            # ===================================================================
            from django.conf import settings
            MAX_INCREASE_PERCENTAGE_POINTS = getattr(settings, 'LANDUSE_MAX_INCREASE_PERCENT', 3)
            
            # Use existing user_percent OR calculate from target_ha if user_percent not set
            if landuse.user_percent is not None:
                current_percent = landuse.user_percent
            elif landuse.parent and landuse.parent.target_ha and landuse.target_ha:
                # Calculate current percentage from target_ha
                current_percent = (landuse.target_ha / landuse.parent.target_ha * 100) if landuse.parent.target_ha > 0 else 0
            else:
                current_percent = 0
            
            if current_percent > 0:
                percentage_point_change = percent_val - current_percent
                
                if percentage_point_change > MAX_INCREASE_PERCENTAGE_POINTS:
                    max_allowed_value = current_percent + MAX_INCREASE_PERCENTAGE_POINTS
                    return JsonResponse({
                        'success': False,
                        'error': f"⚠️ Cannot increase by more than {MAX_INCREASE_PERCENTAGE_POINTS} percentage points.\n\n"
                                f"Current: {current_percent:.2f}%\n"
                                f"Requested: {percent_val:.2f}%\n"
                                f"Increase: {percentage_point_change:.2f} points\n"
                                f"Maximum allowed: {max_allowed_value:.2f}%",
                        'current_value': float(current_percent),
                        'max_allowed_value': float(max_allowed_value),
                    })

            # Auto-unlock if locked (user edits should always be allowed)
            if landuse.target_locked:
                landuse.target_locked = False

            # Recalculate target_ha from parent target (if available)
            parent_target = landuse.parent.target_ha if landuse.parent else None
            if parent_target is not None:
                landuse.target_ha = (parent_target * percent_val) / 100.0

            landuse.user_percent = percent_val

        landuse.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Saved {code}: {landuse.user_percent}%',
            'code': code,
            'user_percent': landuse.user_percent,
            'target_ha': landuse.target_ha,
        })
        
    except LandUse.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'Land use code {code} not found'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def save_all_user_inputs(request):
    """
    API endpoint to save all user input values at once.
    FIXED: Uses model save() to trigger signals for auto-cascade.
    Only the LAST save triggers the full cascade to avoid redundant recalcs.
    NOW TRACKS: old → new values for frontend display
    """
    try:
        data = json.loads(request.body)
        user_inputs = data.get('user_inputs', {})
        
        saved_count = 0
        skipped_locked = 0
        errors = []
        changes = []  # Track old → new values
        
        items_to_save = []
        
        # First pass: prepare all updates
        from django.conf import settings
        MAX_INCREASE_PERCENTAGE_POINTS = getattr(settings, 'LANDUSE_MAX_INCREASE_PERCENT', 3)
        
        for code, percent in user_inputs.items():
            try:
                if percent == '' or percent is None:
                    continue
                    
                percent_val = float(percent)
                
                # Get parent target_ha to calculate new target_ha
                landuse = LandUse.objects.select_related('parent').get(code=code)
                
                # ===================================================================
                # VALIDATION: Prevent excessive land use increases (percentage points)
                # ===================================================================
                # Use existing user_percent OR calculate from target_ha if user_percent not set
                if landuse.user_percent is not None:
                    current_percent = landuse.user_percent
                elif landuse.parent and landuse.parent.target_ha and landuse.target_ha:
                    # Calculate current percentage from target_ha
                    current_percent = (landuse.target_ha / landuse.parent.target_ha * 100) if landuse.parent.target_ha > 0 else 0
                else:
                    current_percent = 0
                
                if current_percent > 0:
                    percentage_point_change = percent_val - current_percent
                    
                    if percentage_point_change > MAX_INCREASE_PERCENTAGE_POINTS:
                        max_allowed_value = current_percent + MAX_INCREASE_PERCENTAGE_POINTS
                        errors.append(
                            f"❌ {code}: Cannot increase by {percentage_point_change:.2f} points "
                            f"(max {MAX_INCREASE_PERCENTAGE_POINTS}). Current: {current_percent:.2f}%, "
                            f"Max allowed: {max_allowed_value:.2f}%"
                        )
                        continue  # Skip this item
                # ===================================================================
                
                # Auto-unlock if locked (user edits should always be allowed)
                if landuse.target_locked:
                    landuse.target_locked = False
                
                # Store old values for change tracking
                old_target_ha = landuse.target_ha
                old_user_percent = landuse.user_percent
                
                if landuse.parent and landuse.parent.target_ha:
                    new_target_ha = (landuse.parent.target_ha * percent_val) / 100.0
                else:
                    new_target_ha = landuse.target_ha  # Keep existing if no parent
                
                landuse.user_percent = percent_val
                landuse.target_ha = new_target_ha
                
                # Track the change
                changes.append({
                    'code': code,
                    'name': landuse.name,
                    'old_percent': round(old_user_percent, 2) if old_user_percent else None,
                    'new_percent': round(percent_val, 2),
                    'old_ha': round(old_target_ha, 2) if old_target_ha else None,
                    'new_ha': round(new_target_ha, 2),
                    'change_ha': round(new_target_ha - old_target_ha, 2) if old_target_ha else None
                })
                
                items_to_save.append(landuse)
                saved_count += 1
                
            except LandUse.DoesNotExist:
                errors.append(f'Code {code} not found')
            except (ValueError, TypeError):
                errors.append(f'Invalid value for {code}: {percent}')
            except Exception as e:
                errors.append(f'Error saving {code}: {str(e)}')
        
        # Second pass: save all items, only LAST one triggers cascade
        for i, landuse in enumerate(items_to_save):
            is_last = (i == len(items_to_save) - 1)
            if is_last:
                # Last item - let signals fire to trigger cascade
                landuse.save()  # NO skip_cascade
            else:
                # Not last - skip cascade to avoid redundant recalcs
                landuse.save(skip_cascade=True)
        
        return JsonResponse({
            'success': True,
            'saved_count': saved_count,
            'skipped_locked': skipped_locked,
            'errors': errors,
            'changes': changes,  # Include changes for frontend display
            'message': f'Saved {saved_count} values - renewables auto-updated' + (f' with {len(errors)} errors' if errors else '')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# PROPER RECURSIVE CASCADE LOGIC - EXACT IMPLEMENTATION
def update_downwards(node, new_percent, total_area):
    """Recursive downward update: parent drives children proportionally"""
    node.user_percent = new_percent
    node.user_ha = total_area * (new_percent / 100)
    node.save()
    
    print(f"📊 Updated {node.code}: {new_percent}% = {node.user_ha:.2f}ha")

    children = node.children.all()
    if not children:
        return

    total_target = sum(child.target_ha for child in children)
    for child in children:
        ratio = child.target_ha / total_target if total_target > 0 else 0
        child_percent = (node.user_ha * ratio / total_area) * 100
        print(f"🔄 Cascading to {child.code}: ratio={ratio:.3f}, new_percent={child_percent:.2f}%")
        update_downwards(child, child_percent, total_area)


def update_upwards(node, total_area):
    """Recursive upward update: children drive parent by summing"""
    parent = node.parent
    if not parent:
        return
    
    parent.user_ha = sum(c.user_ha for c in parent.children.all())
    parent.user_percent = (parent.user_ha / total_area) * 100
    parent.save()
    
    print(f"⬆️ Updated parent {parent.code}: {parent.user_percent:.2f}% = {parent.user_ha:.2f}ha (sum of children)")

    update_upwards(parent, total_area)  # climb upwards


# MASTER UPDATE FUNCTION - EXACT IMPLEMENTATION
def update_node(node, new_percent, total_area):
    """Master function: determines update direction based on node type"""
    if node.children.exists():  # parent node changed
        update_downwards(node, new_percent, total_area)
    else:  # leaf node changed
        node.user_percent = new_percent
        node.user_ha = total_area * (new_percent / 100)
        node.save()
        update_upwards(node, total_area)


@csrf_exempt  
@require_http_methods(["POST"])
def update_user_percent(request, code):
    """API endpoint to update user_percent with proper hierarchical cascading"""
    try:
        node = get_object_or_404(LandUse, code=code)
        new_percent = float(request.POST.get("user_percent", 0))
        
        # Get total area from root node
        root_node = LandUse.objects.get(code="0")
        total_area = root_node.status_ha
        
        print(f"\n{'='*50}")
        print(f"🚀 API CALL: Updating {code} = {new_percent}%")
        print(f"📍 Total area: {total_area:.2f}ha")
        
        # Use master update function
        update_node(node, new_percent, total_area)
        
        # Determine message based on node type
        if node.children.exists():
            message = f"Updated parent {code} and cascaded downwards to {node.children.count()} children"
        else:
            message = f"Updated leaf {code} and cascaded upwards to parents"
            
        print(f"✅ {message}")
        print(f"{'='*50}\n")
        
        return JsonResponse({
            'success': True, 
            'message': message,
            'code': code,
            'user_percent': new_percent
        })
        
    except LandUse.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'LandUse with code {code} not found'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid user_percent value'})
    except Exception as e:
        print(f"❌ Error updating {code}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def verbrauch_view(request):
    """Energy Consumption Data (Verbrauch) - FRESH calculated values from database"""
    from .models import VerbrauchData, RenewableData, LandUse
    from django.db import connection
    
    # Force fresh database read (clear any Django query cache)
    connection.queries_log.clear() if hasattr(connection, 'queries_log') else None
    
    # Get all verbrauch data from database - force fresh query
    verbrauch_data = VerbrauchData.objects.all().order_by('code')
    
    # Convert to list of dictionaries with natural sorting
    temp_data = []
    for item in verbrauch_data:
        # Force refresh from database
        item.refresh_from_db()
        
        # Use stored database values directly (already updated by cascade)
        display_status = item.status
        display_ziel = item.ziel
        
        # Special case: FC-Traktion alternative entries show "Aktiv" or "(Passiv)" based on user_percent
        if "Alternativ zur" in item.category and "Brennstoffzellen (FC)" in item.category:
            from django.utils.safestring import mark_safe
            if item.user_percent == 100.0:
                display_ziel = mark_safe('<span style="color: blue; font-weight: bold;">Aktiv</span>')
            else:
                display_ziel = mark_safe('<span style="color: green; font-weight: bold;">(Passiv)</span>')
        
        # Don't show user_percent for calculated fields - they should be empty
        show_user_percent = item.user_percent if not item.is_calculated else None
        
        # Calculated fields should never be user_editable
        is_user_editable = item.user_editable and not item.is_calculated
        
        temp_data.append({
            'code': item.code,
            'category': item.category,
            'unit': item.unit,
            'status': display_status,
            'ziel': display_ziel,
            'user_percent': show_user_percent,  # Empty for calculated fields
            'is_calculated': item.is_calculated,
            'user_editable': is_user_editable,  # Never editable if calculated
        })
    
    # Apply natural sorting (same as renewable energy)
    def natural_sort_key(item):
        """Natural sorting for hierarchical codes like 1, 1.1, 1.1.1, 1.2, etc."""
        parts = item['code'].split('.')
        return [int(part) for part in parts]
    
    temp_data.sort(key=natural_sort_key)
    
    # Define category headings to be injected (these replace the blue section headers)
    # Format: (code, category_name) - will be inserted before first item with that code prefix
    # Note: 7 and 8 are calculated totals, not section headings
    category_headings = {
        '1': 'Kraft, Licht, Information, Kommunikation, Kälte (KLIK)',
        '2': 'Gebäudewärme (GW)',
        '3': 'Prozesswärme (PW)',
        '4': 'Mobile Anwendungen (MA)',
        '5': 'MA Luftverkehr',
        '6': 'Endenergieverbrauch MA gesamt',
        '9': 'Grundstoff-Synthetisierung',
        '10': 'Fossil',
    }
    
    # Track which category headings have been added
    added_categories = set()
    
    # Process data - NO blue section headers, just category heading rows
    data = []
    
    for item in temp_data:
        code = item['code']
        
        # Check if we need to insert a category heading row
        # Get the major category (first part before any dot)
        major_category = code.split('.')[0]
        
        # Insert category heading row before first item of each major category
        if major_category in category_headings and major_category not in added_categories:
            data.append({
                'is_section_header': False,
                'is_category_heading': True,
                'code': major_category,
                'category': category_headings[major_category],
                'unit': '',
                'status': None,
                'ziel': None,
                'user_percent': None,
                'is_calculated': False,
                'user_editable': False,
            })
            added_categories.add(major_category)
        
        # Skip rows that are just the major category code (e.g., "1", "2", "4", "7", "8", "9", "10")
        # But keep sub-items like "1.1", "2.0", "3.0", "5.0", "6.0", etc.
        if code in category_headings and '.' not in code:
            continue  # Skip - the heading already covers this
        
        # Mark as not a section header (no blue rows)
        item['is_section_header'] = False
        item['is_category_heading'] = False
        data.append(item)
    
    return render(request, 'simulator/verbrauch.html', {"data": data})


@require_http_methods(["POST"])
def save_and_recalculate_verbrauch(request):
    """Recalculate ALL Verbrauch values using fresh database data"""
    from .models import VerbrauchData
    from django.http import JsonResponse
    import json
    
    try:
        # Get ALL calculated items ordered by hierarchy (deepest first)
        def get_hierarchy_level(code):
            return code.count('.')
        
        calculated_items = list(VerbrauchData.objects.filter(is_calculated=True))
        calculated_items.sort(key=lambda x: get_hierarchy_level(x.code), reverse=True)
        
        updated_count = 0
        
        # Recalculate EVERY calculated item using fresh database
        for item in calculated_items:
            try:
                # Force fresh read from database
                item.refresh_from_db()
                
                # Calculate new values
                new_status = item.calculate_value()
                new_ziel = item.calculate_ziel_value()
                
                # Always update regardless of whether value changed
                if new_status is not None:
                    item.status = new_status
                if new_ziel is not None:
                    item.ziel = new_ziel
                
                # Save without cascade
                item.save(skip_cascade=True)
                updated_count += 1
                
            except Exception as e:
                print(f"Error recalculating {item.code}: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Recalculated ALL {updated_count} calculated values',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def gebaeudewaerme_view(request):
    """Building Heat Data (Gebäudewärme) - Load from database"""
    from .models import GebaeudewaermeData
    
    # Get all building heat data from database
    gebaeudewaerme_data = GebaeudewaermeData.objects.all()
    
    # Convert to list of dictionaries with natural sorting
    data = []
    for item in gebaeudewaerme_data:
        # For now, just show database values (calculations will be implemented later)
        if item.is_calculated:
            # For calculated items, use separate calculations for status and ziel when implemented
            display_status = item.calculate_value() or None  # Will be None until formulas implemented
            display_ziel = item.calculate_ziel_value() or None  # Will be None until formulas implemented
        else:
            # For fixed items, show database values
            display_status = item.status
            display_ziel = item.ziel
        
        # Special case: FC-Traktion alternative entries show "Aktiv" or "(Passiv)" based on user_percent
        if "Alternativ zur" in item.category and "Brennstoffzellen (FC)" in item.category:
            from django.utils.safestring import mark_safe
            if item.user_percent == 100.0:
                display_ziel = mark_safe('<span style="color: blue; font-weight: bold;">Aktiv</span>')
            else:
                display_ziel = mark_safe('<span style="color: green; font-weight: bold;">(Passiv)</span>')
        
        data.append({
            'code': item.code,
            'category': item.category,
            'unit': item.unit,
            'status': display_status,
            'ziel': display_ziel,
            'formula': item.formula,
            'user_percent': item.user_percent,
            'is_calculated': item.is_calculated,
        })
    
    # Apply natural sorting (same as other modules)
    def natural_sort_key(item):
        """Natural sorting for hierarchical codes like 2.0, 2.1, 2.1.1, 2.2, etc."""
        parts = item['code'].split('.')
        return [int(part) for part in parts]
    
    data.sort(key=natural_sort_key)
    
    return render(request, 'simulator/gebaeudewaerme.html', {"data": data})


def smard_solar_wind(request):
    """SMARD data visualization for solar and wind energy"""
    # 1️⃣ Find your CSV file
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Actual_generation_202302010000_202401010000_Hour.csv')

    # 2️⃣ Read the CSV (SMARD format)
    df = pd.read_csv(file_path, sep=';', decimal=',')

    # 3️⃣ Clean and select energy sources
    df = df.replace('-', 0)
    
    # Convert German number format to float
    def convert_to_float(value):
        if value == 0 or value == '0':  # Already replaced '-' with 0
            return 0.0
        if isinstance(value, str):
            # German format: 1.721,00 -> English format: 1721.00
            # Remove thousand separators (dots) and replace decimal comma with dot
            value = value.replace('.', '').replace(',', '.')
            return float(value)
        return float(value)
    
    # Convert all energy columns to float
    energy_columns = [
        'Photovoltaics [MWh] Calculated resolutions',
        'Wind onshore [MWh] Calculated resolutions', 
        'Wind offshore [MWh] Calculated resolutions',
        'Hydropower [MWh] Calculated resolutions',
        'Biomass [MWh] Calculated resolutions',
        'Nuclear [MWh] Calculated resolutions',
        'Lignite [MWh] Calculated resolutions',
        'Hard coal [MWh] Calculated resolutions',
        'Fossil gas [MWh] Calculated resolutions'
    ]
    
    for col in energy_columns:
        df[col] = df[col].apply(convert_to_float)

    # Calculate combined values
    df['wind_total_MWh'] = df['Wind onshore [MWh] Calculated resolutions'] + df['Wind offshore [MWh] Calculated resolutions']
    df['total_demand_MWh'] = (df['Photovoltaics [MWh] Calculated resolutions'] + 
                              df['wind_total_MWh'] + 
                              df['Hydropower [MWh] Calculated resolutions'] +
                              df['Biomass [MWh] Calculated resolutions'] +
                              df['Nuclear [MWh] Calculated resolutions'] +
                              df['Lignite [MWh] Calculated resolutions'] +
                              df['Hard coal [MWh] Calculated resolutions'] +
                              df['Fossil gas [MWh] Calculated resolutions'])

    # 4️⃣ Group by day and sum hourly values to get daily totals (MWh/day)
    df['Date'] = pd.to_datetime(df['Start date'])
    df['day'] = df['Date'].dt.date
    
    daily = df.groupby('day').agg({
        'Photovoltaics [MWh] Calculated resolutions': 'sum',
        'wind_total_MWh': 'sum',
        'Hydropower [MWh] Calculated resolutions': 'sum',
        'Biomass [MWh] Calculated resolutions': 'sum',
        'total_demand_MWh': 'sum'
    }).reset_index()

    # 5️⃣ Rename columns with proper units and SMARD designation
    daily = daily.rename(columns={
        'day': 'date',
        'Photovoltaics [MWh] Calculated resolutions': 'solar_smard_MWh',
        'wind_total_MWh': 'wind_smard_MWh',
        'Hydropower [MWh] Calculated resolutions': 'hydro_MWh',
        'Biomass [MWh] Calculated resolutions': 'bio_MWh',
        'total_demand_MWh': 'demand_MWh'
    })
    
    # PART A — Build the scenario generation curve from SMARD + totals
    # 1) Data is already aggregated to daily
    
    # 2) Create the shape (normalize) - per-unit curves
    # Using sum (not max) to keep energy-weighted shape
    solar_total = daily['solar_smard_MWh'].sum()
    wind_total = daily['wind_smard_MWh'].sum()
    hydro_total = daily['hydro_MWh'].sum()
    bio_total = daily['bio_MWh'].sum()
    demand_total = daily['demand_MWh'].sum()
    
    # Create normalized per-unit curves
    daily['solar_pu'] = daily['solar_smard_MWh'] / solar_total if solar_total > 0 else 0
    daily['wind_pu'] = daily['wind_smard_MWh'] / wind_total if wind_total > 0 else 0
    daily['hydro_pu'] = daily['hydro_MWh'] / hydro_total if hydro_total > 0 else 0
    daily['bio_pu'] = daily['bio_MWh'] / bio_total if bio_total > 0 else 0
    daily['demand_pu'] = daily['demand_MWh'] / demand_total if demand_total > 0 else 0
    
    # Add totals for reference
    daily['solar_total_GWh'] = solar_total / 1000  # Convert to GWh
    daily['wind_total_GWh'] = wind_total / 1000
    daily['hydro_total_GWh'] = hydro_total / 1000
    daily['bio_total_GWh'] = bio_total / 1000
    daily['demand_total_GWh'] = demand_total / 1000
    
    # 3) Scale each shape to scenario annual totals (from Renewable data)
    # Get target values from your Renewable data model
    try:
        from .models import RenewableData
        
        # Get scenario targets - looking for specific renewable codes
        pv_target_record = RenewableData.objects.filter(code__icontains='solar').first() or \
                          RenewableData.objects.filter(code__icontains='photovoltaic').first() or \
                          RenewableData.objects.filter(code__icontains='pv').first()
        
        wind_target_record = RenewableData.objects.filter(code__icontains='wind').first()
        
        hydro_target_record = RenewableData.objects.filter(code__icontains='hydro').first() or \
                             RenewableData.objects.filter(code__icontains='water').first()
        
        bio_target_record = RenewableData.objects.filter(code__icontains='bio').first() or \
                           RenewableData.objects.filter(code__icontains='biomass').first()
        
        # Extract target values (assuming they're in GWh/a)
        if not pv_target_record:
            raise ValueError("PV target record not found in database. Please import renewable data.")
        if not wind_target_record:
            raise ValueError("Wind target record not found in database. Please import renewable data.")
        if not hydro_target_record:
            raise ValueError("Hydro target record not found in database. Please import renewable data.")
        if not bio_target_record:
            raise ValueError("Bio target record not found in database. Please import renewable data.")
            
        PV_target_GWh = float(pv_target_record.ziel or pv_target_record.status or 0)
        Wind_target_GWh = float(wind_target_record.ziel or wind_target_record.status or 0)
        Hydro_target_GWh = float(hydro_target_record.ziel or hydro_target_record.status or 0)
        Bio_target_GWh = float(bio_target_record.ziel or bio_target_record.status or 0)
        
    except Exception as e:
        # No fallbacks - database must have proper data
        print(f"ERROR: Renewable targets not found in database: {e}")
        raise ValueError(f"Database missing renewable energy data. Please import data first. Error: {e}")
        Bio_target_GWh = 30.0    # Example target
    
    # Convert annual targets from GWh/a to MWh/a
    PV_target_MWh = PV_target_GWh * 1000
    Wind_target_MWh = Wind_target_GWh * 1000  
    Hydro_target_MWh = Hydro_target_GWh * 1000
    Bio_target_MWh = Bio_target_GWh * 1000
    
    # Distribute targets over the year using the normalized shapes
    daily['solar_scenario_MWh_day'] = daily['solar_pu'] * PV_target_MWh
    daily['wind_scenario_MWh_day'] = daily['wind_pu'] * Wind_target_MWh
    daily['hydro_scenario_MWh_day'] = Hydro_target_MWh / 365  # Constant daily
    daily['bio_scenario_MWh_day'] = daily['bio_pu'] * Bio_target_MWh  # Follow historical pattern
    
    # 4) Sum to total renewable scenario (per day)
    daily['ren_total_MWh_day'] = (daily['solar_scenario_MWh_day'] + 
                                  daily['wind_scenario_MWh_day'] + 
                                  daily['hydro_scenario_MWh_day'] + 
                                  daily['bio_scenario_MWh_day'])
    
    # Quick check: sum(ren_total_MWh_day) ≈ (PV + Wind + Hydro + Bio) targets (in MWh)
    calculated_total_MWh = daily['ren_total_MWh_day'].sum()
    expected_total_MWh = PV_target_MWh + Wind_target_MWh + Hydro_target_MWh + Bio_target_MWh
    daily['calculated_total_GWh'] = calculated_total_MWh / 1000
    daily['expected_total_GWh'] = expected_total_MWh / 1000
    daily['total_check_diff_percent'] = ((calculated_total_MWh - expected_total_MWh) / expected_total_MWh * 100) if expected_total_MWh > 0 else 0
    
    # Add scenario targets for reference
    daily['PV_target_GWh'] = PV_target_GWh
    daily['Wind_target_GWh'] = Wind_target_GWh
    daily['Hydro_target_GWh'] = Hydro_target_GWh
    daily['Bio_target_GWh'] = Bio_target_GWh
    
    # PART B — Create WS.2a "segmentiert" curve (Excel's trick)
    # 5) Make the segmentiert ordering
    # Excel WS.2a sorts days by renewable total (highest → lowest)
    # Create two equally sorted arrays: both sorted descending
    
    # Sort renewable generation by descending order (highest first)
    ren_sorted = daily['ren_total_MWh_day'].sort_values(ascending=False).reset_index(drop=True)
    
    # Use YOUR ACTUAL DEMAND from VerbrauchData instead of SMARD historical demand
    # Get total electricity consumption from VerbrauchData (Code 5)
    try:
        from .models import VerbrauchData
        electricity_total_entry = VerbrauchData.objects.filter(code='5').first()  # Total electricity consumption
        
        if electricity_total_entry:
            # Uses calculation_engine/verbrauch_engine.py with database formulas for all calculations
            if electricity_total_entry.is_calculated:
                verbrauch_status_GWh = electricity_total_entry.calculate_value()
                verbrauch_ziel_GWh = electricity_total_entry.calculate_ziel_value()
            else:
                verbrauch_status_GWh = electricity_total_entry.status
                verbrauch_ziel_GWh = electricity_total_entry.ziel
            
            # Convert to MWh/a
            verbrauch_status_MWh_per_year = verbrauch_status_GWh * 1000
            verbrauch_ziel_MWh_per_year = verbrauch_ziel_GWh * 1000
            
            print(f"🔌 Using YOUR VERBRAUCH DATA for demand:")
            print(f"   Status: {verbrauch_status_GWh:.0f} GWh/a = {verbrauch_status_MWh_per_year:.0f} MWh/a")
            print(f"   Ziel: {verbrauch_ziel_GWh:.0f} GWh/a = {verbrauch_ziel_MWh_per_year:.0f} MWh/a")
            
            # Use STATUS demand for current analysis (you can switch to ZIEL if needed)
            annual_demand_MWh = verbrauch_status_MWh_per_year
            daily_average_demand_MWh = annual_demand_MWh / 365
            
        else:
            raise ValueError("VerbrauchData Code 5 not found in database. Please import verbrauch data.")
            
    except Exception as e:
        print(f"⚠️ Error getting VerbrauchData: {e}")
        raise ValueError(f"Database missing verbrauch energy data. Please import data first. Error: {e}")
    
    # Create demand curve using the historical SMARD demand SHAPE but scaled to YOUR total
    # This gives us a realistic daily variation pattern scaled to your actual consumption
    if daily['demand_MWh'].sum() > 0:
        # Use SMARD shape but scale to your total demand
        smard_demand_shape = daily['demand_MWh'] / daily['demand_MWh'].sum()  # Normalize SMARD shape
        daily['verbrauch_demand_MWh'] = smard_demand_shape * annual_demand_MWh  # Scale to your annual total
    else:
        # Fallback to constant daily demand if no SMARD data
        daily['verbrauch_demand_MWh'] = daily_average_demand_MWh
    
    # Sort YOUR ACTUAL DEMAND by descending order (highest first) - independent of renewables
    dmd_sorted = daily['verbrauch_demand_MWh'].sort_values(ascending=False).reset_index(drop=True)
    
    # Add VerbrauchData totals for reference
    daily['verbrauch_status_GWh'] = verbrauch_status_GWh if 'verbrauch_status_GWh' in locals() else 0
    daily['verbrauch_ziel_GWh'] = verbrauch_ziel_GWh if 'verbrauch_ziel_GWh' in locals() else 0
    daily['annual_demand_check_GWh'] = annual_demand_MWh / 1000 if 'annual_demand_MWh' in locals() else 0
    
    # Create segmentiert dataset (chronology removed, sorted pairs)
    segmentiert_data = pd.DataFrame({
        'day_rank': range(1, len(ren_sorted) + 1),  # 1 to 365 (or number of days)
        'ren_sorted_MWh': ren_sorted,
        'dmd_sorted_MWh': dmd_sorted
    })
    
    # PART C — Compute surplus/deficit & storage flows
    # 6) Daily surplus in the segmentiert space
    surplus_sorted = ren_sorted - dmd_sorted
    
    # 7) Stromaufnahme (Überschussphasen) — Sum only the positive parts
    surplus_positive = surplus_sorted[surplus_sorted > 0]  # Filter only positive surplus
    stromaufnahme_MWh = surplus_positive.sum()  # Sum positive surplus in MWh
    stromaufnahme_GWh = stromaufnahme_MWh / 1000  # Convert to GWh
    
    print(f"📊 STROMAUFNAHME CALCULATION:")
    print(f"   Positive surplus days: {len(surplus_positive)} out of {len(surplus_sorted)} days")
    print(f"   Total surplus energy: {stromaufnahme_MWh:.0f} MWh = {stromaufnahme_GWh:.1f} GWh")
    print(f"🔋 FINAL STROMAUFNAHME VALUE: {stromaufnahme_GWh:.1f} GWh/a")
    
    # Add segmentiert data to daily for template access
    daily['day_rank'] = range(1, len(daily) + 1)
    daily['ren_sorted_MWh'] = ren_sorted
    daily['dmd_sorted_MWh'] = dmd_sorted  # This now uses YOUR VerbrauchData
    daily['surplus_sorted_MWh'] = surplus_sorted
    
    # Add Stromaufnahme values for template access
    daily['stromaufnahme_MWh'] = stromaufnahme_MWh
    daily['stromaufnahme_GWh'] = stromaufnahme_GWh
    daily['surplus_days_count'] = len(surplus_positive)
    daily['total_days_count'] = len(surplus_sorted)
    daily['surplus_days_percent'] = (len(surplus_positive) / len(surplus_sorted) * 100) if len(surplus_sorted) > 0 else 0
    
    # Quick verification: total demand should match your VerbrauchData
    total_demand_check_MWh = daily['verbrauch_demand_MWh'].sum()
    daily['demand_verification_GWh'] = total_demand_check_MWh / 1000
    daily['demand_difference_percent'] = ((total_demand_check_MWh - annual_demand_MWh) / annual_demand_MWh * 100) if 'annual_demand_MWh' in locals() else 0

    # 6️⃣ Send data to the web page
    data = daily.to_dict(orient='records')
    
    # Convert datetime objects to strings for JavaScript
    for record in data:
        if 'date' in record:
            record['date'] = record['date'].strftime('%Y-%m-%d')

    return render(request, 'simulator/smard_solar_wind.html', {'data': data})


@login_required
def bilanz_view(request):
    """
    Bilanz (Balance Sheet) View
    Compares supply (Aktiva: Renewable + Fossil) with demand (Passiva: Verbrauch)
    Structure: Erneuerbar + Fossil (Aktiva) = Verbrauch (Passiva)
    
    All calculations are dynamically pulled from RenewableData and VerbrauchData
    using the bilanz_engine calculation module.
    """
    
    # Import the bilanz calculation engine
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from calculation_engine.bilanz_engine import calculate_bilanz_data
    
    # Get all bilanz data from the calculation engine (fully dynamic)
    bilanz_data = calculate_bilanz_data()
    bilanz_data['latest_run'] = CalculationRun.objects.first()
    
    # Add current section to context
    bilanz_data['current_section'] = 'bilanz'
    
    return render(request, 'simulator/bilanz.html', bilanz_data)

# ============================
# NEW LANDUSE AJAX UPDATE VIEW
# ============================

@csrf_exempt
@login_required
def update_landuse_percent(request, pk):
    """
    Update the user_percent of a LandUse item and recalc target_ha automatically.
    FIXED: Uses model save() to trigger signals for auto-cascade.
    
    VALIDATION: Prevents excessive increases to maintain realistic land use changes.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=400)

    try:
        data = json.loads(request.body)
        new_percent = float(data.get("user_percent"))
        
        # Validate percentage range
        if new_percent < 0 or new_percent > 100:
            return JsonResponse({
                "status": "error", 
                "message": "Percentage must be between 0 and 100"
            }, status=400)
            
    except (ValueError, TypeError) as e:
        return JsonResponse({
            "status": "error", 
            "message": "Invalid percentage value"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error", 
            "message": "Invalid request data"
        }, status=400)

    try:
        landuse = get_object_or_404(LandUse, pk=pk)
        
        if not landuse.parent:
            return JsonResponse({
                "status": "error",
                "message": "Cannot update root level land use"
            }, status=400)
        
        # ===================================================================
        # VALIDATION RULE: Prevent excessive land use increases
        # Maximum allowed increase configured in settings.py (in percentage POINTS)
        # This prevents unrealistic jumps in land use allocation
        # Example: If MAX = 3, user can go from 10% to 13% (not 10% to 10.3%)
        # ===================================================================
        from django.conf import settings
        MAX_INCREASE_PERCENTAGE_POINTS = getattr(settings, 'LANDUSE_MAX_INCREASE_PERCENT', 3)
        
        # Use existing user_percent OR calculate from target_ha if user_percent not set
        # This ensures validation works even when user_percent hasn't been set yet
        if landuse.user_percent is not None:
            current_percent = landuse.user_percent
        elif landuse.parent and landuse.parent.target_ha and landuse.target_ha:
            # Calculate current percentage from target_ha
            current_percent = (landuse.target_ha / landuse.parent.target_ha * 100) if landuse.parent.target_ha > 0 else 0
        else:
            current_percent = 0
        
        # Calculate absolute percentage point change (not relative change)
        if current_percent > 0:
            percentage_point_change = new_percent - current_percent
            
            # Check if increase exceeds maximum allowed (in percentage points)
            if percentage_point_change > MAX_INCREASE_PERCENTAGE_POINTS:
                max_allowed_value = current_percent + MAX_INCREASE_PERCENTAGE_POINTS
                return JsonResponse({
                    "status": "error",
                    "message": f"⚠️ Cannot increase land use by more than {MAX_INCREASE_PERCENTAGE_POINTS} percentage points.\n\n"
                              f"Current: {current_percent:.2f}%\n"
                              f"Requested: {new_percent:.2f}%\n"
                              f"Increase: {percentage_point_change:.2f} percentage points\n"
                              f"Maximum allowed: {max_allowed_value:.2f}%\n\n"
                              f"Please increase gradually to maintain realistic land use changes.",
                    "current_value": float(current_percent),
                    "max_allowed_value": float(max_allowed_value),
                    "max_increase_percent": MAX_INCREASE_PERCENTAGE_POINTS
                }, status=400)
        # If current is 0, allow any positive value up to 100% (starting from zero is OK)
        
        # Auto-unlock if locked (user edits should always be allowed)
        if landuse.target_locked:
            landuse.target_locked = False
        
        # Store old values for change tracking
        old_target_ha = landuse.target_ha
        old_percent = landuse.user_percent if landuse.user_percent is not None else current_percent
        
        # Calculate new target_ha from user_percent
        parent_target = landuse.parent.target_ha or 0
        new_target_ha = (parent_target * new_percent) / 100.0
        
        # Update values
        landuse.user_percent = new_percent
        landuse.target_ha = new_target_ha
        
        # Use model save() to trigger signals - this will auto-cascade to renewables
        # The signal will call unified_recalc_and_balance automatically
        landuse.save()  # NO skip_cascade - let signals fire!

        # Calculate target percent for response
        target_percent = (new_target_ha / parent_target * 100) if parent_target else 0
        
        # Calculate change
        change_ha = new_target_ha - (old_target_ha or 0)

        # Send updated values back to page with change tracking info
        return JsonResponse({
            "status": "ok",
            "code": landuse.code,
            "name": landuse.name,
            "new_target_ha": float(new_target_ha),
            "new_target_percent": float(target_percent),
            "old_target_ha": float(old_target_ha) if old_target_ha else None,
            "change_ha": float(change_ha),
            "message": f"Updated {landuse.code} to {new_percent}% - renewables auto-updated",
            "change": {
                "code": landuse.code,
                "name": landuse.name,
                "old_percent": float(old_percent) if old_percent else None,
                "new_percent": float(new_percent),
                "old_ha": float(old_target_ha) if old_target_ha else None,
                "new_ha": float(new_target_ha),
                "change_ha": float(change_ha)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Failed to update: {str(e)}"
        }, status=500)


# =============================================================================
# CORE BALANCE FUNCTIONS (for unified balance system)
# =============================================================================

def _balance_ws_storage_core(ws_tolerance=10.0, max_iter=30, num_passes=3):
    """
    FAST WS Storage balance logic - uses LIGHTWEIGHT direct column recalc.
    Adjusts stromverbr_raumwaerm_korr (row 366) until ladezustand_netto (row 366) ≈ 0.
    
    OPTIMIZATION: Instead of calling full recalculate_ws_data (which processes 365 rows × 3 passes),
    we directly update only the columns that depend on stromverbr_raumwaerm_korr.
    
    Returns dict with: is_balanced, final_balance, final_stromverbr, iterations, etc.
    """
    from django.db import transaction
    
    # Get initial reference value
    diagram = compute_ws_diagram_reference(use_ws_overrides=False)
    reference_stromverbr = diagram.get("stromverbr_raumwaerm_korr_366", 0) or 0
    
    iterations_log = []
    
    def storage_balance_fast(stromverbr_value: float) -> float:
        """
        FAST: Only update stromverbr_raumwaerm_korr and recalculate ladezustand_netto chain.
        This is 10x+ faster than full recalculate_ws_data().
        """
        # Update row 366 stromverbr_raumwaerm_korr directly
        WSData.objects.filter(tag_im_jahr=366).update(stromverbr_raumwaerm_korr=stromverbr_value)
        
        # Recalculate ONLY the columns that depend on stromverbr_raumwaerm_korr
        # The dependency chain is:
        # stromverbr_raumwaerm_korr_366 -> stromverbr (daily) -> direktverbr_strom -> 
        # ueberschuss_strom -> einspeich/abregelung_z/mangel_last -> ladezustand_netto
        
        # Get all daily rows
        daily_rows = list(WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365))
        row_366 = WSData.objects.get(tag_im_jahr=366)
        
        # Recalculate affected columns for all 365 days
        sum_einspeich = 0
        sum_abregelung = 0
        sum_ausspeich_rueck = 0
        sum_ausspeich_gas = 0
        
        for row in daily_rows:
            vp = row.verbrauch_promille or 0
            # stromverbr = stromverbr_raumwaerm_korr_366 * verbrauch_promille / 1000
            stromverbr = stromverbr_value * vp / 1000 if vp else 0
            row.stromverbr = stromverbr
            row.stromverbr_raumwaerm_korr = stromverbr
            
            # direktverbr_strom = MIN(wind_solar_konstant, stromverbr_raumwaerm_korr)
            wsk = row.wind_solar_konstant or 0
            direktverbr = min(wsk, stromverbr)
            row.direktverbr_strom = direktverbr
            
            # ueberschuss_strom = wind_solar_konstant - direktverbr_strom
            ueberschuss = wsk - direktverbr
            row.ueberschuss_strom = ueberschuss
            
            # einspeich = ueberschuss_strom * 0.65 (ETA_STROM_GAS)
            eta_strom_gas = 0.65
            einspeich = ueberschuss * eta_strom_gas
            row.einspeich = einspeich
            
            # abregelung_z = ueberschuss_strom * 0.35
            abregelung = ueberschuss * 0.35
            row.abregelung_z = abregelung
            
            # mangel_last = MAX(stromverbr_raumwaerm_korr - wind_solar_konstant, 0)
            mangel = max(stromverbr - wsk, 0)
            row.mangel_last = mangel
            
            sum_einspeich += einspeich
            sum_abregelung += abregelung
            sum_ausspeich_rueck += row.ausspeich_rueckverstr or 0
            sum_ausspeich_gas += row.ausspeich_gas or 0
        
        # Bulk update daily rows
        WSData.objects.bulk_update(daily_rows, [
            'stromverbr', 'stromverbr_raumwaerm_korr', 'direktverbr_strom', 
            'ueberschuss_strom', 'einspeich', 'abregelung_z', 'mangel_last'
        ])
        
        # Calculate cumulative ladezustand_netto for each day
        cumulative = 0
        for row in daily_rows:
            einspeich = row.einspeich or 0
            ausspeich_rueck = row.ausspeich_rueckverstr or 0
            ausspeich_gas = row.ausspeich_gas or 0
            selbstentl = row.selbstentl or 0
            
            cumulative += einspeich - ausspeich_rueck - ausspeich_gas - selbstentl
            row.ladezustand_netto = cumulative
        
        # Bulk update ladezustand_netto
        WSData.objects.bulk_update(daily_rows, ['ladezustand_netto'])
        
        # Get day 1 and day 365 values for row 366 formula
        day_1_ladezustand = daily_rows[0].ladezustand_netto if daily_rows else 0
        day_365_ladezustand = daily_rows[-1].ladezustand_netto if daily_rows else 0
        
        # Update row 366 sums
        row_366.stromverbr = stromverbr_value  # CRITICAL: Update row 366 stromverbr to match
        row_366.stromverbr_raumwaerm_korr = stromverbr_value  # CRITICAL: Keep in sync!
        row_366.einspeich = sum_einspeich
        row_366.abregelung_z = sum_abregelung
        row_366.ausspeich_rueckverstr = sum_ausspeich_rueck
        row_366.ausspeich_gas = sum_ausspeich_gas
        # ladezustand_netto for row 366 = day_365 - day_1 (formula from database)
        row_366.ladezustand_netto = day_365_ladezustand - day_1_ladezustand
        row_366._skip_ws_cascade = True  # Skip cascade during balance (we're handling it)
        row_366.save()
        
        iterations_log.append({
            "stromverbr": round(stromverbr_value, 2),
            "ladezustand": round(row_366.ladezustand_netto, 2)
        })
        return row_366.ladezustand_netto or 0.0
    
    x0 = reference_stromverbr
    x1 = reference_stromverbr * 1.05 if reference_stromverbr != 0 else 1.0
    
    # Use transaction.atomic for faster DB operations
    with transaction.atomic():
        final_value = goal_seek(storage_balance_fast, x0, x1, target=0.0, tol=1.0, max_iter=max_iter)
        # Final pass with the converged value
        storage_balance_fast(final_value)
    
    row_366 = WSData.objects.get(tag_im_jahr=366)
    final_balance = row_366.ladezustand_netto or 0.0
    is_balanced = abs(final_balance) < ws_tolerance
    
    # Load WS constants for return values
    ws_consts_cockpit = get_ws_constants()
    abregelung_ws = row_366.abregelung_z or 0.0
    ely_surplus_ws = (row_366.einspeich or 0.0) / ws_consts_cockpit['ETA_STROM_GAS'] if ws_consts_cockpit['ETA_STROM_GAS'] else 0.0

    return {
        "is_balanced": is_balanced,
        "final_balance": final_balance,
        "final_stromverbr": final_value,
        "reference_stromverbr": reference_stromverbr,
        "abregelung_ws": abregelung_ws,
        "ely_surplus_ws": ely_surplus_ws,
        "iterations": len(iterations_log),
    }


def _balance_energy_lu6_core(energy_tolerance=1.0, max_iter=20, num_passes=1):
    """
    FAST Energy balance logic - adjusts LU_6 (Windparkfläche) area until 
    renewable supply matches verbrauch demand.
    Same as _balance_energy_core but specifically for LU_6.
    
    OPTIMIZED: Skips full WS recalc during goal-seek iterations.
    Only does fast renewable recalc. Full WS recalc happens ONCE at the end.
    
    Returns dict with: is_balanced, final_gap, final_ha, demand, renewable, etc.
    """
    from simulator.recalc_service import recalc_all_renewables_full
    from simulator.ws_formula_service import recalculate_all_ws_data
    from simulator.ws_models import WSData
    from simulator.signals import get_ws_constants
    
    driver_code = "LU_6"
    try:
        lu = LandUse.objects.get(code=driver_code)
    except LandUse.DoesNotExist:
        return {"is_balanced": False, "error": f"LandUse {driver_code} not found"}

    # Pre-fetch verbrauch demand once (it doesn't change during goal-seek)
    from calculation_engine.bilanz_engine import calculate_bilanz_data
    initial_bilanz = calculate_bilanz_data()
    cached_demand = initial_bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0

    def set_and_gap_fast(target_ha: float):
        """
        FAST: Update LandUse and recalc only renewables (skip WS).
        WS recalc is expensive - we do it once at the end.
        """
        lu.target_ha = max(0, target_ha)
        lu.save(skip_cascade=True, force_recalc=False)
        
        # STEP 1: Trigger direct renewable dependents for this LandUse
        lu._recalculate_renewable_dependents()
        
        # STEP 2: Recalculate renewables (SKIP WS during goal-seek)
        recalc_all_renewables_full(exclude_ws_dependent=True)
        
        # Calculate renewable total - use 10.1 which is the total energy
        try:
            r101 = RenewableData.objects.get(code='10.1')
            renewable_total = r101.target_value or 0
        except RenewableData.DoesNotExist:
            renewable_total = 0
        
        gap = cached_demand - renewable_total
        return gap, cached_demand, renewable_total, lu.target_ha

    base_ha = lu.target_ha or 0
    gap0, demand0, renewable0, ha0 = set_and_gap_fast(base_ha)

    if abs(gap0) <= energy_tolerance:
        # Energy already balanced, but still need to balance WS storage
        print("  Energy already balanced, proceeding with WS balance...")
        print("  [FINAL] Running full renewable recalc (including WS-dependent codes)...")
        recalc_all_renewables_full(exclude_ws_dependent=False)
        
        print("  [FINAL] Running full WS recalculation...")
        recalculate_all_ws_data(num_passes=1)
        
        # BALANCE WS STORAGE: Adjust stromverbr to make ladezustand_netto = 0 for row 366
        print("  [FINAL] Balancing WS storage (ladezustand_netto → 0)...")
        ws_result = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=10, num_passes=1)
        ws_balanced = ws_result.get("is_balanced", False)
        ws_balance_value = ws_result.get("final_balance", 0)
        print(f"      WS balanced: {ws_balanced}, ladezustand_netto: {ws_balance_value:.2f} GWh")
        
        # Final renewable recalc to update 9.3.x codes with the new WS balance
        print("  [FINAL] Final renewable recalc after WS balance...")
        recalc_all_renewables_full(exclude_ws_dependent=False)
        
        print("  ✅ Energy + WS balance complete (energy was already balanced)")
        
        return {
            "is_balanced": True,
            "final_gap": gap0,
            "final_ha": ha0,
            "demand": demand0,
            "renewable": renewable0,
            "driver": driver_code,
            "iterations": 0,
            "ws_balanced": ws_balanced,
            "ws_balance_value": ws_balance_value,
        }

    # Choose second guess direction based on gap sign
    if gap0 > 0:
        x1 = ha0 * 1.1 + 100 if ha0 == 0 else ha0 * 1.1
    else:
        x1 = max(ha0 * 0.9, 0)

    def gap_func(area):
        g, _, _, _ = set_and_gap_fast(area)
        return g

    # Use transaction.atomic for faster DB operations
    with transaction.atomic():
        final_ha = goal_seek(gap_func, ha0, x1, target=0.0, tol=energy_tolerance, max_iter=max_iter)
        final_gap, final_demand, final_renewable, final_ha = set_and_gap_fast(final_ha)

    is_balanced = abs(final_gap) <= energy_tolerance
    
    print(f"\n  Energy balance complete:")
    print(f"    Driver: {driver_code}")
    print(f"    Final gap: {final_gap:.2f} GWh")
    print(f"    Final ha: {final_ha:.2f}")
    print(f"    Status: {'✅ BALANCED' if is_balanced else '⚠️  PARTIAL'}")
    
    # === FINAL STEP: Now that energy is balanced, do full chain ===
    print("\n  [FINAL] Running full renewable recalc (including WS-dependent codes)...")
    recalc_all_renewables_full(exclude_ws_dependent=False)
    
    print("  [FINAL] Running full WS recalculation...")
    recalculate_all_ws_data(num_passes=1)
    
    # BALANCE WS STORAGE: Adjust stromverbr to make ladezustand_netto = 0 for row 366
    print("  [FINAL] Balancing WS storage (ladezustand_netto → 0)...")
    ws_result = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=10, num_passes=1)
    ws_balanced = ws_result.get("is_balanced", False)
    ws_balance_value = ws_result.get("final_balance", 0)
    print(f"      WS balanced: {ws_balanced}, ladezustand_netto: {ws_balance_value:.2f} GWh")
    
    # Final renewable recalc to update 9.3.x codes with the new WS balance
    print("  [FINAL] Final renewable recalc after WS balance...")
    recalc_all_renewables_full(exclude_ws_dependent=False)
    
    print("  ✅ Full energy + WS balance chain complete\n")
    
    return {
        "is_balanced": is_balanced,
        "final_gap": final_gap,
        "final_ha": final_ha,
        "initial_gap": gap0,
        "initial_ha": ha0,
        "demand": cached_demand,
        "renewable": cached_demand - final_gap,
        "driver": driver_code,
        "ws_balanced": ws_balanced,
        "ws_balance_value": ws_balance_value,
    }


def _balance_energy_core(driver="solar", energy_tolerance=1.0, max_iter=20, num_passes=1):
    """
    FAST Energy balance logic - adjusts LandUse area until 
    renewable supply matches verbrauch demand.
    
    OPTIMIZED: Skips full WS recalc during goal-seek iterations.
    Only does fast renewable recalc. Full WS recalc happens ONCE at the end.
    
    Returns dict with: is_balanced, final_gap, final_ha, demand, renewable, etc.
    """
    from simulator.recalc_service import recalc_all_renewables_full
    from simulator.ws_formula_service import recalculate_all_ws_data
    from simulator.ws_models import WSData
    from simulator.signals import get_ws_constants
    
    driver_code = "LU_2.1" if driver == "solar" else "LU_1.1"
    try:
        lu = LandUse.objects.get(code=driver_code)
    except LandUse.DoesNotExist:
        return {"is_balanced": False, "error": f"LandUse {driver_code} not found"}

    # Pre-fetch verbrauch demand once (it doesn't change during goal-seek)
    from calculation_engine.bilanz_engine import calculate_bilanz_data
    initial_bilanz = calculate_bilanz_data()
    cached_demand = initial_bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0

    def set_and_gap_fast(target_ha: float):
        """
        FAST: Update LandUse and recalc only renewables (skip WS).
        WS recalc is expensive - we do it once at the end.
        """
        lu.target_ha = max(0, target_ha)
        lu.save(skip_cascade=True, force_recalc=False)
        
        # STEP 1: Trigger direct renewable dependents for this LandUse
        lu._recalculate_renewable_dependents()
        
        # STEP 2: Recalculate renewables (SKIP WS during goal-seek)
        recalc_all_renewables_full(exclude_ws_dependent=True)
        
        # Calculate renewable total - use 10.1 which is the total energy
        try:
            r101 = RenewableData.objects.get(code='10.1')
            renewable_total = r101.target_value or 0
        except RenewableData.DoesNotExist:
            renewable_total = 0
        
        gap = cached_demand - renewable_total
        return gap, cached_demand, renewable_total, lu.target_ha

    base_ha = lu.target_ha or 0
    gap0, demand0, renewable0, ha0 = set_and_gap_fast(base_ha)

    if abs(gap0) <= energy_tolerance:
        # Energy already balanced, but still need to balance WS storage
        print("  Energy already balanced, proceeding with WS balance...")
        print("  [FINAL] Running full renewable recalc (including WS-dependent codes)...")
        recalc_all_renewables_full(exclude_ws_dependent=False)
        
        print("  [FINAL] Running full WS recalculation...")
        recalculate_all_ws_data(num_passes=1)
        
        # BALANCE WS STORAGE: Adjust stromverbr to make ladezustand_netto = 0 for row 366
        print("  [FINAL] Balancing WS storage (ladezustand_netto → 0)...")
        ws_result = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=10, num_passes=1)
        ws_balanced = ws_result.get("is_balanced", False)
        ws_balance_value = ws_result.get("final_balance", 0)
        print(f"      WS balanced: {ws_balanced}, ladezustand_netto: {ws_balance_value:.2f} GWh")
        
        # NOTE: Do NOT recalculate WS here - _balance_ws_storage_core already updated
        # all columns correctly. Recalculating would overwrite row 366 ladezustand_netto
        # with the formula (day_365 - day_1) which gives a different value.
        
        # Final renewable recalc to update 9.3.x codes with the new WS balance
        print("  [FINAL] Final renewable recalc after WS balance...")
        recalc_all_renewables_full(exclude_ws_dependent=False)
        
        print("  ✅ Energy + WS balance complete (energy was already balanced)")
        
        return {
            "is_balanced": True,
            "final_gap": gap0,
            "final_ha": ha0,
            "demand": demand0,
            "renewable": renewable0,
            "driver": driver_code,
            "iterations": 0,
            "ws_balanced": ws_balanced,
            "ws_balance_value": ws_balance_value,
        }

    # Choose second guess direction based on gap sign
    if gap0 > 0:
        x1 = ha0 * 1.1 + 100 if ha0 == 0 else ha0 * 1.1
    else:
        x1 = max(ha0 * 0.9, 0)

    def gap_func(area):
        g, _, _, _ = set_and_gap_fast(area)
        return g

    # Use transaction.atomic for faster DB operations
    from django.db import transaction
    with transaction.atomic():
        final_ha = goal_seek(gap_func, ha0, x1, target=0.0, tol=energy_tolerance, max_iter=max_iter)
        final_gap, final_demand, final_renewable, final_ha = set_and_gap_fast(final_ha)

    # CRITICAL: After energy balance completes, trigger full renewable + WS recalculation
    # This ensures WS data (9.3.x codes) and all WS rows are synced with the new energy balance
    print("  [FINAL] Running full renewable recalc (including WS-dependent codes)...")
    recalc_all_renewables_full(exclude_ws_dependent=False)
    
    print("  [FINAL] Running full WS recalculation...")
    recalculate_all_ws_data(num_passes=1)
    
    # BALANCE WS STORAGE: Adjust stromverbr to make ladezustand_netto = 0 for row 366
    print("  [FINAL] Balancing WS storage (ladezustand_netto → 0)...")
    ws_result = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=10, num_passes=1)
    ws_balanced = ws_result.get("is_balanced", False)
    ws_balance_value = ws_result.get("final_balance", 0)
    print(f"      WS balanced: {ws_balanced}, ladezustand_netto: {ws_balance_value:.2f} GWh")
    
    # NOTE: Do NOT recalculate WS here - _balance_ws_storage_core already updated
    # all columns correctly. Recalculating would overwrite row 366 ladezustand_netto
    # with the formula (day_365 - day_1) which gives a different value.
    
    # Final renewable recalc to update 9.3.x codes with the new WS balance
    print("  [FINAL] Final renewable recalc after WS balance...")
    recalc_all_renewables_full(exclude_ws_dependent=False)
    
    print("  ✅ Energy + WS balance complete")

    return {
        "is_balanced": abs(final_gap) <= energy_tolerance,
        "initial_gap": gap0,
        "final_gap": final_gap,
        "initial_ha": ha0,
        "final_ha": final_ha,
        "demand": final_demand,
        "renewable": final_renewable,
        "driver": driver_code,
        "ws_balanced": ws_balanced,
        "ws_balance_value": ws_balance_value,
    }


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_full_system(request):
    """
    Unified balance: iteratively balances BOTH WS Storage AND Energy until 
    the entire system is in equilibrium.
    
    Alternates between WS balance and Energy balance until both converge 
    or max iterations reached.
    """
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}
    
    driver = data.get("driver", "solar")
    max_outer_iterations = int(data.get("max_iterations", 5))
    ws_tolerance = float(data.get("ws_tolerance", 10.0))  # GWh for ladezustand_netto
    energy_tolerance = float(data.get("energy_tolerance", 1.0))  # GWh for bilanz gap
    
    iteration_history = []
    
    print(f"\n{'='*60}")
    print(f"🔄 STARTING UNIFIED BALANCE SYSTEM")
    print(f"   Max iterations: {max_outer_iterations}")
    print(f"   WS tolerance: {ws_tolerance} GWh")
    print(f"   Energy tolerance: {energy_tolerance} GWh")
    print(f"   Driver: {driver}")
    print(f"{'='*60}\n")
    
    for i in range(max_outer_iterations):
        print(f"\n--- Outer Iteration {i+1}/{max_outer_iterations} ---")
        
        # Step 1: Balance Energy FIRST (adjusts LandUse → RenewableData → WS → 9.3.x → 10.1)
        # NOTE: _balance_energy_core now does the FULL CHAIN internally
        print(f"  [1] Balancing Energy (LandUse → Renewable → WS → 9.3.x → 10.1)...")
        energy_result = _balance_energy_core(driver=driver, energy_tolerance=energy_tolerance, max_iter=5, num_passes=1)
        energy_balanced = energy_result.get("is_balanced", False)
        energy_gap = energy_result.get("final_gap", 0)
        print(f"      Energy Result: balanced={energy_balanced}, gap={energy_gap:.2f}")
        
        # Step 2: Balance WS Storage (adjusts stromverbr to get ladezustand_netto ≈ 0)
        print(f"  [2] Balancing WS Storage...")
        ws_result = _balance_ws_storage_core(ws_tolerance=ws_tolerance, max_iter=5, num_passes=1)
        ws_balanced = ws_result.get("is_balanced", False)
        ws_balance_value = ws_result.get("final_balance", 0)
        print(f"      WS Result: balanced={ws_balanced}, ladezustand_netto={ws_balance_value:.2f}")
        
        # Step 3: No WS -> renewable writes; keep fixed values from DB
        
        # Step 4: RE-VERIFY energy balance with the final state
        print(f"  [4] Re-verifying Energy balance...")
        bilanz_recheck = calculate_bilanz_data()
        recheck_demand = bilanz_recheck.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
        
        # Use 10.1 (total renewable) instead of renewable_by_sector
        from calculation_engine.bilanz_engine import get_renewable_value
        recheck_renewable = get_renewable_value('10.1', use_target=True, fail_fast=False) or 0
        
        recheck_gap = recheck_demand - recheck_renewable
        energy_still_balanced = abs(recheck_gap) <= energy_tolerance
        print(f"      Re-check: demand={recheck_demand:.2f}, renewable={recheck_renewable:.2f}, gap={recheck_gap:.2f}, still_balanced={energy_still_balanced}")
        
        # Update energy_gap to the rechecked value for accuracy
        energy_gap = recheck_gap
        energy_balanced = energy_still_balanced
        
        iteration_history.append({
            "iteration": i + 1,
            "ws_balanced": ws_balanced,
            "ws_balance_value": round(ws_balance_value, 2),
            "energy_balanced": energy_balanced,
            "energy_gap": round(energy_gap, 2) if energy_gap else 0,
            "recheck_demand": round(recheck_demand, 2),
            "recheck_renewable": round(recheck_renewable, 2),
        })
        
        # Step 5: Check if BOTH are now balanced with the FINAL values
        if ws_balanced and energy_balanced:
            print(f"\n✅ FULLY BALANCED after {i+1} iterations!")
            # Do ONE final full recalc now that we're done
            from simulator.recalc_service import unified_recalc_all
            unified_recalc_all()
            return JsonResponse({
                "status": "fully_balanced",
                "message": f"System fully balanced after {i+1} iterations",
                "total_iterations": i + 1,
                "ws_result": {
                    "is_balanced": ws_balanced,
                    "final_balance": ws_balance_value,
                    "final_stromverbr": ws_result.get("final_stromverbr", 0),
                },
                "energy_result": {
                    "is_balanced": energy_balanced,
                    "final_gap": energy_gap,
                    "final_ha": energy_result.get("final_ha", 0),
                    "demand": energy_result.get("demand", 0),
                    "renewable": energy_result.get("renewable", 0),
                },
                "iteration_history": iteration_history,
            })
    
    # Max iterations reached
    print(f"\n⚠️ MAX ITERATIONS REACHED ({max_outer_iterations})")
    # Do ONE final full recalc before returning
    from simulator.recalc_service import unified_recalc_all
    unified_recalc_all()
    return JsonResponse({
        "status": "max_iterations_reached",
        "message": f"Reached max {max_outer_iterations} iterations. System may not be fully balanced.",
        "total_iterations": max_outer_iterations,
        "ws_result": {
            "is_balanced": ws_result.get("is_balanced", False),
            "final_balance": ws_result.get("final_balance", 0),
        },
        "energy_result": {
            "is_balanced": energy_result.get("is_balanced", False),
            "final_gap": energy_result.get("final_gap", 0),
        },
        "iteration_history": iteration_history,
    })


def perform_ws_balance(max_iter: int = 30, tol: float = 10.0):
    """
    GoalSeek Stromverbr. Raumw.korr. (row 366) until LadezustandNetto (row 366) == 0.
    Returns a plain dict so it can be reused by multiple views.
    """
    from django.db import transaction
    
    diagram = compute_ws_diagram_reference()
    reference_stromverbr = diagram.get("stromverbr_raumwaerm_korr_366", 0) or 0

    # First pass: seed state with the diagram reference value
    # Must use use_diagram_reference=False so the override is actually applied
    recalculate_ws_data(stromverbr_override=reference_stromverbr, use_diagram_reference=False)

    def storage_balance(stromverbr_value: float) -> float:
        # Override with proposed value; do not recompute from diagram inside the loop
        recalculate_ws_data(stromverbr_override=stromverbr_value, use_diagram_reference=False)
        try:
            row_366 = WSData.objects.get(tag_im_jahr=366)
            return row_366.ladezustand_netto or 0.0
        except WSData.DoesNotExist:
            return 0.0

    # Set initial guesses for secant: current value and a small nudge
    x0 = reference_stromverbr
    x1 = reference_stromverbr * 1.05 if reference_stromverbr != 0 else 1.0

    final_value = goal_seek(storage_balance, x0, x1, target=0.0, tol=tol, max_iter=max_iter)

    # One final pass to persist the converged value
    recalculate_ws_data(stromverbr_override=final_value, use_diagram_reference=False)
    row_366 = WSData.objects.get(tag_im_jahr=366)

    # Derived values for the Annual Electricity diagram after balancing
    abregelung_ws = row_366.abregelung_z or 0.0
    n1_eff = 0.65
    ely_surplus_ws = (row_366.einspeich or 0.0) / n1_eff if n1_eff else 0.0
    h2_surplus_ws = ely_surplus_ws * n1_eff
    gas_storage_ws = h2_surplus_ws
    
    if row_366.ausspeich_rueckverstr is not None:
        t_value_ws = row_366.ausspeich_rueckverstr * 0.585
    else:
        t_value_ws = gas_storage_ws * 0.585

    # No WS -> renewable writes; keep fixed values from DB

    return {
        "reference_stromverbr": reference_stromverbr,
        "final_stromverbr": final_value,
        "ladezustand_netto_row_366": row_366.ladezustand_netto,
        "abregelung_ws": abregelung_ws,
        "ely_surplus_ws": ely_surplus_ws,
        "h2_surplus_ws": h2_surplus_ws,
        "gas_storage_ws": gas_storage_ws,
        "t_value_ws": t_value_ws,
    }


def perform_energy_balance(driver: str = "solar", tolerance: float = 1.0):
    """
    GoalSeek outer loop: adjust Solar (LU_2.1) or Wind (LU_1.1) land area until
    renewable total (10.1) matches verbrauch_gesamt.ziel.gesamt (gap ≈ 0).
    """
    from calculation_engine.bilanz_engine import get_renewable_value
    
    driver_code = "LU_2.1" if driver == "solar" else "LU_1.1"
    lu = LandUse.objects.get(code=driver_code)

    def set_and_gap(target_ha: float):
        lu.target_ha = max(0, target_ha)
        lu.target_locked = True
        lu.save(skip_cascade=False, force_recalc=False)
        lu.refresh_from_db()
        recalc_all_renewables_full()
        bilanz = calculate_bilanz_data()
        demand = bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
        renewable = get_renewable_value('10.1', use_target=True, fail_fast=False) or 0
        gap = demand - renewable  # positive gap => need more renewable
        return gap, demand, renewable, lu.target_ha

    base_ha = lu.target_ha or 0
    gap0, demand0, renewable0, ha0 = set_and_gap(base_ha)

    if abs(gap0) <= tolerance:
        return {
            "status": "balanced",
            "initial_gap": gap0,
            "final_gap": gap0,
            "initial_ha": ha0,
            "final_ha": ha0,
            "demand": demand0,
            "renewable": renewable0,
            "driver": driver_code,
            "iterations": 0,
        }

    # Choose second guess direction based on gap sign
    if gap0 > 0:
        x1 = ha0 * 1.1 + 100 if ha0 == 0 else ha0 * 1.1
    else:
        x1 = max(ha0 * 0.9, 0)

    def gap_func(area):
        g, _, _, _ = set_and_gap(area)
        return g

    final_ha = goal_seek(gap_func, ha0, x1, target=0.0, tol=tolerance, max_iter=30)
    final_gap, final_demand, final_renewable, final_ha = set_and_gap(final_ha)

    return {
        "status": "balanced" if abs(final_gap) <= tolerance else "partial",
        "initial_gap": gap0,
        "final_gap": final_gap,
        "initial_ha": ha0,
        "final_ha": final_ha,
        "demand": final_demand,
        "renewable": final_renewable,
        "driver": driver_code,
        "iterations": None,
    }


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_all(request):
    """
    Iteratively balance both WS storage (LadezustandNetto -> 0) and Bilanz (renewable vs. demand).
    Runs the two goal-seek loops in a transaction so a failure rolls back to the previous state.
    
    FIXED: Uses reasonable default tolerances:
    - WS tolerance: 10.0 GWh (was 1e-4 which is impossible)
    - Energy tolerance: 1.0 GWh
    
    The flow is:
    1. Balance energy (adjust LandUse)
    2. Balance WS storage
    3. Check if balanced, repeat if not
    """
    from django.db import transaction
    
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    driver = data.get("driver", "solar")
    tolerance = float(data.get("tolerance", 1.0))
    # FIXED: ws_tolerance was 1e-4 (impossible), now 10.0 GWh
    ws_tolerance = float(data.get("ws_tolerance", 10.0))
    max_cycles = int(data.get("max_cycles", 6))

    driver_code = "LU_2.1" if driver == "solar" else "LU_1.1"
    if not LandUse.objects.filter(code=driver_code).exists():
        return JsonResponse({
            "status": "error", 
            "message": f"LandUse {driver_code} not found. Available: LU_1.1 (wind), LU_2.1 (solar)"
        }, status=400)

    print(f"\n{'='*60}")
    print(f"⚖️ BALANCE ALL - Starting full balance cycle")
    print(f"   Driver: {driver_code}")
    print(f"   Energy tolerance: {tolerance} GWh")
    print(f"   WS tolerance: {ws_tolerance} GWh")
    print(f"   Max cycles: {max_cycles}")
    print(f"{'='*60}\n")

    cycles = []
    try:
        with transaction.atomic():
            for idx in range(max_cycles):
                print(f"\n--- Cycle {idx + 1}/{max_cycles} ---")
                
                # Step 1: Balance energy (adjust land use)
                # This already does: LandUse → Renewable → WS → 9.3.x → Renewable
                print(f"  [1] Balance Energy...")
                energy_result = _balance_energy_core(driver=driver, energy_tolerance=tolerance)
                energy_summary = {
                    "final_ha": energy_result.get("final_ha"),
                    "final_gap": energy_result.get("final_gap", 0),
                    "demand": energy_result.get("demand", 0),
                    "renewable": energy_result.get("renewable", 0),
                    "is_balanced": energy_result.get("is_balanced", False),
                }
                print(f"      Energy gap: {energy_summary['final_gap']:.2f} GWh")
                
                # Step 2: Balance WS storage (adjust stromverbr to zero out storage)
                print(f"  [2] Balance WS Storage...")
                ws_result = _balance_ws_storage_core(ws_tolerance=ws_tolerance)
                ws_summary = {
                    "final_stromverbr": ws_result.get("final_stromverbr"),
                    "ladezustand_netto_row_366": ws_result.get("final_balance", 0),
                    "abregelung_ws": ws_result.get("abregelung_ws", 0),
                    "ely_surplus_ws": ws_result.get("ely_surplus_ws", 0),
                    "is_balanced": ws_result.get("is_balanced", False),
                }
                print(f"      WS ladezustand: {ws_summary['ladezustand_netto_row_366']:.2f} GWh")
                
                # Step 3: Check final balance
                from calculation_engine.bilanz_engine import get_renewable_value
                bilanz = calculate_bilanz_data()
                demand = bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
                renewable_total = get_renewable_value('10.1', use_target=True, fail_fast=False) or 0
                gap_after_ws = demand - renewable_total
                
                # Re-check WS balance
                row_366 = WSData.objects.get(tag_im_jahr=366)
                final_ws_balance = row_366.ladezustand_netto or 0

                cycles.append({
                    "iteration": idx + 1,
                    "gap_after_ws": gap_after_ws,
                    "ws_ladezustand": final_ws_balance,
                    "stromverbr": ws_summary.get("final_stromverbr"),
                    "landuse_target_ha": energy_summary.get("final_ha"),
                })
                
                print(f"  [4] Final check: Energy gap={gap_after_ws:.2f}, WS balance={final_ws_balance:.2f}")

                # Check if both tolerances are met
                ws_ok = abs(final_ws_balance) <= ws_tolerance
                bilanz_ok = abs(gap_after_ws) <= tolerance
                
                if ws_ok and bilanz_ok:
                    print(f"\n✅ BALANCED after {idx + 1} cycles!")
                    return JsonResponse({
                        "status": "ok",
                        "overall_status": "balanced",
                        "iterations": idx + 1,
                        "gap_after_ws": gap_after_ws,
                        "ws": ws_summary,
                        "energy": energy_summary,
                        "cycles": cycles,
                    })

            raise RuntimeError(f"Unable to balance both loops within {max_cycles} iterations")
    except Exception as exc:
        return JsonResponse({
            "status": "error",
            "message": str(exc),
            "cycles": cycles,
        }, status=500)



@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_ws_storage(request):
    """
    GoalSeek Stromverbr. Raumw.korr. (row 366) until LadezustandNetto (row 366) == 0.
    Uses the core function and returns HTTP response.
    """
    result = _balance_ws_storage_core()
    
    # Get additional values for response
    row_366 = WSData.objects.get(tag_im_jahr=366)
    ws_consts_cockpit = get_ws_constants()
    
    h2_surplus_ws = result.get("ely_surplus_ws", 0) * ws_consts_cockpit['ETA_STROM_GAS']
    gas_storage_ws = h2_surplus_ws
    
    if row_366.ausspeich_rueckverstr is not None:
        t_value_ws = row_366.ausspeich_rueckverstr * ws_consts_cockpit['ETA_GAS_STROM']
    else:
        t_value_ws = gas_storage_ws * ws_consts_cockpit['ETA_GAS_STROM']

    return JsonResponse({
        "status": "balanced" if result["is_balanced"] else "converged_with_residual",
        "message": f"LadezustandNetto366 = {result['final_balance']:.2f} GWh (target: 0)" if not result["is_balanced"] else "Balanced successfully",
        "reference_stromverbr": result.get("reference_stromverbr", 0),
        "final_stromverbr": result.get("final_stromverbr", 0),
        "ladezustand_netto_row_366": result.get("final_balance", 0),
        "is_balanced": result["is_balanced"],
        "abregelung_ws": result.get("abregelung_ws", 0),
        "ely_surplus_ws": result.get("ely_surplus_ws", 0),
        "h2_surplus_ws": h2_surplus_ws,
        "gas_storage_ws": gas_storage_ws,
        "t_value_ws": t_value_ws,
        "iterations": result.get("iterations", 0),
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_energy(request):
    """
    GoalSeek outer loop: adjust Solar (LU_2.1) or Wind (LU_1.1) land area until
    renewable total (10.1) matches verbrauch_gesamt.ziel.gesamt (gap ≈ 0).
    """
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    driver = data.get("driver", "solar")
    tolerance = float(data.get("tolerance", 1.0))  # GWh tolerance for total gap

    driver_code = "LU_2.1" if driver == "solar" else "LU_1.1"
    try:
        lu = LandUse.objects.get(code=driver_code)
    except LandUse.DoesNotExist:
        return JsonResponse({"status": "error", "message": f"LandUse {driver_code} not found. Available: LU_1.1 (wind), LU_2.1 (solar)"}, status=400)

    try:
        # Track old value before balance
        old_ha = lu.target_ha
        old_percent = (lu.target_ha / lu.parent.target_ha * 100) if (lu.parent and lu.parent.target_ha) else 0
        
        # Use core function
        result = _balance_energy_core(driver=driver, energy_tolerance=tolerance)
        
        if result.get("error"):
            return JsonResponse({"status": "error", "message": result["error"]}, status=400)
        
        # Track the change for Recent Changes panel
        lu.refresh_from_db()  # Get updated values
        new_ha = lu.target_ha
        new_percent = (lu.target_ha / lu.parent.target_ha * 100) if (lu.parent and lu.parent.target_ha) else 0
        change_ha = new_ha - old_ha
        
        landuse_change = {
            "code": lu.code,
            "name": lu.name,
            "old_percent": round(old_percent, 2),
            "new_percent": round(new_percent, 2),
            "old_ha": round(old_ha, 2) if old_ha else 0,
            "new_ha": round(new_ha, 2),
            "change_ha": round(change_ha, 2),
            "source": "balance_" + driver  # Mark as automatic change
        }
        
        summary = {
            "status": "balanced" if result["is_balanced"] else "partial",
            "initial_gap": result.get("initial_gap", result.get("final_gap")),
            "final_gap": result.get("final_gap", 0),
            "initial_ha": result.get("initial_ha", result.get("final_ha")),
            "final_ha": result.get("final_ha", 0),
            "demand": result.get("demand", 0),
            "renewable": result.get("renewable", 0),
            "driver": result.get("driver", driver_code),
            "landuse_change": landuse_change,  # Include change for tracking
        }
        return JsonResponse({"status": "ok", "summary": summary})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": f"Balance failed: {str(e)}"}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_energy_lu6(request):
    """
    GoalSeek outer loop: adjust LU_6 (Windparkfläche) land area until
    renewable total (10.1) matches verbrauch_gesamt.ziel.gesamt (gap ≈ 0).
    Same functionality as balance_energy but uses LU_6 instead of LU_2.1/LU_1.1.
    """
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    tolerance = float(data.get("tolerance", 1.0))  # GWh tolerance for total gap

    driver_code = "LU_6"
    try:
        lu = LandUse.objects.get(code=driver_code)
    except LandUse.DoesNotExist:
        return JsonResponse({"status": "error", "message": f"LandUse {driver_code} not found"}, status=400)

    try:
        # Track old value before balance
        old_ha = lu.target_ha
        old_percent = (lu.target_ha / lu.parent.target_ha * 100) if (lu.parent and lu.parent.target_ha) else 0

        # Use modified core function for LU_6
        result = _balance_energy_lu6_core(energy_tolerance=tolerance)
        
        if result.get("error"):
            return JsonResponse({"status": "error", "message": result["error"]}, status=400)
        
        # Track the change for Recent Changes panel
        lu.refresh_from_db()  # Get updated values
        new_ha = lu.target_ha
        new_percent = (lu.target_ha / lu.parent.target_ha * 100) if (lu.parent and lu.parent.target_ha) else 0
        change_ha = new_ha - old_ha
        
        landuse_change = {
            "code": lu.code,
            "name": lu.name,
            "old_percent": round(old_percent, 2),
            "new_percent": round(new_percent, 2),
            "old_ha": round(old_ha, 2) if old_ha else 0,
            "new_ha": round(new_ha, 2),
            "change_ha": round(change_ha, 2),
            "source": "balance_lu6"  # Mark as automatic change
        }
        
        summary = {
            "status": "balanced" if result["is_balanced"] else "partial",
            "initial_gap": result.get("initial_gap", result.get("final_gap")),
            "final_gap": result.get("final_gap", 0),
            "initial_ha": result.get("initial_ha", result.get("final_ha")),
            "final_ha": result.get("final_ha", 0),
            "demand": result.get("demand", 0),
            "renewable": result.get("renewable", 0),
            "driver": result.get("driver", driver_code),
            "landuse_change": landuse_change,  # Include change for tracking
        }
        return JsonResponse({"status": "ok", "summary": summary})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": f"Balance failed: {str(e)}"}, status=500)


@login_required
@require_http_methods(["POST"])
def run_full_recalc_view(request):
    """
    Explicitly run the heavy cascade once and store a CalculationRun snapshot.
    Intended for the staged “calculate once, read many” flow.
    """
    summary = run_full_recalc()
    run = CalculationRun.objects.create(
        duration_ms=summary["duration_ms"],
        summary=summary,
        triggered_by=request.user.username,
    )
    request.session["latest_run_id"] = run.id
    return JsonResponse(
        {
            "status": "ok",
            "run_id": run.id,
            "duration_ms": run.duration_ms,
            "summary": summary,
            "created_at": run.created_at.isoformat(),
            "landuse_changes": summary.get("landuse_changes", []),  # Include changes for tracking
        }
    )


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def recalc_ws_formulas_view(request):
    """
    Recalculate ALL WS data using formulas from WSFormulaTemplate.
    
    UPDATED: 9.3.1 and 9.3.4 are fixed and are not updated from WS.
    """
    import time
    start = time.time()
    
    try:
        # from simulator.ws_formula_service import recalculate_all_ws_data (moved to top)
        # Step 1: Recalculate WS data
        ws_stats = recalculate_all_ws_data()
        
        duration_ms = int((time.time() - start) * 1000)
        
        return JsonResponse({
            'status': 'ok',
            'message': f"WS Recalculation complete! WS: {ws_stats['updated']}",
            'ws_updated': ws_stats['updated'],
            'ws_errors': ws_stats['errors'],
            'duration_ms': duration_ms,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def unified_recalc_view(request):
    """
    🔄 UNIFIED RECALCULATION WITH OPTIONAL AUTO-BALANCE
    
    This is the RECOMMENDED way to recalculate everything at once.
    
    Order:
    1. Recalculate INPUT renewables (excluding 9.3.1, 9.3.4)
    2. Recalculate WS data
    3. Keep 9.3.1/9.3.4 fixed from DB (no WS -> renewable writes)
    4. (Optional) Auto-balance if balance_after=true
    
    Request body (optional):
    {
        "balance_after": true,      // Auto-balance after recalc (default: true)
        "ws_tolerance": 10.0,       // WS balance tolerance GWh (default: 10.0)
        "energy_tolerance": 1.0,    // Energy balance tolerance GWh (default: 1.0)
        "max_balance_cycles": 6     // Max balance iterations (default: 6)
    }
    
    Result: All values are consistent, system is balanced.
    """
    try:
        # Parse request body for options
        try:
            data = json.loads(request.body or "{}")
        except Exception:
            data = {}
        
        balance_after = data.get('balance_after', True)  # Default: auto-balance
        ws_tolerance = float(data.get('ws_tolerance', 10.0))
        energy_tolerance = float(data.get('energy_tolerance', 1.0))
        max_balance_cycles = int(data.get('max_balance_cycles', 6))
        
        # Import the combined function
        from simulator.recalc_service import unified_recalc_and_balance
        
        # Run unified recalc with optional balance
        stats = unified_recalc_and_balance(
            balance_after=balance_after,
            ws_tolerance=ws_tolerance,
            energy_tolerance=energy_tolerance,
            max_balance_cycles=max_balance_cycles
        )
        
        recalc = stats.get('recalc', {})
        balance = stats.get('balance', {})
        
        # Build response message
        message_parts = [
            f"Input: {recalc.get('input_renewables', 0)}",
            f"WS: {recalc.get('ws_updated', 0)}",
            "Fixed 9.3.1/9.3.4 applied"
        ]
        
        if balance_after:
            if stats.get('is_balanced'):
                message_parts.append(f"✅ Balanced (gap: {balance.get('final_gap', 0):.2f} GWh)")
            else:
                message_parts.append(f"⚠️ Balance incomplete (gap: {balance.get('final_gap', 0):.2f} GWh)")
        
        return JsonResponse({
            'status': 'ok',
            'message': f"Unified recalc complete! {' | '.join(message_parts)}",
            'input_renewables': recalc.get('input_renewables', 0),
            'ws_updated': recalc.get('ws_updated', 0),
            'output_renewables': recalc.get('output_renewables', 0),
            'duration_ms': stats.get('duration_ms', 0),
            'is_balanced': stats.get('is_balanced', False),
            'balance': balance,
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
def create_baseline(request):
    """
    Create a baseline backup of the database.
    This is a special backup that can be restored to at any time.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)
    
    try:
        import shutil
        from pathlib import Path
        from django.conf import settings
        import time
        
        # Path to current database
        base_dir = settings.BASE_DIR
        current_db = base_dir / 'db.sqlite3'
        baseline_db = base_dir / 'db_baseline.sqlite3'
        
        if not current_db.exists():
            return JsonResponse({'status': 'error', 'error': 'Database not found'}, status=500)
        
        # Copy current db to baseline
        shutil.copy2(current_db, baseline_db)
        
        # Get timestamp and size
        stat = baseline_db.stat()
        size_mb = stat.st_size / (1024 * 1024)
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
        
        return JsonResponse({
            'status': 'ok',
            'message': 'Baseline backup created successfully',
            'created_at': created_at,
            'size_mb': round(size_mb, 2)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@csrf_exempt
def restore_baseline(request):
    """
    Restore database from baseline backup.
    WARNING: This will overwrite all current data!
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)
    
    try:
        import shutil
        from pathlib import Path
        from django.conf import settings
        from django.db import connection
        
        base_dir = settings.BASE_DIR
        current_db = base_dir / 'db.sqlite3'
        baseline_db = base_dir / 'db_baseline.sqlite3'
        
        if not baseline_db.exists():
            return JsonResponse({
                'status': 'error',
                'error': 'No baseline backup found. Create one first!'
            }, status=404)
        
        # Close all database connections
        connection.close()
        
        # Copy baseline to current
        shutil.copy2(baseline_db, current_db)
        
        return JsonResponse({
            'status': 'ok',
            'message': 'Database restored to baseline successfully. Please refresh the page.'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@csrf_exempt
def get_baseline_info(request):
    """
    Get information about the baseline backup.
    """
    try:
        from pathlib import Path
        from django.conf import settings
        import time
        
        base_dir = settings.BASE_DIR
        baseline_db = base_dir / 'db_baseline.sqlite3'
        
        if not baseline_db.exists():
            return JsonResponse({
                'status': 'ok',
                'exists': False
            })
        
        stat = baseline_db.stat()
        size_mb = stat.st_size / (1024 * 1024)
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
        
        return JsonResponse({
            'status': 'ok',
            'exists': True,
            'created_at': created_at,
            'size_mb': round(size_mb, 2)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@csrf_exempt
def recalc_verbrauch_view(request):
    """
    Recalculate all VerbrauchData items.
    Similar to run_full_recalc but only for Verbrauch table.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)
    
    import time
    start = time.time()
    
    try:
        from simulator.verbrauch_recalculator import recalc_all_verbrauch
        
        # Recalculate all verbrauch items
        updated_count = recalc_all_verbrauch()
        
        duration_ms = int((time.time() - start) * 1000)
        
        return JsonResponse({
            'status': 'ok',
            'updated': updated_count,
            'duration_ms': duration_ms,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


def update_verbrauch_bulk(request):
    """
    Update user_percent for multiple VerbrauchData items in bulk.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        updates = data.get('updates', [])
        
        updated_count = 0
        for update in updates:
            code = update.get('code')
            user_percent = update.get('user_percent')
            
            if code and user_percent is not None:
                try:
                    item = VerbrauchData.objects.get(code=code)
                    item.user_percent = float(user_percent)
                    item.save()
                    updated_count += 1
                except VerbrauchData.DoesNotExist:
                    pass
        
        return JsonResponse({
            'status': 'ok',
            'updated': updated_count,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def save_verbrauch_user_input(request):
    """
    Save user input for a single Verbrauch item and trigger recalculation.
    Similar to land use: saves value, applies it, and recalculates everything.
    
    Returns which percentage siblings were auto-rebalanced for UI highlighting.
    """
    try:
        data = json.loads(request.body)
        code = data.get('code')
        user_percent = data.get('user_percent')
        
        if not code:
            return JsonResponse({'success': False, 'error': 'Missing code'}, status=400)
        
        # Get the item
        try:
            item = VerbrauchData.objects.get(code=code)
        except VerbrauchData.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Verbrauch code {code} not found'}, status=404)
        
        # Update user_percent
        old_value = item.user_percent
        item.user_percent = float(user_percent) if user_percent is not None else None
        item.save()  # This will trigger the cascade via signal
        
        # Get rebalancing info (if this was a percentage in a group)
        rebalanced = {}
        try:
            from simulator.percentage_rebalancer import get_percentage_group
            group = get_percentage_group(code)
            if group and item.unit == '%':
                # Fetch updated values for all group members
                for member_code in group['member_codes']:
                    try:
                        member = VerbrauchData.objects.get(code=member_code)
                        rebalanced[member_code] = {
                            'new': member.ziel,
                            'user_percent': member.user_percent,
                            'is_primary': member_code == code
                        }
                    except VerbrauchData.DoesNotExist:
                        pass
        except Exception as e:
            print(f"Error getting rebalance info: {e}")
        
        return JsonResponse({
            'success': True,
            'code': code,
            'old_value': old_value,
            'new_value': item.user_percent,
            'message': f'Updated {code} user input to {user_percent}% and triggered recalculation',
            'rebalanced': rebalanced  # Dict of sibling codes with their new values
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid value: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

