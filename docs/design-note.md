# Lab 02 — BJT DC Bias Web App: Design Note

- **Course:** ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
- **Lab:** 02 — First DC Bias Web App
- **Status:** Approved — proceeding to implementation plan (2026-11-10)
- **Date:** 2026-11-10
- **Repository:** `BJT_DC_Bias_Web_App`
- **Scope:** Week 2 only — DC Bias, Voltage-Divider Bias, Common Emitter, NPN

---

## 1. Intent

สร้าง Flask Web Application หลายไฟล์ที่คำนวณ **DC Operating Point** ของวงจร BJT NPN Common-Emitter แบบ **Voltage-Divider Bias** ด้วย **Forward-Active Approximation** ตามสมการในเอกสาร Lab 02

ผู้ใช้กรอก `VCC, R1, R2, RC, RE, β, VBE` ผ่าน Browser แล้ว Python Backend คำนวณ `VB, VE, VC, VCE, IC` (พร้อม `IB/IE`) และส่งผลกลับมาแสดงพร้อมหน่วย, validation และ warning เมื่ออยู่นอกสมมติฐาน Forward-Active

เหตุผล: เป็นชิ้นงาน Week 2 ที่ต้องรันจริงผ่าน `http://127.0.0.1:5000/` มี tests และ commit ขึ้น GitHub ภายในคาบ เพื่อเป็นฐานของ Virtual Transistor Laboratory ในสัปดาห์ถัดไป

---

## 2. Goals / Definition of Done

- [ ] `GET /` ตอบ HTTP 200 และแสดงฟอร์ม 7 ค่า
- [ ] `POST /calculate` รับค่าจากฟอร์ม, เรียก Python คำนวณจริง และ render ผลในหน้าเดิม
- [ ] แสดง `VB, VE, VC, VCE` [V], `IC` [mA], `IB` [µA], `IE` [mA] พร้อมหน่วย
- [ ] Validation: missing/non-numeric, `VCC ≤ 0`, `R ≤ 0`, `β ≤ 0`, `VBE ≤ 0` → error ที่อ่านได้, HTTP 200, หน้าเว็บไม่ล้ม
- [ ] Warning: Cutoff (`VTH ≤ VBE`) และ Near Saturation (`VCE < 0.2 V`)
- [ ] Automated tests: อย่างน้อย 3 engineering tests + อย่างน้อย 1 Flask test client test
- [ ] README ที่ clone แล้วติดตั้ง/รันเว็บ/รัน tests ได้ตามคำสั่ง
- [ ] มี `docs/validation.md` พร้อมค่าคำนวณอิสระและ test log
- [ ] มี `docs/reflection.md` และคำตอบคำถามรายบุคคล
- [ ] มี screenshot หน้าจอที่คำนวณสำเร็จ + test log เป็นหลักฐาน submission
- [ ] Commit/Push ผ่าน GitHub Desktop เท่านั้น
- [ ] ไม่มี `.venv/`, `.env`, API keys หรือ credentials ใน commit

---

## 3. Non-goals / Anti-goals

**Non-goals (Week 2):**
- AC analysis, small-signal gain, Bode plot
- Transient analysis, signal generator, amplitude/frequency controls
- SPICE/ngspice integration หรือการสร้าง SPICE solver
- FET, circuit editor, interactive schematic
- Bias types อื่น (Fixed, Emitter, Collector feedback)
- ระบบ login, database, deployment สาธารณะ

**Anti-goals (ถือว่างานล้มเหลวแม้เว็บเปิดได้):**
- Hardcode ผลลัพธ์ใน HTML
- เปิด `templates/index.html` ด้วย `file://` แล้วอ้างว่ารัน Flask
- ฝังสมการฟิสิกส์ใน template แทน `dc_bias.py`
- ไม่มี warning เมื่อแบบจำลอง Forward-Active ใช้ไม่ได้
- อ้างว่า tests ผ่านโดยไม่ได้รันจริง
- Commit `.venv/`, `.env`, keys หรือ credentials

---

## 4. Constraints (จากเอกสาร Lab 02)

