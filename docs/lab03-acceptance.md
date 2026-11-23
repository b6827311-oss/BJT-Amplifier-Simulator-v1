# Lab 03 — Acceptance Record (A1–A5) และการตรวจผลผ่าน Browser

เอกสารนี้เป็นหลักฐานของ Lab 03: การเพิ่ม **Fixed Bias** และ **Emitter Bias**
ลงในเว็บ Flask เดิม โดยคงผลของ **Voltage Divider Bias** จาก Lab 02 ไว้

- **วันที่ตรวจ:** 2026-11-17
- **Repository (Lab 03):** <https://github.com/b6827311-oss/-ENG29_2121_Lab03_BJT_Bias_Web_App>
- **Commit ที่ตรวจ (Lab 03):** `eb8b6ab1751edce26be8fd02333a6023aa66db14`
- **Environment:** Windows, Python 3.15.2, Flask 3.1.3 (`requirements.txt`)
- **รันเว็บ:** `python -m flask --app app run` → <http://127.0.0.1:5000/>
- **วิธีตรวจ:** OpenCode Browser (in-app browser tools) — ดูหมายเหตุเรื่อง Playwright MCP ใน §5
- **ชุดทดสอบเดิม:** `python -m unittest discover -s tests -v` → `Ran 17 tests ... OK`
  ([`test-log-lab03.txt`](test-log-lab03.txt)) — ไม่มีการเพิ่ม/ลด unittest ตามใบงาน

---

## 1. ค่าอ้างอิงอิสระ (คำนวณมือ/Decimal ไม่ใช้โค้ดของเว็บ)

เงื่อนไขร่วมของ A1–A4: `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`, `VBE = 0.70 V`

สมการที่ใช้ (คัดลอกจากใบงาน Lab 03 §03 โดยตรง):

```text
Fixed   IB = (VCC − VBE) / RB
Emitter IB = (VCC − VBE) / [RB + (β + 1)·RE]
Divider IB = (VTH − VBE) / [RTH + (β + 1)·RE]
IC = β·IB          IE = (β + 1)·IB
VE = IE·RE (Fixed: VE = 0)
VB = VE + VBE      VC = VCC − IC·RC      VCE = VC − VE
```

คำนวณด้วย `decimal.Decimal` ความละเอียด 50 หลัก ในสคริปต์แยกที่ **ไม่ import
`dc_bias.py`** จากนั้นจึงเทียบกับผลที่เว็บแสดง

| กรณี | อินพุต | IB (µA) | IC (mA) | IE (mA) | VE (V) | VB (V) | VC (V) | VCE (V) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A1 Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 12.298581 | 1.229858 | 1.242157 | 1.242157 | 1.942157 | 9.294312 | 8.052155 |
| A2 Fixed | RB=1 MΩ (1000 kΩ) | 11.300000 | 1.130000 | 1.141300 | 0 | 0.700000 | 9.514000 | 9.514000 |
| A3 Emitter | RB=1 MΩ, RE=1 kΩ | 10.263397 | 1.026340 | 1.036603 | 1.036603 | 1.736603 | 9.742053 | 8.705450 |
| A4 Emitter | RB=1 MΩ, RE=2 kΩ | 9.400998 | 0.940100 | 0.949501 | 1.899002 | 2.599002 | 9.931780 | 8.032779 |

ขั้นคำนวณที่ตรวจด้วยมือ (ตัวอย่าง A4):

```text
IB  = (12 − 0.70) / [1 000 000 + 101 × 2 000]
    = 11.30 / 1 202 000
    = 9.400998 × 10⁻⁶ A
IC  = 100 × 9.400998 × 10⁻⁶ = 0.940100 mA
VE  = 101 × 9.400998 × 10⁻⁶ × 2 000 = 1.899002 V
VB  = 1.899002 + 0.70 = 2.599002 V
VC  = 12 − 0.940100 × 10⁻³ × 2 200 = 9.931780 V
VCE = 9.931780 − 1.899002 = 8.032779 V
```

---

## 2. ตาราง A1–A5 (ผลที่เห็นจริงจากหน้าเว็บ)

