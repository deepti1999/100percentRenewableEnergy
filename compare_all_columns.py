"""Detailed comparison of all columns for multiple days"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.models import VerbrauchData, RenewableData
from simulator.ws_models import WSData
from simulator.ws_365_service import get_ws_365_data

print("=" * 100)
print("COMPARING ALL COLUMN VALUES")
print("=" * 100)

# Get WS service data
service_data = get_ws_365_data(run_goal_seek=False)
daily_data = service_data['daily_data']

# Now calculate manually using the same logic as test_365days.py
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

GRID_LOSS_RATE = 0.092
annual_demand = verbrauch_7_ziel / (1 - GRID_LOSS_RATE)
raumw_korr_annual = verbrauch_292_ziel * (verbrauch_24_ziel / 100)

# Renewable percentage
sum_renewable = ziel_911 + ziel_912 + ziel_913
value = sum_renewable - ziel_92152
pct = (value / sum_renewable) if sum_renewable > 0 else 0

# Calculate all days manually
stromverbrauch = [annual_demand * verbrauch_promille[d] / 1000 for d in range(365)]
davon_raumw_korr = [raumw_korr_annual * heizung_abwaerm_promille[d] / 365 for d in range(365)]
stromverbr_raumw_korr = [stromverbrauch[d] + davon_raumw_korr[d] for d in range(365)]

solar_strom = [ziel_912 * pct * solar_promille[d] / 1000 for d in range(365)]
wind_strom = [ziel_911 * pct * wind_promille[d] / 1000 for d in range(365)]
sonst_kraftw_daily = ziel_913 * pct / 365
sonst_kraftw = [sonst_kraftw_daily for _ in range(365)]

wind_solar_konstant = [solar_strom[d] + wind_strom[d] + sonst_kraftw[d] for d in range(365)]
direktverbr_strom = [min(wind_solar_konstant[d], stromverbr_raumw_korr[d]) for d in range(365)]

ueberschuss_strom = []
for d in range(365):
    if direktverbr_strom[d] == stromverbr_raumw_korr[d]:
        ueberschuss_strom.append(wind_solar_konstant[d] - stromverbr_raumw_korr[d])
    else:
        ueberschuss_strom.append(0)

einspeich = []
for d in range(365):
    if stromverbr_raumw_korr[d] > 0:
        ratio = ueberschuss_strom[d] / stromverbr_raumw_korr[d]
    else:
        ratio = 0
    if ratio <= 1:
        einspeich.append(ueberschuss_strom[d] * 0.65)
    else:
        einspeich.append(stromverbr_raumw_korr[d] * 1 * 0.65)

abregelung = []
for d in range(365):
    if stromverbr_raumw_korr[d] > 0:
        ratio = ueberschuss_strom[d] / stromverbr_raumw_korr[d]
    else:
        ratio = 0
    if ratio <= 1:
        abregelung.append(0)
    else:
        abregelung.append(ueberschuss_strom[d] - einspeich[d] / 0.65)

mangel_last = [stromverbr_raumw_korr[d] - direktverbr_strom[d] for d in range(365)]

mangel_last_min_value = sum(stromverbr_raumw_korr) - sum(direktverbr_strom)
if mangel_last_min_value > 0:
    brennstoff_factor = ziel_914 / mangel_last_min_value
else:
    brennstoff_factor = 0
brennstoff_ausgleich = [brennstoff_factor * mangel_last[d] for d in range(365)]

speicher_ausgl_strom = [mangel_last[d] - brennstoff_ausgleich[d] for d in range(365)]
ausspeich_rueckverstr = [speicher_ausgl_strom[d] / 0.585 for d in range(365)]
ausspeich_gas = [0 for _ in range(365)]

ladezust_brutto = []
for d in range(365):
    if d == 0:
        prev = 0
    else:
        prev = ladezust_brutto[d - 1]
    ladezust_brutto.append(prev + einspeich[d] - ausspeich_rueckverstr[d] - ausspeich_gas[d])

# Compare first 5 days
print("\n" + "=" * 100)
print("COMPARISON: Days 1-5 (Manual vs Service)")
print("=" * 100)

columns = ['stromverbrauch', 'davon_raumw_korr', 'stromverbr_raumw_korr', 'solar_strom', 'wind_strom', 
           'sonst_kraftw', 'wind_solar_konstant', 'direktverbr_strom', 'ueberschuss_strom', 
           'einspeich', 'abregelung', 'mangel_last', 'brennstoff_ausgleich', 'speicher_ausgl_strom',
           'ausspeich_rueckverstr', 'ausspeich_gas', 'ladezust_brutto']

manual_values = {
    'stromverbrauch': stromverbrauch,
    'davon_raumw_korr': davon_raumw_korr,
    'stromverbr_raumw_korr': stromverbr_raumw_korr,
    'solar_strom': solar_strom,
    'wind_strom': wind_strom,
    'sonst_kraftw': sonst_kraftw,
    'wind_solar_konstant': wind_solar_konstant,
    'direktverbr_strom': direktverbr_strom,
    'ueberschuss_strom': ueberschuss_strom,
    'einspeich': einspeich,
    'abregelung': abregelung,
    'mangel_last': mangel_last,
    'brennstoff_ausgleich': brennstoff_ausgleich,
    'speicher_ausgl_strom': speicher_ausgl_strom,
    'ausspeich_rueckverstr': ausspeich_rueckverstr,
    'ausspeich_gas': ausspeich_gas,
    'ladezust_brutto': ladezust_brutto,
}

# Map service keys (some may be different)
service_key_map = {
    'stromverbrauch': 'stromverbrauch',
    'davon_raumw_korr': 'davon_raumw_korr',
    'stromverbr_raumw_korr': 'stromverbr_raumw_korr',
    'solar_strom': 'solar_strom',
    'wind_strom': 'wind_strom',
    'sonst_kraftw': 'sonst_kraftw',
    'wind_solar_konstant': 'wind_solar_konstant',
    'direktverbr_strom': 'direktverbr_strom',
    'ueberschuss_strom': 'ueberschuss_strom',
    'einspeich': 'einspeich',
    'abregelung': 'abregelung',
    'mangel_last': 'mangel_last',
    'brennstoff_ausgleich': 'brennstoff_ausgleich',
    'speicher_ausgl_strom': 'speicher_ausgl_strom',
    'ausspeich_rueckverstr': 'ausspeich_rueckverstr',
    'ausspeich_gas': 'ausspeich_gas',
    'ladezust_brutto': 'ladezust_brutto',
}

for day in [0, 1, 2, 3, 4]:
    print(f"\n--- DAY {day + 1} ---")
    for col in columns:
        manual = manual_values[col][day]
        service_key = service_key_map[col]
        service_val = daily_data[day][service_key]
        diff = abs(manual - service_val)
        status = "✅" if diff < 0.01 else f"❌ DIFF={diff:.2f}"
        print(f"  {col:25s}: Manual={manual:12.2f}, Service={service_val:12.2f} {status}")
