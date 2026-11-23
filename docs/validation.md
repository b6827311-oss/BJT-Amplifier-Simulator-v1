# Validation — Lab 04 BJT Amplifier Simulator (ngspice)

บันทึกผลตรวจ **B1–B8 จากหน้าเว็บจริง** ตามใบงาน Lab 04
ส่วนของ Lab 02 อยู่ด้านล่าง (แยกหัวข้อชัดเจน)

- **วันที่ตรวจ:** 2026-11-23
- **Environment:** Windows, Python 3.15.2, Flask 3.1.3
- **Engine:** ngspice 47 (`ngspice-47`, `ngspice_con.exe` ที่
  `%LOCALAPPDATA%\ngspice\Spice64\bin\ngspice_con.exe`)
- **BJT model ในทุก netlist:**
  `.model QNPN NPN (IS=1e-14 BF=100 VAF=100 CJE=8p CJC=4p TF=0.3n)`
  — small-signal NPN ทั่วไปเพื่อการเรียน ไม่ใช่รุ่นการค้า
- **วิธีตรวจ browser:** เครื่องมือ **OpenCode `browse`** (ต่อกับ browser ของผู้ใช้)
  และ in-app browser ของ OpenCode ใช้จริงในการรัน Flask ที่
  `http://127.0.0.1:5000/` — **Playwright MCP ไม่พร้อมใช้งานใน session นี้**
  จึงบันทึกตามเครื่องมือที่ใช้จริง ไม่ได้อ้างว่าเป็นผล Playwright MCP
- **ชุดทดสอบ:** `python -m unittest discover -s tests -v` →
  `Ran 42 tests ... OK` (17 เดิม + 25 ใหม่) ดู `docs/test-log-lab04.txt`

### วงจรอ้างอิง (CE voltage-divider, ไม่มี emitter bypass capacitor)

| Parameter | ค่าที่กรอก | หน่วยใน netlist |
|---|---:|---|
| `VCC` | 12 | 12 V |
| `R1`, `R2` | 100, 22 | 100k, 22k Ω |
| `RC`, `RE` | 2.2, 1 | 2.2k, 1k Ω |
| `RL` | 10 | 10k Ω (หลัง `COUT`) |
| `Cin`, `Cout` | 10, 10 | 10u, 10u F |
| Source | 10 mV peak, 1 kHz | `SIN(0 10m 1k)`; `.ac` ใช้ `AC 1` |

### แหล่งอ้างอิงอิสระกับความต่างของสมมติฐาน

| ปริมาณ | คำนวณอิสระ Lab 03 (VBE=0.70 V, β=100) | ngspice `.op` | เหตุผลที่ต่าง |
|---|---:|---:|---|
| `IC` | 1.229858 mA | 1.278193 mA | ngspice ใช้ `IS`, `BF`, `VAF` และอุณหภูมิ 27 °C แทน `VBE` คงที่ |
| `VCE` | 8.052155 V | 7.899956 V | มี `RL` 10k ผ่าน `COUT` ในวงจรจำลอง |
| `VBE` | 0.70 V (กำหนด) | 0.659658 V | ผลจาก diode equation ของโมเดล |

ค่าอิสระมาจาก `docs/lab03-acceptance.md` / `Decimal` 50 หลัก **ไม่ได้อ่านจากโค้ดใหม่**
และไม่ได้นำมาแสดงแทนค่าจาก ngspice — UI แยก “Analytical reference” ออกจาก “SPICE result”

---

## 1. ตารางผล B1–B8