- Flask + Python, โครงสร้างหลายไฟล์
- `dc_bias.py` ต้องไม่รู้จัก HTML/HTTP
- `templates/index.html` แสดง Form/Results โดยไม่ฝังสมการ
- `static/style.css` ดูแลหน้าตา
- Tests ใช้ `unittest` และรันด้วย `python -m unittest discover -s tests -v`
- รันเว็บด้วย `python -m flask --app app run --debug` ที่ `http://127.0.0.1:5000/`
- Flask Debug Server ใช้เฉพาะเครื่องพัฒนา ไม่เปิดสู่เครือข่ายสาธารณะ
- ค่าตัวต้านทานในฟอร์มเป็น kΩ และต้องแปลงเป็น Ω ก่อนเข้าสมการ
- ต้องมีหน่วยกำกับทุกผลลัพธ์
- Commit ผ่าน GitHub Desktop ตามคำสั่งของผู้ใช้

### 4.1 Traceability to the Lab 02 Handout

| หัวข้อใน HTML | สิ่งที่ Design ครอบคลุม |
|---|---|
| 02 ติดตั้ง Git / OpenCode / Superpowers / Python | ตรวจแล้วใน preflight (ดูรายงานก่อนหน้า) |
| 03 Deliverable & Learning Outcomes | §1 Intent, §2 Goals |
| 04 Web App Architecture | §6 Architecture, §10 Data Flow |
| 05 Superpowers Workflow | §18 Approval + Plan ก่อน Execute |
| 06 Engineering Requirements | §7 Model, §8 Validation |
| 07 Lab Activities 180 นาที | ใช้เป็นลำดับงานใน Plan |
| 08 Prompt / Execute / Test | §11 Testing, §13 Git Workflow |
| 09 Acceptance Tests A1–A7 | §15 Acceptance Checklist |
| 10 Submission & Rubric | §12 Documentation & Evidence |
| 11 Next Labs | §3 Non-goals (กัน scope creep) |

---

## 5. Approaches Considered

### A. Server-rendered single page — **เลือก**
`GET /` แสดงฟอร์ม + วงจร + พื้นที่ผลลัพธ์; `POST /calculate` validate → คำนวณ → render `index.html` เดิมพร้อมผล/error/warning ไม่ใช้ JavaScript

**ข้อดี:** ตรงกับสถาปัตยกรรมในเอกสาร, ทดสอบด้วย Flask test client ง่าย, ไม่มี client-side state, เร็วที่สุดภายในคาบ

### B. JSON API + JavaScript fetch — **ตัดทิ้ง**
แยก `POST /api/calculate` แล้วให้ JS อัปเดต DOM
**เหตุผลที่ตัด:** เพิ่ม scope, ต้องทดสอบ client-side, เอกสารกำหนด server-rendered และไม่ได้ช่วยให้ผ่าน A1–A7 ง่ายขึ้น

### C. Two-page flow — **ตัดทิ้ง**
`GET /` ฟอร์ม, `POST /calculate` render `results.html` แยก
**เหตุผลที่ตัด:** เพิ่ม template/route โดยไม่จำเป็น และภาพเป้าหมายเป็นหน้าเดียว

### D. คำนวณใน `app.py` — **ตัดทิ้ง**
**เหตุผลที่ตัด:** ผิดหลักแยก Engineering Module, unit test ยาก, สมการปนกับ HTTP

**สรุป:** เลือก A เพราะเป็นทางเดียวที่ตรงทั้งสถาปัตยกรรม, เวลา, การทดสอบ และ acceptance criteria

---

## 6. Architecture

```
BJT_DC_Bias_Web_App/  (repo root)
├── app.py                  # Flask app, routes, form parsing, unit conversion, error mapping
├── dc_bias.py              # pure engineering calculations (SI units), validation, warnings
├── templates/
│   └── index.html          # form + inline SVG circuit + results/error/warning (Jinja)
├── static/
│   └── style.css           # responsive 3-column layout
├── tests/
│   ├── test_dc_bias.py     # engineering unit tests
│   └── test_web.py         # Flask HTTP tests
├── requirements.txt        # Flask (pin version after install)
├── README.md               # install/run/test/model/limitations
├── AGENTS.md               # AI coding conventions
└── docs/
    ├── design-note.md      # this document
    ├── validation.md       # independent calculation + test log + A1–A7 evidence
    ├── reflection.md       # reflection + individual questions
    ├── screenshot.png      # working page screenshot (submission evidence)
    └── test-log.txt        # captured unittest output (submission evidence)
```