เกณฑ์เทียบ: `IC` ผลต่าง ≤ **0.01 mA**, `VCE` ผลต่าง ≤ **0.02 V**
เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษใน §1

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | เห็นจริงบนหน้าเว็บ | วิธีตรวจ | สถานะ |
|---|---|---|---|---|---|
| **A1** โหมดเดิม | Divider · R1=100, R2=22, RE=1 kΩ | เท่ากับ Lab 2: IC 1.2299 mA · VCE 8.0522 V | `VB 1.94 V · VE 1.24 V · VC 9.29 V · VCE 8.05 V · IB 12.3 µA · IC 1.23 mA · IE 1.24 mA` · Active | OpenCode Browser | **PASS** |
| **A2** Fixed | Fixed · RB=1000 kΩ (=1 MΩ) · ไม่กรอก RE | IC 1.1300 mA · VCE 9.5140 V | `VB 0.70 V · VE 0.00 V · VC 9.51 V · VCE 9.51 V · IB 11.3 µA · IC 1.13 mA · IE 1.14 mA` · Active | OpenCode Browser | **PASS** |
| **A3** Emitter | Emitter · RB=1000 kΩ · RE=1 kΩ | IC 1.0263 mA · VCE 8.7055 V | `VB 1.74 V · VE 1.04 V · VC 9.74 V · VCE 8.71 V · IB 10.3 µA · IC 1.03 mA · IE 1.04 mA` · Active | OpenCode Browser | **PASS** |
| **A4** เปลี่ยนค่าเดียว | Emitter · เหมือน A3 แต่ RE=2 kΩ | ทำนาย: **IC ลดลง** เพราะ RE ใหญ่ขึ้น → ตัวส่วน `RB+(β+1)RE` ใหญ่ขึ้น → IB และ IC ลดลง | `VB 2.60 V · VE 1.90 V · VC 9.93 V · VCE 8.03 V · IB 9.4 µA · IC 0.94 mA · IE 0.95 mA` (IC 1.03 → 0.94 mA) · Active | OpenCode Browser | **PASS** |
| **A5** อินพุตผิด | Fixed · RB=0 | มีข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่แสดงผลรอบก่อน | `RB, RC ต้องมากกว่า 0` · HTTP 200 · ไม่มีตารางผลลัพธ์ · placeholder “ยังไม่มีผลลัพธ์สำหรับรอบนี้” | OpenCode Browser | **PASS** |

หลักฐานภาพหน้าจอ:

- [`lab03-fixed-bias.jpeg`](lab03-fixed-bias.jpeg) — A2 (Fixed, RB=1 MΩ)
- [`lab03-emitter-bias.jpeg`](lab03-emitter-bias.jpeg) — A4 (Emitter, RE=2 kΩ)
- [`lab03-input-error.jpeg`](lab03-input-error.jpeg) — A5 (Fixed, RB=0)

> **หมายเหตุ A4:** ระหว่างตรวจพบว่ารอบแรกที่อ่านผลยังเป็นค่าของ A3
> เพราะหน้าเว็บยังไม่ได้ส่งฟอร์มรอบใหม่ ตัวเลขจึงไม่เปลี่ยน
> เมื่อรอให้ `VCE = 8.03 V` ปรากฏจริงแล้วจึงอ่านผลรอบใหม่
> ซึ่งตรงกับที่ใบงานเตือนเรื่อง “อย่าใช้ผลรอบก่อน” — วิธีไล่ข้อมูลอยู่ใน §6

---

## 3. สิ่งที่เปลี่ยนในโค้ด (Lab 03 Δ)