| Case | Method | Input | Expected / Reference | Observed (อ่านจริง) | Evidence | Status |
|---|---|---|---|---|---|---|
| **B1** Regression | browse + in-app browser: เปิด `/` เลือกโหมดแล้วกด Calculate ทีละโหมด | ชุดค่า Lab 03 (`VCC=12, RC=2.2k, β=100, VBE=0.70`; Divider `R1=100, R2=22, RE=1`; Fixed/Emitter `RB=1000`) | Divider `VCE=8.05 V, IC=1.23 mA`; Fixed `9.51 V, 1.13 mA`; Emitter `8.71 V, 1.03 mA` | Divider `VCE 8.05V / IC 1.23mA`; Fixed `9.51V / 1.13mA`; Emitter `8.71V / 1.03mA` — สลับโหมดได้ | browser snapshot 2026-11-23; [`docs/lab03-acceptance.md`](lab03-acceptance.md) A1–A3 | **PASS** |
| **B2** DC SPICE | `/simulator` → **Run DC (.op)** อ่าน metric + engine/model + `Netlist & ngspice log (provenance)` | ค่าอ้างอิงด้านบน | แสดง `VB/VE/VC/VCE/IC` จาก ngspice พร้อม Model และ Run Status | `VCE 7.90V · IC 1.28mA · VB 1.95V · VE 1.29V · VC 9.19V · VBE 0.660V · IB 11.9µA · IE 1.29mA`; engine `ngspice-47 พร้อมใช้งาน`; `Run OK — DC Operating Point (.op) · 1 data points · 33 ms · raw 1 KB`; log แสดง `ASCII raw file ... run.raw` | [`b2-dc-re1.jpeg`](screenshots/browser/b2-dc-re1.jpeg), netlist/log ในหน้าเว็บ | **PASS** |
| **B3** Change RE | เปลี่ยน `RE` เดียว 1 → 2 kΩ แล้ว Run DC ซ้ำ | `RE=2` (kΩ) | Operating point ต้องเปลี่ยน ไม่ใช่ค่าค้าง | `VCE 9.06V · IC 0.70mA · VB 2.05V · VE 1.40V · VC 10.47V · VBE 0.644V · IB 6.4µA · IE 0.70mA`; netlist เปลี่ยนเป็น `RE ve 0 2k` | [`b3-dc-re2.jpeg`](screenshots/browser/b3-dc-re2.jpeg) + บรรทัด netlist | **PASS** |
| **B4** AC | **Run AC (.ac)** อ่าน metric, แกนกราฟ, netlist/log | ค่าเดิม; `.ac dec 20 0.1 500meg` | Bode magnitude/phase มีหน่วยและค่าจาก run จริง | 194 points, 79 KB; `MIDBAND 4.86dB (1.75×)`; `fL 1.83Hz`; `fH 153MHz`; `@1kHz 4.86dB / −179.9°`; peak ที่ ~10.6 kHz; grid `100mHz … 100MHz`, dB และ degree; netlist `.ac dec 20 100m 500meg` | [`b4-ac.jpeg`](screenshots/browser/b4-ac.jpeg), `svg.chart` 2 เส้น 194 จุด | **PASS** |
| **B5** Transient | **Run Transient (.tran)** ที่ 10 mVpk / 1 kHz | `amp=10`, `freq=1000` | เห็น Vin/Vout ตามเวลา มีป้ายเวลา/แรงดัน และกลับเฟส | `VIN p-p 20.0mV · VOUT p-p 35.0mV · GAIN p-p 1.75× · กลับเฟส 180° (inverted)`; window `4.0–20.0 ms`; 4008 points, 839 KB; chart `Transient — Vin / Vout (mV) vs time (ms)` | [`b5-tran-10mv-1khz.jpeg`](screenshots/browser/b5-tran-10mv-1khz.jpeg) | **PASS** |
| **B6** Change Source | เปลี่ยน amplitude/frequency แล้ว Run ซ้ำ | `amp=20`, `freq=2000` | waveform/แกนเวลา/ค่า p-p ต้องเปลี่ยน | `VIN p-p 40.0mV · VOUT p-p 70.0mV · GAIN p-p 1.75×`; window `2.0–10.0 ms`; time ticks `0,2,4,6,8,10 ms` (เดิม `0,5,10,15,20 ms`); source `20 mVpk · 2000 Hz` | [`b6-tran-20mv-2khz.jpeg`](screenshots/browser/b6-tran-20mv-2khz.jpeg) | **PASS** |
| **B7** Invalid / Fail | กรอก `RE=0` แล้วกด Run DC; อีกกรณีใช้ unittest จำลอง engine error | `RE=0` | แจ้ง error, HTTP 200, ไม่ค้างผลเก่า/ไม่มี success ปลอม | `role="alert"` → **“RE ต้องมากกว่า 0”**; ไม่มี metric grid, ไม่มี chart, ไม่มี run-status; ค่าที่กรอกยังอยู่ในฟอร์ม; route test `test_engine_failure_shows_error_without_fake_success` ผ่าน | [`b7-invalid-re.jpeg`](screenshots/browser/b7-invalid-re.jpeg) + `tests/test_app_simulator.py` | **PASS** (engine-fail จริงแบบจำลองด้วย mock ใน unittest) |
| **B8** UI | browse: emulate `1280×900` และ `390×844`, เปิด `/simulator`, Run AC, สลับโหมด Lab 03 | desktop + mobile | กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่มีเนื้อหาสำคัญถูกตัด | Desktop `scrollWidth 1265 / innerWidth 1280`, ปุ่ม 3 ปุ่มกว้าง 278px; mobile `scrollWidth 390 / innerWidth 390`, ปุ่มกว้าง 320px; SVG chart scaled เหลือ 320px (viewBox เดิม 760px) ไม่ล้น; เปลี่ยนโหมด `fixed → emitter` บน mobile แสดง `#rb/#re` ถูกต้อง | [`b8-desktop.png`](screenshots/browser/b8-desktop.png), [`b8-mobile.png`](screenshots/browser/b8-mobile.png), [`b8-mobile-ac.png`](screenshots/browser/b8-mobile-ac.png), [`b8-mobile-mode.png`](screenshots/browser/b8-mobile-mode.png), [`b8-desktop-mode.png`](screenshots/browser/b8-desktop-mode.png) | **PASS** |

