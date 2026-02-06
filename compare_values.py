"""Compare test_365days.py vs ws_365_service.py"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.models import VerbrauchData, RenewableData
from simulator.ws_models import WSData

print("=" * 70)
print("COMPARING VALUES")
print("=" * 70)

# Get WS data
ws_entries = list(WSData.objects.filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365).order_by('tag_im_jahr'))

solar_promille = [ws.solar_promille or 0 for ws in ws_entries]
wind_promille = [ws.wind_promille or 0 for ws in ws_entries]
heizung_abwaerm_promille = [ws.heizung_abwaerm_promille or 0 for ws in ws_entries]
verbrauch_promille = [ws.verbrauch_promille or 0 for ws in ws_entries]

# Get fixed values
verbrauch_7 = VerbrauchData.objects.get(code='7')
verbrauch_7_ziel = verbrauch_7.ziel or 0
verbrauch_292 = VerbrauchData.objects.get(code='2.9.2')
verbrauch_24 = VerbrauchData.objects.get(code='2.4')
verbrauch_292_ziel = verbrauch_292.ziel or 0
verbrauch_24_ziel = verbrauch_24.ziel or 0

r_911 = RenewableData.objects.get(code='9.1.1')
r_912 = RenewableData.objects.get(code='9.1.2')
r_913 = RenewableData.objects.get(code='9.1.3')
r_914 = RenewableData.objects.get(code='9.1.4')
r_92152 = RenewableData.objects.get(code='9.2.1.5.2')

ziel_911 = r_911.target_value or 0
ziel_912 = r_912.target_value or 0
ziel_913 = r_913.target_value or 0
ziel_914 = r_914.target_value or 0
ziel_92152 = r_92152.target_value or 0

print(f"\n--- DATABASE VALUES ---")
print(f"Verbrauch 7 ziel: {verbrauch_7_ziel:,.0f}")
print(f"Verbrauch 2.9.2 ziel: {verbrauch_292_ziel:,.0f}")
print(f"Verbrauch 2.4 ziel: {verbrauch_24_ziel:,.2f}")
print(f"9.1.1 (Wind): {ziel_911:,.0f}")
print(f"9.1.2 (Solar): {ziel_912:,.0f}")
print(f"9.1.3 (Sonst): {ziel_913:,.0f}")
print(f"9.1.4 (Bio): {ziel_914:,.0f}")
print(f"9.2.1.5.2: {ziel_92152:,.0f}")

GRID_LOSS_RATE = 0.092
annual_demand = verbrauch_7_ziel / (1 - GRID_LOSS_RATE)
raumw_korr_annual = verbrauch_292_ziel * (verbrauch_24_ziel / 100)

print(f"\n--- CALCULATED ---")
print(f"Annual Demand: {annual_demand:,.0f}")
print(f"Raumw.korr Annual: {raumw_korr_annual:,.0f}")

# Calculate Day 1 values
d = 0
stromverbrauch = annual_demand * verbrauch_promille[d] / 1000
davon_raumw_korr = raumw_korr_annual * heizung_abwaerm_promille[d] / 365
stromverbr_raumw_korr = stromverbrauch + davon_raumw_korr

sum_renewable = ziel_911 + ziel_912 + ziel_913
value = sum_renewable - ziel_92152
pct = (value / sum_renewable) if sum_renewable > 0 else 0

solar_strom = ziel_912 * pct * solar_promille[d] / 1000
wind_strom = ziel_911 * pct * wind_promille[d] / 1000
sonst_kraftw = ziel_913 * pct / 365

wind_solar_konstant = solar_strom + wind_strom + sonst_kraftw
direktverbr_strom = min(wind_solar_konstant, stromverbr_raumw_korr)

if direktverbr_strom == stromverbr_raumw_korr:
    ueberschuss_strom = wind_solar_konstant - stromverbr_raumw_korr
else:
    ueberschuss_strom = 0

if stromverbr_raumw_korr > 0:
    ratio = ueberschuss_strom / stromverbr_raumw_korr
else:
    ratio = 0

if ratio <= 1:
    einspeich = ueberschuss_strom * 0.65
else:
    einspeich = stromverbr_raumw_korr * 1 * 0.65

mangel_last = stromverbr_raumw_korr - direktverbr_strom

print(f"\n--- DAY 1 VALUES ---")
print(f"solar_promille[0]: {solar_promille[d]}")
print(f"wind_promille[0]: {wind_promille[d]}")
print(f"verbrauch_promille[0]: {verbrauch_promille[d]}")
print(f"heizung_abwaerm_promille[0]: {heizung_abwaerm_promille[d]}")
print(f"Stromverbrauch: {stromverbrauch:,.2f}")
print(f"davon_raumw_korr: {davon_raumw_korr:,.2f}")
print(f"stromverbr_raumw_korr: {stromverbr_raumw_korr:,.2f}")
print(f"Renewable %: {pct*100:.2f}%")
print(f"Solar Strom: {solar_strom:,.2f}")
print(f"Wind Strom: {wind_strom:,.2f}")
print(f"Sonst.Kraftw: {sonst_kraftw:,.2f}")
print(f"Wind+Solar+konstant: {wind_solar_konstant:,.2f}")
print(f"Direktverbr.Strom: {direktverbr_strom:,.2f}")
print(f"Überschuss Strom: {ueberschuss_strom:,.2f}")
print(f"Ratio: {ratio:.4f}")
print(f"Einspeich: {einspeich:,.2f}")
print(f"Mangel-Last: {mangel_last:,.2f}")

# Calculate Ladezust.Brutto for Day 1
# Need to calculate ausspeich_rueckverstr
# First need brennstoff factor
# This requires sum of mangel_last for all days

stromverbr_all = [annual_demand * verbrauch_promille[d] / 1000 for d in range(365)]
raumw_all = [raumw_korr_annual * heizung_abwaerm_promille[d] / 365 for d in range(365)]
stromverbr_raumw_all = [stromverbr_all[d] + raumw_all[d] for d in range(365)]

solar_strom_all = [ziel_912 * pct * solar_promille[d] / 1000 for d in range(365)]
wind_strom_all = [ziel_911 * pct * wind_promille[d] / 1000 for d in range(365)]
sonst_daily = ziel_913 * pct / 365
wsk_all = [solar_strom_all[d] + wind_strom_all[d] + sonst_daily for d in range(365)]

direkt_all = [min(wsk_all[d], stromverbr_raumw_all[d]) for d in range(365)]
mangel_all = [stromverbr_raumw_all[d] - direkt_all[d] for d in range(365)]

mangel_sum = sum(stromverbr_raumw_all) - sum(direkt_all)
if mangel_sum > 0:
    brennstoff_factor = ziel_914 / mangel_sum
else:
    brennstoff_factor = 0

brennstoff_day1 = brennstoff_factor * mangel_all[0]
speicher_ausgl = mangel_all[0] - brennstoff_day1
ausspeich_rueck = speicher_ausgl / 0.585

print(f"\n--- MANGEL CALCULATION ---")
print(f"Mangel Sum (all days): {mangel_sum:,.2f}")
print(f"9.1.4 (Bio): {ziel_914:,.0f}")
print(f"Brennstoff Factor: {brennstoff_factor:.6f}")
print(f"Brennstoff Day 1: {brennstoff_day1:,.2f}")
print(f"Speicher-Ausgl Day 1: {speicher_ausgl:,.2f}")
print(f"Ausspeich.Rück Day 1: {ausspeich_rueck:,.2f}")

# Ladezust Day 1
ladezust_day1 = 0 + einspeich - ausspeich_rueck - 0
print(f"\n--- LADEZUST DAY 1 ---")
print(f"Ladezust.Brutto Day 1 = 0 + {einspeich:.2f} - {ausspeich_rueck:.2f} = {ladezust_day1:.2f}")