| ไฟล์ | สิ่งที่เพิ่ม/แก้ |
|---|---|
| `dc_bias.py` | เพิ่ม `calculate_fixed_bias()` และ `calculate_emitter_bias()`; แยก `_solve()` ให้ทั้งสามโหมดคืน `dict` คีย์เดียวกัน (`mode, vth, rth, ib, ic, ie, ve, vb, vc, vce, warnings, region`); คง `calculate_dc_bias()` และผลลัพธ์ Divider เดิม |
| `app.py` | ตาราง `MODES` เก็บฟิลด์/หน่วย/ฟังก์ชันของแต่ละโหมด; `_requested_mode()` ตรวจโหมด; `_parse_inputs()` แปลง kΩ→Ω **จุดเดียว**; `if/elif` ผ่าน `MODES[mode]["calculator"]`; unknown mode → error ไม่เดาเป็น Divider |
| `templates/index.html` | `<select name="mode">`, แสดงเฉพาะช่องของโหมด, ซ่อน VTH/RTH เมื่อไม่ใช่ Divider, ระบุโหมดในผลลัพธ์, แสดง error แทนผลรอบก่อน, SVG วงจรแยกตามโหมด |
| `static/style.css` | สไตล์ `select`, ป้ายโหมด, ปุ่มโหลดฟอร์มใหม่ |
| `tests/` | **ไม่แก้** — 17 tests เดิมผ่านทั้งหมด |
| `docs/` | เพิ่มเอกสารนี้, `test-log-lab03.txt`, ภาพหน้าจอ 3 ไฟล์ |

### 3.1 AI สร้างส่วนไหน และนักศึกษาตรวจอะไร

- **AI สร้าง:** ฟังก์ชัน Python ตามสมการในใบงาน, ตาราง `MODES`/dispatch ใน `app.py`,
  ฟอร์มเลือกโหมดและ SVG, เอกสารนี้
- **นักศึกษาตรวจ (ต้องทวนเอง):**
  1. สมการใน `dc_bias.py` ตรงกับ Engineering Electronics: ตัวส่วนของ Fixed ไม่มี `(β+1)RE`,
     Emitter/Divider มี, และ `VE = 0` เฉพาะ Fixed
  2. หน่วย: ฟอร์มเป็น kΩ → คูณ 1000 ครั้งเดียวใน `_parse_inputs()` → engine รับ Ω
     และคืนกระแสเป็น A (แสดงเป็น µA/mA ที่ template)
  3. Warning: `IB ≤ 0` → Cutoff, `VCE ≤ 0.2 V` → Near Saturation และไม่ clamp ค่า
  4. ตาราง A1–A5 ใน §2 ว่าผลจริงตรงกับค่าอ้างอิงอิสระ

### 3.2 เส้นทางข้อมูลของการเลือกฟังก์ชันและแปลงหน่วย

```text
ฟอร์ม (kΩ, V)  --POST /calculate-->  app.py
  request.form["mode"]  -> _requested_mode()  เลือก "divider" | "fixed" | "emitter"
  request.form[name]    -> _parse_inputs()    float() แล้ว ×1000 เฉพาะตัวต้านทาน
  MODES[mode]["calculator"](*args)            เรียกฟังก์ชันใน dc_bias.py
  -> dict (SI)  -> render_template("index.html") -> V / µA / mA
```

---

## 4. ตรวจโค้ดที่เปลี่ยน (review notes)

- `dc_bias.py` ไม่ import Flask/Jinja → ทดสอบแยกได้ (ตาม `AGENTS.md`)
- ไม่ hardcode ผลลัพธ์ใน HTML; ทุกค่ามาจาก `result`
- โหมดที่ไม่รู้จัก: `POST /calculate` ตอบ HTTP 200 พร้อมข้อความ
  “ไม่รู้จักโหมดวงจรที่เลือก …” และไม่คำนวณ
- ฟอร์มที่ไม่มีช่อง `mode` (แบบ Lab 02) ยังทำงานเป็น Divider เพื่อความเข้ากันได้
  แต่ถ้าส่งค่ามาที่ไม่รู้จักจะไม่ถูกเดาเป็น Divider
- เมื่อ error: `result=None` → ไม่มีตารางผลลัพธ์และไม่มีสถานะค้างจากรอบก่อน

---

## 5. MCP / Browser ที่ใช้จริง

**แนวคิด:** MCP (Model Context Protocol) เป็นมาตรฐานให้แอป AI รู้ว่ามีเครื่องมืออะไร
และเรียกใช้ได้อย่างไร ใน Lab นี้ OpenCode เป็น **MCP Client/Host** ส่วน
Playwright MCP เป็น **MCP Server** ที่เปิดเครื่องมือควบคุมเบราว์เซอร์
เบราว์เซอร์เป็นฝ่ายส่ง HTTP ไป Flask; ผลลัพธ์ไหลกลับมาเป็น snapshot ให้เอเจนต์อ่าน