**ความรับผิดชอบ:**
- `app.py` — HTTP GET/POST, `request.form`, แปลง kΩ→Ω, เรียก `dc_bias`, จับ `ValueError`, ส่งข้อมูลให้ template
- `dc_bias.py` — pure function, SI units (V, Ω, A), validate, คำนวณ, คืนผล + warning codes; ไม่ import Flask/Jinja
- `templates/index.html` — แสดงผลเท่านั้น; ไม่มีสมการฟิสิกส์
- `static/style.css` — layout/สี/typography; ไม่มี logic
- `tests/` — ตรวจทั้ง engineering math และ HTTP behavior

---

## 7. Engineering Model

### 7.1 วงจรและสมมติฐาน
NPN Common-Emitter, Voltage-Divider Bias:
- `R1` ต่อ `VCC`–Base
- `R2` ต่อ Base–Ground
- `RC` ต่อ `VCC`–Collector
- `RE` ต่อ Emitter–Ground
- ใช้ Forward-Active Approximation: `β` คงที่, `VBE` คงที่
- ไม่ใช่ ngspice และไม่ใช่แบบจำลองที่แม่นยำนอก Forward-Active

### 7.2 สมการ
```
VTH = VCC × R2 / (R1 + R2)
RTH = R1 × R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1) × RE)
IC  = β × IB
IE  = (β + 1) × IB
VE  = IE × RE
VB  = VE + VBE
VC  = VCC − IC × RC
VCE = VC − VE
```

### 7.3 หน่วย
- `VCC, VBE, VB, VE, VC, VCE` → V
- `R1, R2, RC, RE` → Ω ภายใน engine; ฟอร์มรับ kΩ แล้วแปลง `× 1000`
- `IB` → µA (แสดง), A (ภายใน)
- `IC, IE` → mA (แสดง), A (ภายใน)
- `β` → ไม่มีหน่วย

### 7.4 ค่าอ้างอิง (คำนวณจากสมการในเอกสาร)
ข้อมูลทดลอง: `VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V`

| ปริมาณ | ค่า |
|---|---:|
| VTH | 2.16393 V |
| RTH | 18.03279 kΩ (18,032.79 Ω) |
| IB | 12.2986 µA |
| IC | 1.22986 mA |
| IE | 1.24216 mA |
| VE | 1.24216 V |
| VB | 1.94216 V |
| VC | 9.29431 V |
| VCE | 8.05216 V |

> ค่าเหล่านี้คำนวณจากสมการในเอกสาร ไม่ใช้ตัวเลขจากภาพตัวอย่าง และจะใช้เป็น reference ใน tests

### 7.5 Warning conditions
- **Cutoff:** `VTH ≤ VBE` → โมเดลทำนาย `IB ≤ 0`; แจ้งว่า Forward-Active approximation ใช้ไม่ได้
- **Near Saturation:** `VCE < 0.2 V` → แจ้งว่า `VCE` ใกล้ saturation และ approximation อาจใช้ไม่ได้
- ถ้าเข้าเงื่อนไขทั้งสอง ให้แสดงทั้งสอง warning

**หมายเหตุสำคัญ:** ข้อความในเอกสาร Lab 06 ระบุเพียง “VCE ต่ำใกล้ saturation” ไม่ได้กำหนดเลข 0.2 V; เลข 0.2 V มาจากภาพตัวอย่างซึ่งเอกสารระบุว่าเป็นเพียง concept และตัวเลขในภาพไม่ใช่ค่าอ้างอิง จึงถือเป็น **heuristic assumption** ของ design นี้ เก็บเป็น constant ตัวเดียว (`VCE_SAT_WARNING = 0.2`) เพื่อให้อาจารย์เปลี่ยนได้หากกำหนดเกณฑ์อื่น

---

## 8. Validation

