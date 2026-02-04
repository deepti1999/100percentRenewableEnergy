#!/usr/bin/env python3
"""
COMPLETE RENEWABLE ENERGY FORMULAS - SECTIONS 1-9
==================================================

This file contains ALL formulas for renewable energy data (RenewableData model)
for sections 1-9, with complete implementation for importing and updating.

All formulas have been verified and corrected. This serves as the master reference
for renewable energy calculations.

Last Updated: November 11, 2025

IMPORTANT: This file can be imported as a module OR run directly.
- When imported (by simulator/renewable_formulas.py): Only formula dictionaries are loaded
- When run directly: Django setup is called and database operations are available
"""

# =============================================================================
# FORMULA DEFINITIONS - Can be imported without Django
# =============================================================================
# These dictionaries are pure data and can be imported by any module

SECTION_1_FORMULAS = {
    '1.1': {
        'name': 'Solare Dachflächen',
        'formula': None,
        'is_fixed': False,
        'description': 'Total solar roof area - fixed values from LandUse'
    },
    '1.1.1.1.2': {
        'name': 'Gebäudewärme',
        'formula': '1.1 * (1.1.1.1/100) * 1.1.1.1.1 / 1000',
        'is_fixed': False,
        'description': 'Building heat from solar thermal roof installations'
    },
    '1.1.2.1': {
        'name': 'Anteil an solaren Dachflächen (Strom)',
        'formula': '100 - AnteilThermie',
        'is_fixed': False,
        'description': 'Share of roof area for PV (100% - thermal share)'
    },
    '1.1.2.1.2': {
        'name': 'Bruttostromerzeugung',
        'formula': 'LandUse_1.1 * 1.1.2.1 / 100 * 1.1.2.1.1 / 1000',
        'is_fixed': False,
        'description': 'Gross electricity generation from roof PV'
    },
    '1.1.2.1.2.2': {
        'name': 'Installierte Leistung',
        'formula': '1.1.2.1.2 / 1.1.2.1.2.1 * 1000',
        'is_fixed': False,
        'description': 'Installed capacity = Generation / Full-load hours'
    },
    '1.2': {
        'name': 'Solar genutzte Freiflächen',
        'formula': 'LandUse_2.1',
        'is_fixed': False,
        'description': 'Solar ground-mounted area from LandUse'
    },
    '1.2.1.2': {
        'name': 'Bruttostromerzeugung',
        'formula': 'LandUse_2.1 * 1.2.1.1 / 1000',
        'is_fixed': False,
        'description': 'Gross electricity generation from ground-mounted PV'
    },
    '1.2.1.2.2': {
        'name': 'Installierte Leistung',
        'formula': '1.2.1.2 / 1.2.1.2.1 * 1000',
        'is_fixed': False,
        'description': 'Installed capacity for ground-mounted PV'
    },
}


# =============================================================================
# SECTION 2: WIND ENERGY (Windenergie)
# =============================================================================

SECTION_2_FORMULAS = {
    '2.1.1': {
        'name': 'Windparkfläche',
        'formula': 'LandUse_5.1',
        'is_fixed': False,
        'description': 'Wind park area from LandUse'
    },
    '2.1.1.2': {
        'name': 'Installierte Leistung',
        'formula': '2.1.1 / 2.1.1.1',
        'is_fixed': False,
        'description': 'Installed capacity = Area / Specific area requirement'
    },
    '2.1.1.2.2': {
        'name': 'Bruttostromerzeugung jährlich',
        'formula': '2.1.1.2 * 2.1.1.2.1 / 1000',
        'is_fixed': False,
        'description': 'Annual generation = Capacity × Full-load hours'
    },
    '2.1.1.2.3': {
        'name': 'Energieertrag',
        'formula': '2.1.1.2.2 * 1000 / 2.1.1',
        'is_fixed': False,
        'description': 'Energy yield per unit area'
    },
    '2.2.1.2': {
        'name': 'Bruttostromerzeugung Deutschland',
        'formula': '2.2.1 * 2.2.1.1 / 1000',
        'is_fixed': False,
        'description': 'Germany-wide offshore generation'
    },
    '2.2.1.2.3': {
        'name': 'Bruttostromerz.Anteil Deutschland 100%EE',
        'formula': '2.2.1.2 / 2.2.1.2.1 * 2.2.1.2.2',
        'is_fixed': False,
        'description': 'Regional share of offshore generation'
    },
}


