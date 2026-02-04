#!/usr/bin/env python3
"""
Complete WS and Annual Electricity Formula Seeding Script
==========================================================
Seeds all formulas for:
1. WS daily rows (1-365) - all columns
2. WS row 366 (annual totals)
3. WS row 367 (reference row)
4. Annual Electricity diagram with WS row 366 override logic
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula

def seed_annual_electricity_formulas():
    """
    Seed Annual Electricity diagram formulas.
    These formulas use WS row 366 values when present to override defaults.
    """
    print("\n=== Seeding Annual Electricity Formulas ===")
    
    formulas = [
        # Basic renewable inputs (prefer target, fallback to status)
        {
            'key': 'AE_PV',
            'category': 'annual',
            'expression': 'Renewable_1_1_2_1_2 + Renewable_1_2_1_2',
            'description': 'PV total (K node): sum of codes 1.1.2.1.2 + 1.2.1.2',
        },
        {
            'key': 'AE_WIND',
            'category': 'annual',
            'expression': 'Renewable_2_1_1_2_2 + Renewable_2_2_1_2',
            'description': 'Wind total (J node): sum of codes 2.1.1.2.2 + 2.2.1.2',
        },
        {
            'key': 'AE_HYDRO',
            'category': 'annual',
            'expression': 'Renewable_3_1_1_2',
            'description': 'Hydro/Geo (L node): code 3.1.1.2',
        },
        {
            'key': 'AE_BIO',
            'category': 'annual',
            'expression': 'Renewable_4_4_1',
            'description': 'Biomass (S node): code 4.4.1',
        },
        
        # M node total
        {
            'key': 'AE_M_TOTAL',
            'category': 'annual',
            'expression': 'AE_PV + AE_WIND + AE_HYDRO',
            'description': 'M node total: PV + Wind + Hydro',
        },
        
        # Electrolysis branch from M
        {
            'key': 'AE_ELY_BRANCH',
            'category': 'annual',
            'expression': 'Renewable_9_2_1_5_2',
            'description': 'Electrolysis branch: code 9.2.1.5.2',
        },
        {
            'key': 'AE_H2_OFFER',
            'category': 'annual',
            'expression': 'AE_ELY_BRANCH * WS_ETA_STROM_GAS',
            'description': 'H2 offer from electrolysis: ely_branch * 0.65',
        },
        
        # N node value (after electrolysis)
        {
            'key': 'AE_N_VALUE',
            'category': 'annual',
            'expression': 'AE_M_TOTAL - AE_ELY_BRANCH',
            'description': 'N remaining energy after electrolysis: M - ely_branch',
        },
        
        # Q (Abregelung) - WS row 366 override if present
        {
            'key': 'AE_N_INPUT',
            'category': 'annual',
            'expression': 'WS_ABREGELUNG_Z_366 if WS_ABREGELUNG_Z_366 is not None else Renewable_9_3_4',
            'description': 'Q/Abregelung: use WS row 366 abregelung_z if present, else code 9.3.4',
        },
        
        # N output branch (to storage) - WS row 366 override if present
        {
            'key': 'AE_N_OUTPUT',
            'category': 'annual',
            'expression': '(WS_EINSPEICH_366 / WS_ETA_STROM_GAS) if WS_EINSPEICH_366 is not None else Renewable_9_3_1',
            'description': 'N output to storage: use WS row 366 einspeich/0.65 if present, else code 9.3.1',
        },
        
        # Gas storage (U node)
        {
            'key': 'AE_GAS_STORAGE',
            'category': 'annual',
            'expression': 'AE_N_OUTPUT * WS_ETA_STROM_GAS',
            'description': 'Gas storage (U): n_output_branch * 0.65',
        },
        {
            'key': 'AE_GAS_STORAGE_WS',
            'category': 'annual',
            'expression': 'AE_N_OUTPUT * WS_ETA_STROM_GAS',
            'description': 'Gas storage for WS reference: same as AE_GAS_STORAGE',
        },
        {
            'key': 'AE_H2_SURPLUS',
            'category': 'annual',
            'expression': 'AE_N_OUTPUT * WS_ETA_STROM_GAS',
            'description': 'H2 surplus to storage: n_output_branch * 0.65',
        },
        
        # T (reconversion) - WS row 366 override if present
        {
            'key': 'AE_T_VALUE',
            'category': 'annual',
            'expression': 'AE_GAS_STORAGE - WS_STORAGE_CAPACITY',
            'description': 'T value (gas for reconversion): gas_storage - 160',
        },
        {
            'key': 'AE_T_OUTPUT',
            'category': 'annual',
            'expression': '(WS_AUSSPEICH_RUECKVERSTR_366 * WS_ETA_GAS_STROM) if WS_AUSSPEICH_RUECKVERSTR_366 is not None else (AE_T_VALUE * WS_ETA_GAS_STROM)',
            'description': 'T output (reconversion to electricity): use WS row 366 ausspeich_rueckverstr*0.585 if present, else t_value*0.585',
        },
        
        # N to right (direct to grid)
        {
            'key': 'AE_N_TO_RIGHT',
            'category': 'annual',
            'expression': 'AE_N_VALUE - AE_N_INPUT - AE_N_OUTPUT',
            'description': 'N to right (O, direct to grid): n_value - q_abregelung - n_output_branch',
        },
        
        # Final grid supply (yellow block)
        {
            'key': 'AE_FINAL_STROMNETZ',
            'category': 'annual',
            'expression': 'AE_T_OUTPUT + AE_N_TO_RIGHT + AE_BIO',
            'description': 'Final Stromnetz zum Endverbrauch: t_output + n_to_right + bio (used for WS row 366 col J)',
        },
    ]
    
    for formula_data in formulas:
        formula, created = Formula.objects.update_or_create(
            key=formula_data['key'],
            category=formula_data['category'],
            defaults={
                'expression': formula_data['expression'],
                'description': formula_data['description'],
                'is_active': True,
            }
        )
        status = "✅ Created" if created else "🔄 Updated"
        print(f"{status} {formula.key}: {formula.expression[:60]}...")
    
    print(f"\n✅ Seeded {len(formulas)} Annual Electricity formulas")


def seed_ws_daily_formulas():
    """
    Seed WS daily formulas (rows 1-365).
    These formulas apply to each individual day.
    """
    print("\n=== Seeding WS Daily Formulas (Rows 1-365) ===")
    
    formulas = [
        # FIRST PASS: Non-cumulative columns
        {
            'key': 'WS_STROMVERBR',
            'expression': 'stromverbr_raumwaerm_korr_366 * verbrauch_promille / 1000',
            'description': 'Daily electricity consumption: row366 ref * promille / 1000',
        },
        {
            'key': 'WS_DAVON_RAUMW_KORR',
            'expression': 'davon_raumw_korr_366 * heizung_abwaerm_promille / 365',
            'description': 'Daily heating correction: row366 ref * heating promille / 365',
        },
        {
            'key': 'WS_STROMVERBR_RAUMWAERM_KORR',
            'expression': 'WS_STROMVERBR + WS_DAVON_RAUMW_KORR',
            'description': 'Corrected daily consumption: stromverbr + davon_raumw_korr',
        },
        {
            'key': 'WS_WINDSTROM',
            'expression': 'wind_promille * windstrom_366 / 1000',
            'description': 'Daily wind generation: wind_promille * row366 wind / 1000',
        },
        {
            'key': 'WS_SOLARSTROM',
            'expression': 'solar_promille * solarstrom_366 / 1000',
            'description': 'Daily solar generation: solar_promille * row366 solar / 1000',
        },
        {
            'key': 'WS_SONST_KRAFT_KONSTANT',
            'expression': 'sonst_kraft_konstant_366 / 365',
            'description': 'Daily constant generation (hydro): row366 hydro / 365',
        },
        {
            'key': 'WS_WIND_SOLAR_KONSTANT',
            'expression': 'WS_WINDSTROM + WS_SOLARSTROM + WS_SONST_KRAFT_KONSTANT',
            'description': 'Total daily renewable: wind + solar + hydro',
        },
        {
            'key': 'WS_DIREKTVERBR_STROM',
            'expression': 'min(WS_WIND_SOLAR_KONSTANT, WS_STROMVERBR_RAUMWAERM_KORR)',
            'description': 'Direct consumption: min(renewable, demand)',
        },
        {
            'key': 'WS_UEBERSCHUSS_STROM',
            'expression': '0 if abs(WS_WIND_SOLAR_KONSTANT - WS_STROMVERBR_RAUMWAERM_KORR) < 0.01 else max(0, WS_WIND_SOLAR_KONSTANT - WS_STROMVERBR_RAUMWAERM_KORR)',
            'description': 'Surplus: (renewable - demand) if |diff| >= 0.01, else 0',
        },
        {
            'key': 'WS_EINSPEICH',
            'expression': '(WS_UEBERSCHUSS_STROM * 0.65) if (WS_UEBERSCHUSS_STROM / WS_STROMVERBR_RAUMWAERM_KORR if WS_STROMVERBR_RAUMWAERM_KORR > 0 else 0) <= 1 else (WS_STROMVERBR_RAUMWAERM_KORR * 1.0 * 0.65)',
            'description': 'Storage input: surplus*0.65 if ratio<=1, else demand*1.0*0.65 (n1=0.65, n2=1.0)',
        },
        {
            'key': 'WS_ABREGELUNG_Z',
            'expression': '0 if (WS_UEBERSCHUSS_STROM / WS_STROMVERBR_RAUMWAERM_KORR if WS_STROMVERBR_RAUMWAERM_KORR > 0 else 0) <= 1 else (WS_UEBERSCHUSS_STROM - (WS_EINSPEICH / 0.65))',
            'description': 'Curtailment: 0 if ratio<=1, else surplus - (einspeich/0.65)',
        },
        {
            'key': 'WS_MANGEL_LAST',
            'expression': 'WS_STROMVERBR_RAUMWAERM_KORR - WS_DIREKTVERBR_STROM',
            'description': 'Deficit: corrected demand - direct consumption',
        },
        
        # SECOND PASS: Requires sum_mangel_last from all days
        {
            'key': 'WS_BRENNSTOFF_AUSGLEICHS_STROM',
            'expression': '(bio_value / sum_mangel_last) * WS_MANGEL_LAST if sum_mangel_last > 0 else 0',
            'description': 'Biomass compensation: (bio/total_deficit) * daily_deficit',
        },
        {
            'key': 'WS_SPEICHER_AUSGL_STROM',
            'expression': 'WS_MANGEL_LAST - WS_BRENNSTOFF_AUSGLEICHS_STROM',
            'description': 'Storage compensation: deficit - biomass',
        },
        {
            'key': 'WS_AUSSPEICH_RUECKVERSTR',
            'expression': 'WS_SPEICHER_AUSGL_STROM / 0.585',
            'description': 'Storage output with loss: storage_comp / 0.585 (t1 efficiency)',
        },
        {
            'key': 'WS_AUSSPEICH_GAS',
            'expression': '0',
            'description': 'Gas output: always 0',
        },
        
        # THIRD PASS: Cumulative storage columns
        {
            'key': 'WS_LADEZUST_BURTTO',
            'expression': 'WS_LADEZUST_BURTTO_PREV + WS_EINSPEICH - WS_AUSSPEICH_RUECKVERSTR - WS_AUSSPEICH_GAS',
            'description': 'Gross storage state: prev + input - reconversion - gas',
        },
        {
            'key': 'WS_LADEZUSTAND_ABS_VORL_TL',
            'expression': 'WS_LADEZUST_BURTTO - ladezust_burtto_367',
            'description': 'Absolute gross storage: current - row367 reference',
        },
        {
            'key': 'WS_SELBSTENTL',
            'expression': '0',
            'description': 'Self-discharge: always 0',
        },
        {
            'key': 'WS_LADEZUSTAND_NETTO',
            'expression': 'WS_LADEZUSTAND_NETTO_PREV + WS_EINSPEICH - WS_AUSSPEICH_RUECKVERSTR - WS_AUSSPEICH_GAS - WS_SELBSTENTL',
            'description': 'Net storage state: prev + input - outputs - self-discharge',
        },
        {
            'key': 'WS_LADEZUSTAND_ABS',
            'expression': 'WS_LADEZUSTAND_NETTO - ladezustand_netto_367',
            'description': 'Absolute net storage: current - row367 reference',
        },
    ]
    
    for formula_data in formulas:
        formula, created = Formula.objects.update_or_create(
            key=formula_data['key'],
            category='ws',
            defaults={
                'expression': formula_data['expression'],
                'description': formula_data['description'],
                'is_active': True,
            }
        )
        status = "✅ Created" if created else "🔄 Updated"
        print(f"{status} {formula.key}")
    
    print(f"\n✅ Seeded {len(formulas)} WS daily formulas")


def seed_ws_row_366_formulas():
    """
    Seed WS row 366 formulas (annual totals).
    Most columns sum days 1-365, storage columns use day365-day1 delta.
    """
    print("\n=== Seeding WS Row 366 Formulas (Annual Totals) ===")
    
    formulas = [
        # Reference inputs (not sums)
        {
            'key': 'WS_DAVON_RAUMW_KORR_366',
            'expression': 'V_2_9_2_ziel * (V_2_4_ziel / 100)',
            'description': 'Row 366 heating ref: Verbrauch 2.9.2.ziel * (2.4.ziel / 100)',
        },
        {
            'key': 'WS_STROMVERBR_RAUMWAERM_KORR_366',
            'expression': 'AE_FINAL_STROMNETZ',
            'description': 'Row 366 grid supply: from Annual Electricity final stromnetz',
        },
        
        # Sums over days 1-365
        {
            'key': 'WS_STROMVERBR_366',
            'expression': 'sum_stromverbr',
            'description': 'Row 366 total stromverbr: sum of days 1-365',
        },
        {
            'key': 'WS_WINDSTROM_366',
            'expression': 'sum_windstrom',
            'description': 'Row 366 total wind: sum of days 1-365',
        },
        {
            'key': 'WS_SOLARSTROM_366',
            'expression': 'sum_solarstrom',
            'description': 'Row 366 total solar: sum of days 1-365',
        },
        {
            'key': 'WS_SONST_KRAFT_KONSTANT_366',
            'expression': 'sum_sonst_kraft_konstant',
            'description': 'Row 366 total hydro: sum of days 1-365',
        },
        {
            'key': 'WS_WIND_SOLAR_KONSTANT_366',
            'expression': 'sum_wind_solar_konstant',
            'description': 'Row 366 total renewable: sum of days 1-365',
        },
        {
            'key': 'WS_DIREKTVERBR_STROM_366',
            'expression': 'sum_direktverbr_strom',
            'description': 'Row 366 total direct consumption: sum of days 1-365',
        },
        {
            'key': 'WS_UEBERSCHUSS_STROM_366',
            'expression': 'sum_ueberschuss_strom',
            'description': 'Row 366 total surplus: sum of days 1-365',
        },
        {
            'key': 'WS_EINSPEICH_366',
            'expression': 'sum_einspeich',
            'description': 'Row 366 total storage input: sum of days 1-365',
        },
        {
            'key': 'WS_ABREGELUNG_Z_366',
            'expression': 'sum_abregelung_z',
            'description': 'Row 366 total curtailment: sum of days 1-365',
        },
        {
            'key': 'WS_MANGEL_LAST_366',
            'expression': 'sum_mangel_last',
            'description': 'Row 366 total deficit: sum of days 1-365',
        },
        {
            'key': 'WS_BRENNSTOFF_AUSGLEICHS_STROM_366',
            'expression': 'sum_brennstoff_ausgleichs_strom',
            'description': 'Row 366 total biomass compensation: sum of days 1-365',
        },
        {
            'key': 'WS_SPEICHER_AUSGL_STROM_366',
            'expression': 'sum_speicher_ausgl_strom',
            'description': 'Row 366 total storage compensation: sum of days 1-365',
        },
        {
            'key': 'WS_AUSSPEICH_RUECKVERSTR_366',
            'expression': 'sum_ausspeich_rueckverstr',
            'description': 'Row 366 total reconversion: sum of days 1-365',
        },
        {
            'key': 'WS_AUSSPEICH_GAS_366',
            'expression': '0',
            'description': 'Row 366 total gas output: always 0',
        },
        
        # Storage deltas (day365 - day1)
        {
            'key': 'WS_LADEZUST_BURTTO_366',
            'expression': 'ladezust_burtto_day365 - ladezust_burtto_day1',
            'description': 'Row 366 gross storage change: day365 - day1',
        },
        {
            'key': 'WS_LADEZUSTAND_ABS_VORL_TL_366',
            'expression': 'ladezustand_abs_vorl_tl_day365 - ladezustand_abs_vorl_tl_day1',
            'description': 'Row 366 abs gross change: day365 - day1',
        },
        {
            'key': 'WS_SELBSTENTL_366',
            'expression': '0',
            'description': 'Row 366 total self-discharge: always 0',
        },
        {
            'key': 'WS_LADEZUSTAND_NETTO_366',
            'expression': 'ladezustand_netto_day365 - ladezustand_netto_day1',
            'description': 'Row 366 net storage change: day365 - day1',
        },
        {
            'key': 'WS_LADEZUSTAND_ABS_366',
            'expression': 'ladezustand_abs_day365 - ladezustand_abs_day1',
            'description': 'Row 366 abs net change: day365 - day1',
        },
    ]
    
    for formula_data in formulas:
        formula, created = Formula.objects.update_or_create(
            key=formula_data['key'],
            category='ws',
            defaults={
                'expression': formula_data['expression'],
                'description': formula_data['description'],
                'is_active': True,
            }
        )
        status = "✅ Created" if created else "🔄 Updated"
        print(f"{status} {formula.key}")
    
    print(f"\n✅ Seeded {len(formulas)} WS row 366 formulas")


def seed_ws_row_367_formulas():
    """
    Seed WS row 367 formulas (reference/offset row).
    This row provides baseline offsets for absolute storage levels.
    """
    print("\n=== Seeding WS Row 367 Formulas (Reference Row) ===")
    
    formulas = [
        {
            'key': 'WS_BRENNSTOFF_AUSGLEICHS_STROM_367',
            'expression': 'sum_mangel_last',
            'description': 'Row 367: copies row 366 Mangel-Last sum',
        },
        {
            'key': 'WS_LADEZUST_BURTTO_367',
            'expression': 'min_ladezust_burtto_daily',
            'description': 'Row 367: minimum of daily Ladezust.Burtto (days 1-365)',
        },
        {
            'key': 'WS_LADEZUSTAND_NETTO_367',
            'expression': 'min_ladezustand_netto_daily',
            'description': 'Row 367: minimum of daily Ladezustand.Netto (days 1-365)',
        },
        {
            'key': 'WS_LADEZUSTAND_ABS_367',
            'expression': '0',
            'description': 'Row 367 abs storage: always 0 (reference baseline)',
        },
    ]
    
    for formula_data in formulas:
        formula, created = Formula.objects.update_or_create(
            key=formula_data['key'],
            category='ws',
            defaults={
                'expression': formula_data['expression'],
                'description': formula_data['description'],
                'is_active': True,
            }
        )
        status = "✅ Created" if created else "🔄 Updated"
        print(f"{status} {formula.key}")
    
    print(f"\n✅ Seeded {len(formulas)} WS row 367 formulas")


def main():
    """Run all seeding functions."""
    print("="*70)
    print("COMPLETE WS AND ANNUAL ELECTRICITY FORMULA SEEDING")
    print("="*70)
    
    # Seed in order: Annual Electricity first (needed by WS row 366)
    seed_annual_electricity_formulas()
    
    # Then WS formulas
    seed_ws_daily_formulas()
    seed_ws_row_366_formulas()
    seed_ws_row_367_formulas()
    
    print("\n" + "="*70)
    print("✅ ALL FORMULAS SEEDED SUCCESSFULLY")
    print("="*70)
    
    # Summary
    total_formulas = Formula.objects.filter(is_active=True).count()
    ws_formulas = Formula.objects.filter(category='ws', is_active=True).count()
    annual_formulas = Formula.objects.filter(category='annual', is_active=True).count()
    
    print(f"\nTotal active formulas: {total_formulas}")
    print(f"  - WS formulas: {ws_formulas}")
    print(f"  - Annual Electricity formulas: {annual_formulas}")
    print("\nNext step: Run recalculation to apply formulas to data")


if __name__ == '__main__':
    main()