> หมายเหตุ B1–B7 บันทึกจาก in-app browser ส่วน B8 บันทึกจาก `browse` ที่ต่อกับ browser จริงของผู้ใช้
> ทั้งสองเป็น browser tool จริงที่รันได้ใน session นี้ และทุกค่าด้านบนมาจากหน้าเว็บ/ngspice log
> ไม่ใช่ค่าที่เดาไว้ล่วงหน้า

---

## 2. หลักฐานว่า Bode/Waveform ไม่ใช่ mock data

1. **Provenance ในทุกหน้าผลลัพธ์** — `<details>` ชื่อ *Netlist & ngspice log (provenance)*
   โชว์ netlist ที่ส่งเข้า engine และ log จาก ngspice รวม path ของ `run.raw`
2. **Netlist ถูกสร้างจากฟอร์ม** — ตัวอย่าง B3 แก้ `RE` → บรรทัด `RE ve 0 2k` เปลี่ยนจริง
3. **AC มี 194 จุด / raw 79 KB** และ phase ต่อเนื่องจาก ~−10° ไป −352°
   ไม่ใช่เส้นที่วาดจาก constant; fL/fH ได้จาก interpolation −3 dB เทียบยอด
4. **Transient มี 4008 จุด / raw 839 KB** — เปลี่ยน source 10 mV/1 kHz → 20 mV/2 kHz
   ทำให้ p-p และแกนเวลาเปลี่ยนตาม (B6) และ chart ใช้หน่วย mV ทั้งเส้นกราฟและแกน
5. **Engine error ไม่ปลอม success** — `tests/test_app_simulator.py` จำลอง engine ขัดข้อง
   แล้วตรวจว่าไม่มีตารางผล/กราฟ/status “Run OK” ปรากฏ

---

## 3. Design audit + Impeccable (UI เท่านั้น)

ก่อนปรับ (`docs/impeccable-before-url.json`) detector พบ:
`tiny-text` (`.mode-hint` 11.5px 3 จุด), `straggler`, `ai-color-palette`
(cyan gradient บนปุ่มที่เลือก), `low-contrast` (`small` บนปุ่ม 4.48:1 และ `.eyebrow` 3.8:1),
`nested-cards` (`.model-box`)

สิ่งที่แก้ **เฉพาะ CSS**:

- `.mode-hint`, `.note`, `.model-box__body` → 13–12.5px, `line-height 1.5`, `text-wrap: pretty`
- `.eyebrow` → `#d9ecf8` บน `#103658` (contrast ~10.2:1)
- `.button--run.is-current` / `.tag--accent` → พื้นหลังทึบ `#0b6f68` แทน cyan gradient,
  `small` → `#e6f5f3` (~5.4:1)