ตรวจใน `dc_bias.py` (engineering) และ `app.py` (form parsing):

| กรณี | ผลลัพธ์ |
|---|---|
| ช่องว่าง / ไม่ใช่ตัวเลข | Error: “กรุณากรอกค่าตัวเลขให้ครบทุกช่อง” |
| `VCC ≤ 0` | Error: “VCC ต้องมากกว่า 0” |
| `R1, R2, RC, RE ≤ 0` | Error: “R1, R2, RC, RE ต้องมากกว่า 0” |
| `β ≤ 0` | Error: “β ต้องมากกว่า 0” |
| `VBE ≤ 0` | Error: “VBE ต้องมากกว่า 0” (ส่วนขยายเล็กน้อยจากตัวอย่างในเอกสาร) |

**พฤติกรรม HTTP:**
- ทุกกรณี error ตอบ **HTTP 200** พร้อมฟอร์มและข้อความ error (ไม่ให้หน้าเว็บล้ม/500)
- คงค่าที่ผู้ใช้กรอกไว้ในฟอร์มเมื่อเกิด error
- ไม่คำนวณ/ไม่แสดงผลลัพธ์เมื่อ validation ไม่ผ่าน

---

## 9. UI / UX

### 9.1 Layout
Responsive 3-column บนจอกว้าง:
```
+----------------------+---------------------------+----------------------+
| Input Parameters     | Circuit                   | DC Bias Results      |
| VCC [V]     [12.0]   |   VCC ── R1 ── Base       | VB   1.94 V          |
| R1 [kΩ]     [100]    |          │                | VE   1.24 V          |
| R2 [kΩ]     [22]     |          Q1 NPN           | VC   9.29 V          |
| RC [kΩ]     [2.2]    |          │                | VCE  8.05 V          |
| RE [kΩ]     [1.0]    |   GND ── RE ── Emitter    | IB   12.3 µA         |
| β           [100]    |                           | IC   1.23 mA         |
| VBE [V]     [0.70]   |                           | IE   1.24 mA         |
| [Calculate DC Bias]  |                           | [Active region OK]   |
+----------------------+---------------------------+----------------------+
```
- จอ < 900 px: stack เป็นคอลัมน์เดียว (ฟอร์ม → วงจร → ผลลัพธ์)
- ใช้ CSS Grid; ไม่ใช้ framework ภายนอก
- สีหลักอิง palette ในเอกสาร: navy `#103658`, blue `#1d638b`, teal `#0c8078`, paper `#f5f8fc`
- ฟอนต์ system/Tahoma/Leelawadee UI; ไม่โหลดฟอนต์จากอินเทอร์เน็ต

### 9.2 Form
- 7 ช่อง: `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE`
- ป้ายภาษาไทย + สัญลักษณ์อังกฤษ; หน่วยกำกับชัดเจน
- ค่า default = ข้อมูลทดลองในเอกสาร เพื่อให้กด Calculate แล้วเห็นผลทันที
- ปุ่ม “Calculate DC Bias”
- `label for` ครบ, `inputmode="decimal"`, `step="any"`, `required`

### 9.3 Results
- ตาราง 7 แถว: `VB, VE, VC, VCE, IB, IC, IE`
- รูปแบบ: V = 2 ตำแหน่ง, mA = 2 ตำแหน่ง, µA = 1 ตำแหน่ง; คำนวณด้วยความละเอียดเต็มแล้วค่อย format ตอนแสดง
- Status box:
  - Active → เขียว “Active region approximation OK”
  - Warning → เหลือง/ส้ม พร้อมข้อความ warning
- Error box อยู่เหนือผลลัพธ์, `role="alert"`

### 9.4 Circuit
- Inline SVG แบบ static (ไม่ interactive)
- แสดง `VCC`, `R1`, `R2`, `RC`, `RE`, `Q1 NPN`, `β`
- ถ้าเป็นไปได้ แสดงค่าจากฟอร์มล่าสุดใน SVG; ถ้าไม่มีให้ใช้ค่า default
- ไม่ต้องเหมือนภาพตัวอย่างทุกพิกเซล