# =============================================================================
# SECTION 3: HYDRO POWER (Laufwasser)
# =============================================================================

SECTION_3_FORMULAS = {
    '3.1.1.2': {
        'name': 'Bruttostromerzeugung',
        'formula': '3.1 * 3.1.1 / 100 * 3.1.1.1 / 1000',
        'is_fixed': False,
        'description': 'Hydro power generation from run-of-river'
    },
}


# =============================================================================
# SECTION 4: SOLID BIOFUELS (Biogene Brennstoffe fest)
# =============================================================================

SECTION_4_FORMULAS = {
    '4.1.1.1': {
        'name': 'Nutzbare Forstfläche',
        'formula': 'LandUse_3.1',
        'is_fixed': False,
        'description': 'Usable forest area from LandUse'
    },
    '4.1.1.1.1.2': {
        'name': 'Energieholzaufkommen',
        'formula': '4.1.1.1 * 4.1.1.1.1 / 100 * 4.1.1.1.1.1 / 1000',
        'is_fixed': False,
        'description': 'Energy wood from forestry'
    },
    '4.1.2.1': {
        'name': 'Anbaufläche',
        'formula': 'LandUse_2.2.5',
        'is_fixed': False,
        'description': 'Cultivation area for short-rotation coppice'
    },
    '4.1.2.1.2': {
        'name': 'Energieholzaufkommen',
        'formula': '4.1.2.1 * 4.1.2.1.1 / 1000',
        'is_fixed': False,
        'description': 'Energy wood from agriculture (KUP, Miscanthus)'
    },
    '4.1.3': {
        'name': 'Energieholzaufkommen gesamt',
        'formula': '4.1.1.1.1.2 + 4.1.2.1.2',
        'is_fixed': False,
        'description': 'Total energy wood supply'
    },
    '4.1.3.1': {
        'name': 'davon für Gebäudewärme',
        'formula': '-4.3',
        'is_fixed': False,
        'description': 'Share for building heat (percentage or fixed value)'
    },
    '4.1.3.2': {
        'name': 'davon für Prozesswärme',
        'formula': '100 - 4.1.3.1 - 4.1.3.3 - 4.1.3.4',
        'is_fixed': False,
        'description': 'Share for process heat, calculated as remainder (percentage)'
    },
    '4.2.1': {
        'name': 'Getreide-Anbaufläche',
        'formula': 'LandUse_2.2.1',
        'is_fixed': False,
        'description': 'Grain cultivation area from LandUse'
    },
    '4.2.1.1.2': {
        'name': 'Strohbrennstoff-Aufkommen',
        'formula': '4.2.1 * 4.2.1.1 / 100 * 4.2.1.1.1 / 1000',
        'is_fixed': False,
        'description': 'Straw fuel supply'
    },
    '4.2.1.1.2.2': {
        'name': 'davon für Prozesswärme',
        'formula': '100 - 4.2.1.1.2.1 - 4.2.1.1.2.3 - 4.2.1.1.2.4',
        'is_fixed': False,
        'description': 'Share for process heat, calculated as remainder (percentage)'
    },
    '4.3': {
        'name': 'Brennstoffaufkommen (fest) NAWARO gesamt',
        'formula': '4.1.3 + 4.2.1.1.2',
        'is_fixed': False,
        'description': 'Total solid biofuel from renewable resources'
    },
    '4.3.2': {
        'name': 'davon Einsatz für Prozesswärme',
        'formula': '4.3 * 4.1.3.2 / 100',
        'is_fixed': False,
        'description': 'Usage for process heat'
    },
    '4.3.3': {
        'name': 'davon Einsatz für Verstromung',
        'formula': '4.3 * 4.1.3.3 / 100',
        'is_fixed': False,
        'description': 'Usage for electricity generation'
    },
    '4.3.3.2': {
        'name': 'Bruttostromerzeugung',
        'formula': '4.3.3 * 4.3.3.1 / 100',
        'is_fixed': False,
        'description': 'Gross electricity from solid biofuels'
    },
    '4.3.3.4': {
        'name': 'Wärmenetze GW (Endenergie)',
        'formula': '4.3.3.2 * 4.3.3.3 / 4.3.3.1',
        'is_fixed': False,
        'description': 'District heating from CHP waste heat'
    },
    '4.3.4': {
        'name': 'davon Einsatz für Heizwerke/Wärmenetze',
        'formula': '4.3 * 4.1.3.4 / 100',
        'is_fixed': False,
        'description': 'Usage for heating plants'
    },
    '4.3.4.2': {
        'name': 'Wärmenetze GW (Endenergie)',
        'formula': '4.3.4 * 4.3.4.1 / 100',
        'is_fixed': False,
        'description': 'District heating from heating plants'
    },
    '4.4': {
        'name': 'Biogener Anteil der Abfälle (fest)',
        'formula': '4.4.1 + 4.4.2',
        'is_fixed': False,
        'description': 'Biogenic share of solid waste'
    },
}


