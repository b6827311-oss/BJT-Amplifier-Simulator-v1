# Submission — Lab 04 BJT Amplifier Simulator (ENG29 2121)

เอกสารนี้รวบรวม **ข้อมูลสำหรับการส่งงาน** ตาม Submission Checklist และ Rubric
ของใบงาน Lab 04 ทุกข้ออ้างอิงไฟล์ที่อยู่ใน repo นี้จริง

- **ชื่อ-นามสกุล:** _(เติมชื่อผู้จัดทำ)_
- **รหัสนักศึกษา:** _(เติมรหัส)_
- **วันที่รวบรวม:** 2026-11-24

---

## 1. ข้อมูลRepo และ Commit

| รายการ | ค่า |
|---|---|
| Repository | <https://github.com/b6827311-oss/BJT-Amplifier-Simulator-v1> |
| Branch | `main` |
| Lab 04 code commit | `46bc3d3f27a5bcc6148f97486d77999d1a6e90e8` (`46bc3d3`) |
| **Commit หลักฐาน Playwright MCP + เอกสารส่งงาน** | **`466ab192e0cedb02ddef4fb76dbcad25a99c3374` (`466ab19`)** — *docs: add Playwright MCP B1-B8 evidence and submission package* |
| สถานะ | commit + push แล้ว 2026-11-24 17:43 (origin/main = `466ab19`) |
| วิธีรัน | `.\setup.cmd` → `.\run.cmd` → <http://127.0.0.1:5000/simulator> |

> **SHA ที่ใช้ส่ง:** `466ab19` (เต็ม `466ab192e0cedb02ddef4fb76dbcad25a99c3374`)
> — เป็น commit ที่มีหลักฐาน B1–B8 จาก Playwright MCP, `docs/validation.md` §1.1,
> `docs/submission.md` และภาพ 10 ใบอยู่ในนั้นครบ
> ถ้ามี commit เอกสารเพิ่มหลังจากนี้ HEAD จะมากกว่านี้ แต่ SHA ที่อ้างหลักฐานยังใช้ค่านี้ได้

---

## 2. Submission Checklist

| # | สิ่งที่ใบงานขอ | สถานะ | หลักฐานใน repo |
|---|---|---|---|
| 1 | GitHub Repository URL + Commit SHA ของ Lab 4 | ✅ | §1 ด้านบน |
| 2 | Flask App ที่มี CE SPICE DC / AC / Transient และ DC Bias เดิมครบ 3 แบบ | ✅ | `app.py` (`/`, `/calculate`, `/simulator`, `/simulate`), `dc_bias.py`, `spice_engine.py` |
| 3 | `README.md` มีขั้นตอนติดตั้ง ngspice / Python dependencies, วิธีรัน Server และ Browser | ✅ | `README.md` §Quick Start (setup.cmd → run.cmd → URL), §Troubleshooting |
| 4 | `docs/validation.md` บันทึก B1–B8, วิธีตรวจ, ผลที่เห็นจริง, แหล่งอ้างอิง, ความคลาดเคลื่อน/ข้อจำกัด | ✅ | `docs/validation.md` §1 ตาราง B1–B8, §1.1 Playwright MCP run, §4 ข้อจำกัด |
| 5 | ภาพหน้าจอก่อน/หลัง UI + บันทึกการปรับด้วย Impeccable + Screenshot กราฟจาก Browser จริง | ✅ | `docs/screenshots/before/`, `after/`, `browser/`, `playwright/`, `docs/impeccable-*.json` |
| 6 | บันทึก 3–5 บรรทัด: AI สร้าง/แก้ส่วนใด และนักศึกษาตรวจอะไรเอง | ✅ | §6 ด้านล่าง และ `docs/reflection.md` §12 |

**ไม่ถูก track ใน Git (ถูกต้องตามกติกา):** `.venv/`, `wheels/`, `tools/ngspice/`,
`lab04-chat-session.json` (session log 9.6 MB), `dist/`, `portable/` — เก็บเป็น local artifact

---

## 3. Rubric 10 คะแนน → หลักฐาน

