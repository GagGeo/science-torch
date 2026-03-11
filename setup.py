#!/usr/bin/env python3
"""
setup.py — Configuration initiale interactive de Veille Scientifique
Lance ce script une seule fois pour configurer l'application.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from itertools import combinations

# ── Couleurs terminal ────────────────────────────────────────────────────────
BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"

def print_header():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗
║        🔬  Veille Scientifique — Configuration       ║
╚══════════════════════════════════════════════════════╝{RESET}
    """)

def print_step(n, title):
    print(f"\n{CYAN}{BOLD}── Étape {n} : {title} ──{RESET}")

def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{YELLOW}▶ {prompt}{suffix}: {RESET}").strip()
    return val if val else default

def ask_bool(prompt, default=True):
    suffix = "[O/n]" if default else "[o/N]"
    val = input(f"{YELLOW}▶ {prompt} {suffix}: {RESET}").strip().lower()
    if not val:
        return default
    return val in ("o", "oui", "y", "yes")

def check_dependency(name, check_cmd, install_hint):
    try:
        subprocess.run(check_cmd, capture_output=True, check=True)
        print(f"  {GREEN}✓ {name} détecté{RESET}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  {RED}✗ {name} non trouvé — {install_hint}{RESET}")
        return False

# ── Étape 0 : Vérification des dépendances ──────────────────────────────────
def check_dependencies():
    print_step(0, "Vérification des prérequis")
    ok = True

    ok &= check_dependency(
        "Python 3.9+",
        ["python3", "--version"],
        "https://python.org"
    )
    ok &= check_dependency(
        "Ollama",
        ["ollama", "list"],
        "Installer depuis https://ollama.ai"
    )
    check_dependency(
        "Zotero (optionnel)",
        ["open", "-Ra", "Zotero.app"],
        "Installer depuis https://zotero.org si souhaité"
    )
    return ok

# ── Étape 1 : Dossiers ──────────────────────────────────────────────────────
def configure_paths():
    print_step(1, "Dossiers de stockage")
    home = Path.home()
    default_base = str(home / "Documents" / "VeilleScientifique")
    base = ask("Dossier racine du projet", default_base)
    base = Path(base).expanduser()

    paths = {
        "base":         str(base),
        "pdfs":         str(base / "pdfs"),
        "pdfs_auto":    str(base / "pdfs" / "auto"),
        "pdfs_manual":  str(base / "pdfs" / "manual"),
        "summaries":    str(base / "resumes"),
        "excel":        str(base / "veille.xlsx"),
        "logs":         str(base / "logs"),
    }

    for p in paths.values():
        Path(p).mkdir(parents=True, exist_ok=True)

    print(f"  {GREEN}✓ Dossiers créés dans {base}{RESET}")
    return paths

# ── Étape 2 : Domaines et mots-clés ─────────────────────────────────────────
def configure_domains():
    print_step(2, "Domaines de recherche et mots-clés PubMed")
    print("""
  Entrez vos domaines un par un. Pour chaque domaine, vous définirez :
  - Un nom court (ex: ME)
  - Un nom long (ex: Mémoire Épisodique)
  - Des mots-clés PubMed séparés par des virgules

  Tapez ENTRÉE sans rien écrire pour terminer la saisie des domaines.
    """)

    domains = []
    i = 1
    while True:
        print(f"{BOLD}  Domaine {i} :{RESET}")
        short = ask(f"    Abréviation (ex: ME)", None)
        if not short:
            if i == 1:
                print(f"  {RED}Au moins un domaine est requis.{RESET}")
                continue
            break
        long_name = ask(f"    Nom complet (ex: Mémoire Épisodique)", short)
        keywords_raw = ask(
            f"    Mots-clés PubMed (séparés par des virgules)",
            f"{long_name}"
        )
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        domains.append({
            "short":    short.upper(),
            "name":     long_name,
            "keywords": keywords
        })
        print(f"  {GREEN}✓ Domaine '{short.upper()}' ajouté avec {len(keywords)} mot(s)-clé(s){RESET}")
        i += 1

    return domains

# ── Étape 3 : Combinaisons inter-domaines ───────────────────────────────────
def configure_combinations(domains):
    print_step(3, "Onglets de combinaisons inter-domaines")

    if len(domains) < 2:
        print("  (Moins de 2 domaines — aucune combinaison possible)")
        return []

    all_combos = []
    for r in range(2, len(domains) + 1):
        for combo in combinations(domains, r):
            all_combos.append(combo)

    print(f"\n  {len(all_combos)} combinaison(s) possible(s) :")
    selected = []
    for combo in all_combos:
        shorts = " × ".join(d["short"] for d in combo)
        names  = " + ".join(d["name"]  for d in combo)
        if ask_bool(f"  Activer l'onglet '{shorts}' ({names})?", True):
            selected.append({
                "short":   " x ".join(d["short"] for d in combo),
                "name":    " × ".join(d["name"]  for d in combo),
                "domains": [d["short"] for d in combo]
            })

    print(f"  {GREEN}✓ {len(selected)} combinaison(s) activée(s){RESET}")
    return selected

# ── Étape 4 : Ollama ─────────────────────────────────────────────────────────
def configure_ollama():
    print_step(4, "Modèle Ollama (LLM local)")

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        models = []
        for line in result.stdout.strip().split("\n")[1:]:  # skip header
            parts = line.split()
            if parts:
                models.append(parts[0])

        if models:
            print(f"  Modèles disponibles : {', '.join(models)}")
            default_model = next(
                (m for m in models if any(x in m for x in ["mistral", "llama3", "llama2"])),
                models[0]
            )
        else:
            print(f"  {YELLOW}Aucun modèle trouvé. Installer avec : ollama pull mistral{RESET}")
            default_model = "mistral"

    except FileNotFoundError:
        default_model = "mistral"

    model = ask("Modèle à utiliser", default_model)
    return {"model": model, "base_url": "http://localhost:11434"}