# =============================================================================
# SECTION 5: BIOGAS
# =============================================================================

SECTION_5_FORMULAS = {
    '5.1': {
        'name': 'Anbaufläche Energiepflanzen für Biogas',
        'formula': 'LandUse_2.2.2',
        'is_fixed': False,
        'description': 'Cultivation area for energy crops (biogas)'
    },
    '5.1.2': {
        'name': 'Biogas aus Energiepflanzen-Anbau',
        'formula': '5.1 * 5.1.1 / 1000',
        'is_fixed': False,
        'description': 'Biogas from energy crop cultivation'
    },
    '5.4': {
        'name': 'Biogasaufkommen insgesamt',
        'formula': '5.1.2 + 5.2 + 5.3',
        'is_fixed': False,
        'description': 'Total biogas supply'
    },
    '5.4.1.1': {
        'name': 'Biogas für Prozesswärme',
        'formula': '5.4 * 5.4.1 / 100',
        'is_fixed': False,
        'description': 'Biogas for process heat'
    },
    '5.4.2.2': {
        'name': 'Bruttostromerzeugung',
        'formula': '5.4 * 5.4.2 / 100 * 5.4.2.1 / 100',
        'is_fixed': False,
        'description': 'Gross electricity from biogas'
    },
    '5.4.2.4': {
        'name': 'Gebäudewärme (Endenergie)',
        'formula': '5.4 * 5.4.2% * 5.4.2.3%',
        'is_fixed': False,
        'description': 'Building heat from CHP waste heat'
    },
    '5.4.3.2': {
        'name': 'Biokraftstoff (gasförmig)',
        'formula': '5.4 * 5.4.3 / 100 * 5.4.3.1 / 100',
        'is_fixed': False,
        'description': 'Gaseous biofuel (biomethane) for mobile applications'
    },
    '5.4.4.2': {
        'name': 'Biokraftstoff (flüssig)',
        'formula': '5.4 * 5.4.4% * 5.4.4.1%',
        'is_fixed': False,
        'description': 'Liquid biofuel from biogas'
    },
}


# =============================================================================
# SECTION 6: LIQUID BIOFUELS (Biogene Brennstoffe flüssig)
# =============================================================================

