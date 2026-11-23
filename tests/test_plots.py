import math
import unittest

import plots


class TestFormatFreq(unittest.TestCase):
    def test_sub_hertz_uses_plain_hz(self):
        self.assertEqual(plots.format_freq(0.1), "0.1 Hz")
        self.assertEqual(plots.format_freq(None), "—")

    def test_si_prefixes(self):
        self.assertEqual(plots.format_freq(1000), "1kHz")
        self.assertEqual(plots.format_freq(153e6), "153MHz")


class TestCharts(unittest.TestCase):
    def test_bode_charts_have_units_and_real_data_points(self):
        summary = {
            "freqs": [1.0, 10.0, 100.0, 1000.0],
            "gain_db": [0.0, 6.0, 6.0, 3.0],
            "phase_deg": [-90.0, -180.0, -180.0, -200.0],
            "fl": 3.1622776601683795,
            "fh": 100.0,
        }
        charts = plots.bode_svgs(summary)
        self.assertEqual(set(charts), {"magnitude", "phase"})
        for svg in charts.values():
            self.assertIn("<svg", svg)
            self.assertIn('class="trace"', svg)
            self.assertIn("Frequency (Hz, log scale)", svg)
        self.assertIn("Gain (dB)", charts["magnitude"])
        self.assertIn("Phase (°)", charts["phase"])
        self.assertIn("FL", charts["magnitude"])
        self.assertIn("FH", charts["magnitude"])

    def test_transient_chart_uses_millivolts_on_both_axes(self):
        times = [i * 0.001 for i in range(21)]
        summary = {
            "times": times,
            "vin": [0.01 * math.sin(2 * math.pi * 250 * t) for t in times],
            "vout": [-0.0175 * math.sin(2 * math.pi * 250 * t) for t in times],
        }
        svg = plots.transient_svg(summary)
        self.assertIn("Voltage (mV)", svg)
        self.assertIn("Time (ms)", svg)
        self.assertEqual(svg.count('class="trace"'), 2)
        self.assertIn("Vin", svg)
        self.assertIn("Vout", svg)
        # The 10 mV input must be plotted as a value near 10, not 0.01.
        self.assertIn('stroke="#0c8078"', svg)
        self.assertNotIn(",0.01", svg)

    def test_empty_data_returns_empty_chart(self):
        svg = plots.transient_svg({"times": [], "vin": [], "vout": []})
        self.assertIn("ไม่มีข้อมูล Transient", svg)
        self.assertNotIn('class="trace"', svg)


if __name__ == "__main__":
    unittest.main()
