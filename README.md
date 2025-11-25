# OST Inbox Finder (Windows & macOS, local-only)

Search **Inbox** emails in a single `.ost` using a time window.
- Backend: FastAPI (local-only)
- Frontend: basic HTML/JS
- Parser: `libpff` / `pypff`
- Packaging: PyInstaller for a clickable executable
- Includes a **synthetic test `.ost`** so you can run without real Outlook data

## Folder layout
```
app/
  __init__.py
  main.py
  cli.py
  ost_reader.py
  static/index.html
requirements.txt
run.sh
build-mac.sh
sample_test.ost
```

## Quick Start (Windows dev)
```powershell
py -3.11 -m venv .venv
.\.venv\Scriptsctivate
pip install -r requirements.txt
python -m app.main
# open http://127.0.0.1:8000
```

## Quick Start (macOS dev)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
python3 -m app.main 
#if the above command fails then run the below command
pip install python-multipart
# re run
python3 -m app.main

# open http://127.0.0.1:8000
```

### pypff/libpff installation notes
If `libpff-python` fails to install:
- macOS: `brew install libpff` then `pip install libpff-python`
- Windows: try Python 3.11 x64 for best wheel support, or build from source (see libpff repo).

## Build executable (Windows)
```powershell
.\.venv\Scriptsctivate
pyinstaller --noconfirm --onefile --add-data "app/static;app/static" --name ost-finder app\main.py
# dist\ost-finder.exe
```

## Build executable (macOS)
```bash
source .venv/bin/activate
pyinstaller --noconfirm --onefile --add-data "app/static:app/static" --name ost-finder app/main.py
# dist/ost-finder
```

> macOS Gatekeeper: you may need to allow the binary in Settings → Privacy & Security or run `xattr -dr com.apple.quarantine dist/ost-finder`.

# Testing Scenario
## Prerequisites
1. Python 3.11 or later

2. Project folder structure intact (app/, sample_test.ost, sample_10k.ost, requirements.txt)

3. Virtual environment activated and dependencies installed:

python3 -m venv .venv
source .venv/bin/activate       # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt

# Scenario 1 – Sanity Test (Synthetic Sample)
Goal: Verify the app can read and filter a small .ost file.

## Run:
python -m app.main
Open http://127.0.0.1:8000

Upload sample_test.ost.

Use:
Start: 2024-01-15T00:00
End: 2024-01-27T00:00
Filter by: Received time
Click Search → Expect 12 results.
- Confirms the synthetic OST parsing and date filtering work.

# Scenario 2 – Performance Test (10,000 Emails)
Goal: Validate streaming, performance, and CSV export.
Run the same app (python -m app.main).
Upload sample_10k.ost.
Leave start/end blank → Click Search.
Expect 10,000 results.
Click Download CSV → Ensure a file named results.csv downloads and contains 10k rows.

- Confirms backend handles large inboxes efficiently without loading into memory.

# Scenario 3 – CLI Verification
Goal: Verify backend logic without the UI.

python -m app.cli --ost ./sample_10k.ost \
  --start 2024-01-01T00:00:00 \
  --end 2024-02-01T00:00:00 \
  --mode received \
  --csv out.csv
Expected output:

Wrote 10000 rows to out.csv
- Proves CLI and backend share the same filtering pipeline.

# Scenario 4 – Packaging (Optional)
Goal: Build an offline executable.

- Windows:
.\.venv\Scripts\activate
pyinstaller --noconfirm --onefile --add-data "app/static;app/static" --name ost-finder app\main.py

- macOS:
source .venv/bin/activate
pyinstaller --noconfirm --onefile --add-data "app/static:app/static" --name ost-finder app/main.py
Double-click the generated dist/ost-finder(.exe) and open http://127.0.0.1:8000.