- `.model-box` เปลี่ยนจาก card ซ้อนเป็น section มีเส้นคั่นด้านบน
- `.mode-note`, `.note--strip`, `.placeholder` เปลี่ยน side-border เป็น full border / divider
- `.masthead h1` เพิ่ม `text-wrap: balance`

หลังปรับ: `docs/impeccable-after-desktop.json` = `[]` และ
`docs/impeccable-after-mobile.json` = `[]` ( detector ไม่พบ antipattern )
ภาพก่อน/หลังอยู่ใน `docs/screenshots/before/` และ `docs/screenshots/after/`

**ไม่มีการแตะสมการ netlist parser หรือค่าตัวเลขใด ๆ** — ทดสอบ 42 รายการผ่านหลังปรับ UI แล้ว

---

## 4. ความคลาดเคลื่อน ข้อจำกัด และสถานะที่ไม่ได้ตรวจ

- ค่า DC ของ SPICE ต่างจาก analytical ตามตารางด้านบน เพราะสมมติฐานคนละแบบ
  (ดูแลไม่ได้ “แก้ให้ตรง” โดยการ hardcode)
- `fH ≈ 153 MHz` เป็นขอบความถี่สูงของโมเดล/parasitic ภายในช่วง sweep
  ไม่ใช่ค่าที่คาดไว้จากการเดาเอง — รายงานตามผลจริง
- **B7 แบบ engine หายจริงยังไม่ได้ตรวจใน browser** เนื่องจาก ngspice พร้อมใช้งานตลอดการทดสอบ
  เส้นทางนี้ครอบคลุมด้วย unittest (`test_engine_error_is_visible_before_any_run`,
  `test_engine_failure_shows_error_without_fake_success`) จึงไม่ได้บันทึกเป็น browser PASS
- **Playwright MCP: NOT RUN** — ไม่มี tool ดังกล่าวใน session; ใช้ `browse` + in-app browser แทน
- ไม่มี resistor ของแหล่งสัญญาณ (source resistance = 0) และไม่มี emitter bypass cap
  ตามขอบเขตที่กำหนด

---

## 5. คำสั่งที่ใช้

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\setup.cmd        # ติดตั้ง venv + ngspice บนเครื่องใหม่ (Bypass ExecutionPolicy)
.\run.cmd          # รันเซิร์ฟเวอร์
```

---

# Validation — Lab 02 BJT DC Bias Web App

เอกสารนี้แสดงการตรวจสอบผลลัพธ์อย่างเป็นอิสระ (ไม่ได้ใช้โค้ดของเว็บ),
การเทียบกับผลจาก engine/tests, สถานะ warning และหลักฐาน acceptance A1–A7

- **วันที่ตรวจ:** 2026-11-10
- **Environment:** Windows, Python 3.15.2, Flask 3.1.3
- **ชุดทดสอบ:** `python -m unittest discover -s tests -v`

---

## 1. Independent Calculation

### อินพุตอ้างอิง (ค่าตัวอย่างในเอกสาร)

| พารามิเตอร์ | ค่า | หน่วย SI |
|---|---|---|
| `VCC` | 12 | 12 V |
| `R1` | 100 | 100 000 Ω |
| `R2` | 22 | 22 000 Ω |
| `RC` | 2.2 | 2 200 Ω |
| `RE` | 1 | 1 000 Ω |
| `β` | 100 | – |
| `VBE` | 0.70 | 0.70 V |

### สมการที่ใช้

```
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1) · RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

### ขั้นคำนวณ

