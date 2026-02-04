from django.db import models


class WSData(models.Model):
    """
    WS (Wärmespeicher/Energy Storage) Data Model
    Replicates the Excel structure from WS.xlsm
    Contains daily energy calculations with multiple parameters
    
    🚀 NOW 100% EXTENSIBLE:
    - Add formulas for ANY row (1-367) via database
    - Add custom columns via 'custom_fields' JSONField (no migrations!)
    - Support complex formulas with IF(), MAX(), MIN(), etc.
    """
    
    # Column A-B: Date and Reference
    tag_im_jahr = models.IntegerField(help_text="Tag im Jahr (Day in Year)")
    datum_ref = models.CharField(max_length=20, help_text="Datum Ref.")
    
    # Columns C-F: Promille values
    wind_promille = models.FloatField(null=True, blank=True, help_text="Wind Promille")
    solar_promille = models.FloatField(null=True, blank=True, help_text="Solar Promille")
    heizung_abwaerm_promille = models.FloatField(null=True, blank=True, help_text="Heizung Abwärm. Promille")
    verbrauch_promille = models.FloatField(null=True, blank=True, help_text="Verbrauch Promille")
    
    # Column G: Stromverbrauch
    stromverbr = models.FloatField(null=True, blank=True, help_text="Stromverbr.")
    
    # Columns H-I: davon Raumw.korr. and Raumwärm.Korr.
    davon_raumw_korr = models.FloatField(null=True, blank=True, help_text="davon Raumw.korr.")
    raumwaerm_korr = models.FloatField(null=True, blank=True, help_text="Raumwärm.Korr.")
    
    # Column J: Stromverbr. Raumwärm.Korr.
    stromverbr_raumwaerm_korr = models.FloatField(null=True, blank=True, help_text="Stromverbr. Raumwärm.Korr.")
    
    # Column K: Windstrom
    windstrom = models.FloatField(null=True, blank=True, help_text="Windstrom")
    
    # Column L: Solarstrom
    solarstrom = models.FloatField(null=True, blank=True, help_text="Solarstrom")
    
    # Column M: Sonst.Kraft(konstant)
    sonst_kraft_konstant = models.FloatField(null=True, blank=True, help_text="Sonst.Kraft(konstant)")
    
    # Column N: Wind+Solar Konstant
    wind_solar_konstant = models.FloatField(null=True, blank=True, help_text="Wind+Solar Konstant")
    
    # Column O: Direktverbr. Strom
    direktverbr_strom = models.FloatField(null=True, blank=True, help_text="Direktverbr. Strom")
    
    # Column P: Überschuss Strom
    ueberschuss_strom = models.FloatField(null=True, blank=True, help_text="Überschuss Strom")
    
    # Column Q: Einspeich
    einspeich = models.FloatField(null=True, blank=True, help_text="Einspeich")
    
    # Column R: Abregelung.Z
    abregelung_z = models.FloatField(null=True, blank=True, help_text="Abregelung.Z")
    
    # Column S: Mangel-Last
    mangel_last = models.FloatField(null=True, blank=True, help_text="Mangel-Last")
    
    # Column T: Brennstoff-Ausgleichs-Strom
    brennstoff_ausgleichs_strom = models.FloatField(null=True, blank=True, help_text="Brennstoff-Ausgleichs-Strom")
    
    # Column U: Speicher-Ausgl-Strom
    speicher_ausgl_strom = models.FloatField(null=True, blank=True, help_text="Speicher-Ausgl-Strom")
    
    # Column V: Ausspeich.Rückverstr.
    ausspeich_rueckverstr = models.FloatField(null=True, blank=True, help_text="Ausspeich.Rückverstr.")
    
    # Column W: Ausspeich. Gas
    ausspeich_gas = models.FloatField(null=True, blank=True, help_text="Ausspeich. Gas")
    
    # Column X: Ladezust.Burtto
    ladezust_burtto = models.FloatField(null=True, blank=True, help_text="Ladezust.Burtto")
    
    # Column Y: LadezustandAbs. vorl.TL
    ladezustand_abs_vorl_tl = models.FloatField(null=True, blank=True, help_text="LadezustandAbs. vorl.TL")
    
    # Column Z: Selbstentl.
    selbstentl = models.FloatField(null=True, blank=True, help_text="Selbstentl.")
    
    # Column AA: Ladezustand Netto
    ladezustand_netto = models.FloatField(null=True, blank=True, help_text="Ladezustand Netto")
    
    # Column AB: Ladezustand Abs.
    ladezustand_abs = models.FloatField(null=True, blank=True, help_text="Ladezustand Abs.")
    
    # Column AC: Entsteht.
    entsteht = models.FloatField(null=True, blank=True, help_text="Entsteht.")
    
    # Column V: Aussprech. Rückwärts.
    aussprech_rueckwaerts = models.FloatField(null=True, blank=True, help_text="Aussprech. Rückwärts.")
    
    # Column W: Aussprech. Gas
    aussprech_gas = models.FloatField(null=True, blank=True, help_text="Aussprech. Gas")
    
    # Column X: Ladeabst. Bunto
    ladeabst_bunto = models.FloatField(null=True, blank=True, help_text="Ladeabst. Bunto")
    
    # Column Y: Ladeabbstand Last vom TL
    ladeabbstand_last_vom_tl = models.FloatField(null=True, blank=True, help_text="Ladeabbstand Last vom TL")
    
    # Column Z: Selbstentl.
    selbstentl = models.FloatField(null=True, blank=True, help_text="Selbstentl.")
    
    # Column AA: Ladeabbzustan Ladezust
    ladeabbzustan_ladezust = models.FloatField(null=True, blank=True, help_text="Ladeabbzustan Ladezust")
    
    # Column AB: Netto
    netto = models.FloatField(null=True, blank=True, help_text="Netto")
    
    # Column AC: Ladeabbzustan
    ladeabbzustan = models.FloatField(null=True, blank=True, help_text="Ladeabbzustan")
    
    # Column AD: ABACADAE
    abacadae = models.FloatField(null=True, blank=True, help_text="ABACADAE")
    
    # Column AE: (appears to be combined header)
    # Column AF: Übersicht Speich-Last
    uebersicht_speich_last = models.FloatField(null=True, blank=True, help_text="Übersicht Speich-Last")
    
    # Column AG: Übersicht Aussprech.
    uebersicht_aussprech = models.FloatField(null=True, blank=True, help_text="Übersicht Aussprech.")
    
    # Column AH: Übersicht Entspeich.
    uebersicht_entspeich = models.FloatField(null=True, blank=True, help_text="Übersicht Entspeich.")
    
    # Column AI: Umrechnun
    umrechnun = models.FloatField(null=True, blank=True, help_text="Umrechnun")
    
    # Column AJ: TL/MWh*(1Y)
    tl_mwh_1y = models.FloatField(null=True, blank=True, help_text="TL/MWh*(1Y)")
    
    # Column AK: Konstanstr. (TL)
    konstanstr_tl = models.FloatField(null=True, blank=True, help_text="Konstanstr. (TL)")
    
    # Column AL: Solarstrom (TL)
    solarstrom_tl = models.FloatField(null=True, blank=True, help_text="Solarstrom (TL)")
    
    # Column AM: Windstrom (TL)
    windstrom_tl = models.FloatField(null=True, blank=True, help_text="Windstrom (TL)")
    
    # Column AN: Solar-Konst (TL)
    solar_konst_tl = models.FloatField(null=True, blank=True, help_text="Solar-Konst (TL)")
    
    # Column AO: Konst.+Win Solar (TL)
    konst_win_solar_tl = models.FloatField(null=True, blank=True, help_text="Konst.+Win Solar (TL)")
    
    # Column AP: Verbrauch (TL)
    verbrauch_tl = models.FloatField(null=True, blank=True, help_text="Verbrauch (TL)")
    
    # Column AQ: Konstantstr.
    konstantstr = models.FloatField(null=True, blank=True, help_text="Konstantstr.")
    
    # Column AR: Solar+Kons (1-TageaY.)
    solar_kons_1_tageay = models.FloatField(null=True, blank=True, help_text="Solar+Kons (1-TageaY.)")
    
    # Column AS: Wind. (Sol+ Win<TV)
    wind_sol_win_tv = models.FloatField(null=True, blank=True, help_text="Wind. (Sol+ Win<TV)")
    
    # Column AT: Unterbedeck.
    unterbedeck = models.FloatField(null=True, blank=True, help_text="Unterbedeck.")
    
    # Column AU: Solar (>TV)
    solar_tv = models.FloatField(null=True, blank=True, help_text="Solar (>TV)")
    
    # Column AV: Wind (>TV)
    wind_tv = models.FloatField(null=True, blank=True, help_text="Wind (>TV)")
    
    # Column AW: Ladeabzustan d.Abs. (TL)
    ladeabzustan_d_abs_tl = models.FloatField(null=True, blank=True, help_text="Ladeabzustan d.Abs. (TL)")
    
    # Column AX: Unterbedeck. Ohne Wind
    unterbedeck_ohne_wind = models.FloatField(null=True, blank=True, help_text="Unterbedeck. Ohne Wind")
    
    # Column AY: (Additional column if needed)
    additional_column_ay = models.FloatField(null=True, blank=True, help_text="Column AY")
    
    # Column AZ: (Additional column if needed)
    additional_column_az = models.FloatField(null=True, blank=True, help_text="Column AZ")
    
    # 🚀 CUSTOM FIELDS - Add ANY column without migrations!
    custom_fields = models.JSONField(
        null=True, 
        blank=True, 
        default=dict,
        help_text="Custom fields - Add any column dynamically! Example: {'my_custom_calc': 123.45, 'special_value': 99.9}"
    )
    
    # Meta information
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['tag_im_jahr']
        verbose_name = "WS Data Entry"
        verbose_name_plural = "WS Data Entries"
    
    def __str__(self):
        return f"Day {self.tag_im_jahr} - {self.datum_ref}"
    
    def get_custom_field(self, field_name, default=0):
        """Get value from custom_fields JSON"""
        if not self.custom_fields:
            return default
        return self.custom_fields.get(field_name, default)
    
    def set_custom_field(self, field_name, value):
        """Set value in custom_fields JSON"""
        if not self.custom_fields:
            self.custom_fields = {}
        self.custom_fields[field_name] = value
        return value
