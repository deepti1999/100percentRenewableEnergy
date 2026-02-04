"""
Complete WS Formula System - Database Implementation
Based on exact specifications from WS documentation
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable
from django.core.cache import cache
from django.db import transaction

print("="*80)
print("COMPLETE WS FORMULA SYSTEM - Database Implementation")
print("="*80)

# Delete all existing WS formulas
print("\nDeleting old WS formulas...")
Formula.objects.filter(category='ws').delete()

with transaction.atomic():
    
    # ========================================
    # ROW 366 REFERENCE CALCULATIONS
    # ========================================
    print("\n1. Creating Row 366 Reference Formulas...")
    
    # davon_raumw_korr_366 = Verbrauch 2.9.2.ziel × (Verbrauch 2.4.ziel / 100)
    f = Formula.objects.create(
        key='WS_DAVON_RAUMW_KORR_366',
        category='ws',
        expression='V_2_9_2_ziel * (V_2_4_ziel / 100)',
        description='Row 366: Heating correction reference from Verbrauch'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='V_2_9_2_ziel',
        source_type='verbrauch_ziel',
        source_key='2.9.2',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='V_2_4_ziel',
        source_type='verbrauch_ziel',
        source_key='2.4',
        default_value=0.0
    )
    print("  ✓ WS_DAVON_RAUMW_KORR_366")
    
    # Annual Electricity Diagram Components
    # K (PV) = 1.1.2.1.2 + 1.2.1.2
    f = Formula.objects.create(
        key='WS_REF_PV',
        category='ws',
        expression='R_1_1_2_1_2 + R_1_2_1_2',
        description='PV generation total'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_1_1_2_1_2',
        source_type='renewable_target',
        source_key='1.1.2.1.2',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_1_2_1_2',
        source_type='renewable_target',
        source_key='1.2.1.2',
        default_value=0.0
    )
    print("  ✓ WS_REF_PV")
    
    # J (Wind) = 2.1.1.2.2 + 2.2.1.2
    f = Formula.objects.create(
        key='WS_REF_WIND',
        category='ws',
        expression='R_2_1_1_2_2 + R_2_2_1_2',
        description='Wind generation total'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_2_1_1_2_2',
        source_type='renewable_target',
        source_key='2.1.1.2.2',
        default_value=0.0
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_2_2_1_2',
        source_type='renewable_target',
        source_key='2.2.1.2',
        default_value=0.0
    )
    print("  ✓ WS_REF_WIND")
    
    # L (Hydro) = 3.1.1.2
    f = Formula.objects.create(
        key='WS_REF_HYDRO',
        category='ws',
        expression='R_3_1_1_2',
        description='Hydro generation'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_3_1_1_2',
        source_type='renewable_target',
        source_key='3.1.1.2',
        default_value=0.0
    )
    print("  ✓ WS_REF_HYDRO")
    
    # S (Biomass) = 4.4.1
    f = Formula.objects.create(
        key='WS_REF_BIO',
        category='ws',
        expression='R_4_4_1',
        description='Biomass energy'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_4_4_1',
        source_type='renewable_target',
        source_key='4.4.1',
        default_value=0.0
    )
    print("  ✓ WS_REF_BIO")
    
    # Electrolysis = 9.2.1.5.2
    f = Formula.objects.create(
        key='WS_REF_ELY',
        category='ws',
        expression='R_9_2_1_5_2',
        description='Electrolyzer Power-to-Gas'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_9_2_1_5_2',
        source_type='renewable_target',
        source_key='9.2.1.5.2',
        default_value=0.0
    )
    print("  ✓ WS_REF_ELY")
    
    # N Output = 9.3.1
    f = Formula.objects.create(
        key='WS_REF_N_OUTPUT',
        category='ws',
        expression='R_9_3_1',
        description='N Output Branch'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_9_3_1',
        source_type='renewable_target',
        source_key='9.3.1',
        default_value=0.0
    )
    print("  ✓ WS_REF_N_OUTPUT")
    
    # N Input = 9.3.4
    f = Formula.objects.create(
        key='WS_REF_N_INPUT',
        category='ws',
        expression='R_9_3_4',
        description='N Input Branch'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='R_9_3_4',
        source_type='renewable_target',
        source_key='9.3.4',
        default_value=0.0
    )
    print("  ✓ WS_REF_N_INPUT")
    
    # M total = PV + Wind + Hydro
    f = Formula.objects.create(
        key='WS_REF_TOTAL_GEN',
        category='ws',
        expression='WS_REF_PV + WS_REF_WIND + WS_REF_HYDRO',
        description='Total renewable generation (M node)'
    )
    print("  ✓ WS_REF_TOTAL_GEN")
    
    # N value = M - Electrolysis
    f = Formula.objects.create(
        key='WS_REF_AFTER_ELY',
        category='ws',
        expression='WS_REF_TOTAL_GEN - WS_REF_ELY',
        description='Energy after electrolyzer'
    )
    print("  ✓ WS_REF_AFTER_ELY")
    
    # Gas storage = N_OUTPUT * 0.65
    f = Formula.objects.create(
        key='WS_REF_GAS_STORAGE',
        category='ws',
        expression='WS_REF_N_OUTPUT * 0.65',
        description='Gas storage with 65% efficiency'
    )
    print("  ✓ WS_REF_GAS_STORAGE")
    
    # T value = (Gas storage - 160)
    f = Formula.objects.create(
        key='WS_REF_T_VALUE',
        category='ws',
        expression='WS_REF_GAS_STORAGE - 160',
        description='T value for reconversion'
    )
    print("  ✓ WS_REF_T_VALUE")
    
    # O (direct to grid) = N - N_INPUT - N_OUTPUT
    f = Formula.objects.create(
        key='WS_REF_N_TO_RIGHT',
        category='ws',
        expression='WS_REF_AFTER_ELY - WS_REF_N_INPUT - WS_REF_N_OUTPUT',
        description='Direct to grid (O)'
    )
    print("  ✓ WS_REF_N_TO_RIGHT")
    
    # stromverbr_raumwaerm_korr_366 = (T × 0.585) + O + S
    f = Formula.objects.create(
        key='WS_STROMVERBR_RAUMWAERM_KORR_366',
        category='ws',
        expression='(WS_REF_T_VALUE * 0.585) + WS_REF_N_TO_RIGHT + WS_REF_BIO',
        description='Row 366: Final grid supply from Annual Electricity'
    )
    print("  ✓ WS_STROMVERBR_RAUMWAERM_KORR_366")
    
    # Percentage for distribution = (After_Ely / Total_Gen) * 100
    f = Formula.objects.create(
        key='WS_REF_PERCENTAGE',
        category='ws',
        expression='(WS_REF_AFTER_ELY / WS_REF_TOTAL_GEN) * 100',
        description='Distribution percentage'
    )
    print("  ✓ WS_REF_PERCENTAGE")
    
    # solarstrom_366 = PV * (percentage / 100)
    f = Formula.objects.create(
        key='WS_SOLARSTROM_366',
        category='ws',
        expression='WS_REF_PV * (WS_REF_PERCENTAGE / 100)',
        description='Row 366: Solar share'
    )
    print("  ✓ WS_SOLARSTROM_366")
    
    # windstrom_366 = Wind * (percentage / 100)
    f = Formula.objects.create(
        key='WS_WINDSTROM_366',
        category='ws',
        expression='WS_REF_WIND * (WS_REF_PERCENTAGE / 100)',
        description='Row 366: Wind share'
    )
    print("  ✓ WS_WINDSTROM_366")
    
    # sonst_kraft_konstant_366 = Hydro * (percentage / 100)
    f = Formula.objects.create(
        key='WS_SONST_KRAFT_KONSTANT_366',
        category='ws',
        expression='WS_REF_HYDRO * (WS_REF_PERCENTAGE / 100)',
        description='Row 366: Hydro share'
    )
    print("  ✓ WS_SONST_KRAFT_KONSTANT_366")
    
    # ========================================
    # DAILY FORMULAS (Rows 1-365)
    # ========================================
    print("\n2. Creating Daily Formulas (Rows 1-365)...")
    
    # stromverbr = stromverbr_raumwaerm_korr_366 × verbrauch_promille / 1000
    f = Formula.objects.create(
        key='WS_STROMVERBR',
        category='ws',
        expression='WS_STROMVERBR_RAUMWAERM_KORR_366 * verbrauch_promille / 1000',
        description='Daily consumption'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='verbrauch_promille',
        source_type='ws_current_row',
        source_key='verbrauch_promille',
        default_value=0.0
    )
    print("  ✓ WS_STROMVERBR")
    
    # davon_raumw_korr = davon_raumw_korr_366 × heizung_abwaerm_promille / 365
    f = Formula.objects.create(
        key='WS_DAVON_RAUMW_KORR',
        category='ws',
        expression='WS_DAVON_RAUMW_KORR_366 * heizung_abwaerm_promille / 365',
        description='Daily heating correction'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='heizung_abwaerm_promille',
        source_type='ws_current_row',
        source_key='heizung_abwaerm_promille',
        default_value=0.0
    )
    print("  ✓ WS_DAVON_RAUMW_KORR")
    
    # stromverbr_raumwaerm_korr = stromverbr + davon_raumw_korr
    f = Formula.objects.create(
        key='WS_STROMVERBR_RAUMWAERM_KORR',
        category='ws',
        expression='WS_STROMVERBR + WS_DAVON_RAUMW_KORR',
        description='Consumption + heating'
    )
    print("  ✓ WS_STROMVERBR_RAUMWAERM_KORR")
    
    # windstrom = wind_promille × windstrom_366 / 1000
    f = Formula.objects.create(
        key='WS_WINDSTROM',
        category='ws',
        expression='wind_promille * WS_WINDSTROM_366 / 1000',
        description='Daily wind'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='wind_promille',
        source_type='ws_current_row',
        source_key='wind_promille',
        default_value=0.0
    )
    print("  ✓ WS_WINDSTROM")
    
    # solarstrom = solar_promille × solarstrom_366 / 1000
    f = Formula.objects.create(
        key='WS_SOLARSTROM',
        category='ws',
        expression='solar_promille * WS_SOLARSTROM_366 / 1000',
        description='Daily solar'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='solar_promille',
        source_type='ws_current_row',
        source_key='solar_promille',
        default_value=0.0
    )
    print("  ✓ WS_SOLARSTROM")
    
    # sonst_kraft_konstant = sonst_kraft_konstant_366 / 365
    f = Formula.objects.create(
        key='WS_SONST_KRAFT_KONSTANT',
        category='ws',
        expression='WS_SONST_KRAFT_KONSTANT_366 / 365',
        description='Daily hydro (constant)'
    )
    print("  ✓ WS_SONST_KRAFT_KONSTANT")
    
    # wind_solar_konstant = windstrom + solarstrom + sonst_kraft_konstant
    f = Formula.objects.create(
        key='WS_WIND_SOLAR_KONSTANT',
        category='ws',
        expression='WS_WINDSTROM + WS_SOLARSTROM + WS_SONST_KRAFT_KONSTANT',
        description='Total generation'
    )
    print("  ✓ WS_WIND_SOLAR_KONSTANT")
    
    # direktverbr_strom = min(wind_solar_konstant, stromverbr_raumwaerm_korr)
    f = Formula.objects.create(
        key='WS_DIREKTVERBR_STROM',
        category='ws',
        expression='min(WS_WIND_SOLAR_KONSTANT, WS_STROMVERBR_RAUMWAERM_KORR)',
        description='Direct consumption'
    )
    print("  ✓ WS_DIREKTVERBR_STROM")
    
    # ueberschuss_strom = max(0, wind_solar_konstant - stromverbr_raumwaerm_korr)
    f = Formula.objects.create(
        key='WS_UEBERSCHUSS_STROM',
        category='ws',
        expression='max(0, WS_WIND_SOLAR_KONSTANT - WS_STROMVERBR_RAUMWAERM_KORR)',
        description='Surplus electricity'
    )
    print("  ✓ WS_UEBERSCHUSS_STROM")
    
    # einspeich = min(ueberschuss_strom, stromverbr_raumwaerm_korr) * 0.65
    f = Formula.objects.create(
        key='WS_EINSPEICH',
        category='ws',
        expression='min(WS_UEBERSCHUSS_STROM, WS_STROMVERBR_RAUMWAERM_KORR) * 0.65',
        description='Storage charge (η=0.65)'
    )
    print("  ✓ WS_EINSPEICH")
    
    # abregelung_z = max(0, ueberschuss_strom - (einspeich / 0.65))
    f = Formula.objects.create(
        key='WS_ABREGELUNG_Z',
        category='ws',
        expression='max(0, WS_UEBERSCHUSS_STROM - (WS_EINSPEICH / 0.65))',
        description='Curtailment'
    )
    print("  ✓ WS_ABREGELUNG_Z")
    
    # mangel_last = stromverbr_raumwaerm_korr - direktverbr_strom
    f = Formula.objects.create(
        key='WS_MANGEL_LAST',
        category='ws',
        expression='WS_STROMVERBR_RAUMWAERM_KORR - WS_DIREKTVERBR_STROM',
        description='Deficit'
    )
    print("  ✓ WS_MANGEL_LAST")
    
    # Clear all formula caches
    cache.clear()
    
    print("\n" + "="*80)
    print(f"✅ Created {Formula.objects.filter(category='ws').count()} WS formulas")
    print("="*80)
    print("\nFormulas now reference RenewableData and VerbrauchData directly!")
    print("Row 366 will be calculated from Renewable/Verbrauch data automatically.")