```text
OpenCode --(MCP tool call)--> Playwright MCP Server --(ควบคุม)--> Browser
Browser --(HTTP GET/POST)--> Flask + Python --(HTML)--> Browser
Browser --(snapshot/ผลที่อ่านได้)--> MCP --> OpenCode --> เทียบกับตารางของนักศึกษา
```

**สิ่งที่ใช้ในรอบนี้:** OpenCode Browser (เครื่องมือ `browser_navigate`,
`browser_snapshot`, `browser_select`, `browser_fill`, `browser_click`,
`browser_screenshot`) ซึ่งเป็น Browser Tool ในตัว OpenCode Desktop

**Playwright MCP: NOT RUN** — เครื่องนี้ไม่มี `node`/`npx`
(`node --version` และ `npx --version` ตอบว่าไม่รู้จักคำสั่ง) จึงเริ่ม
`@playwright/mcp` ไม่ได้ ตามใบงาน §05 ให้บันทึกเป็น NOT RUN พร้อมเหตุผล
และใช้ Browser Tool ที่มีแทน โดยใช้ตาราง A1–A5 และเกณฑ์เดียวกัน

> ยังไม่ได้เพิ่ม `opencode.json` เพราะจะทำให้ MCP แสดงสถานะเชื่อมต่อไม่ได้บนเครื่องนี้
> หากติดตั้ง Node.js LTS แล้ว สามารถเพิ่มไฟล์ตามตัวอย่างในใบงาน (V1/V2 ตามรุ่น) ได้ทันที

---

## 6. คำถามปิด Lab: ถ้าเปลี่ยน RE แล้วผลบนเว็บไม่เปลี่ยน จะตรวจอย่างไร

ไล่จากต้นทางไปปลายทางทีละจุด โดยไม่แก้สมการก่อน:

1. **ฟอร์ม** — `<input name="re">` มีอยู่จริงและ `label for="re"` ตรงกับ `id`
   และช่องไม่ถูก `disabled`
2. **ค่าที่ส่งจริง** — เปิด DevTools → Network → คำขอ `POST /calculate`
   แล้วดู Form Data ว่า `re=2` (หรือค่าที่กรอก) ไม่ใช่ค่าก่อนหน้า
3. **ค่าที่ Flask รับ** — ใส่ log ชั่วคราวใน `app.py` พิมพ์ `request.form`
   และ `parsed` ก่อนเรียกฟังก์ชัน เพื่อยืนยันว่า `re` ถูกอ่านและคูณ 1000 แล้ว
4. **ฟังก์ชันที่ถูกเรียก** — ตรวจ `mode` ว่าเป็น `emitter` และ `MODES[mode]["calculator"]`
   คือ `calculate_emitter_bias` ไม่ใช่ฟังก์ชัน Divider/Fixed
5. **สมการ** — ตรวจว่า `calculate_emitter_bias` ใช้ `re` ในตัวส่วน
   `rb + (beta + 1) * re` และ `_solve(..., re, ...)` ส่งต่อไปคำนวณ `VE`
6. **การแสดงผล** — ตรวจว่า template อ่าน `result.*` รอบใหม่ (ไม่ใช่ HTML เก่า)
   และคำขอนั้นเกิดจริง (สถานะ 200 ของ `POST /calculate`)

ถ้าทั้ง 6 จุดถูกต้อง แต่ค่ายังไม่เปลี่ยน ให้สงสัยลำดับ argument ตอนเรียกฟังก์ชัน
หรือการ cache/รีเฟรชหน้าของเบราว์เซอร์เป็นลำดับถัดไป

---

## 7. วิธีทำซ้ำ

```powershell
cd BJT_DC_Bias_Web_App
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run
# เปิด http://127.0.0.1:5000/
# เลือกโหมด → กรอกค่า → Calculate DC Bias
python -m unittest discover -s tests -v
```
