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

## Storage protection
- **Limit:** each user can keep up to 5 question banks; the upload form is replaced by a notice when full.
- **Duplicates:** a file whose questions are already loaded (even renamed, re-saved, reordered or with other IDs)
  is not stored again — the existing bank is opened instead.
- **Retention:** banks and test history of users inactive for 30 days are deleted automatically
  (checked every 6 hours and when the user returns); accounts are kept.
- New columns are added to an existing database automatically on start — no manual migration needed.
