# Playwright MCP setup (ใช้ตรวจ B1–B8)

บันทึกวิธีติดตั้ง/เรียก **Playwright MCP** ที่ใช้ตรวจ B1–B8 ใน `docs/validation.md` §1.1
เมื่อ 2026-11-24 — เป็น tooling ของเครื่องที่ใช้ตรวจ **ไม่ใช่ส่วนของแอป**
จึงไม่ผูกกับ `requirements.txt` และไม่ถูก track ใน Git

## สิ่งที่ใช้

| องค์ประกอบ | ค่า |
|---|---|
| MCP server | `@playwright/mcp` (npm) |
| Browser | Chrome ที่ติดตั้งในเครื่อง (`--browser chrome`) |
| Node.js | portable zip `node-v26.13.1-win-x64` ที่ `%LOCALAPPDATA%\nodejs` |
| Client | OpenCode (MCP tools `playwright_browser_*`) |

## ขั้นตอน

1. ติดตั้ง Node.js (ไม่ต้อง admin) — แตก zip ไปที่ `%LOCALAPPDATA%\nodejs`
2. ติดตั้ง MCP server แบบ local (ไม่ใช้ `npx` ตอนรัน เพื่อให้ path คงที่)

   ```powershell
   npm install --prefix "$env:LOCALAPPDATA\opencode\playwright-mcp" @playwright/mcp
   ```

3. ประกาศ server ใน `opencode.json` ที่ workspace root (นอก repo)

   ```jsonc
   {
     "$schema": "https://opencode.ai/config.json",
     "mcp": {
       "servers": {
         "playwright": {
           "type": "local",
           "command": [
             "C:\\Users\\<user>\\AppData\\Local\\nodejs\\node.exe",
             "C:\\Users\\<user>\\AppData\\Local\\opencode\\playwright-mcp\\node_modules\\@playwright\\mcp\\cli.js",
             "--browser", "chrome",
             "--output-dir", "<repo>\\docs\\screenshots\\playwright"
           ],
           "cwd": "<repo>"
         }
       }
     }
   }
   ```

   OpenCode โหลด config ใหม่เองเมื่อไฟล์ถูกบันทึก (ไม่ต้อง restart)
   ตรวจว่าเชื่อมต่อได้ด้วย `opencode mcp list` หรือ `/mcps`

4. เปิด Flask ก่อนตรวจ

   ```powershell
   .\run.cmd
   ```

5. ตรวจทีละเคสด้วยลำดับเดียวกับใบงาน:
   **Navigate → Snapshot → Select/Fill → Click → Snapshot → Read Values → Compare → Screenshot**

   | ขั้น | MCP tool |
   |---|---|
   | เปิดหน้า | `browser_navigate` |
   | อ่าน element/ref | `browser_snapshot` |
   | เลือกโหมด | `browser_select_option` |
   | กรอกค่า | `browser_type` |
   | กดปุ่ม Run | `browser_click` |
   | อ่านค่าที่คำนวณ/นับจุดใน SVG | `browser_evaluate` |
   | บันทึกภาพ | `browser_take_screenshot` |
   | ตรวจ console/network | `browser_console_messages`, `browser_network_requests` |

## ข้อควรระวังที่เจอจริง

- `--output-dir` ควรเป็น **absolute path ใน repo** เพราะ path สัมพัทธ์จะอ้าง workspace root
  ของ client (อาจไปโผล่นอก repo)
- ภาพที่บันทึกเป็นหลักฐานต้องมีชื่อไฟล์ระบุเอง (`filename`) ไม่ปล่อยเป็นชื่ออัตโนมัติ
- `favicon.ico` 404 ปรากฏใน console เป็นเรื่องปกติของแอปนี้ ไม่ใช่ error ของฟีเจอร์
