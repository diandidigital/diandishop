@echo off
setlocal

echo [1/3] Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo [2/3] Installation/MAJ de PyInstaller...
python -m pip install --upgrade pyinstaller

echo [3/3] Build EXE en cours...
python -m PyInstaller --noconfirm --clean --onefile --name DiandiShop --add-data "templates;templates" --add-data "static;static" app.py

echo.
echo Build termine.
echo EXE: dist\DiandiShop.exe
endlocal
