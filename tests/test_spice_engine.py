import math
import unittest

import spice_engine as se


BASE = dict(
    vcc=12.0,
    r1=100e3,
    r2=22e3,
    rc=2.2e3,
    re=1e3,
    rl=10e3,
    cin=10e-6,
    cout=10e-6,
    amp=10e-3,
    freq=1e3,
)


class TestNetlist(unittest.TestCase):
    def test_spice_number(self):
        cases = {
            0: "0",
            2200: "2.2k",
            10e-6: "10u",
            0.1: "100m",
            500e6: "500meg",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(se.spice_number(value), expected)

    def test_build_netlist_dc_contains_embedded_model_and_saved_currents(self):
        text, meta = se.build_netlist(BASE, "dc")
        self.assertIn(".op", text)
        self.assertIn("@q1[ic]", text)
        self.assertIn(se.MODEL_CARD, text)
        self.assertIn("RE ve 0 1k", text)
        self.assertIn("VIN in 0 DC 0 AC 1 SIN(0 10m 1k)", text)
        self.assertEqual(meta["analysis"], "dc")

    def test_build_netlist_ac_sweep_and_tran_window(self):
        ac, meta_ac = se.build_netlist(BASE, "ac")
        self.assertIn(".ac dec 20 100m 500meg", ac)
        self.assertEqual(meta_ac["ac_fstart"], 0.1)

        tran, meta_tran = se.build_netlist(BASE, "tran")
        self.assertIn(f".tran {se.spice_number(meta_tran['tstep'])} "
                      f"{se.spice_number(meta_tran['tstop'])}", tran)
        self.assertAlmostEqual(meta_tran["tstop"], 0.02)

    def test_transient_timing_is_clamped(self):
        for freq in (10.0, 1e6):
            tstep, tstop = se.transient_timing(freq)
            self.assertGreater(tstop, 0.0)
            self.assertLessEqual(tstop, 1.0)
            self.assertGreaterEqual(tstop, 0.005)
            self.assertAlmostEqual(tstep, tstop / 4000.0)

    def test_unknown_analysis_rejected(self):
        with self.assertRaises(ValueError):
            se.build_netlist(BASE, "bode")


class TestValidation(unittest.TestCase):
    def test_normalize_params_copies_and_accepts_base(self):
        result = se.normalize_params(BASE)
        self.assertEqual(result, BASE)
        self.assertIsNot(result, BASE)

    def test_normalize_params_rejects_bad_values(self):
        bad_cases = (
            {"re": 0.0},
            {"freq": 0.0},
            {"freq": 2e6},
            {"amp": 1.1},
            {"vcc": float("nan")},
            {"rc": float("inf")},
            {"r1": "abc"},
        )
        for change in bad_cases:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    se.normalize_params({**BASE, **change})


RAW = """Title: Lab 04 test
Plotname: AC Analysis
Flags: complex
No. Variables: 2
No. Points: 3
Variables:
\t0\tfrequency\tfrequency
\t1\tv(out)\tvoltage
Values:
0\t(1,0)\t(-1,0)
1\t(10,0)\t(-2,0)
2\t(100,0)\t(-1,0)
"""


class TestRawParsing(unittest.TestCase):
    def test_parse_raw_reads_complex_values_without_blank_line(self):
        plots = se.parse_raw(RAW)
        self.assertEqual(len(plots), 1)
        plot = plots[0]
        self.assertTrue(plot.is_complex)
        self.assertEqual(plot.plotname, "AC Analysis")
        self.assertEqual(plot.n_points, 3)
        self.assertEqual(plot.series("frequency"), [1 + 0j, 10 + 0j, 100 + 0j])
        self.assertEqual(plot.series("v(out)"), [-1 + 0j, -2 + 0j, -1 + 0j])
        self.assertTrue(plot.has("V(OUT)"))

    def test_series_missing_variable_raises(self):
        plot = se.parse_raw(RAW)[0]
        with self.assertRaises(KeyError):
            plot.series("v(in)")

    def test_empty_raw_rejected(self):
        with self.assertRaises(ValueError):
            se.parse_raw("not a raw file")


class TestSummaries(unittest.TestCase):
    def test_summarize_dc(self):
        plot = se.RawPlot(
            variables=[
                "v(vb)", "v(ve)", "v(vc)", "i(@q1[ic])", "i(@q1[ib])",
                "i(@q1[ie])", "v(@q1[vbe])",
            ],
            points=[[1.95, 1.29, 9.19, -1.278e-3, -11.9e-6, -1.29e-3, 0.66]],
        )
        dc = se.summarize_dc(plot)
        self.assertAlmostEqual(dc["vb"], 1.95)
        self.assertAlmostEqual(dc["vce"], 7.9)
        self.assertAlmostEqual(dc["ic"], 1.278e-3)
        self.assertAlmostEqual(dc["ib"], 11.9e-6)
        self.assertEqual(dc["region"], "active")

    def test_dc_region_boundaries(self):
        self.assertEqual(se._dc_region(7.9, 1e-6), "active")
        self.assertEqual(se._dc_region(0.5, 1e-6), "near_saturation")
        self.assertEqual(se._dc_region(0.1, 1e-6), "saturation")
        self.assertEqual(se._dc_region(7.9, 0.0), "cutoff")

    def test_summarize_ac_anchors_phase_and_finds_corners(self):
        freqs = [1.0, 10.0, 100.0]
        vin = [1 + 0j] * 3
        peak = 10 ** (6.0 / 20.0)  # exactly +6 dB
        vout = [-1 + 0j, -peak + 0j, -1 + 0j]
        plot = se.RawPlot(
            variables=["frequency", "v(in)", "v(out)"],
            points=list(zip(freqs, vin, vout)),
        )
        ac = se.summarize_ac(plot, 10.0)
        self.assertAlmostEqual(ac["max_gain_db"], 6.0)
        self.assertAlmostEqual(ac["max_gain_freq"], 10.0)
        self.assertAlmostEqual(ac["gain_at_ref_db"], 6.0)
        self.assertAlmostEqual(ac["phase_at_ref_deg"], -180.0)
        self.assertAlmostEqual(ac["fl"], math.sqrt(10), places=6)
        self.assertAlmostEqual(ac["fh"], 10 * math.sqrt(10), places=6)

    def test_summarize_tran_measures_inverted_gain(self):
        times = [i * 0.001 for i in range(21)]
        vin = [0.01 * math.sin(2 * math.pi * 250 * t) for t in times]
        vout = [-0.0175 * math.sin(2 * math.pi * 250 * t) for t in times]
        plot = se.RawPlot(
            variables=["time", "v(in)", "v(out)"],
            points=list(zip(times, vin, vout)),
        )
        tran = se.summarize_tran(plot, 250.0)
        self.assertAlmostEqual(tran["vin_pp"], 0.02, places=3)
        self.assertAlmostEqual(tran["gain_pp"], 1.75, places=3)
        self.assertTrue(tran["inverted"])
        self.assertIn("180°", tran["phase_text"])
        self.assertGreater(tran["time_window"][0], 0.0)

    def test_analytical_estimate_is_separate_from_spice_result(self):
        estimate = se.analytical_ac_estimate(
            BASE["vcc"], BASE["r1"], BASE["r2"], BASE["rc"],
            BASE["re"], BASE["rl"], 100.0, 0.70,
        )
        self.assertAlmostEqual(estimate["gain_linear"], 1.7665, places=3)
        self.assertAlmostEqual(estimate["dc"]["ic"], 1.229858e-3, places=9)


if __name__ == "__main__":
    unittest.main()
