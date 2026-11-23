# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App หลายไฟล์ที่คำนวณ DC Operating Point ของ BJT NPN Common-Emitter Voltage-Divider Bias ตามสมการใน Lab 02 พร้อม validation, warning, tests, docs และหลักฐาน submission

**Architecture:** Server-rendered Flask single page; `dc_bias.py` เป็น pure engineering module (SI units) แยกจาก HTTP; `app.py` รับฟอร์ม แปลง kΩ→Ω เรียก engine แล้ว render `templates/index.html`; CSS 3-column responsive; ไม่ใช้ JavaScript

**Tech Stack:** Python 3.15.2, Flask, Jinja2, `unittest`, HTML/CSS (inline SVG), Git + GitHub Desktop

**Spec:** `docs/design-note.md`

---

## Global Constraints

- Python: `3.15.2`; Flask ติดตั้งใน `.venv` เท่านั้น
- รันเว็บ: `python -m flask --app app run --debug` ที่ `http://127.0.0.1:5000/`
- รัน tests: `python -m unittest discover -s tests -v`
- อินพุตฟอร์ม: `VCC` [V], `R1/R2/RC/RE` [kΩ], `β` [–], `VBE` [V]
- แปลง `kΩ → Ω` ก่อนเข้า `dc_bias.py`
- เอาต์พุต: `VB, VE, VC, VCE` [V], `IB` [µA], `IC` [mA], `IE` [mA]
- ค่าอ้างอิง: `VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70`
- Warning threshold: `VCE < 0.2 V` เป็น **heuristic assumption** จากภาพตัวอย่าง (เอกสารไม่ได้กำหนดเลขนี้)
- Validation: missing/non-numeric, `VCC≤0`, `R≤0`, `β≤0`, `VBE≤0` → HTTP 200 + inline error
- UI ภาษาไทย, ชื่อพารามิเตอร์อังกฤษ; ไม่ใช้ JavaScript; ไม่โหลด asset ภายนอก
- Commit/Push ผ่าน **GitHub Desktop เท่านั้น**; ห้าม `git commit` CLI
- ห้าม commit `.venv/`, `.env`, keys, credentials
- โครงสร้างไฟล์ต้องตรงตาม `docs/design-note.md §6`

---

## Review Focus

ห้าอินพุต/สภาวะที่เสี่ยงที่สุดและต้องมี test รองรับ:

1. **ช่องว่าง** — ผู้ใช้ไม่กรอกค่าบางช่อง → ต้องเห็น error “กรุณากรอกค่าตัวเลขให้ครบทุกช่อง” และ HTTP 200 ไม่ใช่ 500
2. **ไม่ใช่ตัวเลข** — กรอก `abc` → error เดียวกัน ไม่ crash
3. **ค่าศูนย์/ติดลบ** — `R=0`, `β=0`, `VCC=0`, `VBE=0` → error เฉพาะfield ไม่เกิด division by zero
4. **Cutoff** — `VTH ≤ VBE` → warning “Cutoff” และไม่รายงานว่า Active
5. **Near Saturation / VCE ติดลบ** — `VCE < 0.2 V` → warning “Near Saturation” และไม่รายงานว่า Active

---

## File Structure

| ไฟล์ | ความรับผิดชอบ |
|---|---|
| `.gitignore` | กัน `.venv/`, `__pycache__/`, `.env`, keys |
| `requirements.txt` | Flask (pin version หลังติดตั้ง) |
| `dc_bias.py` | pure calculation, validation, warnings; SI units |
| `app.py` | Flask routes, form parsing, kΩ→Ω, error mapping |
| `templates/index.html` | form + inline SVG + results/error/warning |
| `static/style.css` | 3-column responsive layout |
| `tests/test_dc_bias.py` | 8 engineering tests |
| `tests/test_web.py` | 6 Flask client tests |
| `README.md` | install/run/test/model/limitations |
| `AGENTS.md` | AI coding conventions |
| `docs/design-note.md` | approved design (มีแล้ว) |
| `docs/validation.md` | independent calc + test log + A1–A7 evidence |
| `docs/reflection.md` | reflection + individual questions |
| `docs/screenshot.png` | ภาพหน้าเว็บที่คำนวณสำเร็จ |
| `docs/test-log.txt` | output ของ unittest |