| เกณฑ์ | คะแนน | หลักฐาน |
|---|---:|---|
| ความต่อเนื่องจาก Lab 3 | 1 | Divider/Fixed/Emitter ยังทำงาน — B1 อ่านได้ `VCE 8.05 / 9.51 / 8.71 V` และ `IC 1.23 / 1.13 / 1.03 mA` ตรงค่าอ้างอิง; test เดิม 17 รายการยังผ่านในชุด 42 รายการ |
| การเชื่อม ngspice | 3 | `spice_engine.py` เป็น adapter แยกจาก Flask: `build_netlist()` + `subprocess.run([exe,"-b","-o",log,"-r",raw,circuit])` (ไม่ใช้ `shell=True`, มี timeout 20 s), `parse_raw()` อ่าน ASCII rawfile, `SpiceError` ครอบ engine หาย/timeout/exit≠0/raw ว่าง; B2 `.op` สำเร็จ + provenance netlist/log; B7 error state จริง |
| AC + Transient | 2 | B4: 194 จุด, `4.86 dB (1.75×)`, `fL 1.83 Hz`, `fH 153 MHz`, phase `−179.9° @1 kHz`; B5/B6: waveform 4008 จุด, เปลี่ยน source 10 mV/1 kHz → 20 mV/2 kHz แล้ว p-p และแกนเวลาเปลี่ยนจริง |
| UI และ Impeccable | 2 | `docs/impeccable-before-url.json` พบ `tiny-text`/`ai-color-palette`/`low-contrast`/`nested-cards` → หลังแก้ `docs/impeccable-after-desktop.json` และ `-mobile.json` = `[]`; ภาพ `before/` vs `after/`; แก้เฉพาะ `static/style.css` |
| Browser Acceptance | 1 | B1–B8 ตรวจด้วย **Playwright MCP** (`@playwright/mcp` + Chrome) เมื่อ 2026-11-24 — `docs/validation.md` §1.1 + ภาพ 10 ใบใน `docs/screenshots/playwright/` |
| GitHub + Reproducibility | 1 | Commit SHA, README Quick Start, `setup.ps1` ตรวจ SHA-256 ของ ngspice 47, unittest 42 รายการ, `docs/test-log-lab04.txt` |

---

## 4. คำตอบคำถามสั้นสำหรับตรวจรายบุคคล

### 4.1 โปรแกรม Python ส่งอะไรให้ ngspice และรับผลกลับมาอย่างไร?

1. `app.py` แปลงหน่วยฟอร์ม (kΩ/µF/mV) เป็น SI ที่ `_parse_simulation()` จุดเดียว
2. `spice_engine.build_netlist(params, analysis)` สร้าง netlist เป็นข้อความ
   พร้อม `.model QNPN NPN (IS=1e-14 BF=100 VAF=100 CJE=8p CJC=4p TF=0.3n)`
   ฝังในไฟล์ทุกครั้ง และเลือกคำสั่งวิเคราะห์ `.op` / `.ac dec 20 100m 500meg` / `.tran`
3. `run_analysis()` เขียน `circuit.cir` ใน temp directory ส่วนตัว แล้วเรียก
   `ngspice_con.exe -b -o run.log -r run.raw circuit.cir`
   ผ่าน `subprocess.run([...])` แบบ argument list (ไม่มี `shell=True`) พร้อม timeout 20 วินาที
4. ngspice โหมด batch เขียน **ASCII rawfile** (`run.raw`) และ log (`run.log`)
   Python อ่านทั้งสองไฟล์เอง: `parse_raw()` แยก `Variables:`/`Values:` เป็น
   series ของจำนวนจริง (tran/op) หรือจำนวนเชิงซ้อน (ac)
5. `summarize_dc/ac/tran` คำนวณค่าที่ใช้ตัดสิน (VCE, IC, gain, fL/fH, p-p)
   แล้วส่งกลับเป็น `SpiceRun` (netlist + log + plot + elapsed + raw size) ให้
   `app.py` render เป็น HTML/SVG — netlist และ log ถูกแสดงใน `<details>` เป็น provenance
6. ถ้า engine หาย, timeout, exit code ≠ 0 หรือ raw ว่าง → `SpiceError`
   → หน้าเว็บขึ้น `role="alert"` และไม่แสดงผล/กราฟค้าง; temp directory ถูกลบใน `finally`