```
VTH = 12 × 22 000 / (100 000 + 22 000)
    = 264 000 / 122 000
    = 2.163934426229508 V

RTH = 100 000 × 22 000 / 122 000
    = 2 200 000 000 / 122 000
    = 18 032.78688524590 Ω
    = 18.03278688524590 kΩ

IB  = (2.163934426229508 − 0.70) / (18 032.78688524590 + 101 × 1 000)
    = 1.463934426229508 / (18 032.78688524590 + 101 000)
    = 1.463934426229508 / 119 032.78688524590
    = 12.29858146260846 × 10⁻⁶ A
    = 12.29858146260846 µA

IC  = 100 × 12.29858146260846 × 10⁻⁶
    = 1.229858146260846 × 10⁻³ A
    = 1.229858146260846 mA

IE  = 101 × 12.29858146260846 × 10⁻⁶
    = 1.242156727723454 × 10⁻³ A
    = 1.242156727723454 mA

VE  = 1.242156727723454 × 1 000
    = 1.242156727723454 V

VB  = 1.242156727723454 + 0.70
    = 1.942156727723454 V

VC  = 12 − 1.229858146260846 × 10⁻³ × 2 200
    = 12 − 2.705687921773861
    = 9.294312078226139 V

VCE = 9.294312078226139 − 1.242156727723454
    = 8.052155350502685 V
```

---

## 2. Cross-check: Independent vs Engine vs UI

| ปริมาณ | คำนวณอิสระ | `dc_bias.py` (test) | แสดงบนเว็บ |
|---|---|---|---|
| `VTH` | 2.163934426 V | 2.163934426 V | 2.16 V |
| `RTH` | 18.032786885 kΩ | 18.032786885 kΩ | 18.03 kΩ |
| `IB` | 12.298581 µmA | 12.298581 µmA | 12.3 µA |
| `IC` | 1.229858146 mA | 1.229858146 mA | 1.23 mA |
| `IE` | 1.242156728 mA | 1.242156728 mA | 1.24 mA |
| `VE` | 1.242156728 V | 1.242156728 V | 1.24 V |
| `VB` | 1.942156728 V | 1.942156728 V | 1.94 V |
| `VC` | 9.294312078 V | 9.294312078 V | 9.29 V |
| `VCE` | 8.052155351 V | 8.052155351 V | 8.05 V |

ผลตรงกันถึงระดับที่ test กำหนด (`places=9` สำหรับแรงดัน, `places=12` สำหรับกระแส)

**หลักฐาน:**

- `tests/test_dc_bias.py::test_reference_operating_point`
- `tests/test_web.py::test_post_valid` (ตรวจข้อความ `8.05`, `1.23`, `Active`)

---

## 3. Warning Scenarios

### 3.1 Cutoff — `R2 = 5 kΩ`

```
VTH = 12 × 5 000 / 105 000 = 0.5714285714 V
VTH ≤ VBE (0.5714 ≤ 0.70)  →  warning "cutoff"

IB = (0.5714285714 − 0.70) / (4 761.9048 + 101 000)
   = −1.2156686177 × 10⁻⁶ A   (ติดลบ → ไม่มีความหมายทางกายภาพ)
IC = 100 × IB = −0.1215668618 mA
```

แบบจำลองยังคำนวณต่อได้ แต่ผลติดลบแสดงว่า Forward-Active approximation
ใช้ไม่ได้ → UI แสดง warning **Cutoff** และไม่รายงานสถานะ Active

**หลักฐาน:** `test_cutoff_warning`, `test_post_cutoff_warning`

### 3.2 Near Saturation — `RC = 10 kΩ`

```
IC  = 1.229858146 mA  (ค่าเดิม เพราะ RC ไม่มีผลกับ IB)
VC  = 12 − 1.229858146 × 10⁻³ × 10 000
    = −0.2985814626 V
VCE = −0.2985814626 − 1.2421567277
    = −1.5407381903 V
VCE < 0.2 V  →  warning "near_saturation"
```

`VCE` ติดลบแปลว่า transistor ไม่สามารถอยู่ใน forward-active ด้วย `RC` ค่านี้
→ UI แสดง warning **Near Saturation**

**หลักฐาน:** `test_saturation_warning`, `test_post_saturation_warning`

---

## 4. Automated Test Result

```
python -m unittest discover -s tests -v
Ran 17 tests in 0.091s
OK
```

- Engineering tests: 10 (`tests/test_dc_bias.py`)
- Flask client tests: 7 (`tests/test_web.py`)
- Log เต็ม: [`docs/test-log.txt`](test-log.txt)

### 4.1 Independent Cross-check (Decimal, 40 digits)