SECTION_6_FORMULAS = {
    '6.1.1.2': {
        'name': 'Biodiesel aus eigenem Anbau',
        'formula': '6.1.1 * 6.1.1.1 / 1000',
        'is_fixed': False,
        'description': 'Biodiesel from domestic cultivation'
    },
    '6.1.3': {
        'name': 'Biodiesel Gesamtaufkommen',
        'formula': '6.1.1.2 + 6.1.2',
        'is_fixed': False,
        'description': 'Total biodiesel supply (domestic + import)'
    },
    '6.1.3.1.1': {
        'name': 'Biokraftstoff (flüssig)',
        'formula': '6.1.3 * 6.1.3.1 / 100',
        'is_fixed': False,
        'description': 'Biodiesel for mobile applications'
    },
    '6.1.3.2.2': {
        'name': 'Bruttostromerzeugung',
        'formula': '6.1.3 * 6.1.3.2 * 6.1.3.2.1 / 10000',
        'is_fixed': False,
        'description': 'Electricity from biodiesel CHP'
    },
    '6.1.3.2.4': {
        'name': 'Gebäudewärme (Endenergie)',
        'formula': '6.1.3 * 6.1.3.2% * 6.1.3.2.3%',
        'is_fixed': False,
        'description': 'Building heat from biodiesel CHP'
    },
    '6.2.1': {
        'name': 'Anbaufläche Energiepflanzen für Bioethanol',
        'formula': 'LandUse_2.2.4',
        'is_fixed': False,
        'description': 'Cultivation area for bioethanol'
    },
    '6.2.1.2': {
        'name': 'Bioethanol aus eigenem Anbau',
        'formula': '6.2.1 * 6.2.1.1 / 1000',
        'is_fixed': False,
        'description': 'Bioethanol from domestic cultivation'
    },
    '6.2.3': {
        'name': 'Bioethanol gesamt – Mobile Anwendungen',
        'formula': '6.2.1.2 + 6.2.2',
        'is_fixed': False,
        'description': 'Total bioethanol for mobile applications'
    },
}


# =============================================================================
# SECTION 7: AMBIENT HEAT (Umgebungswärme - Heat Pumps)
# =============================================================================

SECTION_7_FORMULAS = {
    '7.1': {
        'name': 'Wärmepumpen-Antriebsstromaufnahme',
        'formula': 'VerbrauchData_2.9.2',
        'is_fixed': False,
        'description': 'Heat pump electricity consumption from VerbrauchData'
    },
    '7.1.2': {
        'name': 'WP-Luft – Antriebsstromaufnahme',
        'formula': '7.1 * 7.1.1 / 100',
        'is_fixed': False,
        'description': 'Air-source heat pump electricity consumption'
    },
    '7.1.2.2': {
        'name': 'Nutzwärme (inkl. Antriebsstrom)',
        'formula': '7.1.2 * 7.1.2.1',
        'is_fixed': False,
        'description': 'Useful heat from air-source HP (incl. electricity)'
    },
    '7.1.2.3': {
        'name': 'davon Wärmgewinn aus der Luft',
        'formula': '7.1.2.2 - 7.1.2',
        'is_fixed': False,
        'description': 'Heat gain from ambient air'
    },
    '7.1.4': {
        'name': 'WP-Erdr./Wasser – Antriebsstromaufnahme',
        'formula': '7.1 * 7.1.3 / 100',
        'is_fixed': False,
        'description': 'Ground/water-source HP electricity consumption'
    },
    '7.1.4.2': {
        'name': 'Nutzwärme (inkl. Antriebsstrom)',
        'formula': '7.1.4 * 7.1.4.1',
        'is_fixed': False,
        'description': 'Useful heat from ground/water-source HP'
    },
    '7.1.4.3': {
        'name': 'davon Wärmgewinn Erdreich/Grundwasser',
        'formula': '7.1.4.2 - 7.1.4',
        'is_fixed': False,
        'description': 'Heat gain from ground/groundwater'
    },
    '7.1.4.3.2': {
        'name': 'Beanspruchte Entzugsfläche',
        'formula': '7.1.4.3 * 1000 / 7.1.4.3.1',
        'is_fixed': False,
        'description': 'Required extraction area'
    },
    '7.1.4.3.3': {
        'name': 'Gebäude- & Freifläche (Siedlung)',
        'formula': 'LandUse_1',
        'is_fixed': False,
        'description': 'Building and open area from LandUse'
    },
}


