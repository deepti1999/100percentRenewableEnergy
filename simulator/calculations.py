"""
Solar Energy Calculation Service

This module handles all dynamic calculations for renewable energy data.
Instead of storing formulas as text in the database, we compute values
at runtime using Python functions.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional


class SolarCalculationService:
    """Service class for calculating solar energy values dynamically"""
    
    def __init__(self):
        # Cache for calculated values to avoid repeated calculations
        self._calculation_cache = {}
    
    def calculate_value(self, code: str, data_lookup: Dict[str, float]) -> Optional[float]:
        """
        Calculate the value for a given renewable energy code
        
        Args:
            code: The renewable energy code (e.g., "1.1.1.1.2")
            data_lookup: Dictionary of code -> value for lookups
            
        Returns:
            Calculated value or None if not calculable
        """
        # Check cache first
        cache_key = f"{code}_{hash(str(sorted(data_lookup.items())))}"
        if cache_key in self._calculation_cache:
            return self._calculation_cache[cache_key]
        
        result = self._calculate_by_code(code, data_lookup)
        
        # Cache the result
        if result is not None:
            self._calculation_cache[cache_key] = result
            
        return result
    
    def _calculate_by_code(self, code: str, data: Dict[str, float]) -> Optional[float]:
        """Internal calculation logic organized by code"""
        
        try:
            # Solarthermie calculations
            if code == "1.1.1.1.2":  # Gebäudewärme
                return self._calculate_gebaeudewaerme(data)
            
            # Solarstrom calculations  
            elif code == "1.1.2.1":  # Anteil an solaren Dachflächen (Strom)
                return self._calculate_anteil_strom(data)
            
            elif code == "1.1.2.1.2":  # Bruttostromerzeugung (Dachflächen)
                return self._calculate_bruttostromerzeugung_dach(data)
            
            elif code == "1.1.2.1.2.2":  # Installierte Leistung (Dachflächen)
                return self._calculate_installierte_leistung_dach(data)
            
            # Freiflächen calculations
            elif code == "1.2.1.2":  # Bruttostromerzeugung (Freiflächen)
                return self._calculate_bruttostromerzeugung_frei(data)
            
            elif code == "1.2.1.2.2":  # Installierte Leistung (Freiflächen)
                return self._calculate_installierte_leistung_frei(data)
            
            # Wind calculations
            elif code == "2.1.1.2":  # Installierte Leistung Onshore Wind
                return self._calculate_wind_installierte_leistung_onshore(data)
            
            elif code == "2.1.1.2.2":  # Bruttostromerzeugung Onshore Wind
                return self._calculate_wind_bruttostromerzeugung_onshore(data)
            
            elif code == "2.1.1.2.3":  # Vollbetriebsstunden äquivalent Onshore Wind
                return self._calculate_wind_vollbetriebsstunden_aequivalent_onshore(data)
            
            elif code == "2.2.1.2":  # Installierte Leistung Offshore Wind
                return self._calculate_wind_installierte_leistung_offshore(data)
            
            elif code == "2.2.1.2.3":  # Bruttostromerz.Anteil Deutschland 100%EE Offshore Wind
                return self._calculate_wind_offshore_anteil_deutschland(data)
            
            # Water calculations
            elif code == "3.1.1.2":  # Bruttostromerzeugung Laufwasser
                return self._calculate_water_bruttostromerzeugung(data)
            
            # Biogene Brennstoffe calculations
            elif code == "4.1.1.1":  # Nutzbare Forstfläche
                return self._calculate_biogene_forstflaeche(data)
            elif code == "4.1.1.1.1.2":  # Energieholzaufkommen aus Forstwirtschaft
                return self._calculate_biogene_energieholz_forst(data)
            elif code == "4.1.2.1":  # Anbaufläche (KUP, Miscanthus)
                return self._calculate_biogene_anbauflaeche(data)
            elif code == "4.1.2":  # Aus Ackerbau gesamt (sum of forest + agricultural energy wood)
                return self._calculate_biogene_energieholz_total(data)
            elif code == "4.1.2.1.2":  # Energieholzaufkommen aus Ackerbau
                return self._calculate_biogene_energieholz_acker(data)
            elif code == "4.1.3":  # Energieholzaufkommen gesamt
                return self._calculate_biogene_energieholz_gesamt(data)
            elif code == "4.2.1":  # Getreide-Anbaufläche
                return self._calculate_biogene_getreide_flaeche(data)
            elif code == "4.2.1.1.2":  # Strohbrennstoff-Aufkommen
                return self._calculate_biogene_stroh_aufkommen(data)
            elif code == "4.3":  # Brennstoffaufkommen (fest) NAWARO gesamt
                return self._calculate_biogene_nawaro_gesamt(data)
            elif code == "4.3.1":  # davon Einsatz für Gebäudewärme
                return self._calculate_biogene_gebaeudewaerme(data)
            elif code == "4.3.2":  # davon Einsatz für Prozesswärme
                return self._calculate_biogene_prozesswaerme(data)
            elif code == "4.3.3":  # davon Einsatz für Verstromung
                return self._calculate_biogene_verstromung(data)
            elif code == "4.3.3.2":  # Bruttostromerzeugung
                return self._calculate_biogene_bruttostromerzeugung(data)
            elif code == "4.3.3.4":  # Wärmenetze GW (KWK)
                return self._calculate_biogene_waermenetze_kwk(data)
            elif code == "4.3.4":  # davon Einsatz für Heizwerke/Wärmenetze
                return self._calculate_biogene_heizwerke(data)
            elif code == "4.3.4.2":  # Wärmenetze GW (Heizwerk)
                return self._calculate_biogene_waermenetze_heizwerk(data)
            elif code == "4.4":  # Biogener Anteil der Abfälle (fest)
                return self._calculate_biogene_abfaelle_gesamt(data)
            
            # Biogas calculations
            elif code == "5.1":  # Anbaufläche Energiepflanzen für Biogas
                return self._calculate_biogas_anbauflaeche(data)
            elif code == "5.1.2":  # Biogas aus Energiepflanzen-Anbau
                return self._calculate_biogas_energiepflanzen_anbau(data)
            elif code == "5.4":  # Biogasaufkommen insgesamt
                return self._calculate_biogasaufkommen_gesamt(data)
            elif code == "5.4.1.1":  # Biogas für Prozesswärme
                return self._calculate_biogas_prozesswaerme(data)
            elif code == "5.4.2.2":  # Bruttostromerzeugung
                return self._calculate_biogas_bruttostromerzeugung(data)
            elif code == "5.4.2.4":  # Gebäudewärme (Endenergie)
                return self._calculate_biogas_gebaeudewaerme(data)
            elif code == "5.4.3.2":  # Biokraftstoff (gasförmig)
                return self._calculate_biogas_biokraftstoff_gasfoermig(data)
            elif code == "5.4.4.2":  # Biokraftstoff (flüssig)
                return self._calculate_biogas_biokraftstoff_fluessig(data)
            
            # Biogene Brennstoffe (flüssig) calculations
            elif code == "6.1.1.2":  # Biodiesel aus eigenem Anbau
                return self._calculate_biodiesel_eigenanbau(data)
            elif code == "6.1.3":  # Biodiesel Gesamtaufkommen
                return self._calculate_biodiesel_gesamtaufkommen(data)
            elif code == "6.1.3.1.1":  # Biokraftstoff (flüssig) - Biodiesel mobil
                return self._calculate_biodiesel_biokraftstoff_mobil(data)
            elif code == "6.1.3.2.2":  # Bruttostromerzeugung - Biodiesel
                return self._calculate_biodiesel_bruttostromerzeugung(data)
            elif code == "6.1.3.2.4":  # Gebäudewärme (Endenergie) - Biodiesel
                return self._calculate_biodiesel_gebaeudewaerme(data)
            elif code == "6.2.1.2":  # Bioethanol aus eigenem Anbau
                return self._calculate_bioethanol_eigenanbau(data)
            elif code == "6.2.3":  # Bioethanol gesamt – Mobile Anwendungen
                return self._calculate_bioethanol_mobile_anwendungen(data)
            
            # Umgebungswärme (Environmental Heat) calculations
            elif code == "7.1.2":  # WP-Luft – Antriebsstromaufnahme
                return self._calculate_wp_luft_antriebsstrom(data)
            elif code == "7.1.2.2":  # Nutzwärme (inkl. Antriebsstrom) - Luft
                return self._calculate_wp_luft_nutzwaerme(data)
            elif code == "7.1.2.3":  # davon Wärmegewinn aus der Luft
                return self._calculate_wp_luft_waermegewinn(data)
            elif code == "7.1.4":  # WP-Erdr./Wasser – Antriebsstromaufnahme
                return self._calculate_wp_erdreich_antriebsstrom(data)
            elif code == "7.1.4.2":  # Nutzwärme (inkl. Antriebsstrom) - Erdreich/Wasser
                return self._calculate_wp_erdreich_nutzwaerme(data)
            elif code == "7.1.4.3":  # davon Wärmegewinn Erdreich/Grundwasser
                return self._calculate_wp_erdreich_waermegewinn(data)
            elif code == "7.1.4.3.2":  # Beanspruchte Entzugsfläche
                return self._calculate_wp_erdreich_entzugsflaeche(data)
            elif code == "7.1.4.3.4":  # Anteil beanspruchter Siedlungsfläche
                return self._calculate_wp_erdreich_anteil_siedlungsflaeche(data)
            
            # Tiefengeothermie (Deep Geothermal) calculations
            elif code == "8.1.2":  # Bruttostromerzeugung
                return self._calculate_tiefengeothermie_bruttostromerzeugung(data)
            
            # Stromwandlung / Stromspeicherung (Section 9) calculations
            elif code == "9.1.1":  # aus Windenergie
                return self._calculate_stromwandlung_windenergie_gesamt(data)
            elif code == "9.1.2":  # aus Solarenergie (Photovoltaik)
                return self._calculate_stromwandlung_solarenergie_gesamt(data)
            elif code == "9.1.3":  # aus Wasserkraft + Tiefengeothermie
                return self._calculate_stromwandlung_wasser_geothermie_gesamt(data)
            elif code == "9.1.4":  # aus Biobrennstoffen
                return self._calculate_stromwandlung_biobrennstoffe_gesamt(data)
            elif code == "9.2":  # Summe aller Stromwandlung
                v1 = data.get("9.1.1", 0)
                v2 = data.get("9.1.2", 0)
                v3 = data.get("9.1.3", 0)
                v4 = data.get("9.1.4", 0)
                return round((v1 or 0) + (v2 or 0) + (v3 or 0) + (v4 or 0), 3)
            
            # Endenergieangebot (Section 10) calculations
            elif code == "10.1":  # Endenergie aus Erneuerbaren Q. gesamt
                return self._calculate_endenergie_gesamt(data)
            elif code == "10.2":  # Strom (alle Anwendungsbereiche)
                return self._calculate_endenergie_strom_gesamt(data)
            elif code == "10.2.2":  # Anteil Erneuerb. an Stromverbrauch
                return self._calculate_anteil_erneuerbar_stromverbrauch(data)
            elif code == "10.4":  # Gebäudewärme
                return self._calculate_endenergie_gebaeudewaerme_gesamt(data)
            elif code == "10.5":  # Prozesswärme
                return self._calculate_endenergie_prozesswaerme_gesamt(data)
            elif code == "10.6":  # Mobile Anwendungen
                return self._calculate_endenergie_mobile_anwendungen_gesamt(data)
            elif code == "10.7":  # Brennstoffe (alle Anwendungsbereiche)
                return self._calculate_endenergie_brennstoffe_gesamt(data)
            else:
                # No calculation needed - return None for fixed values
                return None
                
        except (KeyError, TypeError, ZeroDivisionError) as e:
            # Missing data or calculation error
            print(f"Calculation error for {code}: {e}")
            return None
    
    def _calculate_gebaeudewaerme(self, data: Dict[str, float]) -> float:
        """
        Gebäudewärme = (Solare Dachflächen * Anteil Thermie % * Energieertrag Thermie) / 1000
        Formula: (1.1 * 1.1.1.1% * 1.1.1.1.1) / 1000
        Note: Anteil Thermie is in percentage (96% = 96/100), result in GWh/a
        """
        ha_dachflaechen = data.get("1.1", 0)  # Solare Dachflächen (ha)
        anteil_thermie = data.get("1.1.1.1", 0)  # Anteil Thermie (%)
        energieertrag_thermie = data.get("1.1.1.1.1", 0)  # Energieertrag (MWh/ha/a)
        
        # Convert percentage to decimal by dividing by 100, then divide by 1000 for GWh/a
        # Result: ha × (% / 100) × MWh/ha/a / 1000 = GWh/a
        result = (ha_dachflaechen * (anteil_thermie / 100) * energieertrag_thermie) / 1000
        return round(result, 3)
    
    def _calculate_anteil_strom(self, data: Dict[str, float]) -> float:
        """
        Anteil Solarstrom = 100 - Anteil Thermie
        Formula: 100 - 1.1.1.1
        """
        anteil_thermie = data.get("1.1.1.1", 0)  # Anteil Thermie (%)
        result = 100 - anteil_thermie
        return round(result, 1)
    
    def _calculate_bruttostromerzeugung_dach(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung Dachflächen = (Solare Dachflächen * Anteil Strom % * Energieertrag Strom) / 1000
        Formula: (1.1 * 1.1.2.1% * 1.1.2.1.1) / 1000
        Note: Anteil Strom is in percentage (96% = 96/100), result in GWh/a
        """
        ha_dachflaechen = data.get("1.1", 0)  # Solare Dachflächen (ha)
        anteil_strom = self._calculate_anteil_strom(data)  # Calculated value (%)
        energieertrag_strom = data.get("1.1.2.1.1", 0)  # Energieertrag Strom (MWh/ha/a)
        
        # Convert percentage to decimal by dividing by 100, then divide by 1000 for GWh/a
        # Final result: ha × (% / 100) × MWh/ha/a / 1000 = GWh/a
        result = (ha_dachflaechen * (anteil_strom / 100) * energieertrag_strom) / 1000
        return round(result, 3)
    
    def _calculate_installierte_leistung_dach(self, data: Dict[str, float]) -> float:
        """
        Installierte Leistung Dachflächen = (Bruttostromerzeugung * 1000) / Vollbetriebsstunden
        Formula: (1.1.2.1.2 * 1000) / 1.1.2.1.2.1
        Note: Bruttostromerzeugung is in GWh/a, multiply by 1000 to get MWh/a, then divide by hours
        """
        bruttostromerzeugung = self._calculate_bruttostromerzeugung_dach(data)  # GWh/a
        vollbetriebsstunden = data.get("1.1.2.1.2.1", 927)  # Default 927 h/a
        
        if vollbetriebsstunden == 0:
            return 0
            
        # Convert GWh/a to MWh/a by multiplying by 1000, then divide by hours
        result = (bruttostromerzeugung * 1000) / vollbetriebsstunden
        return round(result, 3)
    
    def _calculate_bruttostromerzeugung_frei(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung Freiflächen = (Solar Freiflächen * Energieertrag) / 1000
        Formula: (2.1 * 1.2.1.1) / 1000
        Note: Uses LandUse code 2.1 for Freiflächen area
        """
        ha_freiflaechen = data.get("2.1", 0)  # Solar Freiflächen from LandUse (ha)
        energieertrag = data.get("1.2.1.1", 0)  # Energieertrag (MWh/ha/a)
        
        result = (ha_freiflaechen * energieertrag) / 1000
        return round(result, 3)
    
    def _calculate_installierte_leistung_frei(self, data: Dict[str, float]) -> float:
        """
        Installierte Leistung Freiflächen = (Bruttostromerzeugung * 1000) / Vollbetriebsstunden
        Formula: (1.2.1.2 * 1000) / 1.2.1.2.1
        """
        bruttostromerzeugung = self._calculate_bruttostromerzeugung_frei(data)
        vollbetriebsstunden = data.get("1.2.1.2.1", 927)  # Default 927 h/a
        
        if vollbetriebsstunden == 0:
            return 0
            
        result = (bruttostromerzeugung * 1000) / vollbetriebsstunden
        return round(result, 3)
    
    def _calculate_wind_installierte_leistung_onshore(self, data: Dict[str, float]) -> float:
        """
        Installierte Leistung Onshore Wind = Windparkfläche ÷ spezifischer Flächenbedarf
        Formula: 2.1.1.2 = 2.1.1 ÷ 2.1.1.1
        """
        windparkflaeche = data.get("2.1.1", 0)  # Windparkfläche (ha)
        spez_flaechenbedarf = data.get("2.1.1.1", 0)  # spezifischer Flächenbedarf (ha/MW)
        
        # Calculate: ha ÷ (ha/MW) = MW
        if spez_flaechenbedarf == 0:
            return 0
        result = windparkflaeche / spez_flaechenbedarf
        return round(result, 3)
    
    def _calculate_wind_bruttostromerzeugung_onshore(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung Onshore Wind = (Installierte Leistung * Vollbetriebsstunden) / 1000
        Formula: 2.1.1.2 * 2.1.1.2.1 / 1000
        Units: MW × h/a ÷ 1000 = GWh/a
        """
        installierte_leistung = self._calculate_wind_installierte_leistung_onshore(data)  # MW (calculated)
        vollbetriebsstunden = data.get("2.1.1.2.1", 0)  # Vollbetriebsstunden jährlich (h/a)
        
        if installierte_leistung is None or vollbetriebsstunden == 0:
            return 0
            
        # Calculate: MW × h/a ÷ 1000 = GWh/a
        result = (installierte_leistung * vollbetriebsstunden) / 1000
        return round(result, 3)
    
    def _calculate_wind_vollbetriebsstunden_aequivalent_onshore(self, data: Dict[str, float]) -> float:
        """
        Vollbetriebsstunden äquivalent Onshore Wind = (Bruttostromerzeugung * 1000) / Gesamtpotenzial
        Formula: 2.1.1.2.2 * 1000 / 2.1.1
        Units: GWh/a × 1000 ÷ MW = h/a
        """
        bruttostromerzeugung = self._calculate_wind_bruttostromerzeugung_onshore(data)  # GWh/a (calculated)
        gesamtpotenzial = data.get("2.1.1", 0)  # Gesamtpotenzial installierte Leistung (MW)
        
        if bruttostromerzeugung is None or gesamtpotenzial == 0:
            return 0
            
        # Calculate: GWh/a × 1000 ÷ MW = h/a
        result = (bruttostromerzeugung * 1000) / gesamtpotenzial
        return round(result, 3)
    
    def _calculate_wind_installierte_leistung_offshore(self, data: Dict[str, float]) -> float:
        """
        Installierte Leistung Offshore Wind = Gesamtpotenzial * Ausschöpfung / 1000
        Formula: 2.2.1 * 2.2.1.1 / 1000
        Units: MW × % ÷ 1000 = GW (converted back to MW by multiplying with 1000)
        """
        gesamtpotenzial = data.get("2.2.1", 0)  # Gesamtpotenzial Offshore (MW)
        ausschoepfung = data.get("2.2.1.1", 0)  # Ausschöpfung (%)
        
        if gesamtpotenzial == 0 or ausschoepfung == 0:
            return 0
            
        # Calculate: MW × % ÷ 1000 = GW, then convert back to MW
        # Actually: MW × (% / 100) would be correct for percentage
        # But formula says / 1000, so following exactly as specified
        result = (gesamtpotenzial * ausschoepfung) / 1000
        return round(result, 3)
    
    def _calculate_wind_offshore_anteil_deutschland(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerz.Anteil Deutschland 100%EE Offshore Wind
        Formula: 2.2.1.2.3 = 2.2.1.2 / 2.2.1.2.1 * 2.2.1.2.2
        Units: GWh/a ÷ Menschen × Menschen = GWh/a
        """
        bruttostromerzeugung = data.get("2.2.1.2", 0)  # Bruttostromerzeugung Deutschland (GWh/a)
        einwohner_deutschland = data.get("2.2.1.2.1", 0)  # Einwohner Deutschland
        energieverbraucher_deutschland = data.get("2.2.1.2.2", 0)  # Energieverbraucher Deutschland 100%EE
        
        if einwohner_deutschland == 0:
            return 0
            
        # Calculate: GWh/a ÷ Menschen × Menschen = GWh/a
        result = (bruttostromerzeugung / einwohner_deutschland) * energieverbraucher_deutschland
        return round(result, 3)
    
    def _calculate_water_bruttostromerzeugung(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung Laufwasser = Bodenfläche * Nutzanteil * Energieertrag / 1000
        Formula: 3.1 * 3.1.1% * 3.1.1.1 / 1000
        Units: ha × (% / 100) × MWh/ha/a ÷ 1000 = GWh/a
        """
        bodenflaeche = data.get("3.1", 0)  # Bodenfläche Nds. (ha)
        nutzanteil = data.get("3.1.1", 0)  # Nutzanteil am techn. Potenzial (%)
        energieertrag = data.get("3.1.1.1", 0)  # Energieertrag (techn. Potenzial) (MWh/ha/a)
        
        if bodenflaeche == 0 or nutzanteil == 0 or energieertrag == 0:
            return 0
            
        # Calculate: ha × (% / 100) × MWh/ha/a ÷ 1000 = GWh/a
        # Convert percentage to decimal by dividing by 100, then divide by 1000 for GWh/a
        result = (bodenflaeche * (nutzanteil / 100) * energieertrag) / 1000
        return round(result, 3)
    
    # Biogene Brennstoffe calculation methods
    
    def _calculate_biogene_forstflaeche(self, data: Dict[str, float]) -> float:
        """
        Nutzbare Forstfläche = Maps to original LandUse "3.1" (forest area)
        Uses ORIGINAL_3.1 key to avoid conflict with water mapping that overwrites "3.1"
        """
        # Use the original forest area stored under special key
        forest_area = data.get("ORIGINAL_3.1", 0)  # Original LandUse 3.1 forest area (ha)
        return round(forest_area, 0)
    
    def _calculate_biogene_energieholz_forst(self, data: Dict[str, float]) -> float:
        """
        Energieholzaufkommen aus Forstwirtschaft = (Forstfläche * Nutzungsgrad * Energieertrag) / 1000
        Formula: (4.1.1.1 * 4.1.1.1.1% * 4.1.1.1.1.1) / 1000
        """
        forstflaeche = self._calculate_biogene_forstflaeche(data)  # ha (calculated)
        nutzungsgrad = data.get("4.1.1.1.1", 0)  # Energet. genutzter Anteil am Zuwachs (%)
        energieertrag = data.get("4.1.1.1.1.1", 0)  # Energieertrag (MWh/ha/a)
        
        if forstflaeche == 0 or nutzungsgrad == 0 or energieertrag == 0:
            return 0
            
        # Calculate: (ha × % / 100 × MWh/ha/a) / 1000 = GWh/a
        result = (forstflaeche * (nutzungsgrad / 100) * energieertrag) / 1000
        return round(result, 3)
    
    def _calculate_biogene_anbauflaeche(self, data: Dict[str, float]) -> float:
        """
        Anbaufläche für KUP, Miscanthus usw. = Maps to LandUse "2.2.5" (short rotation coppice)
        """
        # This will be the short rotation coppice area from LandUse data
        kup_area = data.get("2.2.5", 0)  # Short rotation coppice area (ha)
        return round(kup_area, 0)
    
    def _calculate_biogene_energieholz_acker(self, data: Dict[str, float]) -> float:
        """
        Energieholzaufkommen aus Ackerbau = Anbaufläche * Energieertrag / 1000
        Formula: 4.1.2.1 * 4.1.2.1.1 / 1000
        """
        anbauflaeche = self._calculate_biogene_anbauflaeche(data)  # ha (calculated)
        energieertrag = data.get("4.1.2.1.1", 0)  # Energieertrag (MWh/ha/a)
        
        if anbauflaeche == 0 or energieertrag == 0:
            return 0
            
        # Calculate: ha × MWh/ha/a ÷ 1000 = GWh/a
        result = (anbauflaeche * energieertrag) / 1000
        return round(result, 3)
    
    def _calculate_biogene_energieholz_total(self, data: Dict[str, float]) -> float:
        """
        Energieholz total (4.1.2) = Forest energy wood + Agricultural energy wood
        Formula: 4.1.1.1.1.2 + 4.1.2.1.2
        """
        aufkommen_forst = self._calculate_biogene_energieholz_forst(data)  # GWh/a (calculated)
        aufkommen_acker = self._calculate_biogene_energieholz_acker(data)  # GWh/a (calculated)
        
        result = aufkommen_forst + aufkommen_acker
        return round(result, 3)
    
    def _calculate_biogene_energieholz_gesamt(self, data: Dict[str, float]) -> float:
        """
        Energieholzaufkommen gesamt = Aufkommen Forst + Aufkommen Acker
        Formula: 4.1.1.1.1.2 + 4.1.2.1.2
        """
        aufkommen_forst = self._calculate_biogene_energieholz_forst(data)  # GWh/a (calculated)
        aufkommen_acker = self._calculate_biogene_energieholz_acker(data)  # GWh/a (calculated)
        
        result = aufkommen_forst + aufkommen_acker
        return round(result, 3)
    
    def _calculate_biogene_getreide_flaeche(self, data: Dict[str, float]) -> float:
        """
        Getreide-Anbaufläche = Maps to LandUse "2.2.1" (grain cultivation)
        """
        # This will be the grain cultivation area from LandUse data
        grain_area = data.get("2.2.1", 0)  # Grain cultivation area (ha)
        return round(grain_area, 0)
    
    def _calculate_biogene_stroh_aufkommen(self, data: Dict[str, float]) -> float:
        """
        Strohbrennstoff-Aufkommen = (Getreide-Anbaufläche * Nutzungsgrad * Energieertrag) / 1000
        Formula: (4.2.1 * 4.2.1.1% * 4.2.1.1.1) / 1000
        """
        getreide_flaeche = self._calculate_biogene_getreide_flaeche(data)  # ha (calculated)
        nutzungsgrad = data.get("4.2.1.1", 0)  # Energet. genutzter Teil am Strohanfall (%)
        energieertrag = data.get("4.2.1.1.1", 0)  # Energieertrag (MWh/ha/a)
        
        if getreide_flaeche == 0 or nutzungsgrad == 0 or energieertrag == 0:
            return 0
            
        # Calculate: (ha × % / 100 × MWh/ha/a) / 1000 = GWh/a
        result = (getreide_flaeche * (nutzungsgrad / 100) * energieertrag) / 1000
        return round(result, 3)
    
    def _calculate_biogene_nawaro_gesamt(self, data: Dict[str, float]) -> float:
        """
        Brennstoffaufkommen (fest) NAWARO gesamt = Forest energy wood + Agricultural energy wood + Straw
        Formula: 4.3 = 4.1.1.1.2 + 4.1.2.1.2 + 4.2.1.1.2
        """
        energieholz_forst = self._calculate_biogene_energieholz_forst(data)  # 4.1.1.1.2 (GWh/a)
        energieholz_acker = self._calculate_biogene_energieholz_acker(data)  # 4.1.2.1.2 (GWh/a)
        stroh_aufkommen = self._calculate_biogene_stroh_aufkommen(data)  # 4.2.1.1.2 (GWh/a)
        
        result = energieholz_forst + energieholz_acker + stroh_aufkommen
        return round(result, 3)
    
    def _calculate_biogene_gebaeudewaerme(self, data: Dict[str, float]) -> float:
        """
        Einsatz für Gebäudewärme = (Forest energy wood * percentage) + (Straw * percentage)
        Formula: 4.3.1 = (4.1.1.1.2 × 4.1.3.1%) + (4.2.1.1.2 × 4.2.1.1.2.1%)
        """
        energieholz_forst = self._calculate_biogene_energieholz_forst(data)  # 4.1.1.1.2 (GWh/a)
        anteil_forst_gebaeudewaerme = data.get("4.1.3.1", 0)  # Forest percentage for building heat (%)
        
        stroh_aufkommen = self._calculate_biogene_stroh_aufkommen(data)  # 4.2.1.1.2 (GWh/a)
        anteil_stroh_gebaeudewaerme = data.get("4.2.1.1.2.1", 0)  # Straw percentage for building heat (%)
        
        # Calculate: (GWh/a × %) + (GWh/a × %) = GWh/a
        result = (energieholz_forst * (anteil_forst_gebaeudewaerme / 100)) + (stroh_aufkommen * (anteil_stroh_gebaeudewaerme / 100))
        return round(result, 3)
    
    def _calculate_biogene_prozesswaerme(self, data: Dict[str, float]) -> float:
        """
        Einsatz für Prozesswärme = (Forest energy wood * percentage) + (Straw * percentage)
        Formula: 4.3.2 = (4.1.1.1.2 * 4.1.3.2%) + (4.2.1.1.2 * 4.2.1.1.2.2%)
        """
        energieholz_forst = self._calculate_biogene_energieholz_forst(data)  # 4.1.1.1.2 (GWh/a)
        anteil_forst_prozess = data.get("4.1.3.2", 0)  # Forest percentage for process heat (%)
        
        stroh_aufkommen = self._calculate_biogene_stroh_aufkommen(data)  # 4.2.1.1.2 (GWh/a)
        anteil_stroh_prozess = data.get("4.2.1.1.2.2", 0)  # Straw percentage for process heat (%)
        
        # Calculate: (GWh/a × %) + (GWh/a × %) = GWh/a (% already means /100)
        result = (energieholz_forst * (anteil_forst_prozess / 100)) + (stroh_aufkommen * (anteil_stroh_prozess / 100))
        return round(result, 3)
    
    def _calculate_biogene_verstromung(self, data: Dict[str, float]) -> float:
        """
        Einsatz für Verstromung = (Forest energy wood * percentage) + (Straw * percentage)
        Formula: 4.3.3 = (4.1.1.1.2 * 4.1.3.3%) + (4.2.1.1.2 * 4.2.1.1.2.3%)
        """
        energieholz_forst = self._calculate_biogene_energieholz_forst(data)  # 4.1.1.1.2 (GWh/a)
        anteil_forst_verstromung = data.get("4.1.3.3", 0)  # Forest percentage for electricity (%)
        
        stroh_aufkommen = self._calculate_biogene_stroh_aufkommen(data)  # 4.2.1.1.2 (GWh/a)
        anteil_stroh_verstromung = data.get("4.2.1.1.2.3", 0)  # Straw percentage for electricity (%)
        
        # Calculate: (GWh/a × %) + (GWh/a × %) = GWh/a (% already means /100)
        result = (energieholz_forst * (anteil_forst_verstromung / 100)) + (stroh_aufkommen * (anteil_stroh_verstromung / 100))
        return round(result, 3)
    
    def _calculate_biogene_bruttostromerzeugung(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung = Einsatz für Verstromung * Nutzungsgrad
        Formula: 4.3.3.2 = 4.3.3 * 4.3.3.1%
        """
        verstromung = self._calculate_biogene_verstromung(data)  # GWh/a (calculated)
        nutzungsgrad = data.get("4.3.3.1", 0)  # Nutzungsgrad Kraftwerk (%)
        
        if verstromung == 0 or nutzungsgrad == 0:
            return 0
            
        # Calculate: GWh/a × % = GWh/a (as per exact formula 4.3.3.2 = 4.3.3 * 4.3.3.1%)
        result = verstromung * (nutzungsgrad / 100)
        return round(result, 3)
    
    def _calculate_biogene_waermenetze_kwk(self, data: Dict[str, float]) -> float:
        """
        Wärmenetze GW (KWK) = Einsatz für Verstromung * KWK-Abwärme Nutzungsgrad
        Formula: 4.3.3.4 = 4.3.3 * 4.3.3.3%
        """
        verstromung = self._calculate_biogene_verstromung(data)  # GWh/a (calculated)
        kwk_nutzungsgrad = data.get("4.3.3.3", 0)  # Nutzungsgrad KWK-Abwärme effektiv (%)
        
        if verstromung == 0 or kwk_nutzungsgrad == 0:
            return 0
            
        # Calculate: GWh/a × % = GWh/a (as per exact formula 4.3.3.4 = 4.3.3 * 4.3.3.3%)
        result = verstromung * (kwk_nutzungsgrad / 100)
        return round(result, 3)
    
    def _calculate_biogene_heizwerke(self, data: Dict[str, float]) -> float:
        """
        Einsatz für Heizwerke/Wärmenetze = (Forest energy wood * percentage) + (Straw * percentage)
        Formula: 4.3.4 = (4.1.1.1.2 * 4.1.3.4%) + (4.2.1.1.2 * 4.2.1.1.2.4%)
        """
        energieholz_forst = self._calculate_biogene_energieholz_forst(data)  # 4.1.1.1.2 (GWh/a)
        anteil_forst_heizwerk = data.get("4.1.3.4", 0)  # Forest percentage for heating networks (%)
        
        stroh_aufkommen = self._calculate_biogene_stroh_aufkommen(data)  # 4.2.1.1.2 (GWh/a)
        anteil_stroh_heizwerk = data.get("4.2.1.1.2.4", 0)  # Straw percentage for heating networks (%)
        
        # Calculate: (GWh/a × %) + (GWh/a × %) = GWh/a (% already means /100)
        result = (energieholz_forst * (anteil_forst_heizwerk / 100)) + (stroh_aufkommen * (anteil_stroh_heizwerk / 100))
        return round(result, 3)
    
    def _calculate_biogene_waermenetze_heizwerk(self, data: Dict[str, float]) -> float:
        """
        Wärmenetze GW (Heizwerk) = Einsatz für Heizwerke * Nutzungsgrad Heizwerk
        Formula: 4.3.4.2 = 4.3.4 * 4.3.4.1%
        """
        heizwerke_einsatz = self._calculate_biogene_heizwerke(data)  # GWh/a (calculated)
        heizwerk_nutzungsgrad = data.get("4.3.4.1", 0)  # Nutzungsgrad Heizwerk/Wärmenetz (%)
        
        if heizwerke_einsatz == 0 or heizwerk_nutzungsgrad == 0:
            return 0
            
        # Calculate: GWh/a × % = GWh/a (as per formula 4.3.4.2 = 4.3.4 * 4.3.4.1%, % already means /100)
        result = heizwerke_einsatz * (heizwerk_nutzungsgrad / 100)
        return round(result, 3)
    
    def _calculate_biogene_abfaelle_gesamt(self, data: Dict[str, float]) -> float:
        """
        Biogener Anteil der Abfälle (fest) = Bruttostromerzeugung + Wärmenetze GW (Endenergie)
        Formula: 4.4 = 4.4.1 + 4.4.2
        """
        bruttostromerzeugung = data.get("4.4.1", 0)  # Bruttostromerzeugung (GWh/a)
        waermenetze_endenergie = data.get("4.4.2", 0)  # Wärmenetze GW (Endenergie) (GWh/a)
        
        result = bruttostromerzeugung + waermenetze_endenergie
        return round(result, 3)
    
    # Biogas calculation methods
    
    def _calculate_biogas_anbauflaeche(self, data: Dict[str, float]) -> float:
        """
        Anbaufläche Energiepflanzen für Biogas
        Maps to LandUse 2.2.2 (Energiepfl. (Biogas))
        """
        # This gets the area from LandUse data through the mapping in views.py
        # data_lookup["5.1"] = data_lookup["2.2.2"]
        anbauflaeche = data.get("2.2.2", 0)  # Direct LandUse reference
        return anbauflaeche
    
    def _calculate_biogas_energiepflanzen_anbau(self, data: Dict[str, float]) -> float:
        """
        Biogas aus Energiepflanzen-Anbau
        Formula: 5.1.2 = 5.1 * 5.1.1 / 1000
        """
        anbauflaeche = data.get("5.1", 0)  # Anbaufläche Energiepflanzen für Biogas (ha)
        methanertrag = data.get("5.1.1", 0)  # Biogas – Methanertrag (MWh/ha/a)
        
        if anbauflaeche == 0 or methanertrag == 0:
            return 0
            
        # Calculate: (ha × MWh/ha/a) / 1000 = GWh/a
        result = (anbauflaeche * methanertrag) / 1000
        return round(result, 3)
    
    def _calculate_biogasaufkommen_gesamt(self, data: Dict[str, float]) -> float:
        """
        Biogasaufkommen insgesamt
        Formula: 5.4 = 5.1.2 + 5.2 + 5.3
        """
        energiepflanzen_anbau = self._calculate_biogas_energiepflanzen_anbau(data)  # 5.1.2 (GWh/a)
        abfall_reststoff = data.get("5.2", 0)  # Biogas aus Abfall-/Reststoffverwertung (GWh/a)
        klaeranlagen_deponien = data.get("5.3", 0)  # Biogas aus Kläranlagen und Deponien (GWh/a)
        
        result = energiepflanzen_anbau + abfall_reststoff + klaeranlagen_deponien
        return round(result, 3)
    
    def _calculate_biogas_prozesswaerme(self, data: Dict[str, float]) -> float:
        """
        Biogas für Prozesswärme
        Formula: 5.4.1.1 = 5.4 * 5.4.1 / 100
        """
        biogasaufkommen_gesamt = self._calculate_biogasaufkommen_gesamt(data)  # 5.4 (GWh/a)
        anteil_prozesswaerme = data.get("5.4.1", 0)  # davon Einsatz für Prozesswärme (%)
        
        # Calculate: GWh/a × % / 100 = GWh/a
        result = biogasaufkommen_gesamt * (anteil_prozesswaerme / 100)
        return round(result, 3)
    
    def _calculate_biogas_bruttostromerzeugung(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung
        Formula: 5.4.2.2 = 5.4 * 5.4.2 / 100 * 5.4.2.1 / 100
        """
        biogasaufkommen_gesamt = self._calculate_biogasaufkommen_gesamt(data)  # 5.4 (GWh/a)
        anteil_verstromung = data.get("5.4.2", 0)  # davon für Verstromung (%)
        nutzungsgrad_kraftwerk = data.get("5.4.2.1", 0)  # Nutzungsgrad Kraftwerk (%)
        
        # Calculate: GWh/a × % / 100 × % / 100 = GWh/a
        result = biogasaufkommen_gesamt * (anteil_verstromung / 100) * (nutzungsgrad_kraftwerk / 100)
        return round(result, 3)
    
    def _calculate_biogas_gebaeudewaerme(self, data: Dict[str, float]) -> float:
        """
        Gebäudewärme (Endenergie)
        Formula: 5.4.2.4 = 5.4 * 5.4.2% * 5.4.2.3%
        """
        biogasaufkommen_gesamt = self._calculate_biogasaufkommen_gesamt(data)  # 5.4 (GWh/a)
        anteil_verstromung = data.get("5.4.2", 0)  # davon für Verstromung (%)
        nutzungsgrad_kwk_abwaerme = data.get("5.4.2.3", 0)  # Nutzungsgrad KWK-Abwärme effektiv (%)
        
        # Calculate: GWh/a × % / 100 × % / 100 = GWh/a
        result = biogasaufkommen_gesamt * (anteil_verstromung / 100) * (nutzungsgrad_kwk_abwaerme / 100)
        return round(result, 3)
    
    def _calculate_biogas_biokraftstoff_gasfoermig(self, data: Dict[str, float]) -> float:
        """
        Biokraftstoff (gasförmig)
        Formula: 5.4.3.2 = 5.4 * 5.4.3 / 100 * 5.4.3.1 / 100
        """
        biogasaufkommen_gesamt = self._calculate_biogasaufkommen_gesamt(data)  # 5.4 (GWh/a)
        anteil_biomethan = data.get("5.4.3", 0)  # davon Biomethan für mobile Anwendungen (%)
        nutzungsgrad_kraftstoffbereitstellung = data.get("5.4.3.1", 0)  # Nutzungsgrad Kraftstoffbereitstellung (%)
        
        # Calculate: GWh/a × % / 100 × % / 100 = GWh/a
        result = biogasaufkommen_gesamt * (anteil_biomethan / 100) * (nutzungsgrad_kraftstoffbereitstellung / 100)
        return round(result, 3)
    
    def _calculate_biogas_biokraftstoff_fluessig(self, data: Dict[str, float]) -> float:
        """
        Biokraftstoff (flüssig)
        Formula: 5.4.4.2 = 5.4 * 5.4.4 / 100 * 5.4.4.1 / 100
        """
        biogasaufkommen_gesamt = self._calculate_biogasaufkommen_gesamt(data)  # 5.4 (GWh/a)
        anteil_fluessigkraftstoff = data.get("5.4.4", 0)  # davon Flüssigkraftstoff für mobile Anwendungen (%)
        nutzungsgrad_kraftstofferzeugung = data.get("5.4.4.1", 0)  # Nutzungsgrad Kraftstofferzeugung (%)
        
        # Calculate: GWh/a × % / 100 × % / 100 = GWh/a
        result = biogasaufkommen_gesamt * (anteil_fluessigkraftstoff / 100) * (nutzungsgrad_kraftstofferzeugung / 100)
        return round(result, 3)
    
    # Biogene Brennstoffe (flüssig) calculation methods
    
    def _calculate_biodiesel_eigenanbau(self, data: Dict[str, float]) -> float:
        """
        Biodiesel aus eigenem Anbau
        Formula: 6.1.1.2 = 6.1.1 * 6.1.1.1 / 1000
        """
        anbauflaeche_oelpflanzen = data.get("6.1.1", 0)  # Anbaufläche Ölpflanzen für Biodiesel (ha)
        energieertrag_biodiesel = data.get("6.1.1.1", 0)  # Biodiesel – Energieertrag (MWh/ha/a)
        
        # Calculate: ha × MWh/ha/a = MWh/a, then convert to GWh/a
        result = (anbauflaeche_oelpflanzen * energieertrag_biodiesel) / 1000
        return round(result, 3)
    
    def _calculate_biodiesel_gesamtaufkommen(self, data: Dict[str, float]) -> float:
        """
        Biodiesel Gesamtaufkommen
        Formula: 6.1.3 = 6.1.1.2 + 6.1.2
        """
        biodiesel_eigenanbau = self._calculate_biodiesel_eigenanbau(data)  # 6.1.1.2 (GWh/a)
        biodiesel_import_export = data.get("6.1.2", 0)  # Biodiesel aus Import (+) / Export (-) (GWh/a)
        
        result = biodiesel_eigenanbau + biodiesel_import_export
        return round(result, 3)
    
    def _calculate_biodiesel_biokraftstoff_mobil(self, data: Dict[str, float]) -> float:
        """
        Biokraftstoff (flüssig) - Mobile Anwendungen
        Formula: 6.1.3.1.1 = 6.1.3 * 6.1.3.1 / 100
        """
        biodiesel_gesamtaufkommen = self._calculate_biodiesel_gesamtaufkommen(data)  # 6.1.3 (GWh/a)
        anteil_mobile_anwendungen = data.get("6.1.3.1", 0)  # davon Einsatz für mobile Anwendungen (%)
        
        # Calculate: GWh/a × % / 100 = GWh/a
        result = biodiesel_gesamtaufkommen * (anteil_mobile_anwendungen / 100)
        return round(result, 3)
    
    def _calculate_biodiesel_bruttostromerzeugung(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung - Biodiesel
        Formula: 6.1.3.2.2 = 6.1.3 × 6.1.3.2% × 6.1.3.2.1% / 10000
        """
        biodiesel_gesamtaufkommen = self._calculate_biodiesel_gesamtaufkommen(data)  # 6.1.3 (GWh/a)
        anteil_verstromung = data.get("6.1.3.2", 0)  # davon Einsatz für Verstromung (%)
        nutzungsgrad_bhkw = data.get("6.1.3.2.1", 0)  # Nutzungsgrad Blockheizkraftwerk (%)
        
        # Calculate: GWh/a × % × % / 10000 = GWh/a (percentages not divided by 100 first)
        result = biodiesel_gesamtaufkommen * anteil_verstromung * nutzungsgrad_bhkw / 10000
        return round(result, 3)
    
    def _calculate_biodiesel_gebaeudewaerme(self, data: Dict[str, float]) -> float:
        """
        Gebäudewärme (Endenergie) - Biodiesel
        Formula: 6.1.3.2.4 = 6.1.3 * 6.1.3.2% * 6.1.3.2.3%
        """
        gesamtaufkommen = self._calculate_biodiesel_gesamtaufkommen(data)  # 6.1.3 (GWh/a) 
        einsatz_verstromung = data.get("6.1.3.2", 0)  # davon Einsatz für Verstromung (%)
        nutzungsgrad_kwk_abwaerme = data.get("6.1.3.2.3", 0)  # Nutzungsgrad KWK-Abwärme effektiv (%)
        
        # Calculate: GWh/a × (% / 100) × (% / 100) = GWh/a
        result = gesamtaufkommen * (einsatz_verstromung / 100) * (nutzungsgrad_kwk_abwaerme / 100)
        return round(result, 3)
    
    def _calculate_bioethanol_eigenanbau(self, data: Dict[str, float]) -> float:
        """
        Bioethanol aus eigenem Anbau
        Formula: 6.2.1.2 = 6.2.1 * 6.2.1.1 / 1000
        """
        anbauflaeche_energiepflanzen = data.get("6.2.1", 0)  # Anbaufläche Energiepflanzen für Bioethanol (ha)
        energieertrag_bioethanol = data.get("6.2.1.1", 0)  # Bioethanol – Energieertrag (brutto) (MWh/ha/a)
        
        # Calculate: ha × MWh/ha/a = MWh/a, then convert to GWh/a
        result = (anbauflaeche_energiepflanzen * energieertrag_bioethanol) / 1000
        return round(result, 3)
    
    def _calculate_bioethanol_mobile_anwendungen(self, data: Dict[str, float]) -> float:
        """
        Bioethanol gesamt – Mobile Anwendungen
        Formula: 6.2.3 = 6.2.1.2 + 6.2.2
        """
        bioethanol_eigenanbau = self._calculate_bioethanol_eigenanbau(data)  # 6.2.1.2 (GWh/a)
        bioethanol_import_export = data.get("6.2.2", 0)  # Bioethanol aus Import (+) / Export (-) (GWh/a)
        
        result = bioethanol_eigenanbau + bioethanol_import_export
        return round(result, 3)
    
    # Umgebungswärme (Environmental Heat/Heat Pump) calculations
    
    def _calculate_wp_luft_antriebsstrom(self, data: Dict[str, float]) -> float:
        """
        WP-Luft – Antriebsstromaufnahme
        Formula: 7.1.2 = 7.1 * 7.1.1 / 100
        """
        gesamt_antriebsstrom = data.get("7.1", 0)  # Wärmepumpen-Antriebsstromaufnahme (GWh/a)
        anteil_luftkopplung = data.get("7.1.1", 0)  # davon Anlagen mit Luftkopplung (%)
        
        if gesamt_antriebsstrom == 0 or anteil_luftkopplung == 0:
            return 0
        
        result = gesamt_antriebsstrom * (anteil_luftkopplung / 100)
        return round(result, 3)
    
    def _calculate_wp_luft_nutzwaerme(self, data: Dict[str, float]) -> float:
        """
        Nutzwärme (inkl. Antriebsstrom) - Luft
        Formula: 7.1.2.2 = 7.1.2 * 7.1.2.1
        """
        antriebsstrom_luft = self._calculate_wp_luft_antriebsstrom(data)  # 7.1.2 (GWh/a)
        jahresarbeitszahl = data.get("7.1.2.1", 0)  # WP-Luft – Jahresarbeitszahl
        
        if antriebsstrom_luft == 0 or jahresarbeitszahl == 0:
            return 0
        
        result = antriebsstrom_luft * jahresarbeitszahl
        return round(result, 3)
    
    def _calculate_wp_luft_waermegewinn(self, data: Dict[str, float]) -> float:
        """
        davon Wärmegewinn aus der Luft
        Formula: 7.1.2.3 = 7.1.2.2 - 7.1.2
        """
        nutzwaerme = self._calculate_wp_luft_nutzwaerme(data)  # 7.1.2.2 (GWh/a)
        antriebsstrom = self._calculate_wp_luft_antriebsstrom(data)  # 7.1.2 (GWh/a)
        
        result = nutzwaerme - antriebsstrom
        return round(result, 3)
    
    def _calculate_wp_erdreich_antriebsstrom(self, data: Dict[str, float]) -> float:
        """
        WP-Erdreich/Wasser – Antriebsstromaufnahme
        Formula: 7.1.4 = 7.1 * 7.1.3 / 100
        """
        gesamt_antriebsstrom = data.get("7.1", 0)  # Wärmepumpen-Antriebsstromaufnahme (GWh/a)
        anteil_erdreich = data.get("7.1.3", 0)  # davon Anlagen mit Erdreich-/Wasserkopplung (%)
        
        if gesamt_antriebsstrom == 0 or anteil_erdreich == 0:
            return 0
        
        result = gesamt_antriebsstrom * (anteil_erdreich / 100)
        return round(result, 3)
    
    def _calculate_wp_erdreich_nutzwaerme(self, data: Dict[str, float]) -> float:
        """
        Nutzwärme (inkl. Antriebsstrom) - Erdreich/Wasser
        Formula: 7.1.4.2 = 7.1.4 * 7.1.4.1
        """
        antriebsstrom_erdreich = self._calculate_wp_erdreich_antriebsstrom(data)  # 7.1.4 (GWh/a)
        jahresarbeitszahl = data.get("7.1.4.1", 0)  # WP-Erdreich/Wasser – Jahresarbeitszahl
        
        if antriebsstrom_erdreich == 0 or jahresarbeitszahl == 0:
            return 0
        
        result = antriebsstrom_erdreich * jahresarbeitszahl
        return round(result, 3)
    
    def _calculate_wp_erdreich_waermegewinn(self, data: Dict[str, float]) -> float:
        """
        davon Wärmegewinn Erdreich/Grundwasser
        Formula: 7.1.4.3 = 7.1.4.2 - 7.1.4
        """
        nutzwaerme = self._calculate_wp_erdreich_nutzwaerme(data)  # 7.1.4.2 (GWh/a)
        antriebsstrom = self._calculate_wp_erdreich_antriebsstrom(data)  # 7.1.4 (GWh/a)
        
        result = nutzwaerme - antriebsstrom
        return round(result, 3)
    
    def _calculate_wp_erdreich_entzugsflaeche(self, data: Dict[str, float]) -> float:
        """
        Beanspruchte Entzugsfläche
        Formula: 7.1.4.3.2 = 7.1.4.3 / 7.1.4.3.1
        """
        waermegewinn = self._calculate_wp_erdreich_waermegewinn(data)  # 7.1.4.3 (GWh/a)
        waermeertrag = data.get("7.1.4.3.1", 0)  # Wärmeertrag Erdreich/Grundwasser (MWh/ha/a)
        
        if waermegewinn == 0 or waermeertrag == 0:
            return 0
        
        # Convert GWh/a to MWh/a, then divide by MWh/ha/a to get ha
        result = (waermegewinn * 1000) / waermeertrag
        return round(result, 3)
    
    def _calculate_wp_erdreich_anteil_siedlungsflaeche(self, data: Dict[str, float]) -> float:
        """
        Anteil beanspruchter Siedlungsfläche
        Formula: 7.1.4.3.4 = 7.1.4.3.2 / (7.1.4.3.3 / 100)
        """
        entzugsflaeche = self._calculate_wp_erdreich_entzugsflaeche(data)  # 7.1.4.3.2 (ha)
        siedlungsflaeche = data.get("7.1.4.3.3", 0)  # Gebäude- & Freifläche (Siedlung) (ha)
        
        if entzugsflaeche == 0 or siedlungsflaeche == 0:
            return 0
        
        # Calculate percentage: (entzugsfläche / siedlungsfläche) * 100
        # But formula says divide by (siedlungsfläche / 100), which means multiply by 100/siedlungsfläche
        result = entzugsflaeche / (siedlungsflaeche / 100)
        return round(result, 6)
    
    # Tiefengeothermie (Deep Geothermal) calculations
    
    def _calculate_tiefengeothermie_bruttostromerzeugung(self, data: Dict[str, float]) -> float:
        """
        Tiefengeothermie Bruttostromerzeugung
        Formula: 8.1.2 = 8.1 * 8.1.1 / 1000
        """
        netzanschlussleistung = data.get("8.1", 0)  # Netzanschlussleistung (elektrisch) (MW)
        vollbetriebsstunden = data.get("8.1.1", 0)  # Stromerzeugung – Vollbetriebsstunden (h/a)
        
        if netzanschlussleistung == 0 or vollbetriebsstunden == 0:
            return 0
        
        # Calculate: MW × h/a ÷ 1000 = MWh/a ÷ 1000 = GWh/a
        result = (netzanschlussleistung * vollbetriebsstunden) / 1000
        return round(result, 3)
    
    # Stromwandlung / Stromspeicherung (Section 9) calculations
    
    def _calculate_stromwandlung_windenergie_gesamt(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung aus Windenergie gesamt
        Formula: 9.1.1 = 2.1.1.2.2 + 2.2.1.2.3
        """
        onshore_wind = data.get("2.1.1.2.2", 0)  # Bruttostromerzeugung Onshore Wind (GWh/a)
        offshore_wind = data.get("2.2.1.2.3", 0)  # Bruttostromerz.Anteil Deutschland Offshore Wind (GWh/a)
        
        # Calculate sum: GWh/a + GWh/a = GWh/a
        result = onshore_wind + offshore_wind
        return round(result, 3)
    
    def _calculate_stromwandlung_solarenergie_gesamt(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung aus Solarenergie (Photovoltaik) gesamt
        Formula: 9.1.2 = 1.1.2.1.2 + 1.2.1.2
        """
        dach = self._calculate_bruttostromerzeugung_dach(data)
        frei = self._calculate_bruttostromerzeugung_frei(data)
        return round((dach or 0) + (frei or 0), 3)

    def _calculate_stromwandlung_wasser_geothermie_gesamt(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung aus Wasserkraft + Tiefengeothermie gesamt
        Formula: 9.1.3 = 3.1.1.2 + 8.1.2
        """
        wasser = data.get("3.1.1.2", 0)
        geo = data.get("8.1.2", 0)
        return round((wasser or 0) + (geo or 0), 3)

    def _calculate_stromwandlung_biobrennstoffe_gesamt(self, data: Dict[str, float]) -> float:
        """
        Bruttostromerzeugung aus Biobrennstoffen gesamt
        Formula: 9.1.4 = 4.3.3.2 + 4.4.1 + 5.4.2.2 + 6.1.3.2.2
        """
        kwk = data.get("4.3.3.2", 0)
        abfall = data.get("4.4.1", 0)
        biogas = data.get("5.4.2.2", 0)
        biodiesel = data.get("6.1.3.2.2", 0)
        return round((kwk or 0) + (abfall or 0) + (biogas or 0) + (biodiesel or 0), 3)

    def get_calculation_info(self, code: str) -> Dict[str, Any]:
        """
        Get information about how a value is calculated
        
        Returns:
            Dictionary with calculation metadata
        """
        calculation_map = {
            "1.1.1.1.2": {
                "name": "Gebäudewärme",
                "formula_text": "(1.1 * 1.1.1.1 * 1.1.1.1.1) / 1000",
                "dependencies": ["1.1", "1.1.1.1", "1.1.1.1.1"],
                "description": "Wärmeerzeugung aus solarer Dachfläche"
            },
            "1.1.2.1": {
                "name": "Anteil Solarstrom",
                "formula_text": "100 - 1.1.1.1",
                "dependencies": ["1.1.1.1"],
                "description": "Anteil der Dachfläche für Stromerzeugung"
            },
            "1.1.2.1.2": {
                "name": "Bruttostromerzeugung Dachflächen",
                "formula_text": "(1.1 * 1.1.2.1 * 1.1.2.1.1) / 1000",
                "dependencies": ["1.1", "1.1.2.1", "1.1.2.1.1"],
                "description": "Stromerzeugung aus solarer Dachfläche"
            },
            "1.1.2.1.2.2": {
                "name": "Installierte Leistung Dachflächen",
                "formula_text": "(1.1.2.1.2 * 1000) / 1.1.2.1.2.1",
                "dependencies": ["1.1.2.1.2", "1.1.2.1.2.1"],
                "description": "Installierte PV-Leistung auf Dachflächen"
            },
            "1.2.1.2": {
                "name": "Bruttostromerzeugung Freiflächen",
                "formula_text": "(1.2 * 1.2.1.1) / 1000",
                "dependencies": ["1.2", "1.2.1.1"],
                "description": "Stromerzeugung aus solaren Freiflächen"
            },
            "1.2.1.2.2": {
                "name": "Installierte Leistung Freiflächen", 
                "formula_text": "(1.2.1.2 * 1000) / 1.2.1.2.1",
                "dependencies": ["1.2.1.2", "1.2.1.2.1"],
                "description": "Installierte PV-Leistung auf Freiflächen"
            },
            "2.1.1.2": {
                "name": "Installierte Leistung Onshore Wind",
                "formula_text": "2.1.1 / 2.1.1.1",
                "dependencies": ["2.1.1", "2.1.1.1"],
                "description": "Installierte Windkraft-Leistung Onshore"
            },
            "2.1.1.2.2": {
                "name": "Bruttostromerzeugung Onshore Wind",
                "formula_text": "2.1.1.2 * 2.1.1.2.1 / 1000",
                "dependencies": ["2.1.1.2", "2.1.1.2.1"],
                "description": "Bruttostromerzeugung aus Onshore-Windkraft"
            },
            "2.1.1.2.3": {
                "name": "Vollbetriebsstunden äquivalent Onshore Wind",
                "formula_text": "2.1.1.2.2 * 1000 / 2.1.1",
                "dependencies": ["2.1.1.2.2", "2.1.1"],
                "description": "Vollbetriebsstunden äquivalent aus Onshore-Windkraft"
            },
            "2.2.1.2": {
                "name": "Installierte Leistung Offshore Wind",
                "formula_text": "2.2.1 * 2.2.1.1 / 1000",
                "dependencies": ["2.2.1", "2.2.1.1"],
                "description": "Installierte Windkraft-Leistung Offshore"
            },
            "2.2.1.2.3": {
                "name": "Bruttostromerz.Anteil Deutschland 100%EE",
                "formula_text": "2.2.1.2 / 2.2.1.2.1 * 2.2.1.2.2",
                "dependencies": ["2.2.1.2", "2.2.1.2.1", "2.2.1.2.2"],
                "description": "Bruttostromerz. Anteil Deutschland 100%EE Offshore Wind"
            },
            "3.1.1.2": {
                "name": "Bruttostromerzeugung Laufwasser",
                "formula_text": "3.1 * 3.1.1% * 3.1.1.1 / 1000",
                "dependencies": ["3.1", "3.1.1", "3.1.1.1"],
                "description": "Bruttostromerzeugung aus Laufwasser"
            },
            # Biogene Brennstoffe calculations
            "4.1.1.1": {
                "name": "Nutzbare Forstfläche",
                "formula_text": "Original LandUse 3.1 (Forest area)",
                "dependencies": ["ORIGINAL_3.1"],
                "description": "Nutzbare Forstfläche aus originalem LandUse 3.1"
            },
            "4.1.1.1.1.2": {
                "name": "Energieholzaufkommen Forst",
                "formula_text": "4.1.1.1 * 4.1.1.1.1% * 4.1.1.1.1.1 / 1000",
                "dependencies": ["4.1.1.1", "4.1.1.1.1", "4.1.1.1.1.1"],
                "description": "Energieholzaufkommen aus Forstwirtschaft"
            },
            "4.1.2.1": {
                "name": "Anbaufläche KUP",
                "formula_text": "LandUse 2.2.5 (Short rotation coppice)",
                "dependencies": ["2.2.5"],
                "description": "Anbaufläche für KUP, Miscanthus usw."
            },
            "4.1.2.1.2": {
                "name": "Energieholzaufkommen Acker",
                "formula_text": "4.1.2.1 * 4.1.2.1.1 / 1000",
                "dependencies": ["4.1.2.1", "4.1.2.1.1"],
                "description": "Energieholzaufkommen aus Ackerbau"
            },
            "4.1.2": {
                "name": "Aus Ackerbau gesamt",
                "formula_text": "4.1.1.1.1.2 + 4.1.2.1.2",
                "dependencies": ["4.1.1.1.1.2", "4.1.2.1.2"],
                "description": "Gesamtes Energieholzaufkommen aus Ackerbau"
            },
            "4.1.3": {
                "name": "Energieholzaufkommen gesamt",
                "formula_text": "4.1.1.1.1.2 + 4.1.2.1.2",
                "dependencies": ["4.1.1.1.1.2", "4.1.2.1.2"],
                "description": "Gesamtes Energieholzaufkommen"
            },
            "4.2.1": {
                "name": "Getreide-Anbaufläche",
                "formula_text": "LandUse 2.2.1 (Grain cultivation)",
                "dependencies": ["2.2.1"],
                "description": "Getreide-Anbaufläche für Stroh"
            },
            "4.2.1.1.2": {
                "name": "Strohbrennstoff-Aufkommen",
                "formula_text": "4.2.1 * 4.2.1.1% * 4.2.1.1.1 / 1000",
                "dependencies": ["4.2.1", "4.2.1.1", "4.2.1.1.1"],
                "description": "Strohbrennstoff-Aufkommen aus Getreideanbau"
            },
            "4.3": {
                "name": "NAWARO gesamt",
            },
            "4.2.1.1.2": {
                "name": "Strohbrennstoff-Aufkommen",
                "formula_text": "4.2.1 * 4.2.1.1% * 4.2.1.1.1 / 1000",
                "dependencies": ["4.2.1", "4.2.1.1", "4.2.1.1.1"],
                "description": "Strohbrennstoff-Aufkommen aus Getreideanbau"
            },
            "4.3": {
                "name": "NAWARO gesamt",
                "formula_text": "4.1.3 + 4.2.1.1.2",
                "dependencies": ["4.1.3", "4.2.1.1.2"],
                "description": "Brennstoffaufkommen (fest) NAWARO gesamt"
            },
            "4.3.1": {
                "name": "Einsatz Gebäudewärme",
                "formula_text": "4.3 * 4.1.3.1% / 100",
                "dependencies": ["4.3", "4.1.3.1"],
                "description": "NAWARO-Einsatz für Gebäudewärme"
            },
            "4.3.2": {
                "name": "Einsatz Prozesswärme", 
                "formula_text": "4.3 * 4.1.3.2% / 100",
                "dependencies": ["4.3", "4.1.3.2"],
                "description": "NAWARO-Einsatz für Prozesswärme"
            },
            "4.3.3": {
                "name": "Einsatz Verstromung",
                "formula_text": "4.3 * 4.1.3.3% / 100",
                "dependencies": ["4.3", "4.1.3.3"],
                "description": "NAWARO-Einsatz für Verstromung"
            },
            "4.3.3.2": {
                "name": "Bruttostromerzeugung NAWARO",
                "formula_text": "4.3.3 * 4.3.3.1% / 100",
                "dependencies": ["4.3.3", "4.3.3.1"],
                "description": "Bruttostromerzeugung aus NAWARO"
            },
            "4.3.3.4": {
                "name": "Wärmenetze KWK",
                "formula_text": "4.3.3 * 4.3.3.3% / 100",
                "dependencies": ["4.3.3", "4.3.3.3"],
                "description": "Wärmenetze aus KWK-Abwärme"
            },
            "4.3.4": {
                "name": "Einsatz Heizwerke",
                "formula_text": "4.3 - (4.3.1 + 4.3.2 + 4.3.3)",
                "dependencies": ["4.3", "4.3.1", "4.3.2", "4.3.3"],
                "description": "NAWARO-Einsatz für Heizwerke/Wärmenetze"
            },
            "4.3.4.2": {
                "name": "Wärmenetze Heizwerk",
                "formula_text": "4.3.4 * 4.3.4.1% / 100",
                "dependencies": ["4.3.4", "4.3.4.1"],
                "description": "Wärmenetze aus Heizwerken"
            },
            "4.4": {
                "name": "Biogene Abfälle gesamt",
                "formula_text": "4.4.1 + 4.4.2",
                "dependencies": ["4.4.1", "4.4.2"],
                "description": "Biogener Anteil der Abfälle (fest)"
            },
            # Biogas calculations
            "5.1": {
                "name": "Anbaufläche Energiepflanzen",
                "formula_text": "LandUse 2.2.2 (Energiepfl. Biogas)",
                "dependencies": ["2.2.2"],
                "description": "Anbaufläche Energiepflanzen für Biogas (ha)"
            },
            "5.1.2": {
                "name": "Biogas Energiepflanzen",
                "formula_text": "5.1 × 5.1.1 ÷ 1000",
                "dependencies": ["5.1", "5.1.1"],
                "description": "Biogas aus Energiepflanzen-Anbau (GWh/a)"
            },
            "5.4": {
                "name": "Biogasaufkommen gesamt",
                "formula_text": "5.1.2 + 5.2 + 5.3",
                "dependencies": ["5.1.2", "5.2", "5.3"],
                "description": "Biogasaufkommen insgesamt (GWh/a)"
            },
            "5.4.1.1": {
                "name": "Biogas Prozesswärme",
                "formula_text": "5.4 × (5.4.1 ÷ 100)",
                "dependencies": ["5.4", "5.4.1"],
                "description": "Biogas für Prozesswärme (GWh/a)"
            },
            "5.4.2.2": {
                "name": "Bruttostromerzeugung",
                "formula_text": "5.4 × (5.4.2 ÷ 100) × (5.4.2.1 ÷ 100)",
                "dependencies": ["5.4", "5.4.2", "5.4.2.1"],
                "description": "Bruttostromerzeugung (GWh/a)"
            },
            "5.4.2.4": {
                "name": "Gebäudewärme Endenergie",
                "formula_text": "5.4 × (5.4.2 ÷ 100) × (5.4.2.3 ÷ 100)",
                "dependencies": ["5.4", "5.4.2", "5.4.2.3"],
                "description": "Gebäudewärme (Endenergie) (GWh/a)"
            },
            "5.4.3.2": {
                "name": "Biokraftstoff gasförmig",
                "formula_text": "5.4 × (5.4.3 ÷ 100) × (5.4.3.1 ÷ 100)",
                "dependencies": ["5.4", "5.4.3", "5.4.3.1"],
                "description": "Biokraftstoff (gasförmig) (GWh/a)"
            },
            "5.4.4.2": {
                "name": "Biokraftstoff flüssig",
                "formula_text": "5.4 × (5.4.4 ÷ 100) × (5.4.4.1 ÷ 100)",
                "dependencies": ["5.4", "5.4.4", "5.4.4.1"],
                "description": "Biokraftstoff (flüssig) (GWh/a)"
            },
            # Biogene Brennstoffe (flüssig) calculations
            "6.1.1.2": {
                "name": "Biodiesel Eigenanbau",
                "formula_text": "6.1.1 × 6.1.1.1 ÷ 1000",
                "dependencies": ["6.1.1", "6.1.1.1"],
                "description": "Biodiesel aus eigenem Anbau (GWh/a)"
            },
            "6.1.3": {
                "name": "Biodiesel Gesamtaufkommen",
                "formula_text": "6.1.1.2 + 6.1.2",
                "dependencies": ["6.1.1.2", "6.1.2"],
                "description": "Biodiesel Gesamtaufkommen (GWh/a)"
            },
            "6.1.3.1.1": {
                "name": "Biokraftstoff flüssig mobil",
                "formula_text": "6.1.3 × (6.1.3.1 ÷ 100)",
                "dependencies": ["6.1.3", "6.1.3.1"],
                "description": "Biokraftstoff (flüssig) (GWh/a)"
            },
            "6.1.3.2.2": {
                "name": "Bruttostromerzeugung Biodiesel",
                "formula_text": "6.1.3 × 6.1.3.2% × 6.1.3.2.1% ÷ 10000",
                "dependencies": ["6.1.3", "6.1.3.2", "6.1.3.2.1"],
                "description": "Bruttostromerzeugung (GWh/a)"
            },
            "6.1.3.2.4": {
                "name": "Gebäudewärme Biodiesel",
                "formula_text": "6.1.3.2.2 × (6.1.3.2.3 ÷ 100)",
                "dependencies": ["6.1.3.2.2", "6.1.3.2.3"],
                "description": "Gebäudewärme (Endenergie) (GWh/a)"
            },
            "6.2.1.2": {
                "name": "Bioethanol Eigenanbau",
                "formula_text": "6.2.1 × 6.2.1.1 ÷ 1000",
                "dependencies": ["6.2.1", "6.2.1.1"],
                "description": "Bioethanol aus eigenem Anbau (GWh/a)"
            },
            "6.2.3": {
                "name": "Bioethanol Mobile Anwendungen",
                "formula_text": "6.2.1.2 + 6.2.2",
                "dependencies": ["6.2.1.2", "6.2.2"],
                "description": "Bioethanol gesamt – Mobile Anwendungen (GWh/a)"
            },
            # Umgebungswärme (Environmental Heat) calculations
            "7.1.2": {
                "name": "WP-Luft Antriebsstrom",
                "formula_text": "7.1 × 7.1.1 ÷ 100",
                "dependencies": ["7.1", "7.1.1"],
                "description": "WP-Luft – Antriebsstromaufnahme (GWh/a)"
            },
            "7.1.2.2": {
                "name": "WP-Luft Nutzwärme",
                "formula_text": "7.1.2 × 7.1.2.1",
                "dependencies": ["7.1.2", "7.1.2.1"],
                "description": "Nutzwärme (inkl. Antriebsstrom) - Luft (GWh/a)"
            },
            "7.1.2.3": {
                "name": "WP-Luft Wärmegewinn",
                "formula_text": "7.1.2.2 - 7.1.2",
                "dependencies": ["7.1.2.2", "7.1.2"],
                "description": "davon Wärmegewinn aus der Luft (GWh/a)"
            },
            "7.1.4": {
                "name": "WP-Erdreich Antriebsstrom",
                "formula_text": "7.1 × 7.1.3 ÷ 100",
                "dependencies": ["7.1", "7.1.3"],
                "description": "WP-Erdreich/Wasser – Antriebsstromaufnahme (GWh/a)"
            },
            "7.1.4.2": {
                "name": "WP-Erdreich Nutzwärme",
                "formula_text": "7.1.4 × 7.1.4.1",
                "dependencies": ["7.1.4", "7.1.4.1"],
                "description": "Nutzwärme (inkl. Antriebsstrom) - Erdreich/Wasser (GWh/a)"
            },
            "7.1.4.3": {
                "name": "WP-Erdreich Wärmegewinn",
                "formula_text": "7.1.4.2 - 7.1.4",
                "dependencies": ["7.1.4.2", "7.1.4"],
                "description": "davon Wärmegewinn Erdreich/Grundwasser (GWh/a)"
            },
            "7.1.4.3.2": {
                "name": "Beanspruchte Entzugsfläche",
                "formula_text": "7.1.4.3 ÷ 7.1.4.3.1",
                "dependencies": ["7.1.4.3", "7.1.4.3.1"],
                "description": "Beanspruchte Entzugsfläche (ha)"
            },
            "7.1.4.3.4": {
                "name": "Anteil beanspruchter Siedlungsfläche",
                "formula_text": "7.1.4.3.2 ÷ (7.1.4.3.3 ÷ 100)",
                "dependencies": ["7.1.4.3.2", "7.1.4.3.3"],
                "description": "Anteil beanspruchter Siedlungsfläche (%)"
            },
            # Tiefengeothermie (Deep Geothermal) calculations
            "8.1.2": {
                "name": "Tiefengeothermie Bruttostromerzeugung",
                "formula_text": "8.1 × 8.1.1 ÷ 1000",
                "dependencies": ["8.1", "8.1.1"],
                "description": "Bruttostromerzeugung (GWh/a)"
            },
            # Stromwandlung / Stromspeicherung (Section 9) calculations
            "9.1.1": {
                "name": "Bruttostromerzeugung aus Windenergie gesamt",
                "formula_text": "2.1.1.2.2 + 2.2.1.2.3",
                "dependencies": ["2.1.1.2.2", "2.2.1.2.3"],
                "description": "Gesamte Bruttostromerzeugung aus Windenergie (GWh/a)"
            },
            "9.1.2": {
                "name": "Bruttostromerzeugung aus Solarenergie gesamt",
                "formula_text": "1.1.2.1.2 + 1.2.1.2",
                "dependencies": ["1.1.2.1.2", "1.2.1.2"],
                "description": "Gesamte Bruttostromerzeugung aus Photovoltaik (GWh/a)"
            },
            "9.1.3": {
                "name": "Bruttostromerzeugung aus Wasserkraft + Tiefengeothermie gesamt",
                "formula_text": "3.1.1.2 + 8.1.2",
                "dependencies": ["3.1.1.2", "8.1.2"],
                "description": "Gesamte Bruttostromerzeugung aus Wasser und Geothermie (GWh/a)"
            },
            "9.1.4": {
                "name": "Bruttostromerzeugung aus Biobrennstoffen gesamt",
                "formula_text": "4.3.3.2 + 4.4.1 + 5.4.2.2 + 6.1.3.2.2",
                "dependencies": ["4.3.3.2", "4.4.1", "5.4.2.2", "6.1.3.2.2"],
                "description": "Gesamte Bruttostromerzeugung aus Biobrennstoffen (GWh/a)"
            },
            "9.2": {
                "name": "Bruttostromerzeugung gesamt (Stromwandlung)",
                "formula_text": "9.1.1 + 9.1.2 + 9.1.3 + 9.1.4",
                "dependencies": ["9.1.1", "9.1.2", "9.1.3", "9.1.4"],
                "description": "Summe aller Bruttostromerzeugung aus Stromwandlung (GWh/a)"
            }
        }
        
        return calculation_map.get(code, {
            "name": "Fixed Value",
            "formula_text": "Direct from CSV",
            "dependencies": [],
            "description": "Fixed value from data source"
        })
    
    def clear_cache(self):
        """Clear the calculation cache"""
        self._calculation_cache.clear()


class SolarTargetCalculationService(SolarCalculationService):
    """Service class for calculating solar energy TARGET values dynamically"""
    
    def calculate_value(self, code: str, data_lookup: Dict[str, float]) -> Optional[float]:
        """
        Calculate the TARGET value for a given renewable energy code
        
        Args:
            code: The renewable energy code (e.g., "1.1.1.1.2")
            data_lookup: Dictionary of code -> TARGET value for lookups
            
        Returns:
            Calculated target value or None if not calculable
        """
        # Check cache first
        cache_key = f"target_{code}_{hash(str(sorted(data_lookup.items())))}"
        if cache_key in self._calculation_cache:
            return self._calculation_cache[cache_key]
        
        result = self._calculate_by_code(code, data_lookup)
        
        # Cache the result
        if result is not None:
            self._calculation_cache[cache_key] = result
            
        return result
    
    def get_calculation_info(self, code: str) -> Dict[str, Any]:
        """
        Get information about how a TARGET value is calculated
        
        Returns:
            Dictionary with calculation metadata for targets
        """
    calculation_map = {
            "1.1.1.1.2": {
                "name": "Gebäudewärme (Target)",
                "formula_text": "(1.1_target * 1.1.1.1_target * 1.1.1.1.1_target) / 1000",
                "dependencies": ["1.1", "1.1.1.1", "1.1.1.1.1"],
                "description": "Ziel-Wärmeerzeugung aus solarer Dachfläche"
            },
            "9.1.4": {
                "name": "Bruttostromerzeugung aus Biobrennstoffen gesamt",
                "formula_text": "4.3.3.2 + 4.4.1 + 5.4.2.2 + 6.1.3.2.2",
                "dependencies": ["4.3.3.2", "4.4.1", "5.4.2.2", "6.1.3.2.2"],
                "description": "Gesamte Bruttostromerzeugung aus Biobrennstoffen (GWh/a)"
            },
            "9.2": {
                "name": "Bruttostromerzeugung gesamt (Stromwandlung)",
                "formula_text": "9.1.1 + 9.1.2 + 9.1.3 + 9.1.4",
                "dependencies": ["9.1.1", "9.1.2", "9.1.3", "9.1.4"],
                "description": "Summe aller Bruttostromerzeugung aus Stromwandlung (GWh/a)"
            }
        }


# Global instances for use throughout the application
solar_calculator = SolarCalculationService()
solar_target_calculator = SolarTargetCalculationService()