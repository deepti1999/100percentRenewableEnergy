"""
Correct WS formulas based on actual calculation logic from archive scripts
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable
from django.core.cache import cache
from django.db import transaction

print("="*80)
print("FIXING WS FORMULAS - Using CORRECT logic from archive scripts")
print("="*80)

# Delete all existing WS formulas to start fresh
print("\nDeleting old WS formulas...")
deleted_count = Formula.objects.filter(category='ws').delete()[0]
print(f"Deleted {deleted_count} old formulas")

correct_formulas = []

with transaction.atomic():
    # ========================================
    # DAILY FORMULAS (rows 1-365)
    # ========================================
    
    # Column G: stromverbr
    f = Formula.objects.create(
        key='WS_STROMVERBR',
        category='ws',
        expression='stromverbr_raumwaerm_korr_366 * verbrauch_promille / 1000',
        description='Daily consumption from row 366 reference'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='stromverbr_raumwaerm_korr_366',
        source_type='ws_row_366',
        source_key='stromverbr_raumwaerm_korr',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='verbrauch_promille',
        source_type='ws_current_row',
        source_key='verbrauch_promille',
        default_value=0.0
    )
    correct_formulas.append('WS_STROMVERBR')
    
    # Column H: davon_raumw_korr
    f = Formula.objects.create(
        key='WS_DAVON_RAUMW_KORR',
        category='ws',
        expression='davon_raumw_korr_366 * heizung_abwaerm_promille / 365',
        description='Daily heating correction'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='davon_raumw_korr_366',
        source_type='ws_row_366',
        source_key='davon_raumw_korr',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='heizung_abwaerm_promille',
        source_type='ws_current_row',
        source_key='heizung_abwaerm_promille',
        default_value=0.0
    )
    correct_formulas.append('WS_DAVON_RAUMW_KORR')
    
    # Column J: stromverbr_raumwaerm_korr
    f = Formula.objects.create(
        key='WS_STROMVERBR_RAUMWAERM_KORR',
        category='ws',
        expression='(stromverbr_raumwaerm_korr_366 * verbrauch_promille / 1000) + davon_raumw_korr',
        description='Consumption + heating'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='stromverbr_raumwaerm_korr_366',
        source_type='ws_row_366',
        source_key='stromverbr_raumwaerm_korr',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='verbrauch_promille',
        source_type='ws_current_row',
        source_key='verbrauch_promille',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='davon_raumw_korr',
        source_type='ws_current_row',
        source_key='davon_raumw_korr',
        default_value=0.0
    )
    correct_formulas.append('WS_STROMVERBR_RAUMWAERM_KORR')
    
    # Column K: windstrom
    f = Formula.objects.create(
        key='WS_WINDSTROM',
        category='ws',
        expression='wind_promille * windstrom_366 / 1000',
        description='Daily wind electricity'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='wind_promille',
        source_type='ws_current_row',
        source_key='wind_promille',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='windstrom_366',
        source_type='ws_row_366',
        source_key='windstrom',
        default_value=0.0
    )
    correct_formulas.append('WS_WINDSTROM')
    
    # Column L: solarstrom
    f = Formula.objects.create(
        key='WS_SOLARSTROM',
        category='ws',
        expression='solar_promille * solarstrom_366 / 1000',
        description='Daily solar electricity'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='solar_promille',
        source_type='ws_current_row',
        source_key='solar_promille',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='solarstrom_366',
        source_type='ws_row_366',
        source_key='solarstrom',
        default_value=0.0
    )
    correct_formulas.append('WS_SOLARSTROM')
    
    # Column M: sonst_kraft_konstant
    f = Formula.objects.create(
        key='WS_SONST_KRAFT_KONSTANT',
        category='ws',
        expression='sonst_kraft_konstant_366 / 365',
        description='Daily hydro (constant distribution)'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='sonst_kraft_konstant_366',
        source_type='ws_row_366',
        source_key='sonst_kraft_konstant',
        default_value=0.0
    )
    correct_formulas.append('WS_SONST_KRAFT_KONSTANT')
    
    # Column N: wind_solar_konstant
    f = Formula.objects.create(
        key='WS_WIND_SOLAR_KONSTANT',
        category='ws',
        expression='windstrom + solarstrom + sonst_kraft_konstant',
        description='Total generation'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='windstrom',
        source_type='ws_current_row',
        source_key='windstrom',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='solarstrom',
        source_type='ws_current_row',
        source_key='solarstrom',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='sonst_kraft_konstant',
        source_type='ws_current_row',
        source_key='sonst_kraft_konstant',
        default_value=0.0
    )
    correct_formulas.append('WS_WIND_SOLAR_KONSTANT')
    
    # Column O: direktverbr_strom
    f = Formula.objects.create(
        key='WS_DIREKTVERBR_STROM',
        category='ws',
        expression='min(wind_solar_konstant, stromverbr_raumwaerm_korr)',
        description='Direct consumption (minimum of generation and demand)'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='wind_solar_konstant',
        source_type='ws_current_row',
        source_key='wind_solar_konstant',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='stromverbr_raumwaerm_korr',
        source_type='ws_current_row',
        source_key='stromverbr_raumwaerm_korr',
        default_value=0.0
    )
    correct_formulas.append('WS_DIREKTVERBR_STROM')
    
    # Column P: ueberschuss_strom
    f = Formula.objects.create(
        key='WS_UEBERSCHUSS_STROM',
        category='ws',
        expression='max(0, wind_solar_konstant - stromverbr_raumwaerm_korr)',
        description='Surplus electricity'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='wind_solar_konstant',
        source_type='ws_current_row',
        source_key='wind_solar_konstant',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='stromverbr_raumwaerm_korr',
        source_type='ws_current_row',
        source_key='stromverbr_raumwaerm_korr',
        default_value=0.0
    )
    correct_formulas.append('WS_UEBERSCHUSS_STROM')
    
    print(f"\n✅ Created {len(correct_formulas)} correct WS formulas")
    for key in correct_formulas:
        print(f"   - {key}")
        cache.delete(f'formula_{key}')

print("\n" + "="*80)
print("✅ DONE! WS formulas corrected")
print("="*80)
print("\nNote: These formulas reference row 366 values which must be calculated first")
print("from RenewableData and VerbrauchData using the calculation engine.")