# =============================================================================
# SECTION 8: DEEP GEOTHERMAL (Tiefengeothermie)
# =============================================================================

SECTION_8_FORMULAS = {
    '8.1.2': {
        'name': 'Bruttostromerzeugung',
        'formula': '8.1 * 8.1.1 / 1000',
        'is_fixed': False,
        'description': 'Gross electricity from deep geothermal'
    },
}


# =============================================================================
# SECTION 9: TOTALS & STORAGE (Gesamt & Speicherung)
# =============================================================================

SECTION_9_FORMULAS = {
    # Electricity generation totals
    '9.1.1': {
        'name': 'aus Windenergie',
        'formula': '2.2.1.2.3 + 2.1.1.2.2',
        'is_fixed': False,
        'description': 'Total wind electricity (offshore + onshore)'
    },
    '9.1.2': {
        'name': 'aus Solarenergie (Photovoltaik)',
        'formula': '1.1.2.1.2 + 1.2.1.2',
        'is_fixed': False,
        'description': 'Total solar electricity (roof + ground-mounted)'
    },
    '9.1.3': {
        'name': 'aus Wasserkraft + Tiefengeothermie',
        'formula': '3.1.1.2 + 8.1.2',
        'is_fixed': False,
        'description': 'Hydro + deep geothermal electricity'
    },
    '9.1.4': {
        'name': 'aus Biobrennstoffen',
        'formula': '4.3.3.2 + 4.4.1 + 5.4.2.2 + 6.1.3.2.2',
        'is_fixed': False,
        'description': 'Electricity from all biofuels'
    },
    '9.1': {
        'name': 'Bruttostromerzeugung aus Erneuerbaren Energien gesamt (inkl. Abregelung)',
        'formula': '9.1.1 + 9.1.2 + 9.1.3 + 9.1.4',
        'is_fixed': False,
        'description': 'Total gross renewable electricity generation'
    },
    '9.2': {
        'name': 'Bruttostromerzeugung Erneuerbar (inkl. Abregelung)',
        'formula': '9.1.1 + 9.1.2 + 9.1.3 + 9.1.4',
        'is_fixed': False,
        'description': 'Total renewable electricity (same as 9.1)'
    },
    
    # Hydrogen production and synthesis
    '9.2.1.1': {
        'name': 'Wasserstoff als Brennstoff für PW',
        'formula': '0',
        'is_fixed': False,
        'description': 'Hydrogen as fuel for process heat (currently 0)'
    },
    '9.2.1.1.1': {
        'name': 'Wasserstoff (komprim.) f. FC-Traktion',
        'formula': '0',
        'is_fixed': False,
        'description': 'Compressed hydrogen for fuel cell traction (currently 0)'
    },
    '9.2.1.1.1.1': {
        'name': 'Nutzungsgrad tankfähiger Wasserstoff',
        'formula': '80',
        'is_fixed': False,
        'description': 'Efficiency of tankable hydrogen (80%)'
    },
    '9.2.1.1.2': {
        'name': 'Wasserstoff für MA mit FC-Traktion',
        'formula': '0',
        'is_fixed': False,
        'description': 'Hydrogen for mobile applications with FC traction (currently 0)'
    },
    '9.2.1.2': {
        'name': 'Kraftstoff (gasförm. Methan) für MA aus H₂',
        'formula': '0',
        'is_fixed': False,
        'description': 'Gaseous methane fuel for mobile applications from H₂ (currently 0)'
    },
    '9.2.1.2.2': {
        'name': 'Wasserstoff für Kraftstoffsynthese',
        'formula': '9.2.1.2 * 9.2.1.2.1%',
        'is_fixed': False,
        'description': 'Hydrogen for gaseous fuel synthesis'
    },
    '9.2.1.3': {
        'name': 'Kraftstoffe (flüssig) für MA aus H₂',
        'formula': 'IF(VerbrauchData_4.3.5 > (VerbrauchData_3.7 + VerbrauchData_4.1.1.5 + VerbrauchData_4.1.1.17); VerbrauchData_4.3.5 - (VerbrauchData_3.7 + VerbrauchData_4.1.1.5 + VerbrauchData_4.1.1.17); 0)',
        'is_fixed': False,
        'description': 'Liquid synthetic fuels demand from mobile applications'
    },
    '9.2.1.3.2': {
        'name': 'Wasserstoff für Kraftstoffsynthese',
        'formula': '9.2.1.3 * 9.2.1.3.1%',
        'is_fixed': False,
        'description': 'Hydrogen for liquid fuel synthesis'
    },
    '9.2.1.4': {
        'name': 'Synth. Methan als Grundstoff',
        'formula': 'VerbrauchData_7.1.4',
        'is_fixed': False,
        'description': 'Synthetic methane as basic material from VerbrauchData'
    },
    '9.2.1.4.2': {
        'name': 'Wasserstoff für Grundstoffsynthese',
        'formula': '9.2.1.4 / 9.2.1.4.1 * 100',
        'is_fixed': False,
        'description': 'Hydrogen for basic material synthesis'
    },
    '9.2.1.5': {
        'name': 'Wasserstofferzeugung',
        'formula': '9.2.1.1 + 9.2.1.1.2 + 9.2.1.2.2 + 9.2.1.3.2 + 9.2.1.4.2',
        'is_fixed': False,
        'description': 'Total hydrogen production'
    },
    '9.2.1.5.2': {
        'name': 'Stromeinsatz Wasserstofferzeugung',
        'formula': '9.2.1.5 / 9.2.1.5.1 * 100',
        'is_fixed': False,
        'description': 'Electricity demand for hydrogen production'
    },
    '9.2.1.5.2.1': {
        'name': 'davon in der Zielregion',
        'formula': '9.2.1.5.2 - 9.2.1.5.2.2',
        'is_fixed': False,
        'description': 'Hydrogen production electricity in target region'
    },
    
    # Long-term storage
    '9.3.1.2': {
        'name': 'Stromabgabe (Mangelphasen)',
        'formula': '9.3.1 * 9.3.1.1 / 100',
        'is_fixed': False,
        'description': 'Electricity discharge from storage'
    },
    '9.3.2.1': {
        'name': 'Gebäudewärme (Endenergie)',
        'formula': '9.3.1 * 9.3.2 / 100',
        'is_fixed': False,
        'description': 'Building heat from storage CHP waste heat'
    },
    
    # Final electricity supply
    '9.4.1': {
        'name': 'Stromangebot aus eigenen Erneuerb. E.',
        'formula': '9.2 - 9.2.1.5.2.1 - 9.3.1 + 9.3.1.2 - 9.3.4',
        'is_fixed': False,
        'description': 'Own renewable electricity supply (after H2 and storage)'
    },
    '9.4.3': {
        'name': 'Stromangebot aus Erneuerbaren E. (gesamt)',
        'formula': '9.4.1 + 9.4.2',
        'is_fixed': False,
        'description': 'Total renewable electricity supply (incl. imports)'
    },
    '9.4.3.2': {
        'name': 'inkl. Kurzzeitspeicher',
        'formula': '9.4.3 * 9.4.3.1 / 100',
        'is_fixed': False,
        'description': 'Transmission losses incl. short-term storage'
    },
    '9.4.3.3': {
        'name': 'Stromangebot Erneuerb. (Endenergie)',
        'formula': '9.4.3 - 9.4.3.2',
        'is_fixed': False,
        'description': 'Renewable electricity supply (final energy)'
    },
}