### 9.5 Language
- UI ภาษาไทยเป็นหลัก
- คงชื่อพารามิเตอร์สากล `VCC, R1, R2, RC, RE, β, VBE`
- ข้อความ error/warning ภาษาไทยที่อ่านเข้าใจได้

### 9.6 Minimum Demo (ตาม HTML หมวด 09)

1. เปิด `http://127.0.0.1:5000/` → เห็นฟอร์ม
2. กรอก/ใช้ค่า `VCC=12, R1=100, R2=22, RC=2.2, RE=1, β=100, VBE=0.70`
3. กด **Calculate DC Bias** → เห็น `VB, VE, VC, VCE, IB, IC, IE` พร้อมหน่วย
4. กรอกค่าผิด เช่น `R1=0` → เห็น error ชัดเจน หน้าเว็บไม่ล้ม
5. แสดง test log จาก `python -m unittest discover -s tests -v`
6. แสดง GitHub commit ล่าสุดที่ push แล้ว

---

## 10. Routes and Data Flow

| Route | Method | Behavior |
|---|---|---|
| `/` | GET | แสดงฟอร์มพร้อมค่า default, ยังไม่มีผลลัพธ์ |
| `/calculate` | POST | parse form → validate → แปลง kΩ→Ω → เรียก `calculate_dc_bias()` → render `index.html` พร้อมผล/error/warning |

**Data flow:**
```
Browser form
  → POST /calculate
  → app.py: request.form, parse floats, kΩ→Ω
  → dc_bias.calculate_dc_bias(...)
  → dict {vth, rth, ib, ic, ie, ve, vb, vc, vce, warnings, region}
  → render_template("index.html", ...)
  → HTML response
```

**Interface (design-level):**
```python
# dc_bias.py
def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict:
    """SI units: V, Ω, A. Raises ValueError for invalid inputs."""
```
- `warnings`: list of codes เช่น `["cutoff"]`, `["near_saturation"]`
- `region`: `"active" | "cutoff" | "near_saturation"`
- `app.py` map warning codes → ข้อความภาษาไทยใน template

---

## 11. Testing Strategy

### 11.1 Engineering tests — `tests/test_dc_bias.py`
1. `test_reference_operating_point` — ค่าอ้างอิง 7.4 ครบทุกค่า (tolerance `1e-6` หรือ `places=6`)
2. `test_rejects_zero_resistor` — `R1=0` → `ValueError`
3. `test_rejects_zero_beta` — `β=0` → `ValueError`
4. `test_rejects_zero_vcc` — `VCC=0` → `ValueError`
5. `test_rejects_non_positive_vbe` — `VBE=0` → `ValueError`
6. `test_cutoff_warning` — `R2=5 kΩ` → `VTH < VBE`, warning `cutoff`
7. `test_saturation_warning` — `RC=10 kΩ` → `VCE < 0.2 V`, warning `near_saturation`
8. `test_active_region_has_no_warning` — ข้อมูลอ้างอิง → ไม่มี warning, region `active`

### 11.2 Flask tests — `tests/test_web.py`
1. `test_get_form` — `GET /` → 200, มีช่อง `VCC`, `R1`, ..., ปุ่ม Calculate
2. `test_post_valid` — POST ข้อมูลอ้างอิง → 200, มี `8.05`, `1.23`, “Active”
3. `test_post_invalid_resistor` — `R1=0` → 200, มีข้อความ error, ไม่ 500
4. `test_post_missing_field` — ไม่ส่ง `VCC` → 200, มีข้อความ error
5. `test_post_cutoff_warning` — ข้อมูล cutoff → 200, มี warning
6. `test_post_saturation_warning` — ข้อมูล saturation → 200, มี warning

