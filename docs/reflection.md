# Reflection — Lab 02 BJT DC Bias Web App

- **ชื่อ-นามสกุล:** _(เติมชื่อผู้จัดทำ)_
- **รหัสนักศึกษา:** _(เติมรหัส)_
- **วันที่:** 2026-11-10

---

## 1. เหตุใดการเปิด `templates/index.html` ตรง ๆ จึงไม่เท่ากับการรัน Flask?

เพราะ `index.html` เป็น **template** ไม่ใช่หน้าเว็บสมบูรณ์
ในไฟล์มี syntax ของ Jinja2 เช่น `{{ url_for(...) }}`, `{% if result %}`,
`{{ "%.2f"|format(result.vb) }}`

- ถ้าเปิดด้วย `file://` เบราว์เซอร์จะไม่รู้จัก Jinja
  จึงเห็นข้อความ template ดิบ ๆ หรือเห็นเฉพาะส่วนที่อยู่นอก block
- `url_for('static', ...)` ต้องให้ Flask แปลงเป็น URL จริงของไฟล์ CSS
- ค่าผลลัพธ์ (`result`, `values`) ถูกส่งมาจาก Python ตอน render
  เปิดไฟล์ตรง ๆ จึงไม่มีข้อมูลเหล่านี้

การรัน Flask ทำให้เกิดขั้นตอน **request → Python คำนวณ → Jinja render → HTML สมบูรณ์**
จึงได้หน้าเว็บที่มี CSS, ค่าจากฟอร์ม และผลลัพธ์จริง

---

## 2. ฟอร์มส่งข้อมูลไป Python อย่างไร?

1. HTML ใช้ `<form method="post" action="/calculate">`
2. เมื่อกด **Calculate DC Bias** เบราว์เซอร์รวบรวมค่าจาก `<input name="...">`
   ทั้ง 7 ช่อง แล้วส่งเป็น body แบบ `application/x-www-form-urlencoded`
   ไปยัง route `POST /calculate`
3. ฝั่ง Flask อ่านค่าด้วย `request.form` ใน `app.py`
4. แปลงข้อความเป็น `float`, เปลี่ยน kΩ → Ω (`×1000`)
5. เรียก `calculate_dc_bias(...)` ใน `dc_bias.py`
6. นำผลลัพธ์ไป `render_template("index.html", ...)` แล้วส่ง HTML กลับมา

ไม่มี JavaScript ในขั้นตอนนี้ทั้งหมด — เป็นการทำงานฝั่งเซิร์ฟเวอร์ล้วน

---

## 3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่?

**โดยปกติไม่ต้อง** เพราะ template แยกจากสมการ:

- `dc_bias.py` คืนค่าเป็น dict เช่น `vb`, `vc`, `vce`
- `index.html` เพียงนำค่าเหล่านั้นไปแสดง

ถ้าแก้สูตรแต่ชื่อ key และหน่วยยังเหมือนเดิม → ไม่ต้องแก้ HTML

แต่ต้องแก้ HTML เมื่อ:

- เพิ่ม/ลบปริมาณที่ต้องแสดง (เช่น เพิ่ม `VTH`)
- เปลี่ยนหน่วยหรือจำนวนทศนิยมที่แสดง
- เปลี่ยนชื่อ key ที่ template อ้างอิง

นี่คือเหตุผลที่แยก engineering core ออกจาก UI:
แก้สมการแล้วยังทดสอบได้ด้วย `unittest` โดยไม่ต้องเปิดเบราว์เซอร์

---

## 4. ทำไมผลใน Region ที่แบบจำลองใช้ไม่ได้จึงต้องมี Warning?

เพราะสมการ Forward-Active ยัง **คำนวณต่อได้** แม้อยู่นอกขอบเขตที่ใช้ได้
ทำให้ได้ตัวเลขที่ดูเหมือนถูกต้อง แต่มีความหมายทางกายภาพผิด เช่น

- **Cutoff** (`VTH ≤ VBE`): ได้ `IB` และ `IC` ติดลบ
  ซึ่งเป็นไปไม่ได้ในวงจรจริง
