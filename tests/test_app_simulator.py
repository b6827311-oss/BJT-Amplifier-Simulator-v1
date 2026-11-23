import unittest
from types import SimpleNamespace
from unittest.mock import patch

import spice_engine as se
from app import app


SIM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "rl": "10",
    "cin": "10",
    "cout": "10",
    "amp": "10",
    "freq": "1000",
    "analysis": "dc",
}

ENGINE = {
    "path": "C:/fake/ngspice_con.exe",
    "version": "ngspice-47",
    "label": "ngspice-47",
}


def stub_run(params, analysis):
    """A deterministic SpiceRun-shaped object; no ngspice is started."""

    plot = se.RawPlot(
        variables=[
            "v(vb)", "v(ve)", "v(vc)", "i(@q1[ic])", "i(@q1[ib])",
            "i(@q1[ie])", "v(@q1[vbe])",
        ],
        points=[[1.95, 1.29, 9.19, -1.278e-3, -11.9e-6, -1.29e-3, 0.66]],
    )
    return se.SpiceRun(
        analysis=analysis,
        netlist="* stub netlist\n.end\n",
        log="* stub log\n",
        plot=plot,
        engine=ENGINE,
        elapsed=0.012,
        raw_bytes=1024,
        meta={},
    )


class TestSimulatorRoutes(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_get_simulator_has_expected_controls_and_no_results(self):
        res = self.client.get("/simulator")
        self.assertEqual(res.status_code, 200)
        text = res.get_data(as_text=True)
        self.assertIn("Run DC", text)
        self.assertIn("Run AC", text)
        self.assertIn("Run Transient", text)
        self.assertIn("Amplitude", text)
        self.assertNotIn("Run OK", text)

    def test_post_converts_form_units_once(self):
        with patch.object(se, "engine_info", return_value=ENGINE), \
             patch.object(se, "run_analysis", side_effect=stub_run) as run:
            res = self.client.post("/simulate", data=SIM)
        self.assertEqual(res.status_code, 200)
        params, analysis = run.call_args.args
        self.assertEqual(analysis, "dc")
        self.assertAlmostEqual(params["r1"], 100e3)
        self.assertAlmostEqual(params["cin"], 10e-6)
        self.assertAlmostEqual(params["amp"], 10e-3)
        self.assertAlmostEqual(params["freq"], 1000.0)
        text = res.get_data(as_text=True)
        self.assertIn("Run OK", text)
        self.assertIn("7.90", text)
        self.assertIn("1.28", text)

    def test_invalid_re_shows_error_without_stale_results(self):
        with patch.object(se, "run_analysis", side_effect=stub_run) as run:
            res = self.client.post("/simulate", data={**SIM, "re": "0"})
        self.assertEqual(res.status_code, 200)
        run.assert_not_called()
        text = res.get_data(as_text=True)
        self.assertIn('role="alert"', text)
        self.assertIn("RE ต้องมากกว่า 0", text)
        self.assertNotIn("Run OK", text)

    def test_engine_failure_shows_error_without_fake_success(self):
        failure = se.SpiceError("ไม่พบ ngspice บนเครื่องนี้", "detail")
        with patch.object(se, "engine_info", return_value=ENGINE), \
             patch.object(se, "run_analysis", side_effect=failure):
            res = self.client.post("/simulate", data=SIM)
        self.assertEqual(res.status_code, 200)
        text = res.get_data(as_text=True)
        self.assertIn('role="alert"', text)
        self.assertIn("ไม่พบ ngspice", text)
        self.assertNotIn("Run OK", text)

    def test_engine_error_is_visible_before_any_run(self):
        failure = se.SpiceNotFound("test")
        with patch.object(se, "engine_info", side_effect=failure):
            res = self.client.get("/simulator")
        text = res.get_data(as_text=True)
        self.assertIn("ไม่พบ ngspice", text)


if __name__ == "__main__":
    unittest.main()