### 4.2 เหตุใดกราฟ `.ac` และ `.tran` จึงไม่ใช่สิ่งเดียวกัน?

| | `.ac` | `.tran` |
|---|---|---|
| โดเมน | ความถี่ (frequency domain) | เวลา (time domain) |
| สมมติฐาน | small-signal **เชิงเส้น** รอบจุด bias | large-signal **ไม่เชิงเส้น** ตามเวลาจริง |
| แหล่งสัญญาณ | `AC 1` (1 V มาตรฐาน ไม่สนใจ amplitude ในฟอร์ม) | `SIN(0 10m 1k)` ตามค่า amplitude/frequency ที่กรอก |
| ข้อมูลดิบ | จำนวนเชิงซ้อนต่อความถี่ (194 จุด) | จำนวนจริงต่อเวลา (4008 จุด) |
| สิ่งที่วัด | Bode magnitude/phase, fL/fH ที่ −3 dB | p-p ของ Vin/Vout, ทิศทางเฟส, หน้าต่างเวลา |

ทั้งคู่ให้ "gain" ใกล้กัน (1.75×) แต่มาจากคนละการทดลอง: `.ac` บอกการตอบสนอง
ต่อความถี่ ส่วน `.tran` บอก waveform จริงบนแกนเวลา — ใช้แทนกันไม่ได้

### 4.3 ถ้าเปลี่ยน Amplitude แล้วกราฟไม่เปลี่ยน จะตรวจข้อมูลตรงไหนก่อน?

1. **Run Status** — มีการรันใหม่จริงหรือไม่ (`data points`, เวลารัน, `raw` size เปลี่ยนไหม)
2. **Netlist** ใน `<details>` — บรรทัด `VIN in 0 DC 0 AC 1 SIN(0 <ค่า> 1k)` อัปเดตหรือยัง
3. **ปุ่มที่กด** — ต้องกด **Run Transient** (`.tran`) หลังแก้ค่า; ถ้ากด Run AC กราฟจะไม่เปลี่ยนตาม amplitude โดยธรรมชาติ
4. **กราฟ/หน่วย** — trace มาจาก `result.charts` และแกนเป็น mV/ms ไม่ใช่ SVG คงที่
5. **`plots.py`** — ตรวจการ scale หน่วย (เคสที่เคยพลาดคือวาดเป็น V แทน mV) และช่วง p-p ที่ตัด 20% แรกออก

### 4.4 Impeccable เปลี่ยนอะไรได้ และไม่ควรเปลี่ยนอะไร?

- **เปลี่ยนได้ (UI/CSS เท่านั้น):** ขนาดตัวอักษร, contrast, `line-height`, การจัดวาง,
  เปลี่ยน side-border เป็น full border, ลด gradient ที่ดูเป็น AI, `text-wrap`,
  และเลิกซ้อนการ์ด (`.model-box`)
- **ไม่ควรเปลี่ยน:** สมการใน `dc_bias.py`, netlist/model card ใน `spice_engine.py`,
  ตัวอ่าน rawfile, ค่าอ้างอิง และผลการจำลอง — **ห้ามแก้ตัวเลขหรือการจำลองให้ "ดูดีขึ้น"**
- หลักฐาน: detector ก่อนแก้พบ 4 กลุ่มปัญหา → หลังแก้ได้ `[]` ทั้ง desktop/mobile
  และ unittest 42 รายการยังผ่าน (ไม่ได้แตะตรรกะ)

### 4.5 รู้ได้อย่างไรว่า Bode Plot เป็นผลจำลองจริง ไม่ใช่ Mock Data?

1. **Provenance ในหน้าผล** — netlist ที่ส่งเข้า engine + log จริง + path ของ `run.raw`
2. **จำนวนจุดตรงกัน** — log ระบุ `No. of Data Rows : 194` และ `polyline` ใน
   `svg.chart` มี **194 จุด** (นับด้วย `browser_evaluate` ผ่าน Playwright MCP)
