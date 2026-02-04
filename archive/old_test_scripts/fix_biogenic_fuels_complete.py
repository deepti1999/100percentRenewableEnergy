#!/usr/bin/env python
"""
Fix ALL Biogenic Fuels (Code 4.x and 5.x) formulas and values to match Excel exactly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, LandUse

def fix_biogenic_fuels():
    """Fix all biogenic fuel formulas and values"""
    
    print("="*80)
    print("FIXING BIOGENIC FUELS (CODE 4.x and 5.x) TO MATCH EXCEL")
    print("="*80)
    
    # Get LandUse values
    forstfl = LandUse.objects.get(code='3.1')  # Forstfläche
    kup = LandUse.objects.get(code='2.2.5')  # Kurzumtrieb
    getreide = LandUse.objects.get(code='2.2.1')  # Getreide
    biogas_fl = LandUse.objects.get(code='2.2.2')  # Biogas Anbaufläche
    
    print(f"\nLandUse base values:")
    print(f"  3.1 Forstfläche: {forstfl.status_ha:,.0f} → {forstfl.target_ha:,.0f} ha")
    print(f"  2.2.5 KUP: {kup.status_ha:,.0f} → {kup.target_ha:,.0f} ha")
    print(f"  2.2.1 Getreide: {getreide.status_ha:,.0f} → {getreide.target_ha:,.0f} ha")
    print(f"  2.2.2 Biogas: {biogas_fl.status_ha:,.0f} → {biogas_fl.target_ha:,.0f} ha")
    
    print("\n" + "="*80)
    print("FIXING CODE 4.x - BIOGENE BRENNSTOFFE (FEST)")
    print("="*80)
    
    # 4.1.1.1 - Nutzbare Forstfläche (comes from LandUse 3.1)
    entry = RenewableData.objects.get(code='4.1.1.1')
    entry.status_value = forstfl.status_ha
    entry.target_value = forstfl.target_ha
    entry.formula = 'AUTOMATIC from LandUse 3.1'
    entry.save()
    print(f"✓ 4.1.1.1 Nutzbare Forstfläche: {entry.status_value:,.0f} → {entry.target_value:,.0f} ha")
    
    # 4.1.1.1.1.2 - Energieholzaufkommen Forst = 4.1.1.1 * 4.1.1.1.1% * 4.1.1.1.1.1 / 1000
    anteil_s = RenewableData.objects.get(code='4.1.1.1.1').status_value
    anteil_t = RenewableData.objects.get(code='4.1.1.1.1').target_value
    ertrag_s = RenewableData.objects.get(code='4.1.1.1.1.1').status_value
    ertrag_t = RenewableData.objects.get(code='4.1.1.1.1.1').target_value
    
    entry = RenewableData.objects.get(code='4.1.1.1.1.2')
    entry.status_value = forstfl.status_ha * anteil_s / 100 * ertrag_s / 1000
    entry.target_value = forstfl.target_ha * anteil_t / 100 * ertrag_t / 1000
    entry.formula = '4.1.1.1 * 4.1.1.1.1 / 100 * 4.1.1.1.1.1 / 1000'
    entry.save()
    print(f"✓ 4.1.1.1.1.2 Energieholzaufkommen Forst: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.1.2.1 - Anbaufläche KUP (comes from LandUse 2.2.5)
    entry = RenewableData.objects.get(code='4.1.2.1')
    entry.status_value = kup.status_ha
    entry.target_value = kup.target_ha
    entry.formula = 'AUTOMATIC from LandUse 2.2.5'
    entry.save()
    print(f"✓ 4.1.2.1 Anbaufläche KUP: {entry.status_value:,.0f} → {entry.target_value:,.0f} ha")
    
    # 4.1.2.1.2 - Energieholzaufkommen Ackerbau = 4.1.2.1 * 4.1.2.1.1 / 1000
    ertrag_kup_s = RenewableData.objects.get(code='4.1.2.1.1').status_value
    ertrag_kup_t = RenewableData.objects.get(code='4.1.2.1.1').target_value
    
    entry = RenewableData.objects.get(code='4.1.2.1.2')
    entry.status_value = kup.status_ha * ertrag_kup_s / 1000
    entry.target_value = kup.target_ha * ertrag_kup_t / 1000
    entry.formula = '4.1.2.1 * 4.1.2.1.1 / 1000'
    entry.save()
    print(f"✓ 4.1.2.1.2 Energieholzaufkommen Ackerbau: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.1.3 - Energieholzaufkommen gesamt = 4.1.1.1.1.2 + 4.1.2.1.2
    forst_s = RenewableData.objects.get(code='4.1.1.1.1.2').status_value
    forst_t = RenewableData.objects.get(code='4.1.1.1.1.2').target_value
    acker_s = RenewableData.objects.get(code='4.1.2.1.2').status_value
    acker_t = RenewableData.objects.get(code='4.1.2.1.2').target_value
    
    entry = RenewableData.objects.get(code='4.1.3')
    entry.status_value = forst_s + acker_s
    entry.target_value = forst_t + acker_t
    entry.formula = '4.1.1.1.1.2 + 4.1.2.1.2'
    entry.save()
    print(f"✓ 4.1.3 Energieholzaufkommen gesamt: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.2.1 - Getreide-Anbaufläche (comes from LandUse 2.2.1)
    entry = RenewableData.objects.get(code='4.2.1')
    entry.status_value = getreide.status_ha
    entry.target_value = getreide.target_ha
    entry.formula = 'AUTOMATIC from LandUse 2.2.1'
    entry.save()
    print(f"✓ 4.2.1 Getreide-Anbaufläche: {entry.status_value:,.0f} → {entry.target_value:,.0f} ha")
    
    # 4.2.1.1.2 - Strohbrennstoff-Aufkommen = 4.2.1 * 4.2.1.1% * 4.2.1.1.1 / 1000
    anteil_stroh_s = RenewableData.objects.get(code='4.2.1.1').status_value
    anteil_stroh_t = RenewableData.objects.get(code='4.2.1.1').target_value
    ertrag_stroh_s = RenewableData.objects.get(code='4.2.1.1.1').status_value
    ertrag_stroh_t = RenewableData.objects.get(code='4.2.1.1.1').target_value
    
    entry = RenewableData.objects.get(code='4.2.1.1.2')
    entry.status_value = getreide.status_ha * anteil_stroh_s / 100 * ertrag_stroh_s / 1000
    entry.target_value = getreide.target_ha * anteil_stroh_t / 100 * ertrag_stroh_t / 1000
    entry.formula = '4.2.1 * 4.2.1.1 / 100 * 4.2.1.1.1 / 1000'
    entry.save()
    print(f"✓ 4.2.1.1.2 Strohbrennstoff-Aufkommen: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.3 - Brennstoffaufkommen NAWARO gesamt = 4.1.3 + 4.2.1.1.2
    holz_s = RenewableData.objects.get(code='4.1.3').status_value
    holz_t = RenewableData.objects.get(code='4.1.3').target_value
    stroh_s = RenewableData.objects.get(code='4.2.1.1.2').status_value
    stroh_t = RenewableData.objects.get(code='4.2.1.1.2').target_value
    
    entry = RenewableData.objects.get(code='4.3')
    entry.status_value = holz_s + stroh_s
    entry.target_value = holz_t + stroh_t
    entry.formula = '4.1.3 + 4.2.1.1.2'
    entry.save()
    print(f"✓ 4.3 Brennstoffaufkommen NAWARO gesamt: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.3.1 - Einsatz für Gebäudewärme = 4.3 * 4.1.3.1 / 100
    nawaro_s = RenewableData.objects.get(code='4.3').status_value
    nawaro_t = RenewableData.objects.get(code='4.3').target_value
    anteil_gw_s = RenewableData.objects.get(code='4.1.3.1').status_value
    anteil_gw_t = RenewableData.objects.get(code='4.1.3.1').target_value
    
    entry = RenewableData.objects.get(code='4.3.1')
    entry.status_value = nawaro_s * anteil_gw_s / 100
    entry.target_value = nawaro_t * anteil_gw_t / 100
    entry.formula = '4.3 * 4.1.3.1 / 100'
    entry.save()
    print(f"✓ 4.3.1 Einsatz für Gebäudewärme: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.3.2 - Einsatz für Prozesswärme = 4.3 * 4.1.3.2 / 100
    anteil_pw_s = RenewableData.objects.get(code='4.1.3.2').status_value
    anteil_pw_t = RenewableData.objects.get(code='4.1.3.2').target_value
    
    entry = RenewableData.objects.get(code='4.3.2')
    entry.status_value = nawaro_s * anteil_pw_s / 100
    entry.target_value = nawaro_t * anteil_pw_t / 100
    entry.formula = '4.3 * 4.1.3.2 / 100'
    entry.save()
    print(f"✓ 4.3.2 Einsatz für Prozesswärme: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.3.3 - Einsatz für Verstromung = 4.3 * 4.1.3.3 / 100
    anteil_v_s = RenewableData.objects.get(code='4.1.3.3').status_value
    anteil_v_t = RenewableData.objects.get(code='4.1.3.3').target_value
    
    entry = RenewableData.objects.get(code='4.3.3')
    entry.status_value = nawaro_s * anteil_v_s / 100
    entry.target_value = nawaro_t * anteil_v_t / 100
    entry.formula = '4.3 * 4.1.3.3 / 100'
    entry.save()
    print(f"✓ 4.3.3 Einsatz für Verstromung: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 4.3.3.2 - Bruttostromerzeugung = 4.3.3 * 4.3.3.1 / 100
    verstr_s = RenewableData.objects.get(code='4.3.3').status_value
    verstr_t = RenewableData.objects.get(code='4.3.3').target_value
    nutz_s = RenewableData.objects.get(code='4.3.3.1').status_value
    nutz_t = RenewableData.objects.get(code='4.3.3.1').target_value
    
    entry = RenewableData.objects.get(code='4.3.3.2')
    entry.status_value = verstr_s * nutz_s / 100
    entry.target_value = verstr_t * nutz_t / 100
    entry.formula = '4.3.3 * 4.3.3.1 / 100'
    entry.save()
    print(f"✓ 4.3.3.2 Bruttostromerzeugung: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    print("\n" + "="*80)
    print("FIXING CODE 5.x - BIOGAS")
    print("="*80)
    
    # 5.1 - Anbaufläche Energiepflanzen für Biogas (comes from LandUse 2.2.2)
    entry = RenewableData.objects.get(code='5.1')
    entry.status_value = biogas_fl.status_ha
    entry.target_value = biogas_fl.target_ha
    entry.formula = 'AUTOMATIC from LandUse 2.2.2'
    entry.save()
    print(f"✓ 5.1 Anbaufläche Biogas: {entry.status_value:,.0f} → {entry.target_value:,.0f} ha")
    
    # 5.1.2 - Biogas aus Energiepflanzen = 5.1 * 5.1.1 / 1000
    methan_s = RenewableData.objects.get(code='5.1.1').status_value
    methan_t = RenewableData.objects.get(code='5.1.1').target_value
    
    entry = RenewableData.objects.get(code='5.1.2')
    entry.status_value = biogas_fl.status_ha * methan_s / 1000
    entry.target_value = biogas_fl.target_ha * methan_t / 1000
    entry.formula = '5.1 * 5.1.1 / 1000'
    entry.save()
    print(f"✓ 5.1.2 Biogas aus Energiepflanzen: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 5.4 - Biogasaufkommen insgesamt = 5.1.2 + 5.2 + 5.3
    ep_s = RenewableData.objects.get(code='5.1.2').status_value
    ep_t = RenewableData.objects.get(code='5.1.2').target_value
    abfall_s = RenewableData.objects.get(code='5.2').status_value
    abfall_t = RenewableData.objects.get(code='5.2').target_value
    klaer_s = RenewableData.objects.get(code='5.3').status_value
    klaer_t = RenewableData.objects.get(code='5.3').target_value
    
    entry = RenewableData.objects.get(code='5.4')
    entry.status_value = ep_s + abfall_s + klaer_s
    entry.target_value = ep_t + abfall_t + klaer_t
    entry.formula = '5.1.2 + 5.2 + 5.3'
    entry.save()
    print(f"✓ 5.4 Biogasaufkommen insgesamt: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 5.4.1.1 - Biogas für Prozesswärme = 5.4 * 5.4.1 / 100
    biogas_s = RenewableData.objects.get(code='5.4').status_value
    biogas_t = RenewableData.objects.get(code='5.4').target_value
    anteil_pw_biogas_s = RenewableData.objects.get(code='5.4.1').status_value
    anteil_pw_biogas_t = RenewableData.objects.get(code='5.4.1').target_value
    
    entry = RenewableData.objects.get(code='5.4.1.1')
    entry.status_value = biogas_s * anteil_pw_biogas_s / 100
    entry.target_value = biogas_t * anteil_pw_biogas_t / 100
    entry.formula = '5.4 * 5.4.1 / 100'
    entry.save()
    print(f"✓ 5.4.1.1 Biogas für Prozesswärme: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 5.4.2.2 - Bruttostromerzeugung Biogas = 5.4 * 5.4.2 / 100 * 5.4.2.1 / 100
    anteil_v_biogas_s = RenewableData.objects.get(code='5.4.2').status_value
    anteil_v_biogas_t = RenewableData.objects.get(code='5.4.2').target_value
    nutz_biogas_s = RenewableData.objects.get(code='5.4.2.1').status_value
    nutz_biogas_t = RenewableData.objects.get(code='5.4.2.1').target_value
    
    entry = RenewableData.objects.get(code='5.4.2.2')
    entry.status_value = biogas_s * anteil_v_biogas_s / 100 * nutz_biogas_s / 100
    entry.target_value = biogas_t * anteil_v_biogas_t / 100 * nutz_biogas_t / 100
    entry.formula = '5.4 * 5.4.2 / 100 * 5.4.2.1 / 100'
    entry.save()
    print(f"✓ 5.4.2.2 Bruttostromerzeugung Biogas: {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    # 5.4.3.2 - Biokraftstoff (gasförmig) = 5.4 * 5.4.3 / 100 * 5.4.3.1 / 100
    anteil_mobil_s = RenewableData.objects.get(code='5.4.3').status_value
    anteil_mobil_t = RenewableData.objects.get(code='5.4.3').target_value
    nutz_mobil_s = RenewableData.objects.get(code='5.4.3.1').status_value
    nutz_mobil_t = RenewableData.objects.get(code='5.4.3.1').target_value
    
    entry = RenewableData.objects.get(code='5.4.3.2')
    entry.status_value = biogas_s * anteil_mobil_s / 100 * nutz_mobil_s / 100
    entry.target_value = biogas_t * anteil_mobil_t / 100 * nutz_mobil_t / 100
    entry.formula = '5.4 * 5.4.3 / 100 * 5.4.3.1 / 100'
    entry.save()
    print(f"✓ 5.4.3.2 Biokraftstoff (gasförmig): {entry.status_value:,.0f} → {entry.target_value:,.0f} GWh/a")
    
    print("\n" + "="*80)
    print("✅ ALL BIOGENIC FUEL VALUES FIXED!")
    print("="*80)

if __name__ == "__main__":
    fix_biogenic_fuels()