### 11.3 Commands
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
# อีก terminal จาก environment เดียวกัน
python -m unittest discover -s tests -v
```

> ถ้า `unittest discover` ไม่พบ tests ให้เพิ่ม `tests/__init__.py` (ว่าง) แล้วรันซ้ำ

---

## 12. Documentation and Submission Evidence

| ไฟล์ | เนื้อหา |
|---|---|
| `README.md` | ภาพรวม, โครงสร้าง, วิธีติดตั้ง/รัน/ทดสอบ, ตัวอย่าง input/output, สมมติฐานและข้อจำกัด |
| `AGENTS.md` | กติกา AI: แยก engineering logic, SI units, ห้ามเพิ่ม AC/SPICE, รัน tests ก่อน commit, commit ผ่าน GitHub Desktop |
| `docs/design-note.md` | เอกสารนี้ |
| `docs/validation.md` | คำนวณอิสระ, ตารางผล, test log, checklist A1–A7 |
| `docs/reflection.md` | Reflection + คำตอบคำถามรายบุคคล 4 ข้อ |
| `docs/screenshot.png` | ภาพหน้าเว็บที่คำนวณสำเร็จ |
| `docs/test-log.txt` | output ของ `python -m unittest discover -s tests -v` |

**คำถามรายบุคคลที่ต้องตอบ (ใน `docs/reflection.md`):**
1. เหตุใดการเปิด `templates/index.html` ตรง ๆ จึงไม่เท่ากับการรัน Flask?
2. ฟอร์มส่งข้อมูลไป Python อย่างไร?
3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่?
4. ทำไมผลใน Region ที่แบบจำลองใช้ไม่ได้จึงต้องมี Warning?

**Submission:** Repository URL + Commit SHA ผ่าน Moodle พร้อม screenshot, test log, README และ reflection

---

## 13. Git Workflow (GitHub Desktop only)

- ห้ามใช้ `git commit` ผ่าน CLI; ผู้ใช้เป็นผู้กด **Commit → Push** ใน GitHub Desktop
- AI เตรียมไฟล์, ตรวจ `git status` และ diff ให้ก่อน
- `.gitignore` ต้องมีก่อนสร้าง `.venv`:
  ```
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
- ตรวจก่อน commit ว่าไม่มี `.venv/`, `.env`, keys, credentials
- Commit messages ที่เสนอ:
  1. `docs: add approved Lab 02 design note`
  2. `feat: add DC bias calculation engine`
  3. `feat: add Flask UI for voltage-divider bias`
  4. `test: add engineering and Flask tests`
  5. `docs: add README, validation, and reflection`
  6. `chore: add submission evidence`

---

## 14. Decisions and Assumptions

| # | Decision | Reason | เปลี่ยนได้? |
|---|---|---|---|
| 1 | 3-column responsive layout | ตรง Design Target และเห็นฟอร์ม/วงจร/ผลพร้อมกัน | ได้ โดยไม่กระทบ logic |
| 2 | `POST /calculate` | แยก GET form กับ POST calculate ชัดเจน, test ง่าย | ได้ (เอกสารอนุญาต `POST /`) |
| 3 | ตัวต้านทานกรอกเป็น kΩ | ตรงภาพตัวอย่างและค่าทดลอง; แปลงเป็น Ω ใน `app.py` | ได้ |
| 4 | `VCE < 0.2 V` = near saturation | heuristic จากภาพตัวอย่าง; เอกสารไม่มีเลขนี้ | **ได้ — ควรยืนยันกับอาจารย์** |
| 5 | `VBE ≤ 0` เป็น error | ป้องกันค่าที่ทำให้แบบจำลองไร้ความหมาย | ได้ |
| 6 | ไม่ใช้ JavaScript | ลด scope และทดสอบง่าย | ได้ |
| 7 | UI ภาษาไทย + ชื่อพารามิเตอร์อังกฤษ | อ่านง่ายสำหรับนักศึกษาไทย | ได้ |
| 8 | ใช้ `unittest` + Flask test client | ตรงคำสั่งในเอกสาร | ไม่ควรเปลี่ยน |
| 9 | แสดง IB เป็น µA, IC/IE เป็น mA | ตรงภาพตัวอย่างและอ่านง่าย | ได้ |
| 10 | ไม่ทำ unit dropdown | ลด complexity; ใช้ kΩ/V fix | ได้ |

---

## 15. Acceptance Checklist (A1–A7)

