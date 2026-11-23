# AGENTS.md — กติกาสำหรับ AI / Code Agents

ไฟล์นี้กำหนดกติกาเมื่อมี agent หรือนักพัฒนาเข้ามาแก้โปรเจกต์นี้
อ่านร่วมกับ `README.md` และ `docs/design-note.md`

> **อัปเดต Lab 04 (2026-11-23) — ให้ถือว่าส่วนที่ขัดกับ Lab 03 ด้านล่างนี้ถูกแทนที่:**
>
> - เป้าหมายตอนนี้คือ **Lab 04 BJT Amplifier Simulator** (ต่อยอด Lab 03)
>   โดยรัน **ngspice จริง** `.op` / `.ac` / `.tran` เท่านั้น
> - ห้าม hardcode ผลลัพธ์, gain, fL/fH หรือ waveform — ทุกค่าต้องมาจาก rawfile/log จริง
>   และต้องโชว์ provenance (netlist + log) ในหน้าเว็บ
> - เพิ่ม `spice_engine.py` (engineering adapter, ไม่ import Flask), `plots.py` (SVG ฝั่งเซิร์ฟเวอร์),
>   `run_app.py`, `setup.ps1`/`.cmd`, `run.ps1`/`.cmd`, `make-portable.ps1`/`.cmd`
> - Route ใหม่: `GET /simulator`, `POST /simulate`; `/` และ `/calculate` ของ Lab 03 คงเดิม
> - หน่วยฟอร์มใหม่: kΩ/µF/mV → SI แปลงที่ `_parse_simulation()` ใน `app.py` เท่านั้น
> - ต้องระบุ version ของ ngspice, model card และแยก SPICE result ออกจาก analytical reference เสมอ
> - UI ยังเป็น server-rendered ไม่มี JavaScript/CDN และต้องแยก error state ชัดเจน
>   (engine หาย/ngspice fail → `role="alert"`, HTTP 200, ไม่มีผลหรือกราฟปลอมค้าง)
> - **ชุดทดสอบปัจจุบันคือ 42 รายการ** (17 เดิม + 25 ใหม่) ต้องผ่านทั้งหมด
> - หลักฐาน browser คือตาราง **B1–B8 ใน `docs/validation.md`** +
>   screenshot ใน `docs/screenshots/`; ใช้ `browse`/in-app browser ที่รันได้จริง
>   (Playwright MCP ไม่มีใน session นี้ → ห้ามอ้างว่าใช้ Playwright MCP)
> - ปรับ UI ได้เฉพาะไฟล์ UI/CSS; ห้ามแก้สมการหรือ parser เพื่อให้ detector ผ่าน
> - **Commit/Push ผ่าน GitHub Desktop เท่านั้น** และต้องเป็น local clone ที่
>   `C:\Users\advic\Projects\BJT-Amplifier-Simulator-v1` (ไม่ใช่โฟลเดอร์ OneDrive)

## เป้าหมายของโปรเจกต์

Flask web app สำหรับคำนวณ DC operating point ของ
BJT NPN Common-Emitter สามแบบ — **Voltage Divider**, **Fixed** และ **Emitter Bias**
ตาม Lab 02–03 (ENG29 2121) ขอบเขต **DC Operating Point เท่านั้น**

## สถาปัตยกรรม

| ไฟล์ | หน้าที่ | กติกา |
|---|---|---|
| `dc_bias.py` | pure engineering core | ห้าม import Flask, Jinja, `request` หรือ HTML; รับ/คืน SI units; คง `calculate_dc_bias()` (Divider) และเพิ่ม `calculate_fixed_bias()` / `calculate_emitter_bias()` ที่คืน `dict` คีย์เดียวกัน |
| `app.py` | HTTP layer | จัดการ form, เลือกฟังก์ชันตาม `mode`, แปลง kΩ → Ω จุดเดียว, map warning code → ข้อความ, render template |
| `templates/index.html` | server-rendered UI | ห้ามใส่ผลลัพธ์ hardcode; ใช้ค่าจาก context เท่านั้น |
| `static/style.css` | layout | CSS ล้วน ไม่มี framework หรือ asset ภายนอก |
| `tests/` | automated tests | ทุก behavior ใหม่ต้องมี test |

หลักการ: **engineering logic ต้องทดสอบได้โดยไม่ต้องมี Flask**
ถ้าจะเพิ่มสมการ ให้เพิ่มใน `dc_bias.py` และเขียน test ที่ `tests/test_dc_bias.py`

## หน่วยและตัวเลข