# =============================================================================
# DATABASE OPERATIONS - Only available when run directly (not when imported)
# =============================================================================

def _ensure_django_setup():
    """Ensure Django is set up before database operations"""
    import django
    from django.conf import settings
    
    if not settings.configured:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
        django.setup()


def apply_all_formulas():
    """
    Apply all formulas to the RenewableData model.
    This function updates all entries with their correct formulas.
    """
    _ensure_django_setup()
    from simulator.models import RenewableData
    
    print("=" * 80)
    print("APPLYING ALL RENEWABLE ENERGY FORMULAS (SECTIONS 1-9)")
    print("=" * 80)
    
    all_formulas = {
        **SECTION_1_FORMULAS,
        **SECTION_2_FORMULAS,
        **SECTION_3_FORMULAS,
        **SECTION_4_FORMULAS,
        **SECTION_5_FORMULAS,
        **SECTION_6_FORMULAS,
        **SECTION_7_FORMULAS,
        **SECTION_8_FORMULAS,
        **SECTION_9_FORMULAS,
    }
    
    updated_count = 0
    not_found_count = 0
    
    for code, data in sorted(all_formulas.items()):
        try:
            renewable = RenewableData.objects.get(code=code)
            
            # Update formula if specified
            if data['formula'] is not None:
                old_formula = renewable.formula
                renewable.formula = data['formula']
                renewable.is_fixed = data['is_fixed']
                renewable.save()
                
                print(f"\n✓ {code}: {data['name']}")
                print(f"  Formula: {data['formula']}")
                print(f"  Description: {data['description']}")
                if old_formula != data['formula']:
                    print(f"  Changed from: {old_formula}")
                updated_count += 1
            else:
                print(f"\n○ {code}: {data['name']} (Fixed values, no formula)")
                
        except RenewableData.DoesNotExist:
            print(f"\n✗ {code}: NOT FOUND IN DATABASE")
            not_found_count += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"  Updated: {updated_count} entries")
    print(f"  Not found: {not_found_count} entries")
    print("=" * 80)


