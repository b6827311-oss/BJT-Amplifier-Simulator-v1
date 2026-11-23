import unittest

from dc_bias import calculate_dc_bias

REF = dict(
    vcc=12.0,
    r1=100_000.0,
    r2=22_000.0,
    rc=2_200.0,
    re=1_000.0,
    beta=100.0,
    vbe=0.70,
)


class TestDCBias(unittest.TestCase):
    def test_reference_operating_point(self):
        r = calculate_dc_bias(**REF)
        self.assertAlmostEqual(r["vth"], 2.163934426229508, places=9)
        self.assertAlmostEqual(r["rth"], 18032.7868852459, places=6)
        self.assertAlmostEqual(r["ib"], 12.298581462608456e-6, places=12)
        self.assertAlmostEqual(r["ic"], 1.2298581462608456e-3, places=12)
        self.assertAlmostEqual(r["ie"], 1.242156727723454e-3, places=12)
        self.assertAlmostEqual(r["ve"], 1.242156727723454, places=9)
        self.assertAlmostEqual(r["vb"], 1.942156727723454, places=9)
        self.assertAlmostEqual(r["vc"], 9.29431207822614, places=9)
        self.assertAlmostEqual(r["vce"], 8.052155350502686, places=9)
        self.assertEqual(r["warnings"], [])
        self.assertEqual(r["region"], "active")

    def test_rejects_zero_resistor(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**REF, "r1": 0.0})

    def test_rejects_zero_beta(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**REF, "beta": 0.0})

    def test_rejects_zero_vcc(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**REF, "vcc": 0.0})

    def test_rejects_non_positive_vbe(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**REF, "vbe": 0.0})

    def test_cutoff_warning(self):
        r = calculate_dc_bias(**{**REF, "r2": 5_000.0})
        self.assertIn("cutoff", r["warnings"])
        self.assertEqual(r["region"], "cutoff")

    def test_saturation_warning(self):
        r = calculate_dc_bias(**{**REF, "rc": 10_000.0})
        self.assertIn("near_saturation", r["warnings"])
        self.assertEqual(r["region"], "near_saturation")

    def test_active_region_has_no_warning(self):
        r = calculate_dc_bias(**REF)
        self.assertEqual(r["warnings"], [])
        self.assertEqual(r["region"], "active")

    def test_rejects_non_finite_input(self):
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            for bad in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(field=field, value=bad):
                    with self.assertRaises(ValueError):
                        calculate_dc_bias(**{**REF, field: bad})

    def test_rejects_overflowing_input(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**REF, "r1": 1e308, "r2": 1e308})


if __name__ == "__main__":
    unittest.main()
