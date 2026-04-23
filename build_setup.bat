@echo off
setlocal

set ISS_PATH=C:\Users\TOSHIBA\AppData\Local\Programs\Inno Setup 6\ISCC.exe

if not exist "%ISS_PATH%" (
  echo Inno Setup ^(ISCC.exe^) introuvable: %ISS_PATH%
  exit /b 1
)

echo Compilation du setup Inno...
"%ISS_PATH%" "DiandiShopSetup.iss"

echo.
echo Setup termine.
echo Fichier: installer\DiandiShop-Setup.exe

endlocal