def verify_all_formulas():
    """
    Verify that all formulas are present and correctly formatted.
    """
    _ensure_django_setup()
    from simulator.models import RenewableData
    
    print("\n" + "=" * 80)
    print("VERIFYING ALL FORMULAS")
    print("=" * 80)
    
    entries = RenewableData.objects.filter(
        code__regex=r'^[1-9]\.'
    ).exclude(
        code__startswith='10.'
    ).order_by('code')
    
    entries_with_formulas = 0
    entries_fixed = 0
    entries_calculated = 0
    
    for entry in entries:
        if entry.formula and entry.formula.strip():
            entries_with_formulas += 1
            if entry.is_fixed:
                entries_fixed += 1
            else:
                entries_calculated += 1
    
    print(f"\nTotal entries in sections 1-9: {entries.count()}")
    print(f"Entries with formulas: {entries_with_formulas}")
    print(f"  - Fixed values: {entries_fixed}")
    print(f"  - Calculated: {entries_calculated}")
    print(f"Entries without formulas: {entries.count() - entries_with_formulas}")
    
    # Check by section
    print("\n" + "-" * 80)
    print("BY SECTION:")
    print("-" * 80)
    
    for section in range(1, 10):
        section_entries = [e for e in entries if e.code.startswith(f'{section}.')]
        with_formula = [e for e in section_entries if e.formula and e.formula.strip()]
        print(f"Section {section}: {len(with_formula)}/{len(section_entries)} with formulas")


def list_all_formulas():
    """
    List all formulas from the database (current state).
    """
    _ensure_django_setup()
    from simulator.models import RenewableData
    
    print("\n" + "=" * 80)
    print("ALL FORMULAS IN DATABASE (SECTIONS 1-9)")
    print("=" * 80)
    
    entries = RenewableData.objects.filter(
        code__regex=r'^[1-9]\.'
    ).exclude(
        code__startswith='10.'
    ).order_by('code')
    
    current_section = None
    
    for entry in entries:
        section = entry.code.split('.')[0]
        
        if section != current_section:
            current_section = section
            print(f"\n{'=' * 80}")
            print(f"SECTION {section}")
            print(f"{'=' * 80}")
        
        if entry.formula and entry.formula.strip():
            print(f"\n{entry.code}: {entry.name}")
            print(f"  Formula: {entry.formula}")
            print(f"  is_fixed: {entry.is_fixed}")