- `dc_bias.py` ใช้ **SI units**: V และ Ω เท่านั้น
- ฟอร์มรับตัวต้านทานเป็น **kΩ**; การแปลงเป็น Ω ต้องอยู่ใน `app.py` เท่านั้น
- แสดงผล: V 2 ตำแหน่ง, mA 2 ตำแหน่ง, µA 1 ตำแหน่ง
- ค่าอ้างอิงสำหรับ regression (`VCC=12, RC=2.2k, β=100, VBE=0.70`):
  - Divider `R1=100k, R2=22k, RE=1k` → `VCE = 8.052155 V`, `IC = 1.229858 mA`
  - Fixed `RB=1M` → `VCE = 9.514000 V`, `IC = 1.130000 mA`
  - Emitter `RB=1M, RE=1k` → `VCE = 8.705450 V`, `IC = 1.026340 mA`
  - Emitter `RB=1M, RE=2k` → `VCE = 8.032779 V`, `IC = 0.940100 mA`
- ค่าอ้างอิงต้องคำนวณอิสระจากโค้ด (ดู `docs/lab03-acceptance.md`)

## Warning codes

คงชื่อรหัสเหล่านี้ไว้ เพราะ `app.py` และ tests อ้างอิง:

- `cutoff` — เมื่อ `IB ≤ 0` (โหมด Divider เทียบเท่า `VTH ≤ VBE`)
- `near_saturation` — เมื่อ `VCE ≤ 0.2 V` (`VCE_SAT_WARNING`)

`0.2 V` เป็น heuristic จากภาพตัวอย่างในเอกสาร ไม่ใช่ข้อกำหนดของ Lab
ถ้าจะเปลี่ยน ต้องอัปเดต `docs/design-note.md`, tests และ README พร้อมกัน

## UI

- Server-rendered, **ไม่ใช้ JavaScript**
- UI ภาษาไทยเป็นหลัก แต่คงชื่อพารามิเตอร์ `VCC`, `R1`, `R2`, `RB`, `RC`, `RE`, `β`, `VBE`
- 3 คอลัมน์บนจอกว้าง และ stack เมื่อจอแคบ
- Error ต้องมี `role="alert"` และตอบ HTTP 200 (ไม่ใช่ 500)
- ห้ามโหลดฟอนต์/สคริปต์จากอินเทอร์เน็ต
- ฟอร์มต้องแสดงเฉพาะช่องที่โหมดนั้นใช้ และต้องไม่มีผลของรอบก่อนค้างเมื่อ error

## Tests

รันก่อน commit ทุกครั้ง:

```powershell
python -m unittest discover -s tests -v
```

- ต้องได้ `Ran 17 tests ... OK` (หรือมากกว่าเมื่อเพิ่ม test)
- **Lab 03 ไม่เพิ่ม unittest** — ตรวจฟอร์ม/ผลผ่าน Browser ตามตาราง A1–A5
  ใน `docs/lab03-acceptance.md` และบันทึกวิธีที่ใช้จริง
- ห้ามลบ/ลด tolerance ของ test เพื่อให้ผ่าน
- test ใหม่ต้องเห็นสถานะ fail ก่อน แล้วจึง implement

## ขอบเขต

ทำได้แล้ว (Lab 02–03):

- Voltage Divider Bias, Fixed Bias, Emitter Bias (NPN Common-Emitter)
- Forward-Active approximation, validation รายโหมด, warning
- เลือกโหมดจากฟอร์มและตรวจผลผ่าน Browser

ห้ามเพิ่ม:

- AC analysis, transient, Bode plot
- signal generator / waveform viewer
- SPICE/ngspice integration
- FET หรือวงจร BJT แบบอื่นนอกเหนือจากสามแบบข้างต้น
- interactive schematic (ลากชิ้นส่วนได้)
- DC load line (อยู่ในสัปดาห์ถัดไป)

## Git

- **Commit/Push ผ่าน GitHub Desktop เท่านั้น** — ห้ามรัน `git commit` ใน CLI
- AI เตรียมไฟล์และตรวจ `git status` / diff ให้ผู้ใช้ก่อนกด commit
- ห้าม commit `.venv/`, `.env`, `.env.*`, `*.key`, `*.pem`, credentials
- ตรวจว่า `.gitignore` ครอบคลุมก่อนสร้าง venv

## Definition of Done

- [ ] `python -m unittest discover -s tests -v` ผ่านทั้งหมด (17 tests)
- [ ] เปิด `http://127.0.0.1:5000/` แล้วคำนวณค่าอ้างอิงได้ทั้งสามโหมด
- [ ] Divider ยังให้ผลเดิมเมื่อกรอกค่าเดิม
- [ ] error และ warning แสดงถูกต้อง ไม่ทำให้หน้าเว็บล้ม และไม่ค้างผลรอบก่อน
- [ ] ตาราง A1–A5 ใน `docs/lab03-acceptance.md` กรอกผลจริงพร้อมวิธีตรวจ
- [ ] README/validation/reflection เป็นปัจจุบัน
- [ ] ไม่มี secret หรือไฟล์ venv ถูก track