# ── Étape 5 : Zotero ─────────────────────────────────────────────────────────
def configure_zotero():
    print_step(5, "Intégration Zotero (optionnelle)")

    use_zotero = ask_bool("Activer la synchronisation Zotero?", True)
    if not use_zotero:
        return {"enabled": False}

    print("""
  Pour l'API locale Zotero, vous avez besoin de :
  1. Zotero ouvert avec Better BibTeX installé
  2. Dans Zotero : Édition > Préférences > Avancées > API locale
     → Activer l'API locale (port 23119 par défaut)
    """)

    port = ask("Port API locale Zotero", "23119")
    library_type = ask("Type de bibliothèque (user/group)", "user")

    collection = ask("Nom de la collection Zotero à utiliser (laisser vide = racine)", "")

    return {
        "enabled":      True,
        "base_url":     f"http://localhost:{port}",
        "library_type": library_type,
        "collection":   collection,
        "port":         int(port)
    }

# ── Étape 6 : Planification ──────────────────────────────────────────────────
def configure_scheduler():
    print_step(6, "Planification de la recherche automatique")

    days = {
        "1": "Lundi", "2": "Mardi", "3": "Mercredi",
        "4": "Jeudi", "5": "Vendredi", "6": "Samedi", "7": "Dimanche"
    }
    print("  Jours : " + ", ".join(f"{k}={v}" for k, v in days.items()))
    day_num = ask("Jour de la recherche hebdomadaire", "1")
    day_name = days.get(day_num, "Lundi").lower()

    time_str = ask("Heure de lancement (format HH:MM)", "08:00")

    notifications = ask_bool("Activer les notifications macOS?", True)

    return {
        "day":           day_name,
        "time":          time_str,
        "notifications": notifications
    }

# ── Étape 7 : PubMed ─────────────────────────────────────────────────────────
def configure_pubmed():
    print_step(7, "Configuration PubMed")
    print("""
  L'API PubMed est gratuite. Pour des recherches plus intensives,
  un email NCBI est recommandé (pas obligatoire).
    """)
    email = ask("Votre email (pour l'API NCBI, optionnel)", "")
    max_results = ask("Nombre max d'articles par recherche hebdomadaire", "50")

    return {
        "email":       email,
        "max_results": int(max_results),
        "base_url":    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    }

# ── Sauvegarde config ────────────────────────────────────────────────────────
def save_config(config, config_path):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n  {GREEN}✓ Configuration sauvegardée dans {config_path}{RESET}")

# ── Installation des dépendances Python ──────────────────────────────────────
def install_requirements():
    print_step("8", "Installation des dépendances Python")
    req_path = Path(__file__).parent / "requirements.txt"
    if not req_path.exists():
        print(f"  {RED}requirements.txt introuvable{RESET}")
        return

    do_install = ask_bool("Installer les dépendances Python maintenant?", True)
    if do_install:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            check=True
        )
        print(f"  {GREEN}✓ Dépendances installées{RESET}")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print_header()
    print("  Bienvenue ! Ce script va configurer votre outil de veille scientifique.")
    print("  Vous pourrez modifier ces paramètres à tout moment dans config.json\n")

    if not check_dependencies():
        print(f"\n  {YELLOW}Certains prérequis manquent — continuez quand même ? {RESET}")
        if not ask_bool("Continuer malgré tout?", False):
            sys.exit(1)

    paths     = configure_paths()
    domains   = configure_domains()
    combos    = configure_combinations(domains)
    ollama    = configure_ollama()
    zotero    = configure_zotero()
    scheduler = configure_scheduler()
    pubmed    = configure_pubmed()

    config = {
        "version":      "1.0.0",
        "paths":        paths,
        "domains":      domains,
        "combinations": combos,
        "ollama":       ollama,
        "zotero":       zotero,
        "scheduler":    scheduler,
        "pubmed":       pubmed,
        "article_types": {
            "experimental": {
                "label": "Expérimental / Méta-analyse",
                "columns": [
                    "Référence", "Année", "Clé citable", "BibTeX", "Type",
                    "Hypothèse(s)", "Population", "N par groupe",
                    "Type de groupe", "Critères inclusion/exclusion",
                    "Méthode / Outils", "Résultats principaux",
                    "Taille d'effet", "Conclusion", "Take Home Message",
                    "Domaines", "Lu", "PDF disponible", "Chemin PDF"
                ]
            },
            "review": {
                "label": "Revue de littérature",
                "columns": [
                    "Référence", "Année", "Clé citable", "BibTeX", "Type",
                    "Objectif de la revue", "Corpus couvert",
                    "Nombre d'articles inclus", "Période couverte",
                    "Thèmes principaux", "Consensus identifiés",
                    "Débats / Controverses", "Limites identifiées",
                    "Taille d'effet globale (méta)", "Hétérogénéité I²",
                    "Take Home Message", "Domaines", "Lu",
                    "PDF disponible", "Chemin PDF"
                ]
            }
        }
    }

    config_path = Path(__file__).parent / "config.json"
    save_config(config, config_path)

    install_requirements()

    print(f"""
{GREEN}{BOLD}╔══════════════════════════════════════════════════════╗
║          ✅  Configuration terminée !                ║
╚══════════════════════════════════════════════════════╝{RESET}

  Pour lancer l'application :
  {CYAN}python main.py{RESET}

  L'icône 🔬 apparaîtra dans votre barre de menu macOS.
    """)

if __name__ == "__main__":
    main()