ตรวจ `calculate_dc_bias()` เทียบกับ implementation อิสระที่ใช้ `decimal.Decimal`
(ความละเอียด 40 หลัก) โดยไม่ใช้โค้ดชุดเดียวกัน:

| การตรวจ | ผล |
|---|---|
| ค่าอ้างอิง 9 ปริมาณ | relative error สูงสุด **1.79 × 10⁻¹⁶** |
| สุ่ม 5,000 ชุดอินพุต × 9 ค่า | คลาดเคลื่อน > 1e-9: **0 รายการ** |
| Warning/region logic 2,000 เคส | ไม่ตรงกัน: **0 รายการ** |

การตรวจนี้ยืนยันว่าสมการใน `dc_bias.py` ตรงกับสมการอ้างอิงในเอกสาร §06
และ warning ถูกตัดสินจากเงื่อนไขเดียวกัน

### 4.2 หมายเหตุเรื่องค่าตัวเลขในภาพตัวอย่าง

ภาพหน้าจอตัวอย่างในเอกสาร Lab 02 ระบุชัดว่าเป็น **“ค่าประกอบภาพ”
ไม่ใช่คำตอบอ้างอิงหรือผลการจำลองที่ตรวจสอบแล้ว** ตัวเลขในภาพ
(เช่น `VB = 2.20 V`, `VCE = 7.20 V`) มาจากการประมาณอย่างหยาบ
โดยถือ `IC ≈ IE ≈ (VTH − VBE)/RE` และปัด `VTH` เป็น 2.20 V
ซึ่ง **ละเลย `RTH` และ base-current loading**

เมื่อใช้สมการครบตามเอกสาร §06 (`IB` มี `RTH + (β+1)RE` ในตัวส่วน)
จะได้ `VCE = 8.05 V` ตามที่แสดงใน §1–§2 ของเอกสารนี้
แอปนี้จึงยึดสมการในเอกสาร ไม่ยึดตัวเลขในภาพ

---

## 5. Acceptance Checklist A1–A7

| # | เกณฑ์ | หลักฐาน | สถานะ |
|---|---|---|---|
| A1 | `GET /` ตอบ HTTP 200 และมีฟอร์ม 7 ช่อง | `test_get_form` + `docs/screenshot.png` | ผ่าน |
| A2 | `POST /calculate` คำนวณจริง ไม่ hardcode | `test_post_valid` + ตรวจ `app.py` เรียก `calculate_dc_bias()` | ผ่าน |
| A3 | `VB, VE, VC, VCE, IC` ตรงคำนวณอิสระ | §2 + `test_reference_operating_point` | ผ่าน |
| A4 | `R ≤ 0`, `β ≤ 0`, non-numeric, non-finite → error ชัดเจน | `test_rejects_*`, `test_post_invalid_resistor`, `test_post_missing_field`, `test_post_nan_rejected` + ตรวจบนเบราว์เซอร์ | ผ่าน |
| A5 | Cutoff / Saturation warning | §3 + `test_*_warning` และ web tests | ผ่าน |
| A6 | ≥ 3 engineering tests + ≥ 1 Flask test | 10 + 7 tests, `docs/test-log.txt` | ผ่าน |
| A7 | Clone/install/run/test ตาม README ได้ | ทดสอบคำสั่งใน README บนเครื่องนี้ (§6) | ผ่าน |

---

## 6. Manual Browser Checks (2026-11-10)

| การทดสอบ | ผล |
|---|---|
| เปิด `http://127.0.0.1:5000/` | HTTP 200, ฟอร์มแสดงค่า default ครบ 7 ช่อง |
| กด Calculate ด้วยค่า default | แสดง `VB 1.94 V`, `VE 1.24 V`, `VC 9.29 V`, `VCE 8.05 V`, `IB 12.3 µA`, `IC 1.23 mA`, `IE 1.24 mA`, สถานะ Active |
| เปลี่ยน `R2 = 5` แล้ว Calculate | แสดง warning Cutoff และสถานะ Cutoff |
| เปลี่ยน `R1 = 0` แล้ว Calculate | แสดง error “R1, R2, RC, RE ต้องมากกว่า 0”, HTTP 200 |
| ลบ `R1` แล้ว submit | แสดง error “กรุณากรอกค่าตัวเลขให้ครบทุกช่อง”, HTTP 200 |
| ส่ง `vcc=nan` ผ่าน HTTP | แสดง error “ค่าอินพุตต้องเป็นจำนวนจำกัด …”, HTTP 200, ไม่มีตารางผลลัพธ์ |
| ย่อหน้าต่าง/จอแคบ | layout stack เป็นคอลัมน์เดียวโดยไม่ล้น |

