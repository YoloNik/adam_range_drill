# Range Drill — theory test trainer

Flask app for practising multiple-choice tests from an Excel file.

## Languages
The interface is in **Polish by default**; users can switch to English with the PL / EN toggle in the header
(the choice is kept in a cookie for a year). All texts live in `i18n.py` — to change a wording, edit it there.
The downloadable Excel template is generated in the selected language.

Fonts are self-hosted in `static/fonts` (no requests to Google), so the site has no third-party calls.

## Excel format (first sheet)
| A | B | C–E | F |
|---|---|---|---|
| Question ID | Question | Answer options | Correct answer: `A/B/C`, `C/D/E`, `1/2/3` or the exact option text |

A header row is detected automatically. A sample file can be downloaded on the dashboard.

## Modes
| Mode | Mistakes allowed | Pass condition |
|---|---|---|
| Easy | unlimited | score ≥ `EASY_PASS_RATIO` (default 80%) |
| Medium | 5 | finish without a 6th mistake |
| Hard | 2 | finish without a 3rd mistake |
| Impossible | 0 | no mistakes |

## Run in your Wi-Fi network (one computer = server)
Other devices in the same Wi-Fi open the site in a browser; no internet is needed after the first start.

**Windows**
1. Install Python 3 from python.org (tick *Add python.exe to PATH*).
2. Double-click `start.bat`. The first start installs packages (needs internet once).
3. When Windows Firewall asks, allow access for **Private networks**
   (or double-click `allow-firewall.bat` once — it asks for administrator rights itself).
4. The window shows the address, e.g. `http://192.168.1.25:8000`, and a QR code for phones.

**macOS / Linux:** run `./start.sh`.

Tips
- Wi-Fi must be set as a *Private* network in Windows (Settings → Network → Wi-Fi → network properties).
- Guest Wi-Fi networks often block devices from seeing each other ("client/AP isolation") — use the main network or disable isolation in the router.
- Reserve a fixed IP for the server computer in the router (DHCP reservation), so the address and printed QR code never change.
- Turn off sleep on the server computer while the range is open.
- Autostart on Windows: press Win+R, type `shell:startup`, put a shortcut to `start.bat` there.
- Data is stored in `instance/range_drill.db` — copy this file to back it up.
- Use another port: `start.bat --port 8080` (then run `allow-firewall.bat 8080`).

## Run locally for development
```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```

## Environment variables
| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Session signing key. Render generates it. Locally a random key is created in `instance/secret_key` |
| `DATABASE_URL` | Postgres URL (`postgres://` / `postgresql://` both work). Without it a local SQLite file is used (**not persistent on Render free**) |
| `REGISTRATION_CODE` | Optional: only people who know this code can register |
| `SECURE_COOKIES` | `1` behind HTTPS (set by `render.yaml`) |
| `APP_NAME` | Name shown in the header |
| `EASY_PASS_RATIO` | Pass mark for Easy mode, e.g. `0.8` |

## Deploy to Render (free) + Neon Postgres (free)
1. **Database** — sign up at neon.tech → *Create project* (region: Europe / Frankfurt) →
   *Connect* → copy the connection string (`postgresql://...neon.tech/neondb?sslmode=require...`).
2. **Web service** — render.com → *New* → *Blueprint* → connect GitHub → pick this repo.
   Render reads `render.yaml` and asks for the secret values:
   - `DATABASE_URL` — paste the Neon string;
   - `REGISTRATION_CODE` — optional access code (leave empty for open registration).
3. Click *Deploy*. After ~2–3 minutes the site is live at `https://<name>.onrender.com`.
   Tables are created automatically on first start.

Every `git push` to `main` redeploys automatically.

Notes for the free plans
- Render free sleeps after 15 min without visitors; the first request then takes about a minute.
- Neon free sleeps after 5 min idle and wakes up in a moment; data is kept (0.5 GB is plenty here).
- If the Render log shows `DATABASE_URL is not set`, the site runs on temporary storage — set the variable.