- **Near Saturation** (`VCE < 0.2 V`): transistor ไม่อยู่ใน active
  สมมติฐาน `IC = β·IB` จึงไม่ใช้

ถ้าไม่มี warning ผู้ใช้อาจนำค่าติดลบหรือ `VCE` ต่ำผิดปกติไปใช้ต่อ
โดยเข้าใจว่าเป็นผลที่ถูกต้อง Warning จึงทำหน้าที่:

1. บอกขอบเขตความน่าเชื่อถือของแบบจำลอง
2. ชี้จุดที่ควรตรวจวงจรหรือเลือกค่าองค์ประกอบใหม่
3. แยก “ตัวเลขที่คำนวณได้” ออกจาก “ผลที่ใช้ได้จริง”

Warning ไม่ได้แก้ค่าที่คำนวณ แต่ป้องกันการตีความผิด ซึ่งสำคัญกว่าการได้ตัวเลขสวย ๆ

---

## 5. สิ่งที่ได้เรียนรู้เพิ่มเติม

- การแยก **pure function** (`dc_bias.py`) ออกจาก HTTP layer ทำให้เขียน test
  ได้เร็วและแม่นกว่า การทดสอบผ่านหน้าเว็บอย่างเดียว
- การแปลงหน่วยควรอยู่ที่ขอบระบบ (form → SI) จุดเดียว เพื่อลดโอกาสผิดพลาด
- การเขียน test ก่อนทำให้เห็นว่า error path (missing, `R=0`) ทำงานจริง
  ไม่ใช่แค่ “คิดว่าน่าจะทำงาน”
- Warning ที่ดีต้องบอกทั้ง **เงื่อนไข** และ **ผลกระทบ** ไม่ใช่แค่คำว่า error

## 6. ข้อจำกัดและสิ่งที่ควรพัฒนาต่อ

- ค่า `VCE < 0.2 V` เป็น heuristic ควรยืนยันกับอาจารย์
- ยังไม่จำลอง Early effect, อุณหภูมิ หรือ load
- ~~ยังไม่มี AC/transient analysis ตามขอบเขต Week 2~~ (ทำแล้วใน Lab 04)
- ~~ในสัปดาห์ถัดไปสามารถเพิ่มกราฟ DC load line หรือเชื่อมกับ SPICE ได้~~
  (เชื่อม ngspice แล้วใน Lab 04; DC load line ยังอยู่นอกขอบเขต)

---

# Lab 04 — BJT Amplifier Simulator (เพิ่ม)

- **วันที่:** 2026-11-23
- **Engine:** ngspice 47 · model `QNPN` (generic small-signal NPN)

## 7. Python ส่งอะไรให้ ngspice และรับผลกลับมาอย่างไร?

`spice_engine.build_netlist()` แปลงค่าจากฟอร์ม (SI แล้ว) เป็น netlist ข้อความ เช่น
`VIN in 0 DC 0 AC 1 SIN(0 10m 1k)`, `R1 vcc vb 100k`, `.ac dec 20 100m 500meg`
พร้อม `.model QNPN ...` ที่ฝังอยู่ในไฟล์ทุกครั้ง

จากนั้น `run_analysis()` เรียก `ngspice_con.exe -b <netlist>` แบบ argument list
(no `shell=True`) ใน temp directory ส่วนตัว ngspice เขียน `run.raw` (ASCII)
และ `run.log` — Python อ่าน `run.raw` เองแยก `Values:` ออกเป็นตัวเลขจริง
แล้วส่งสรุป (เช่น gain, fL/fH, VCE) ให้ `app.py` render เป็น HTML/SVG
ถ้า engine หายหรือ ngspice return error จะได้ `SpiceError` → แสดง `role="alert"`
แทนการแสดงผลเก่า

## 8. ทำไมกราฟ `.ac` กับ `.tran` จึงไม่ใช่สิ่งเดียวกัน?

`.ac` เป็น **frequency-domain small-signal** — ngspice ฉีด AC 1 V แล้วสแกน
0.1 Hz ถึง 500 MHz ได้เป็น amplitude/phase เทียบความถี่ (Bode)
ไม่ใช่สัญญาณเวลาจริงและไม่สนใจ amplitude ของ source (จึงใช้ 1 V มาตรฐาน)