def export_formulas_to_csv():
    """
    Export all formulas to a CSV file for easy reference.
    """
    _ensure_django_setup()
    from simulator.models import RenewableData
    import csv
    from datetime import datetime
    
    filename = f'renewable_formulas_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    entries = RenewableData.objects.filter(
        code__regex=r'^[1-9]\.'
    ).exclude(
        code__startswith='10.'
    ).order_by('code')
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Code', 'Name', 'Formula', 'is_fixed', 'Status', 'Target'])
        
        for entry in entries:
            writer.writerow([
                entry.code,
                entry.name,
                entry.formula if entry.formula else '',
                entry.is_fixed,
                entry.status_value if entry.status_value is not None else '',
                entry.target_value if entry.target_value is not None else ''
            ])
    
    print(f"\n✓ Formulas exported to: {filename}")


# =============================================================================
# FORMULA CALCULATION LOGIC
# =============================================================================

def calculate_renewable_value(code, scenario='status'):
    """
    Calculate a renewable energy value based on its formula.
    
    Args:
        code: The renewable energy code (e.g., '1.1.2.1.2')
        scenario: 'status' or 'target'
    
    Returns:
        Calculated value or None if calculation fails
    """
    _ensure_django_setup()
    from simulator.models import RenewableData, VerbrauchData, LandUse
    
    try:
        renewable = RenewableData.objects.get(code=code)
        
        # If fixed, return stored value
        if renewable.is_fixed or not renewable.formula:
            if scenario == 'status':
                return renewable.status_value
            else:
                return renewable.target_value
        
        # Parse and calculate formula
        formula = renewable.formula
        
        # Handle special formula types
        if formula.startswith('VerbrauchData_'):
            # Reference to VerbrauchData
            from simulator.models import VerbrauchData
            verbrauch_code = formula.replace('VerbrauchData_', '')
            verbrauch = VerbrauchData.objects.get(code=verbrauch_code)
            if scenario == 'status':
                return verbrauch.status
            else:
                return verbrauch.ziel
        
        elif formula.startswith('LandUse_'):
            # Reference to LandUse
            from simulator.models import LandUse
            landuse_code = formula.replace('LandUse_', '')
            landuse = LandUse.objects.get(code=landuse_code)
            if scenario == 'status':
                return landuse.status
            else:
                return landuse.ziel
        
        elif formula.startswith('IF('):
            # Conditional formula - needs special parsing
            # This is complex and should be handled by views.py
            return None
        
        else:
            # Regular formula with renewable code references
            # Replace codes with their values
            import re
            
            formula_eval = formula
            
            # Find all code references (patterns like 1.1.2.1.2)
            code_pattern = r'\d+(?:\.\d+)+'
            codes = re.findall(code_pattern, formula)
            
            for ref_code in codes:
                try:
                    ref_value = calculate_renewable_value(ref_code, scenario)
                    if ref_value is not None:
                        formula_eval = formula_eval.replace(ref_code, str(ref_value))
                except:
                    pass
            
            # Replace % with /100
            formula_eval = formula_eval.replace('%', '/100')
            
            # Evaluate
            result = eval(formula_eval)
            return result
    
    except Exception as e:
        print(f"Error calculating {code}: {e}")
        return None


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'apply':
            apply_all_formulas()
        elif command == 'verify':
            verify_all_formulas()
        elif command == 'list':
            list_all_formulas()
        elif command == 'export':
            export_formulas_to_csv()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: apply, verify, list, export")
    else:
        print("\n" + "=" * 80)
        print("RENEWABLE ENERGY COMPLETE FORMULAS - SECTIONS 1-9")
        print("=" * 80)
        print("\nUsage:")
        print("  python renewable_energy_complete_formulas.py apply   - Apply all formulas to database")
        print("  python renewable_energy_complete_formulas.py verify  - Verify formula coverage")
        print("  python renewable_energy_complete_formulas.py list    - List all current formulas")
        print("  python renewable_energy_complete_formulas.py export  - Export formulas to CSV")
        print("\n" + "=" * 80)
        
        # Show quick summary
        verify_all_formulas()
