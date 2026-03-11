#!/bin/bash
# build.sh — Crée le lanceur .app et le .dmg pour Veille Scientifique
# Usage : bash build.sh

set -e

BOLD="\033[1m"
CYAN="\033[96m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
RESET="\033[0m"

APP_NAME="Veille Scientifique"
APP_VERSION="1.0.0"
DIST_DIR="dist"
DMG_NAME="VeilleScientifique-${APP_VERSION}.dmg"
PROJECT_PATH="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_PATH/.venv/bin/python3"
VENV_ACTIVATE="$PROJECT_PATH/.venv/bin/activate"
LOG_PATH="\$HOME/Documents/VeilleScientifique/logs/launch.log"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║    🔬  Build — Veille Scientifique macOS App        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Vérifications ─────────────────────────────────────────────────────────────
echo -e "${BOLD}1. Vérifications...${RESET}"
if [ ! -f ".venv/bin/activate" ]; then
    echo -e "${RED}❌ .venv introuvable. Lancez d'abord : bash install.sh${RESET}"
    exit 1
fi
if [ ! -f "config.json" ]; then
    echo -e "${RED}❌ config.json introuvable. Lancez d'abord : python setup.py${RESET}"
    exit 1
fi
echo -e "${GREEN}✓ Projet : $PROJECT_PATH${RESET}"
echo -e "${GREEN}✓ Python  : $VENV_PYTHON${RESET}"

# ── Création du .app via AppleScript ─────────────────────────────────────────
echo -e "\n${BOLD}2. Création du .app...${RESET}"
mkdir -p "$DIST_DIR"
APP_PATH="$DIST_DIR/${APP_NAME}.app"
rm -rf "$APP_PATH"

osacompile -o "$APP_PATH" << APPLEEOF
on run
    do shell script "cd '$PROJECT_PATH' && source '$VENV_ACTIVATE' && '$VENV_PYTHON' '$PROJECT_PATH/main.py' > $LOG_PATH 2>&1 &"
end run
APPLEEOF

echo -e "${GREEN}✓ .app créé : $APP_PATH${RESET}"

# ── Copie sur le bureau ───────────────────────────────────────────────────────
echo -e "\n${BOLD}3. Copie sur le bureau...${RESET}"
DESKTOP_APP="$HOME/Desktop/${APP_NAME}.app"
rm -rf "$DESKTOP_APP"
cp -r "$APP_PATH" "$DESKTOP_APP"
echo -e "${GREEN}✓ App copiée sur le bureau${RESET}"

# ── Création du .dmg ─────────────────────────────────────────────────────────
echo -e "\n${BOLD}4. Création du .dmg...${RESET}"
rm -f "$DIST_DIR/$DMG_NAME"
DMG_STAGING="$DIST_DIR/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"
cp -r "$APP_PATH" "$DMG_STAGING/"
ln -sf /Applications "$DMG_STAGING/Applications"

hdiutil create \
    -volname "$APP_NAME $APP_VERSION" \
    -srcfolder "$DMG_STAGING" \
    -ov -format UDZO \
    "$DIST_DIR/$DMG_NAME" 2>&1 | tail -2

rm -rf "$DMG_STAGING"

if [ -f "$DIST_DIR/$DMG_NAME" ]; then
    SIZE=$(du -sh "$DIST_DIR/$DMG_NAME" | cut -f1)
    echo -e "${GREEN}✓ DMG créé : $DIST_DIR/$DMG_NAME ($SIZE)${RESET}"
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅  Build terminé !                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "  ${BOLD}Lanceur créé sur votre bureau :${RESET}"
echo -e "  ${CYAN}~/Desktop/Veille Scientifique.app${RESET}"
echo -e "  Double-cliquez pour lancer — aucun terminal requis."
echo ""
echo -e "  ${BOLD}Pour partager :${RESET}"
echo -e "  Envoyez ${CYAN}$DIST_DIR/$DMG_NAME${RESET} + ce dossier projet."
echo -e "  Le destinataire doit avoir Ollama installé."
