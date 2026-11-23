import unittest

from app import app

VALID = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


class TestWeb(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_get_form(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        text = res.get_data(as_text=True)
        for name in ["vcc", "r1", "r2", "rc", "re", "beta", "vbe"]:
            self.assertIn(f'name="{name}"', text)
        self.assertIn("Calculate DC Bias", text)

    def test_post_valid(self):
        res = self.client.post("/calculate", data=VALID)
        self.assertEqual(res.status_code, 200)
        text = res.get_data(as_text=True)
        self.assertIn("8.05", text)
        self.assertIn("1.23", text)
        self.assertIn("Active", text)
        self.assertIn("VCE = 8.05 V", text)

    def test_post_invalid_resistor(self):
        res = self.client.post("/calculate", data={**VALID, "r1": "0"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", res.get_data(as_text=True))

    def test_post_missing_field(self):
        data = dict(VALID)
        data.pop("vcc")
        res = self.client.post("/calculate", data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(
            "กรุณากรอกค่าตัวเลขให้ครบทุกช่อง",
            res.get_data(as_text=True),
        )

    def test_post_cutoff_warning(self):
        res = self.client.post("/calculate", data={**VALID, "r2": "5"})
        self.assertEqual(res.status_code, 200)
        text = res.get_data(as_text=True)
        self.assertIn("Cutoff", text)
        self.assertIn("VBE = 0.70 V", text)

    def test_post_saturation_warning(self):
        res = self.client.post("/calculate", data={**VALID, "rc": "10"})
        self.assertEqual(res.status_code, 200)
        text = res.get_data(as_text=True)
        self.assertIn("Near Saturation", text)
        self.assertIn("VCE = -1.54 V", text)

    def test_post_nan_rejected(self):
        res = self.client.post("/calculate", data={**VALID, "vcc": "nan"})
        self.assertEqual(res.status_code, 200)
        text = res.get_data(as_text=True)
        self.assertIn("จำนวนจำกัด", text)
        self.assertNotIn("results__table", text)


if __name__ == "__main__":
    unittest.main()