---

## Task 1: Engineering Core (`dc_bias.py`)

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `tests/test_dc_bias.py`
- Create: `dc_bias.py`

**Interfaces:**
- Produces: `calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict`
- Return keys: `vth, rth, ib, ic, ie, ve, vb, vc, vce` (float; SI units)
- `warnings`: `list[str]` — `"cutoff"`, `"near_saturation"`
- `region`: `"active" | "cutoff" | "near_saturation"`
- Raises `ValueError` for invalid engineering inputs

- [ ] **Step 1: Create `.gitignore`**

Content:
```gitignore
.venv/
__pycache__/
*.py[cod]
.env
.env.*
*.key
*.pem
.pytest_cache/
Thumbs.db
.DS_Store
```

- [ ] **Step 2: Create `.venv`, install Flask, pin version**

Run:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install Flask
python -m pip show Flask
```

เขียน `requirements.txt` ด้วยเวอร์ชันที่ติดตั้งจริง เช่น:
```
Flask==<version-from-pip-show>
```

- [ ] **Step 3: Write `tests/test_dc_bias.py` (failing tests first)**

```python
import unittest
from dc_bias import calculate_dc_bias

REF = dict(
    vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
    re=1_000.0, beta=100.0, vbe=0.70,
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
```

- [ ] **Step 4: Run tests and verify they fail**

Run:
```powershell
python -m unittest discover -s tests -p "test_dc_bias.py" -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 5: Implement `dc_bias.py`**

Signature:
```python
VCE_SAT_WARNING = 0.2  # V (heuristic)

def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict:
    ...
```

Requirements:
- Validate: `vcc > 0`, `r1/r2/rc/re > 0`, `beta > 0`, `vbe > 0`; raise `ValueError` with Thai messages:
  - `"VCC ต้องมากกว่า 0"`
  - `"R1, R2, RC, RE ต้องมากกว่า 0"`
  - `"β ต้องมากกว่า 0"`
  - `"VBE ต้องมากกว่า 0"`
- คำนวณตามสมการใน `docs/design-note.md §7.2` ทุกตัว
- `warnings = []`; ถ้า `vth <= vbe` เพิ่ม `"cutoff"`; ถ้า `vce < VCE_SAT_WARNING` เพิ่ม `"near_saturation"`
- `region = "cutoff"` ถ้ามี cutoff; else `"near_saturation"` ถ้ามี near_saturation; else `"active"`
- Return dict ตาม Interfaces; ไม่ import Flask/Jinja

- [ ] **Step 6: Run tests and verify they pass**

Run:
```powershell
python -m unittest discover -s tests -p "test_dc_bias.py" -v
```
Expected: PASS — 8 tests, 0 failures

- [ ] **Step 7: Commit ผ่าน GitHub Desktop**

เปิด GitHub Desktop → ตรวจ Changes → Commit message:
```
feat: add DC bias calculation engine
```
→ Push

---

## Task 2: Flask Route + Form + Web Tests

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `tests/test_web.py`

**Interfaces:**
- Consumes: `dc_bias.calculate_dc_bias(...)`
- Produces: Flask `app`; routes `GET /`, `POST /calculate`
- Template context: `values` (dict of str), `result` (dict | None), `error` (str | None), `warning_messages` (list[str])

- [ ] **Step 1: Write `tests/test_web.py` (failing tests first)**

```python
import unittest
from app import app

VALID = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.70",
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

    def test_post_invalid_resistor(self):
        res = self.client.post("/calculate", data={**VALID, "r1": "0"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", res.get_data(as_text=True))

    def test_post_missing_field(self):
        data = dict(VALID)
        data.pop("vcc")
        res = self.client.post("/calculate", data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn("กรุณากรอกค่าตัวเลขให้ครบทุกช่อง", res.get_data(as_text=True))

    def test_post_cutoff_warning(self):
        res = self.client.post("/calculate", data={**VALID, "r2": "5"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Cutoff", res.get_data(as_text=True))

    def test_post_saturation_warning(self):
        res = self.client.post("/calculate", data={**VALID, "rc": "10"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Near Saturation", res.get_data(as_text=True))
```

- [ ] **Step 2: Run tests and verify they fail**

Run:
```powershell
python -m unittest discover -s tests -p "test_web.py" -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Implement `app.py`**

Requirements:
- `app = Flask(__name__)`
- `DEFAULTS` = example values as strings: `12, 100, 22, 2.2, 1, 100, 0.70`
- `GET /` → `render_template("index.html", values=DEFAULTS, result=None, error=None, warning_messages=[])`
- `POST /calculate`:
  - อ่าน `request.form` ทั้ง 7 ชื่อ
  - ถ้า missing/`float()` ไม่ได้ → `error = "กรุณากรอกค่าตัวเลขให้ครบทุกช่อง"`
  - แปลง `r1/r2/rc/re` เป็น Ω (`×1000`)
  - เรียก `calculate_dc_bias(...)`; จับ `ValueError` → `error = str(exc)`
  - map warning codes:
    - `"cutoff"` → `"Cutoff: VTH ≤ VBE — Forward-Active approximation ใช้ไม่ได้"`
    - `"near_saturation"` → `"Near Saturation: VCE < 0.2 V — ผลอาจไม่แม่นยำ"`
  - render `index.html` ด้วย `values` (raw strings เพื่อคงค่า), `result`, `error`, `warning_messages`
- ไม่มี `app.run()` ที่ระดับ module; ใส่ใน `if __name__ == "__main__":` เท่านั้น

- [ ] **Step 4: Implement minimal `templates/index.html`**

Requirements:
- `<form method="post" action="{{ url_for('calculate') }}">`
- input names ตรง: `vcc, r1, r2, rc, re, beta, vbe`; มี label + หน่วย
- ปุ่ม `<button type="submit">Calculate DC Bias</button>`
- `{% if error %}` → `<div role="alert">{{ error }}</div>`
- `{% if result %}` → ตาราง:
  - `VB`, `VE`, `VC`, `VCE` → `"%.2f"|format(result.vb)` ฯลฯ + `V`
  - `IB` → `"%.1f"|format(result.ib * 1e6)` + `µA`
  - `IC` → `"%.2f"|format(result.ic * 1e3)` + `mA`
  - `IE` → `"%.2f"|format(result.ie * 1e3)` + `mA`
- `{% for msg in warning_messages %}` แสดง warning
- status: `Active` เมื่อ `result.region == "active"`; ไม่แสดง Active เมื่อมี warning
- ยังไม่ต้องทำ CSS/SVG เต็ม (Task 3)

- [ ] **Step 5: Run web tests and verify they pass**

Run:
```powershell
python -m unittest discover -s tests -p "test_web.py" -v
```
Expected: PASS — 6 tests, 0 failures

- [ ] **Step 6: Run all tests**

Run:
```powershell
python -m unittest discover -s tests -v
```
Expected: PASS — 14 tests, 0 failures

- [ ] **Step 7: Commit ผ่าน GitHub Desktop**

Commit message:
```
feat: add Flask route and DC bias form
```
→ Push

---

## Task 3: Responsive 3-Column UI + Circuit SVG

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`

**Interfaces:**
- ไม่เปลี่ยน route หรือ signature; ใช้ context เดิมจาก Task 2

- [ ] **Step 1: Add `static/style.css`**

Requirements:
- CSS variables: navy `#103658`, blue `#1d638b`, teal `#0c8078`, paper `#f5f8fc`, ink `#17344b`, line `#d3e0ec`
- `.layout { display:grid; grid-template-columns: 320px minmax(360px,1fr) 340px; gap:18px; }`
- `@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }`
- card style, form grid, results table, status box (green active / amber warning), error box (red)
- ปุ่มหลักสี teal/navy, hover state
- ไม่ใช้ `@import` หรือ external font

- [ ] **Step 2: Add inline SVG circuit**

Requirements:
- วางในคอลัมน์กลาง
- แสดง `VCC`, `R1`, `R2`, `RC`, `RE`, `Q1 NPN`, `β`
- ใช้ `currentColor`/CSS variables; ขนาด responsive (`viewBox`, `width:100%`)
- static ไม่มี interaction; ไม่ต้องเหมือนภาพตัวอย่างทุกพิกเซล
- ถ้าไม่ซับซ้อน ให้ใช้ label ค่าจาก `values` (เช่น `{{ values.r1 }} kΩ`) เพื่อให้ตรงกับฟอร์ม

- [ ] **Step 3: Update `templates/index.html` to 3-column layout**

Requirements:
- header: “Lab 02: BJT DC Bias Web App” + “ENG29 2121 — Common Emitter (Voltage Divider Bias)”
- 3 การ์ด: Input Parameters | Circuit | DC Bias Results
- error box อยู่ใต้ header หรือเหนือผลลัพธ์
- status box อยู่ใต้ตาราง
- คง `name=` และข้อความ “Calculate DC Bias” ตาม tests

- [ ] **Step 4: Run all tests**

Run:
```powershell
python -m unittest discover -s tests -v
```
Expected: PASS — 14 tests

- [ ] **Step 5: Manual browser verification**

Run:
```powershell
python -m flask --app app run --debug
```
เปิด `http://127.0.0.1:5000/` แล้วตรวจ:
- ค่า default แสดงครบ
- กด Calculate → เห็นผล + Active
- `R1=0` → error
- `R2=5` → Cutoff warning
- `RC=10` → Near Saturation warning
- ย่อหน้าต่าง < 900px → layout stack

- [ ] **Step 6: Capture screenshot**

บันทึกภาพหน้าเว็บที่คำนวณสำเร็จเป็น `docs/screenshot.png`

- [ ] **Step 7: Commit ผ่าน GitHub Desktop**

Commit message:
```
feat: add responsive three-column DC bias UI
```
→ Push

---

## Task 4: Documentation + Validation Evidence

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`
- Create: `docs/test-log.txt`

**Interfaces:**
- ใช้ผลจริงจาก Task 1–3; ไม่มี API ใหม่

- [ ] **Step 1: Capture test log**

Run:
```powershell
python -m unittest discover -s tests -v 2>&1 | Tee-Object -FilePath docs/test-log.txt
```
Expected: 14 tests, OK

- [ ] **Step 2: Write `README.md`**

ต้องมี:
- ชื่อโปรเจกต์ + ภาพรวม
- โครงสร้างไฟล์
- วิธีติดตั้ง:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  python -m pip install -r requirements.txt
  ```
- วิธีรัน:
  ```powershell
  python -m flask --app app run --debug
  ```
  เปิด `http://127.0.0.1:5000/`
- วิธีทดสอบ:
  ```powershell
  python -m unittest discover -s tests -v
  ```
- แบบจำลอง/สมการ, หน่วย, ค่าตัวอย่าง, warning/limitations
- ระบุชัดว่าไม่ใช่ ngspice และใช้ Forward-Active approximation
- ระบุ `VCE < 0.2 V` เป็น heuristic assumption

- [ ] **Step 3: Write `AGENTS.md`**

ต้องมี:
- แยก `dc_bias.py` จาก Flask/HTML
- SI units ใน engine; ฟอร์ม kΩ
- ห้ามเพิ่ม AC/Transient/SPICE/FET ใน Week 2
- รัน tests ก่อน commit
- commit ผ่าน GitHub Desktop
- ห้าม commit `.venv`/`.env`/keys

- [ ] **Step 4: Write `docs/validation.md`**

ต้องมี:
- ตารางคำนวณอิสระ (VTH, RTH, IB, IC, IE, VE, VB, VC, VCE) พร้อมสูตร
- ผลจากเว็บ/เทสต์เทียบค่าอ้างอิง
- ตาราง A1–A7 พร้อมหลักฐาน
- สรุป test log
- หมายเหตุ 0.2 V assumption

- [ ] **Step 5: Write `docs/reflection.md`**

ต้องมีคำตอบ 4 ข้อ:
1. ทำไมเปิด `templates/index.html` ตรง ๆ ไม่เท่ากับรัน Flask
2. ฟอร์มส่งข้อมูลไป Python อย่างไร
3. แก้สมการใน `dc_bias.py` ต้องแก้ HTML หรือไม่
4. ทำไม Region ที่แบบจำลองใช้ไม่ได้ต้องมี Warning

- [ ] **Step 6: Verify README commands**

รันคำสั่งติดตั้ง/รัน/ทดสอบตาม README ใน environment เดียวกัน และยืนยันว่าได้ผลตามที่เขียน

- [ ] **Step 7: Commit ผ่าน GitHub Desktop**

Commit message:
```
docs: add README, validation, and reflection
```
→ Push

---

## Task 5: Final Acceptance + GitHub Submission

**Files:**
- Modify: `docs/validation.md` (เพิ่ม commit SHA / หลักฐานสุดท้าย)

- [ ] **Step 1: Run full test suite fresh**

Run:
```powershell
python -m unittest discover -s tests -v
```
Expected: PASS — 14 tests, 0 failures

- [ ] **Step 2: Manual acceptance A1–A5**

รันเว็บและตรวจ:
- A1: `GET /` → 200 + form
- A2: POST valid → ผลจาก Python
- A3: ค่าตรง reference
- A4: `R1=0`, `β=0`, missing, `abc` → error
- A5: cutoff + saturation warning

- [ ] **Step 3: Pre-commit safety check**

Run:
```powershell
git status
git diff --stat
```
ตรวจ:
- ไม่มี `.venv/`, `.env`, keys
- ไฟล์ครบตาม file structure
- ไม่มี hardcoded results ใน template

- [ ] **Step 4: Commit/Push รอบสุดท้ายผ่าน GitHub Desktop**

เปิด GitHub Desktop → ตรวจ Changes ทั้งหมด → Commit:
```
chore: finalize Lab 02 submission
```
→ Push

- [ ] **Step 5: Record repository URL + commit SHA**

รัน:
```powershell
git remote get-url origin
git rev-parse HEAD
```
นำ URL + SHA ใส่ `docs/validation.md`

- [ ] **Step 6: Commit/Push การอัปเดตหลักฐานผ่าน GitHub Desktop**

Commit:
```
docs: record final commit SHA and evidence
```
→ Push

- [ ] **Step 7: Stop Flask server**

กด `Ctrl+C` ใน terminal ที่รัน Flask

---

## Self-Review

### Spec coverage

| Design section | Task |
|---|---|
| §6 Architecture / file responsibilities | Task 1–3 |
| §7 Engineering model / equations / units | Task 1 |
| §8 Validation | Task 1–2 |
| §9 UI/UX / 3-column / SVG | Task 3 |
| §10 Routes / data flow | Task 2 |
| §11 Testing strategy | Task 1–2 |
| §12 Documentation & evidence | Task 4–5 |
| §13 Git workflow | Task 1–5 (GitHub Desktop steps) |
| §15 Acceptance A1–A7 | Task 5 |
| §16 Risks | Global constraints + manual checks |

### Step scan
- ทุก step มี action + checkable result
- ไม่มี “TBD”, “handle edge cases”, หรือ “write tests for the above”
- Test steps มีชื่อ test + assertion + ค่าที่ต้องได้
- Code steps ระบุ signature/ไฟล์/ค่าคงที่; ไม่เขียน body แทน implementer

### Type consistency
- `calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe)` ใช้ชื่อเดียวกันใน Task 1, Task 2, tests
- Return keys `vth, rth, ib, ic, ie, ve, vb, vc, vce, warnings, region` ใช้ตรงกันใน template/tests
- Warning codes `cutoff`, `near_saturation` ใช้ตรงกันใน engine/app/tests

### Review Focus coverage
- Missing field → `test_post_missing_field`
- Non-numeric → same error path (เพิ่ม manual check `abc` ใน Task 5)
- Zero/negative → `test_rejects_*`, `test_post_invalid_resistor`
- Cutoff → `test_cutoff_warning`, `test_post_cutoff_warning`
- Near saturation → `test_saturation_warning`, `test_post_saturation_warning`

### Proportion
Plan เน้น interface, test assertions, ค่าคงที่ และ acceptance; ไม่ใช่ transcript ของ implementation ทั้งไฟล์
