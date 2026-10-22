#!/bin/bash
# Windows build via Wine: PyInstaller onedir + Inno Setup installer + onefile portable + zip
set -e
export WINEPREFIX=/workspace/exwifi/.wine WINEDEBUG=-all
cd "$(dirname "$0")"
V=$(grep -oP 'APP_VERSION = "\K[^"]+' fireout_shine.py)
PY='C:\Python311\python.exe'
python3 test/check_glyphs.py || { echo "GLYPH CHECK FAILED"; exit 1; }      # v1.0.4: no missing Japanese glyphs
wine "$PY" -m PyInstaller --noconfirm "FIREOUT SHINE.spec" > build_dir.log 2>&1; echo DIR_DONE
wine "C:\\InnoSetup\\ISCC.exe" installer.iss > build_iss.log 2>&1; echo ISS_DONE
wine "$PY" -m PyInstaller --noconfirm --workpath build_onefile --distpath dist_onefile "FIREOUT SHINE onefile.spec" > build_1f.log 2>&1
cp "dist_onefile/FIREOUT SHINE.exe" dist/FIREOUT-SHINE-Portable.exe; echo ONEFILE_DONE
cd dist && rm -f FIREOUT-SHINE-$V-Windows-x64.zip && python3 -c "import shutil; shutil.make_archive('FIREOUT-SHINE-$V-Windows-x64', 'zip', '.', 'FIREOUT SHINE')" && echo ZIP_DONE
ls -la