| # | เกณฑ์ | หลักฐานที่จะมี |
|---|---|---|
| A1 | `GET /` HTTP 200 + form | `test_get_form` + screenshot |
| A2 | `POST /calculate` คำนวณจริง ไม่ hardcode | `test_post_valid` + code review |
| A3 | VB, VE, VC, VCE, IC ตรงคำนวณอิสระ | `test_reference_operating_point` + `docs/validation.md` |
| A4 | R≤0, β≤0, non-numeric → error ชัดเจน | unit/web tests + screenshot error |
| A5 | Cutoff/Saturation warning | unit/web tests + screenshot warning |
| A6 | ≥3 engineering + ≥1 Flask test | 10 + 7 tests, test log |
| A7 | Clone/install/run/test ตาม README | README + manual clean-run check |

---

## 16. Risks and Mitigations

| ความเสี่ยง | แนวทางลด |
|---|---|
| Flask เข้ากันไม่ได้กับ Python 3.15.2 | สร้าง `.venv` และติดตั้ง/flask import test เป็นขั้นแรกของ Execute; ถ้าติดปัญหา รายงานทันที |
| เวลา 3 ชั่วโมงไม่พอ | ทำ A1–A7 ก่อน; ตัด SVG detail/สีตกแต่งถ้าจำเป็น |
| CSS 3 คอลัมน์ใช้เวลานาน | ใช้ CSS Grid ง่าย ๆ + media query; ไม่ไล่ pixel-perfect |
| Test discovery ไม่พบ tests | รันคำสั่งเอกสาร; ถ้าไม่พบ เพิ่ม `tests/__init__.py` |
| 0.2 V ไม่ตรงเกณฑ์อาจารย์ | ระบุเป็น assumption + constant เดียว; เปลี่ยนได้ทันที |
| เผลอ commit `.venv`/secrets | `.gitignore` ก่อนสร้าง venv + ตรวจ diff ใน GitHub Desktop |
| GitHub Desktop commit พลาด | AI เตรียม/ตรวจ diff; ผู้ใช้กด Commit/Push |

---

## 17. What Is Left to the Builder

- กำหนดสี/ระยะห่าง/typography จริงใน `style.css` (อิง palette เอกสาร)
- วาด geometry ของ SVG วงจร (static, readable)
- กำหนด tolerance ของ tests และ format ทศนิยม
- ตรวจภาษาไทยของ error/warning ให้สั้น ชัด และตรงประเด็น
- ถ่าย screenshot และ capture test log ลง `docs/`
- ตรวจว่า README ทำตามได้จริงบนเครื่องนี้

---

## 18. Approval

Design นี้ได้รับ **อนุมัติจากผู้ใช้เมื่อ 2026-11-10** และเข้าสู่ขั้น Implementation Plan แล้ว

Implementation Plan อยู่ที่:
`docs/superpowers/plans/2026-11-10-bjt-dc-bias.md`

ลำดับถัดไป:
1. ผู้ใช้ตรวจ Plan และเลือกวิธี Execute (Native หรือ Subagent-driven)
2. Execute ตาม plan พร้อม tests/review
3. Commit/Push ผ่าน GitHub Desktop
4. เก็บหลักฐาน submission (screenshot, test log, commit SHA)

**ยังไม่มีการเขียนโค้ดหรือติดตั้ง Flask ในขั้นนี้**

---

## 19. Lab 03 Delta (2026-11-17)

ส่วนขยายจาก Lab 02 โดยไม่รื้อโครงเดิม:

| # | การตัดสินใจ | เหตุผล |
|---|---|---|
| 1 | เพิ่ม `calculate_fixed_bias()` และ `calculate_emitter_bias()` ใน `dc_bias.py` | คงหลัก “engineering logic ทดสอบได้โดยไม่ต้องมี Flask”; `calculate_dc_bias()` ไม่เปลี่ยนพฤติกรรม |
| 2 | ทุกโหมดคืน `dict` คีย์เดียวกัน (`mode, vth, rth, ib, ic, ie, ve, vb, vc, vce, warnings, region`) | ให้ `app.py`/template ใช้ร่วมกันได้; `vth`/`rth` เป็น `None` เมื่อไม่ใช่ Divider |
| 3 | ตาราง `MODES` ใน `app.py` เก็บฟิลด์, ตัวต้านทานที่ต้องแปลงหน่วย และฟังก์ชัน | เลือกฟังก์ชันด้วย `if`/lookup ตาม `mode`; unknown mode → error ไม่เดาเป็น Divider |
| 4 | ฟอร์มใช้ `<select name="mode">` + ปุ่ม “เปลี่ยนโหมด” (`formmethod="get"`) | เปลี่ยนโหมดแล้วโหลดฟอร์มใหม่ได้โดยไม่ใช้ JavaScript |
| 5 | Warning ใช้ `IB ≤ 0` (Cutoff) และ `VCE ≤ 0.2 V` (Near Saturation) ทุกโหมด | ตรงใบงาน Lab 03; สำหรับ Divider เทียบเท่า `VTH ≤ VBE` เดิม |
| 6 | ไม่เพิ่ม unittest; ตรวจ A1–A5 ผ่าน Browser | ตามใบงาน; tests เดิม 17 ตัวยังเป็น regression ของ Divider |
| 7 | ใช้ OpenCode Browser แทน Playwright MCP | เครื่องไม่มี Node.js/npx; ใบงานอนุญาตให้ใช้ Browser Tool และระบุวิธีจริง |

รายละเอียดผลตรวจ: [`docs/lab03-acceptance.md`](lab03-acceptance.md)

---

## 20. Lab 04 Delta (2026-11-23)

| # | การตัดสินใจ | เหตุผล |
|---|---|---|
| 1 | แยก `spice_engine.py` ออกจาก `app.py` | engineering/adapter test ได้โดยไม่ต้องมี Flask; ตอบคำถาม “Python ส่งอะไรให้ ngspice” ได้ชัด |
| 2 | ฝัง `.model QNPN ...` ไว้ในทุก netlist | netlist self-contained และ reproduce ได้; ไม่พึ่งพา `model.lib` ของเครื่อง |
| 3 | เรียก `ngspice_con.exe -b` แบบ argument list, `cwd` = temp ส่วนตัว, ไม่ใช้ `shell=True` | ปลอดภัยและแยกไฟล์ `run.raw`/`run.log` ของแต่ละรัน |
| 4 | อ่าน ASCII rawfile เอง + `.save all @q1[ic] @q1[ib] ...` | ได้ค่าจาก ngspice จริง ไม่ต้องพึ่งพา raw parser ของ package อื่น |
| 5 | แปลง kΩ/µF/mV → SI เฉพาะใน `_parse_simulation()` ของ `app.py` | คงกติกาเดิม: ขอบระบบเป็นที่เดียวที่แปลงหน่วย |
| 6 | `.ac dec 20 0.1 500meg` หา fL/fH จาก −3 dB เทียบยอด | ครอบ both coupling high-pass และ high-frequency shelf; ไม่เดาค่าจากสูตร |
| 7 | `.tran` รัน ~20 รอบ, ตัด 20% แรก, ใช้หน่วย mV/ms บนกราฟ | วัด steady-state p-p และทิศทางเฟสได้ตรงกับ waveforms |
| 8 | SVG ถูก generate บนเซิร์ฟเวอร์ (`plots.py`) ไม่มี JavaScript/CDN | ตรงกติกา UI เดิมและใช้จอแคบได้ |
| 9 | แยก “Analytical reference” กับ “SPICE result” | สมมติฐานต่างกัน (`VBE` คงที่ vs diode equation + `RL`) ต้องอธิบายไม่ใช่ซ่อน |
| 10 | `setup.ps1` + `.cmd` launcher, ตรวจ SHA-256 archive | เครื่องใหม่ติดตั้งได้โดยไม่เป็น admin และไม่ติด ExecutionPolicy |
| 11 | `make-portable.ps1` รวม wheels 3.10–3.13 + ngspice | ทำ USB offline bundle ได้จริง ไม่ต้องพึ่งอินเทอร์เน็ตตอนรัน |
| 12 | ปรับเฉพาะ CSS ตาม Impeccable แล้ว rerun 42 tests | พิสูจน์ว่า UI polish ไม่กระทบผลคำนวณ |

รายละเอียดผลตรวจและหลักฐาน: [`docs/validation.md`](validation.md) (B1–B8)
