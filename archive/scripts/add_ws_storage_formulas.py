"""
WS Second-Pass Storage Formulas
Requires sum_mangel_last to be computed first
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable
from django.core.cache import cache
from django.db import transaction

print("="*80)
print("WS SECOND-PASS STORAGE FORMULAS")
print("="*80)

with transaction.atomic():
    
    # ========================================
    # SECOND PASS - Storage & Compensation
    # ========================================
    print("\n3. Creating Second-Pass Storage Formulas...")
    
    # brennstoff_ausgleichs_strom = (bio_value / sum_mangel_last) × mangel_last
    # bio_value needs to be available as WS_REF_BIO
    f = Formula.objects.create(
        key='WS_BRENNSTOFF_AUSGLEICHS_STROM',
        category='ws',
        expression='(WS_REF_BIO / sum_mangel_last) * WS_MANGEL_LAST if sum_mangel_last > 0 else 0',
        description='Biomass compensation'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='sum_mangel_last',
        source_type='ws_sum',
        source_key='mangel_last',
        default_value=1.0
    )
    print("  ✓ WS_BRENNSTOFF_AUSGLEICHS_STROM")
    
    # speicher_ausgl_strom = mangel_last - brennstoff_ausgleichs_strom
    f = Formula.objects.create(
        key='WS_SPEICHER_AUSGL_STROM',
        category='ws',
        expression='WS_MANGEL_LAST - WS_BRENNSTOFF_AUSGLEICHS_STROM',
        description='Storage compensation'
    )
    print("  ✓ WS_SPEICHER_AUSGL_STROM")
    
    # ausspeich_rueckverstr = speicher_ausgl_strom / 0.585
    f = Formula.objects.create(
        key='WS_AUSSPEICH_RUECKVERSTR',
        category='ws',
        expression='WS_SPEICHER_AUSGL_STROM / 0.585',
        description='Storage discharge for reconversion (η=0.585)'
    )
    print("  ✓ WS_AUSSPEICH_RUECKVERSTR")
    
    # ausspeich_gas = 0 (always zero per spec)
    f = Formula.objects.create(
        key='WS_AUSSPEICH_GAS',
        category='ws',
        expression='0',
        description='Gas discharge (always 0)'
    )
    print("  ✓ WS_AUSSPEICH_GAS")
    
    # ladezust_burtto = previous + einspeich - ausspeich_rueckverstr - ausspeich_gas
    # This requires cumulative calculation - will be handled specially in code
    f = Formula.objects.create(
        key='WS_LADEZUST_BURTTO',
        category='ws',
        expression='prev_ladezust_burtto + WS_EINSPEICH - WS_AUSSPEICH_RUECKVERSTR - WS_AUSSPEICH_GAS',
        description='Gross storage level (cumulative)'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='prev_ladezust_burtto',
        source_type='ws_previous_row',
        source_key='ladezust_burtto',
        default_value=0.0
    )
    print("  ✓ WS_LADEZUST_BURTTO")
    
    # selbstentl = 0 (self-discharge, currently zero)
    f = Formula.objects.create(
        key='WS_SELBSTENTL',
        category='ws',
        expression='0',
        description='Self-discharge (currently 0)'
    )
    print("  ✓ WS_SELBSTENTL")
    
    # ladezustand_abs_vorl_tl = ladezust_burtto - ladezust_burtto_367
    f = Formula.objects.create(
        key='WS_LADEZUSTAND_ABS_VORL_TL',
        category='ws',
        expression='WS_LADEZUST_BURTTO - ladezust_burtto_367',
        description='Absolute storage (preliminary)'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='ladezust_burtto_367',
        source_type='ws_row_367',
        source_key='ladezust_burtto',
        default_value=0.0
    )
    print("  ✓ WS_LADEZUSTAND_ABS_VORL_TL")
    
    # ladezustand_netto cumulative (like brutto but with selbstentl)
    f = Formula.objects.create(
        key='WS_LADEZUSTAND_NETTO',
        category='ws',
        expression='prev_ladezustand_netto + WS_EINSPEICH - WS_AUSSPEICH_RUECKVERSTR - WS_AUSSPEICH_GAS - WS_SELBSTENTL',
        description='Net storage level (cumulative)'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='prev_ladezustand_netto',
        source_type='ws_previous_row',
        source_key='ladezustand_netto',
        default_value=0.0
    )
    print("  ✓ WS_LADEZUSTAND_NETTO")
    
    # ladezustand_abs = ladezustand_netto - ladezustand_netto_367
    f = Formula.objects.create(
        key='WS_LADEZUSTAND_ABS',
        category='ws',
        expression='WS_LADEZUSTAND_NETTO - ladezustand_netto_367',
        description='Absolute net storage'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='ladezustand_netto_367',
        source_type='ws_row_367',
        source_key='ladezustand_netto',
        default_value=0.0
    )
    print("  ✓ WS_LADEZUSTAND_ABS")
    
    # ========================================
    # ROW 367 FORMULAS
    # ========================================
    print("\n4. Creating Row 367 Offset Formulas...")
    
    # brennstoff_ausgleichs_strom_367 = sum_mangel_last
    f = Formula.objects.create(
        key='WS_BRENNSTOFF_AUSGLEICHS_STROM_367',
        category='ws',
        expression='sum_mangel_last',
        description='Row 367: Biomass total'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='sum_mangel_last',
        source_type='ws_sum',
        source_key='mangel_last',
        default_value=0.0
    )
    print("  ✓ WS_BRENNSTOFF_AUSGLEICHS_STROM_367")
    
    # ladezust_burtto_367 = min of daily values (1-365)
    # This needs to be computed specially, but here's the formula reference
    f = Formula.objects.create(
        key='WS_LADEZUST_BURTTO_367',
        category='ws',
        expression='min_ladezust_burtto',
        description='Row 367: Minimum gross storage'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='min_ladezust_burtto',
        source_type='ws_min',
        source_key='ladezust_burtto',
        default_value=0.0
    )
    print("  ✓ WS_LADEZUST_BURTTO_367")
    
    # ladezustand_netto_367 = min of daily net values
    f = Formula.objects.create(
        key='WS_LADEZUSTAND_NETTO_367',
        category='ws',
        expression='min_ladezustand_netto',
        description='Row 367: Minimum net storage'
    )
    FormulaVariable.objects.create(
        formula=f,
        variable_name='min_ladezustand_netto',
        source_type='ws_min',
        source_key='ladezustand_netto',
        default_value=0.0
    )
    print("  ✓ WS_LADEZUSTAND_NETTO_367")
    
    # ========================================
    # ROW 366 SUM FORMULAS
    # ========================================
    print("\n5. Creating Row 366 Sum Formulas...")
    
    # For row 366, most columns are sums of days 1-365
    sum_columns = [
        ('WS_STROMVERBR_366', 'stromverbr', 'Sum of daily consumption'),
        ('WS_WINDSTROM_366_SUM', 'windstrom', 'Sum of daily wind'),
        ('WS_SOLARSTROM_366_SUM', 'solarstrom', 'Sum of daily solar'),
        ('WS_SONST_KRAFT_KONSTANT_366_SUM', 'sonst_kraft_konstant', 'Sum of daily hydro'),
        ('WS_WIND_SOLAR_KONSTANT_366', 'wind_solar_konstant', 'Sum of daily generation'),
        ('WS_DIREKTVERBR_STROM_366', 'direktverbr_strom', 'Sum of daily direct consumption'),
        ('WS_UEBERSCHUSS_STROM_366', 'ueberschuss_strom', 'Sum of daily surplus'),
        ('WS_EINSPEICH_366', 'einspeich', 'Sum of daily charging'),
        ('WS_ABREGELUNG_Z_366', 'abregelung_z', 'Sum of daily curtailment'),
        ('WS_MANGEL_LAST_366', 'mangel_last', 'Sum of daily deficit'),
        ('WS_BRENNSTOFF_AUSGLEICHS_STROM_366', 'brennstoff_ausgleichs_strom', 'Sum of biomass compensation'),
        ('WS_SPEICHER_AUSGL_STROM_366', 'speicher_ausgl_strom', 'Sum of storage compensation'),
        ('WS_AUSSPEICH_RUECKVERSTR_366', 'ausspeich_rueckverstr', 'Sum of storage discharge'),
    ]
    
    for key, column, desc in sum_columns:
        f = Formula.objects.create(
            key=key,
            category='ws',
            expression=f'sum_{column}',
            description=f'Row 366: {desc}'
        )
        FormulaVariable.objects.create(
            formula=f,
            variable_name=f'sum_{column}',
            source_type='ws_sum',
            source_key=column,
            default_value=0.0
        )
        print(f"  ✓ {key}")
    
    # Storage deltas for row 366 (day 365 - day 1)
    delta_columns = [
        ('WS_LADEZUST_BURTTO_366', 'ladezust_burtto', 'Gross storage delta'),
        ('WS_LADEZUSTAND_ABS_VORL_TL_366', 'ladezustand_abs_vorl_tl', 'Preliminary absolute delta'),
        ('WS_LADEZUSTAND_NETTO_366', 'ladezustand_netto', 'Net storage delta'),
        ('WS_LADEZUSTAND_ABS_366', 'ladezustand_abs', 'Absolute storage delta'),
    ]
    
    for key, column, desc in delta_columns:
        f = Formula.objects.create(
            key=key,
            category='ws',
            expression=f'{column}_day_365 - {column}_day_1',
            description=f'Row 366: {desc}'
        )
        FormulaVariable.objects.create(
            formula=f,
            variable_name=f'{column}_day_365',
            source_type='ws_row',
            source_key=f'{column}:365',
            default_value=0.0
        )
        FormulaVariable.objects.create(
            formula=f,
            variable_name=f'{column}_day_1',
            source_type='ws_row',
            source_key=f'{column}:1',
            default_value=0.0
        )
        print(f"  ✓ {key}")
    
    cache.clear()
    
    print("\n" + "="*80)
    print(f"✅ Total WS formulas: {Formula.objects.filter(category='ws').count()}")
    print("="*80)
    print("\nComplete formula system created!")
    print("- Row 366 references from Renewable/Verbrauch")
    print("- Daily formulas for rows 1-365")
    print("- Second-pass storage calculations")
    print("- Row 367 offset values")
    print("- Row 366 sums and deltas")
