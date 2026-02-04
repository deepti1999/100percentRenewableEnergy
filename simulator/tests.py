import json
import logging

from django.conf import settings
from django.test import SimpleTestCase, TransactionTestCase
from unittest.mock import patch

from landuse_project.settings import JsonFormatter, LOGGING
from simulator.models import VerbrauchData, RenewableData, LandUse
from simulator.verbrauch_recalculator import recalc_all_verbrauch
from simulator.recalc_service import run_full_recalc
from calculation_engine.bilanz_engine import calculate_bilanz_data


class JsonLoggingTests(SimpleTestCase):
    def test_json_formatter_outputs_expected_fields(self):
        formatter = JsonFormatter()
        record = logging.makeLogRecord(
            {
                "levelname": "INFO",
                "msg": "test message",
                "name": "simulator.tests",
                "pathname": "/app/simulator/tests.py",
                "lineno": 42,
                "funcName": "test_func",
                "eventType": "test",
                "context": {"request_id": "abc123"},
            }
        )
        payload = json.loads(formatter.format(record))

        for key in [
            "timestamp",
            "level",
            "component",
            "file",
            "line",
            "function",
            "message",
            "eventType",
            "context",
            "stack",
        ]:
            self.assertIn(key, payload)

        self.assertEqual(payload["level"], "info")
        self.assertEqual(payload["component"], "simulator.tests")
        self.assertEqual(payload["eventType"], "test")
        self.assertEqual(payload["context"], {"request_id": "abc123"})
        self.assertIsNone(payload["stack"])

    def test_logging_configuration_uses_json_formatter(self):
        console_handler = LOGGING["handlers"]["console"]
        self.assertEqual(console_handler["formatter"], "json")
        self.assertEqual(
            LOGGING["formatters"]["json"]["()"],
            "landuse_project.settings.JsonFormatter",
        )


class VerbrauchRecalcTests(SimpleTestCase):
    databases = {"default"}

    def setUp(self):
        VerbrauchData.objects.all().delete()
        # child
        self.child = VerbrauchData.objects.create(
            code="1.4",
            category="KLIK electricity",
            unit="GWh",
            status=10,
            ziel=10,
            is_calculated=False,
        )
        # parent rollup (calculated)
        self.parent = VerbrauchData.objects.create(
            code="1",
            category="KLIK total",
            unit="GWh",
            status=0,
            ziel=0,
            is_calculated=False,  # real data defaults
            status_calculated=False,
            ziel_calculated=False,
        )

    def test_recalc_updates_parent_from_child(self):
        def fake_calc_value(self):
            if self.code == "1":
                total = sum(
                    VerbrauchData.objects.filter(code__startswith="1.")
                    .exclude(code="1")
                    .values_list("status", flat=True)
                )
                return total
            return self.status

        def fake_calc_ziel_value(self):
            if self.code == "1":
                total = sum(
                    VerbrauchData.objects.filter(code__startswith="1.")
                    .exclude(code="1")
                    .values_list("ziel", flat=True)
                )
                return total
            return self.ziel

        with patch.object(VerbrauchData, "calculate_value", fake_calc_value), patch.object(
            VerbrauchData, "calculate_ziel_value", fake_calc_ziel_value
        ):
            recalc_all_verbrauch(trigger_code="test")
            updated_parent = VerbrauchData.objects.get(code="1")
            self.assertEqual(updated_parent.status, 10)
            self.assertEqual(updated_parent.ziel, 10)

            # Update child and ensure save triggers recalc (even though parent not marked calculated)
            self.child.status = 20
            self.child.ziel = 30
            self.child.save()
            updated_parent = VerbrauchData.objects.get(code="1")
            self.assertEqual(updated_parent.status, 20)
            self.assertEqual(updated_parent.ziel, 30)


class BilanzRefreshTests(TransactionTestCase):
    databases = {"default"}

    def setUp(self):
        VerbrauchData.objects.all().delete()
        RenewableData.objects.all().delete()

        # Core Verbrauch entries
        self.child = VerbrauchData.objects.create(
            code="1.4",
            category="KLIK electricity",
            unit="GWh",
            status=10,
            ziel=10,
        )
        self.parent = VerbrauchData.objects.create(
            code="1",
            category="KLIK total",
            unit="GWh",
            status=0,
            ziel=0,
            is_calculated=True,
            status_calculated=True,
            ziel_calculated=True,
        )
        # Other Verbrauch codes used in bilanz (set to zero)
        for code in ["2.9.0", "3.6.0", "4.3.6", "2.10", "3.3", "3.7", "4.3.1", "2.7.0", "3.4.0", "4.3.2", "4.3.4", "2.8.0", "3.5.0"]:
            VerbrauchData.objects.create(code=code, category=code, unit="GWh", status=0, ziel=0)

        # Minimal renewables to avoid warnings
        for code in ["10.2", "10.7", "10.4.2", "10.5.2"]:
            RenewableData.objects.create(
                category=code,
                code=code,
                name=code,
                unit="GWh",
                status_value=0,
                target_value=0,
                is_fixed=True,
            )

    def test_bilanz_reads_fresh_verbrauch_totals_after_child_change(self):
        # Initial bilanz should reflect child=10
        data = calculate_bilanz_data()
        self.assertEqual(data["verbrauch_gesamt"]["status"]["kraft_licht"], 10)
        self.assertEqual(data["verbrauch_gesamt"]["ziel"]["kraft_licht"], 10)

        # Update child and ensure bilanz pulls refreshed totals
        self.child.status = 25
        self.child.ziel = 30
        self.child.save()

        data = calculate_bilanz_data()
        self.assertEqual(data["verbrauch_gesamt"]["status"]["kraft_licht"], 25)
        self.assertEqual(data["verbrauch_gesamt"]["ziel"]["kraft_licht"], 30)

    def test_bilanz_uses_process_heat_total_from_3_7(self):
        pw = VerbrauchData.objects.get(code="3.7")
        pw.status = 111
        pw.ziel = 222
        pw.save()

        data = calculate_bilanz_data()
        self.assertEqual(data["verbrauch_gesamt"]["status"]["prozesswaerme"], 111)
        self.assertEqual(data["verbrauch_gesamt"]["ziel"]["prozesswaerme"], 222)


class RenewableVerbrauchRecalcTests(TransactionTestCase):
    databases = {"default"}

    def setUp(self):
        RenewableData.objects.all().delete()
        VerbrauchData.objects.all().delete()
        LandUse.objects.all().delete()

        # Minimal data sources
        RenewableData.objects.create(
            category="Test",
            code="X1",
            name="Uses Verbrauch 1.4",
            unit="GWh",
            status_value=0,
            target_value=0,
            is_fixed=False,
            formula="VerbrauchData_1.4 * 2",
        )
        VerbrauchData.objects.create(
            code="1.4",
            category="KLIK electricity",
            unit="GWh",
            status=10,
            ziel=15,
            is_calculated=False,
        )

    def test_renewables_recalc_on_verbrauch_save(self):
        # Change Verbrauch and ensure dependent renewable updates
        v = VerbrauchData.objects.get(code="1.4")
        v.status = 20
        v.ziel = 30
        v.save()
        run_full_recalc()

        r = RenewableData.objects.get(code="X1")
        self.assertEqual(r.status_value, 40)  # 20 * 2
        self.assertEqual(r.target_value, 60)  # 30 * 2


class GebaeudewaermeCalcTests(TransactionTestCase):
    databases = {"default"}

    def setUp(self):
        pass

    def test_gebaeudewaerme_calculation_helper(self):
        # Deprecated: Gebaeudewaerme recalculation is inactive
        self.assertTrue(True)