---

## 7. Reproducibility

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
python -m unittest discover -s tests -v
```

เวอร์ชันที่ใช้ตรวจ: Python 3.15.2, Flask 3.1.3 (ดู `requirements.txt`)

---

## 8. Notes and Assumptions

- `VCE < 0.2 V` เป็น **heuristic assumption** จากภาพตัวอย่างในเอกสาร
  ไม่ใช่ค่าที่เอกสาร Lab 02 กำหนด และไม่กระทบการคำนวณ
- อินพุตที่ไม่ใช่จำนวนจำกัด (`NaN`, `±Infinity`) และอินพุตที่ล้นจนคำนวณไม่ได้
  ถูกปฏิเสธด้วย `ValueError` เพื่อไม่ให้หน้าเว็บแสดง `nan` เป็นผลลัพธ์
- แบบจำลองไม่ clamp ค่ากระแส/แรงดันเมื่อออกนอก forward-active
  จึงอาจได้ค่าติดลบ ซึ่งเป็นสัญญาณให้ผู้ใช้เห็นว่าแบบจำลองใช้ไม่ได้
- ไม่ได้จำลอง Early effect, อุณหภูมิ, series resistance หรือ load
- ไม่ใช่ SPICE simulator และไม่มี AC/transient analysis

---

## 9. Submission Record

- **Repository:** <https://github.com/b6827311-oss/BJT_DC_Bias_Web_App.git>
- **Branch:** `main` (upstream `origin/main`)
- **Commit SHA (latest code commit):** `b7e5977db02c46794d7ca71ed896512822073d08` (`b7e5977`)
  — `fix: reject non-finite inputs and show region check`
- **Commit history:**

  | SHA | ข้อความ |
  |---|---|
  | `f3c9366` | `feat: add BJT DC bias Flask web app with tests and docs` |
  | `f28156e` | `docs: record final commit SHA and evidence` |
  | `b7e5977` | `fix: reject non-finite inputs and show region check` |

- **สถานะ:** Push ผ่าน GitHub Desktop เมื่อ 2026-11-10
- **Screenshot:** [`docs/screenshot.png`](screenshot.png)
- **Test log:** [`docs/test-log.txt`](test-log.txt)
- **หมายเหตุ:** ไฟล์ `docs/validation.md` นี้ถูกปรับปรุงหลัง `b7e5977`
  ใน commit เอกสาร (`docs: record latest commit SHA and cross-check`)
  โดยไม่มีการเปลี่ยนแปลงโค้ดหรือผลการทดสอบ

---

## 10. Lab 03 (2026-11-17)

Lab 03 เพิ่ม **Fixed Bias** และ **Emitter Bias** ในแอปเดิม
โดยผลของ Divider (A1) ยังตรงกับ §1–§2 ของเอกสารนี้ทุกค่า

> Lab 03 ส่งใน repository ใหม่:
> <https://github.com/b6827311-oss/-ENG29_2121_Lab03_BJT_Bias_Web_App>
> (ลิงก์ใน §9 เป็นหลักฐานของ Lab 02 ใน repository เดิม)

- ตาราง A1–A5, ค่าอ้างอิงอิสระ (Decimal 50 หลัก), วิธีตรวจผ่าน Browser
  และข้อจำกัดของ Playwright MCP: [`lab03-acceptance.md`](lab03-acceptance.md)
- Test log: [`test-log-lab03.txt`](test-log-lab03.txt) — `Ran 17 tests ... OK`
- ภาพหน้าจอ: [`lab03-fixed-bias.jpeg`](lab03-fixed-bias.jpeg),
  [`lab03-emitter-bias.jpeg`](lab03-emitter-bias.jpeg),
  [`lab03-input-error.jpeg`](lab03-input-error.jpeg)
