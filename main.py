#!/usr/bin/env python3
"""
main.py — Point d'entrée de Science Torch
Détecte automatiquement la plateforme (macOS / Linux / Windows)
et charge le bon module d'interface.
"""

import json
import sys
import os
import platform
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from utils.logger import get_logger, add_file_handler

SYSTEM = platform.system()  # "Darwin" | "Linux" | "Windows"

LOCAL_CONFIG = PROJECT_DIR / "config.json"

# Emplacements possibles pour config.json — dans l'ordre de priorité
CONFIG_SEARCH_PATHS = [
    LOCAL_CONFIG,                                                    # Dossier projet (dev)
    Path.home() / "Documents" / "ScienceTorch" / "config.json",    # Défaut macOS/Linux
    Path.home() / "Documents" / "ScienceTorch" / "config.json",    # Défaut Windows
    Path.home() / "ScienceTorch" / "config.json",                  # Sans Documents/
]


def find_config() -> Path:
    """Cherche config.json dans tous les emplacements connus."""
    for p in CONFIG_SEARCH_PATHS:
        if p.exists():
            return p
    return None


def run_setup():
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
    # Support --setup flag for Windows first-run
    if "--setup" in sys.argv:
        run_setup()
        return

    config = load_config()

    log_dir = config.get("paths", {}).get(
        "logs",
        str(Path(config.get("paths", {}).get("base", str(Path.home() / "Documents" / "ScienceTorch"))) / "logs")
    )
    add_file_handler(log_dir)
    logger = get_logger(__name__)
    logger.info(f"Démarrage Science Torch ({SYSTEM})")

    try:
        if SYSTEM == "Darwin":
            from ui.menu_bar import VeilleApp
            app = VeilleApp(config)
            print("🔬 Science Torch démarrée — icône dans la barre de menu")
            app.run_app()

        elif SYSTEM == "Linux":
            from ui.menu_bar_linux import VeilleAppLinux
            app = VeilleAppLinux(config)
            print("🔬 Science Torch démarrée — icône dans la barre système")
            app.run_app()

        elif SYSTEM == "Windows":
            try:
                from ui.menu_bar_linux import VeilleAppLinux
                app = VeilleAppLinux(config)
                print("🔬 Science Torch démarrée — icône dans la barre système")
                app.run_app()
            except ImportError:
                print("❌ Version Windows en cours de développement.")
                print("   Installez pystray et pillow : pip install pystray pillow")
                sys.exit(1)

        else:
            print(f"❌ Plateforme non supportée : {SYSTEM}")
            sys.exit(1)

    except ImportError as e:
        print(f"❌ Dépendance manquante : {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Au revoir !")
        sys.exit(0)


if __name__ == "__main__":
    main()
