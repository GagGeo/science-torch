#!/usr/bin/env python3
"""
main.py — Point d'entrée de Science Torch
"""

import json
import sys
import os
import subprocess
from pathlib import Path

# S'assurer que le dossier du projet est dans le path Python
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from utils.logger import get_logger, add_file_handler

# Config dans ~/Documents/VeilleScientifique/config.json
# (persiste entre les mises à jour de l'app)
USER_CONFIG = Path.home() / "Documents" / "VeilleScientifique" / "config.json"
# Fallback : config à côté du script (mode développeur)
LOCAL_CONFIG = PROJECT_DIR / "config.json"

def find_config() -> Path:
    if USER_CONFIG.exists():
        return USER_CONFIG
    if LOCAL_CONFIG.exists():
        return LOCAL_CONFIG
    return None

def run_setup():
    """Lance le wizard de configuration au premier démarrage."""
    setup_script = PROJECT_DIR / "setup.py"
    if setup_script.exists():
        subprocess.run([sys.executable, str(setup_script)], check=False)
    else:
        print("❌ setup.py introuvable.")
        sys.exit(1)

def load_config() -> dict:
    config_path = find_config()
    if not config_path:
        print("Premier lancement détecté — lancement de la configuration...")
        run_setup()
        config_path = find_config()
        if not config_path:
            print("❌ Configuration introuvable après setup.")
            sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def main():
    config = load_config()

    log_dir = config.get("paths", {}).get("logs", str(Path.home() / "Documents" / "VeilleScientifique" / "logs"))
    add_file_handler(log_dir)

    logger = get_logger(__name__)
    logger.info("Démarrage Science Torch")

    try:
        from ui.menu_bar import VeilleApp
        app = VeilleApp(config)
        print("🔬 Science Torch démarrée — icône dans la barre de menu")
        app.run_app()

    except ImportError as e:
        print(f"❌ Dépendance manquante : {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Au revoir !")
        sys.exit(0)

if __name__ == "__main__":
    main()