3. **เปลี่ยน input แล้วผลเปลี่ยน** — B3 แก้ `RE` 1→2 kΩ: netlist เปลี่ยนเป็น
   `RE ve 0 2k` และ DC เปลี่ยนจาก `VCE 7.90` เป็น `9.06 V`
4. **Source เปลี่ยนแล้ว waveform เปลี่ยน** — B6: 10 mV/1 kHz → 20 mV/2 kHz
   ทำให้ p-p เป็น 40/70 mV และแกนเวลาเป็น 2–10 ms
5. **Phase ต่อเนื่อง** ~−10° ถึง −352° และ fL/fH มาจากการ interpolate จุด −3 dB
   ไม่ใช่เส้นตรง/ค่าคงที่ในโค้ด
6. **มี test ที่กันการปลอม** — `tests/test_app_simulator.py` จำลอง engine ล้มเหลว
   แล้วยืนยันว่าไม่มีกราฟ/ข้อความ success ปรากฏ

---

## 5. หลักฐาน Playwright MCP (Browser Acceptance)

- เครื่องมือ: `@playwright/mcp` ขับ Chrome จริง ผ่าน MCP tools ใน OpenCode
  (Navigate → Snapshot → Select/Fill → Click → Snapshot → Read Values → Screenshot)
- ผล: **B1–B8 ผ่านครบ 8 เคส** — ตารางค่าที่อ่านได้จริงอยู่ที่
  [`docs/validation.md`](validation.md) §1.1
- ภาพ: `docs/screenshots/playwright/`
  - `b1-regression-emitter.png` — Lab 03 regression (Emitter)
  - `b2-dc-re1.png` — `.op` ค่าเริ่มต้น
  - `b3-dc-re2.png` — เปลี่ยน `RE=2 kΩ`
  - `b4-ac.png` — Bode magnitude + phase
  - `b5-tran-10mv-1khz.png` — `.tran` 10 mV / 1 kHz
  - `b6-tran-20mv-2khz.png` — `.tran` 20 mV / 2 kHz
  - `b7-invalid-re.png` — error state (`RE = 0`)
  - `b8-desktop.png`, `b8-mobile-ac.png`, `b8-mobile-mode.png` — responsive
- Console: 0 error ของแอป (มีเฉพาะ `favicon.ico` 404 — log เก็บไว้ในโฟลเดอร์เดียวกัน)
- Network: request ไปที่ `127.0.0.1:5000` เท่านั้น — ไม่มี CDN/JavaScript ภายนอก
- วิธีติดตั้ง/เรียก tool ซ้ำ: [`docs/mcp-playwright.md`](mcp-playwright.md)

---

## 6. บันทึก 3–5 บรรทัด: AI ทำอะไร / นักศึกษาตรวจอะไร

AI เขียน `spice_engine.py`, `plots.py`, route `/simulator`–`/simulate`,
สคริปต์ `setup.ps1`/`run.ps1`/`make-portable.ps1` และร่างตาราง B1–B8 จากค่าที่รันจริง
AI ปรับ CSS ตาม Impeccable, เก็บภาพ before/after และตั้ง Playwright MCP เพื่อตรวจ B1–B8 ซ้ำ
นักศึกษาตรวจสมการ/หน่วย/warning ของ Lab 03, netlist และ model card, เทียบตัวเลข B1–B8
กับ ngspice log ด้วยตัวเอง และตอบคำถามข้อ 4.1–4.5 ก่อนส่ง

---

## 7. เช็กลิสต์ก่อนกดส่ง

- [ ] เติมชื่อ-นามสกุล และรหัสนักศึกษา ในเอกสารนี้และ `docs/reflection.md`
- [x] รัน `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` → `Ran 42 tests ... OK`
- [x] เปิด `http://127.0.0.1:5000/simulator` แล้วรัน `.op` / `.ac` / `.tran` อย่างละครั้ง
- [x] Commit + Push ผ่าน GitHub Desktop (ห้าม commit `.venv/`, session log, wheels) → `466ab19`
- [x] เอา SHA มาเติมใน §1 แล้ว (`466ab19`)
- [x] ตรวจว่า `docs/screenshots/playwright/` ถูก track (ภาพ PNG 10 ใบ) — อยู่ใน commit `466ab19`
