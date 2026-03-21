@echo off
REM build_windows.bat — Crée le .exe Science Torch pour Windows
REM Usage : double-cliquer ou lancer dans une invite de commande
REM Prérequis : Python 3.9+, pip

setlocal EnableDelayedExpansion

set APP_NAME=ScienceTorch
set APP_VERSION=1.0.0
set DIST_DIR=dist_windows

echo.
echo ====================================================
echo   🔬  Build — Science Torch Windows
echo ====================================================
echo.

REM ── Vérification Python ──────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python introuvable. Installez Python 3.9+ depuis python.org
    pause
    exit /b 1
)
echo [OK] Python detecte

REM ── Environnement virtuel ────────────────────────────
if not exist ".venv" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo [OK] Environnement virtuel active

REM ── Installation des dependances ─────────────────────
echo Installation des dependances...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
pip install pystray pillow --quiet
echo [OK] Dependances installees

REM ── Nettoyage ────────────────────────────────────────
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "build" rmdir /s /q "build"
if exist "%APP_NAME%.spec" del "%APP_NAME%.spec"
echo [OK] Nettoyage effectue

REM ── Build PyInstaller ────────────────────────────────
echo Construction du .exe...
pyinstaller ^
    --name "%APP_NAME%" ^
    --onefile ^
    --windowed ^
    --icon "assets\icon.ico" ^
    --add-data "config.example.json;." ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --add-data "utils;utils" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "openpyxl" ^
    --hidden-import "requests" ^
    --hidden-import "schedule" ^
    --hidden-import "flask" ^
    --hidden-import "pyzotero" ^
    --hidden-import "pypdf" ^
    --distpath "%DIST_DIR%" ^
    main.py

if errorlevel 1 (
    echo [ERREUR] Build PyInstaller echoue. Verifiez les erreurs ci-dessus.
    pause
    exit /b 1
)
echo [OK] .exe cree : %DIST_DIR%\%APP_NAME%.exe

REM ── Copie des fichiers supplementaires ───────────────
copy "INSTALLATION_GUIDE.md" "%DIST_DIR%\" >nul 2>&1
copy "config.example.json" "%DIST_DIR%\" >nul 2>&1
echo [OK] Fichiers supplementaires copies

REM ── Creation d'un lanceur setup.bat ──────────────────
echo @echo off > "%DIST_DIR%\setup.bat"
echo echo Lancement de la configuration Science Torch... >> "%DIST_DIR%\setup.bat"
echo %APP_NAME%.exe --setup >> "%DIST_DIR%\setup.bat"
echo pause >> "%DIST_DIR%\setup.bat"

REM ── Résumé ───────────────────────────────────────────
echo.
echo ====================================================
echo   Build termine !
echo ====================================================
echo.
echo   Executable : %DIST_DIR%\%APP_NAME%.exe
echo.
echo   Pour distribuer :
echo   1. Envoyer le dossier %DIST_DIR%\
echo   2. Le destinataire lance setup.bat la premiere fois
echo   3. Puis double-clique sur ScienceTorch.exe
echo.
echo   Note : Ollama doit etre installe sur la machine cible.
echo   Telechargement : https://ollama.ai
echo.
pause