`.tran` เป็น **time-domain large-signal** — ใช้ `SIN(0 10m 1k)` จริง รันตามเวลา
ประมาณ 20 รอบ แล้ววัด p-p ของ Vin/Vout และทิศทางเฟส
ข้อมูลดิบคนละอย่าง (complex vs real) คนละแกน และคนละคำถามทางวิศวกรรม

## 9. เปลี่ยน Amplitude แต่กราฟไม่เปลี่ยน จะตรวจตรงไหนก่อน?

1. ดู **Run Status** ว่ามีการรันใหม่จริงหรือไม่ (data points / time / raw size เปลี่ยนไหม)
2. ขยาย **Netlist & ngspice log** ดูบรรทัด `VIN ... SIN(0 <ค่า> ...)`
3. ตรวจฟอร์มว่ากดปุ่ม **Run Transient** หลังแก้ค่าหรือยัง
4. ตรวจ chart ว่ามี unit mV/ms และ trace มาจาก `result.charts` ไม่ใช่ SVG คงที่
5. ถ้ายังตรงอยู่ ดู `plots.py` ว่ามีการ scale ค่าผิดหรือไม่ (เคยเจอ bug หน่วย V แทน mV)

## 10. Impeccable เปลี่ยนอะไรได้ และไม่ควรเปลี่ยนอะไร?

เปลี่ยนได้เฉพาะ **UI/CSS**: ขนาดตัวอักษร, contrast, การจัดวาง, border แทน side-tab,
ลด gradient ที่ดูเหมือน AI, `text-wrap` และการซ้อนการ์ด
ไม่ควรเปลี่ยน smoke/math: สมการใน `dc_bias.py`, netlist ใน `spice_engine.py`,
parser ของ rawfile, ค่าอ้างอิง หรือการจำลองที่ผิดให้ “ดูดีขึ้น”
ในโปรเจกต์นี้แก้เฉพาะ `static/style.css` แล้ว detector ผ่าน `[]` ทั้ง desktop/mobile
พร้อมรัน unittest 42 รายการซ้ำเพื่อยืนยันว่าผลคำนวณไม่เสีย

## 11. รู้ได้อย่างไรว่า Bode Plot เป็นผลจำลองจริง ไม่ใช่ Mock Data?

- ในหน้าผลมี **provenance** โชว์ netlist ที่ส่งเข้า engine และ ngspice log จริง
  พร้อม path ของ `run.raw`
- log บอก `No. of Data Rows : 194` และ `raw 79 KB` ตรงกับจำนวนจุดใน `polyline`
- เปลี่ยน `RE` → ผล DC เปลี่ยนและบรรทัด `RE ve 0 2k` ใน netlist เปลี่ยนตาม
- เปลี่ยน amplitude/frequency → waveform และแกนเวลาเปลี่ยน (B6)
- phase ไหลต่อเนื่อง ~−10° ไป −352° และ fL/fH คำนวณจากการ interpolate −3 dB
  ไม่ใช่เส้นตรง/ค่าคงที่ที่เขียนไว้ในโค้ด
- มี unittest ที่จำลอง engine ล้มเหลวแล้วตรวจว่า **ไม่มี** กราฟ/ข้อความ success โผล่

## 12. สรุป 3–5 บรรทัด: AI ทำอะไร / นักศึกษาตรวจอะไร

AI เขียน `spice_engine.py`, `plots.py`, route `/simulator`–`/simulate`,
สคริปต์ `setup.ps1`/`run.ps1`/`make-portable.ps1` และร่างตาราง B1–B8 จากค่าที่รันจริง
AI ปรับ CSS ตาม Impeccable และเก็บ screenshot ก่อน/หลัง
นักศึกษาตรวจสมการ/หน่วย/warning ของ Lab 03, netlist และ model card,
เทียบตัวเลข B1–B8 กับ ngspice log ด้วยตัวเอง และตอบคำถามข้อ 7–11 ก่อนส่ง

