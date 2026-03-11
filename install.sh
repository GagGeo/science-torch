#!/bin/bash
# install.sh — Installation automatique de Science Torch
# Usage : bash install.sh

set -e

BOLD="\033[1m"
CYAN="\033[96m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║      🔬  Installation — Science Torch         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Python ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}1. Vérification Python...${RESET}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 non trouvé. Installer depuis https://python.org${RESET}"
    exit 1
fi
PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✓ Python ${PYTHON_VER} détecté${RESET}"

# ── Environnement virtuel ─────────────────────────────────────────────────────
echo -e "\n${BOLD}2. Création de l'environnement virtuel...${RESET}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Environnement virtuel créé dans .venv/${RESET}"
else
    echo -e "${GREEN}✓ Environnement virtuel déjà présent${RESET}"
fi

# Activer le venv
source .venv/bin/activate
python3 -m pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip mis à jour${RESET}"

# ── Dépendances ───────────────────────────────────────────────────────────────
echo -e "\n${BOLD}3. Installation des dépendances...${RESET}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Dépendances installées${RESET}"
else
    echo -e "${RED}❌ requirements.txt introuvable${RESET}"
    exit 1
fi

# ── Ollama ────────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}4. Vérification Ollama...${RESET}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama détecté${RESET}"

    # Vérifier si un modèle est disponible
    MODELS=$(ollama list 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
    if [ "$MODELS" -eq "0" ]; then
        echo -e "${YELLOW}⚠ Aucun modèle Ollama installé.${RESET}"
        echo -e "  Recommandé : ${CYAN}ollama pull mistral${RESET}"
        read -p "Télécharger mistral maintenant ? [O/n] " choice
        if [[ "$choice" != "n" && "$choice" != "N" ]]; then
            ollama pull mistral
        fi
    else
        echo -e "${GREEN}✓ ${MODELS} modèle(s) Ollama disponible(s)${RESET}"
    fi
else
    echo -e "${YELLOW}⚠ Ollama non trouvé.${RESET}"
    echo -e "  Installer depuis : ${CYAN}https://ollama.ai${RESET}"
    echo -e "  L'application fonctionnera sans, mais sans analyse automatique."
fi

# ── Configuration ─────────────────────────────────────────────────────────────
echo -e "\n${BOLD}5. Configuration initiale...${RESET}"
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}Lancement du wizard de configuration...${RESET}"
    source .venv/bin/activate && python3 setup.py
else
    echo -e "${GREEN}✓ config.json déjà présent — configuration ignorée${RESET}"
    read -p "Reconfigurer depuis zéro ? [o/N] " choice
    if [[ "$choice" == "o" || "$choice" == "O" ]]; then
        source .venv/bin/activate && python3 setup.py
    fi
fi

# ── Alias de lancement ────────────────────────────────────────────────────────
echo -e "\n${BOLD}6. Création du raccourci de lancement...${RESET}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAUNCH_SCRIPT="$HOME/.local/bin/veille"

mkdir -p "$HOME/.local/bin"
cat > "$LAUNCH_SCRIPT" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
source .venv/bin/activate
python3 main.py
EOF
chmod +x "$LAUNCH_SCRIPT"

# Vérifier si ~/.local/bin est dans le PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}  Ajout de ~/.local/bin au PATH dans ~/.zshrc${RESET}"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo -e "  Redémarrez votre terminal ou lancez : ${CYAN}source ~/.zshrc${RESET}"
fi

echo -e "${GREEN}✓ Raccourci créé : tapez 'veille' dans votre terminal pour lancer l'app${RESET}"

# ── Fin ───────────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅  Installation terminée !                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "  Pour lancer : ${CYAN}python3 main.py${RESET} ou ${CYAN}veille${RESET}"
echo -e "  L'icône 🔬 apparaîtra dans votre barre de menu macOS.\n"
