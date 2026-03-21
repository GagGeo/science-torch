#!/usr/bin/env python3
"""
setup.py — Configuration initiale interactive de Science Torch
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


# ── Langue globale ────────────────────────────────────────────────────────────
LANG = "en"  # Défaut anglais — mis à jour par configure_language()

# Chaînes bilingues pour le setup
T = {
    "welcome":       {"fr": "Bienvenue ! Ce script va configurer votre outil de veille scientifique.",
                      "en": "Welcome! This script will configure your Science Torch tool."},
    "edit_later":    {"fr": "Vous pourrez modifier ces paramètres à tout moment dans config.json",
                      "en": "You can modify these settings at any time in config.json"},
    "step":          {"fr": "Étape", "en": "Step"},
    "prereqs":       {"fr": "Vérification des prérequis", "en": "Checking prerequisites"},
    "detected":      {"fr": "détecté", "en": "detected"},
    "not_found":     {"fr": "non trouvé — ", "en": "not found — "},
    "continue_anyway":{"fr": "Certains prérequis manquent — continuez quand même ?",
                       "en": "Some prerequisites are missing — continue anyway?"},
    "continue_q":    {"fr": "Continuer malgré tout?", "en": "Continue anyway?"},
    "storage":       {"fr": "Dossiers de stockage", "en": "Storage folders"},
    "domains_title": {"fr": "Domaines de recherche et mots-clés PubMed",
                      "en": "Research domains and PubMed keywords"},
    "combos_title":  {"fr": "Onglets de combinaisons inter-domaines",
                      "en": "Cross-domain combination tabs"},
    "ollama_title":  {"fr": "Modèle Ollama (LLM local)", "en": "Ollama model (local LLM)"},
    "zotero_title":  {"fr": "Intégration Zotero (optionnelle)", "en": "Zotero integration (optional)"},
    "scheduler_title":{"fr": "Planification de la recherche automatique",
                       "en": "Automatic search scheduling"},
    "pubmed_title":  {"fr": "Configuration PubMed", "en": "PubMed configuration"},
    "excel_title":   {"fr": "Champs du fichier Excel", "en": "Excel file fields"},
    "install_title": {"fr": "Installation des dépendances Python",
                      "en": "Installing Python dependencies"},
    "yes_no":        {"fr": "[O/n]", "en": "[Y/n]"},
    "no_yes":        {"fr": "[o/N]", "en": "[y/N]"},
    "saved":         {"fr": "Configuration sauvegardée dans", "en": "Configuration saved to"},
    "done":          {"fr": "Configuration terminée !", "en": "Configuration complete!"},
    "launch":        {"fr": "Pour lancer l'application :", "en": "To launch the app:"},
    "icon_appears":  {"fr": "L'icône 🔬 apparaîtra dans votre barre de menu.",
                      "en": "The 🔬 icon will appear in your menu bar."},
}

def t(key: str) -> str:
    """Retourne la chaîne traduite selon la langue courante."""
    return T.get(key, {}).get(LANG, T.get(key, {}).get("en", key))

# ── Étape 0 bis : Choix de la langue ─────────────────────────────────────────
def configure_language() -> str:
    """Première question : choix de la langue."""
    global LANG
    print(f"\n{CYAN}{BOLD}── Language / Langue ──{RESET}")
    print("  Choose your language / Choisissez votre langue :")
    print("  1. English")
    print("  2. Français")
    choice = input(f"{YELLOW}▶ [1/2] (default: 1): {RESET}").strip()
    LANG = "fr" if choice == "2" else "en"
    print(f"  {GREEN}✓ Language set to: {'Français' if LANG == 'fr' else 'English'}{RESET}")
    return LANG

def print_header():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗
║        🔬  Science Torch — Configuration       ║
╚══════════════════════════════════════════════════════╝{RESET}
    """)

def print_step(n, title):
    step_word = t("step")
    print(f"\n{CYAN}{BOLD}── {step_word} {n} : {title} ──{RESET}")

def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{YELLOW}▶ {prompt}{suffix}: {RESET}").strip()
    return val if val else default

def ask_bool(prompt, default=True):
    suffix = t("yes_no") if default else t("no_yes")
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
    print_step(1, t("storage"))
    home = Path.home()

    # ── Nom du dossier ────────────────────────────────────────────────────
    if LANG == "fr":
        print("""
  Choisissez le nom et l'emplacement du dossier où seront stockés
  vos articles, PDFs et résumés.
        """)
        default_name = "ScienceTorch"
        name_prompt  = "Nom du dossier de données"
        loc_prompt   = "Dossier parent (où créer le dossier de données)"
        default_loc  = str(home / "Documents")
    else:
        print("""
  Choose the name and location of the folder where your articles,
  PDFs and summaries will be stored.
        """)
        default_name = "ScienceTorch"
        name_prompt  = "Data folder name"
        loc_prompt   = "Parent folder (where to create the data folder)"
        default_loc  = str(home / "Documents")

    folder_name = ask(name_prompt, default_name).strip() or default_name
    parent_loc  = ask(loc_prompt, default_loc).strip() or default_loc
    base        = Path(parent_loc).expanduser() / folder_name

    # Nom du fichier Excel
    if LANG == "fr":
        excel_name = ask("Nom du fichier Excel", "veille.xlsx").strip() or "veille.xlsx"
        summaries_name = "resumes"
    else:
        excel_name     = ask("Excel file name", "watch.xlsx").strip() or "watch.xlsx"
        summaries_name = "summaries"

    if not excel_name.endswith(".xlsx"):
        excel_name += ".xlsx"

    paths = {
        "base":         str(base),
        "pdfs":         str(base / "pdfs"),
        "pdfs_auto":    str(base / "pdfs" / "auto"),
        "pdfs_manual":  str(base / "pdfs" / "manual"),
        "summaries":    str(base / summaries_name),
        "excel":        str(base / excel_name),
        "logs":         str(base / "logs"),
    }

    for p in paths.values():
        Path(p).mkdir(parents=True, exist_ok=True)

    if LANG == "fr":
        print(f"  {GREEN}✓ Dossiers créés dans {base}{RESET}")
    else:
        print(f"  {GREEN}✓ Folders created in {base}{RESET}")
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


# ── Configuration des champs Excel ───────────────────────────────────────────
DEFAULT_COLS_EXPERIMENTAL = [
    {"name": "Référence",              "width": 40},
    {"name": "Année",                  "width": 8},
    {"name": "Clé citable",            "width": 15},
    {"name": "BibTeX",                 "width": 30},
    {"name": "Type",                   "width": 20},
    {"name": "Hypothèse(s)",           "width": 40},
    {"name": "Population",             "width": 25},
    {"name": "N par groupe",           "width": 15},
    {"name": "Type de groupe",         "width": 25},
    {"name": "Critères incl./excl.",   "width": 35},
    {"name": "Méthode / Outils",       "width": 35},
    {"name": "Résultats principaux",   "width": 45},
    {"name": "Taille d'effet",         "width": 15},
    {"name": "Tests statistiques",     "width": 30},
    {"name": "Seuil de significativité","width": 20},
    {"name": "Intervalles de confiance","width": 25},
    {"name": "Puissance statistique",  "width": 20},
    {"name": "Conclusion",             "width": 40},
    {"name": "Take Home Message",      "width": 40},
    {"name": "Domaines",               "width": 20},
    {"name": "Lu",                     "width": 8},
    {"name": "PDF disponible",         "width": 15},
    {"name": "Chemin PDF",             "width": 40},
    {"name": "Date ajout",             "width": 15},
    {"name": "PMID",                   "width": 12},
    {"name": "DOI",                    "width": 30},
]

DEFAULT_COLS_REVIEW = [
    {"name": "Référence",              "width": 40},
    {"name": "Année",                  "width": 8},
    {"name": "Clé citable",            "width": 15},
    {"name": "BibTeX",                 "width": 30},
    {"name": "Type",                   "width": 20},
    {"name": "Objectif de la revue",   "width": 45},
    {"name": "Corpus couvert",         "width": 35},
    {"name": "Nb articles inclus",     "width": 15},
    {"name": "Période couverte",       "width": 20},
    {"name": "Thèmes principaux",      "width": 45},
    {"name": "Consensus identifiés",   "width": 40},
    {"name": "Débats / Controverses",  "width": 40},
    {"name": "Limites identifiées",    "width": 35},
    {"name": "Taille d'effet globale", "width": 18},
    {"name": "Hétérogénéité I²",      "width": 15},
    {"name": "Take Home Message",      "width": 40},
    {"name": "Domaines",               "width": 20},
    {"name": "Lu",                     "width": 8},
    {"name": "PDF disponible",         "width": 15},
    {"name": "Chemin PDF",             "width": 40},
    {"name": "Date ajout",             "width": 15},
    {"name": "PMID",                   "width": 12},
    {"name": "DOI",                    "width": 30},
]

def configure_excel_columns():
    """Configure les champs Excel — affiche les défauts et permet de les modifier."""
    print_step("8", "Champs du fichier Excel")
    print("""
  Science Torch utilise deux types de fiches :
    • Expérimental / Méta-analyse
    • Revue de littérature

  Chaque type a ses propres colonnes. Vous pouvez utiliser les colonnes
  par défaut ou les personnaliser (ajouter / supprimer des champs).
    """)

    use_defaults = ask_bool("Utiliser les colonnes par défaut ?", True)
    if use_defaults:
        print(f"  {GREEN}✓ Colonnes par défaut conservées{RESET}")
        return {
            "experimental": DEFAULT_COLS_EXPERIMENTAL,
            "review":       DEFAULT_COLS_REVIEW,
        }

    # Personnalisation articles expérimentaux
    print(f"\n  {CYAN}── Colonnes pour articles expérimentaux ──{RESET}")
    print("  Colonnes actuelles :")
    for i, col in enumerate(DEFAULT_COLS_EXPERIMENTAL, 1):
        print(f"    {i:2}. {col['name']}")

    exp_cols = _customize_columns(DEFAULT_COLS_EXPERIMENTAL)

    # Personnalisation revues
    print(f"\n  {CYAN}── Colonnes pour revues de littérature ──{RESET}")
    print("  Colonnes actuelles :")
    for i, col in enumerate(DEFAULT_COLS_REVIEW, 1):
        print(f"    {i:2}. {col['name']}")

    rev_cols = _customize_columns(DEFAULT_COLS_REVIEW)

    return {
        "experimental": exp_cols,
        "review":       rev_cols,
    }

def _customize_columns(defaults: list) -> list:
    """Permet d'ajouter ou supprimer des colonnes."""
    cols = list(defaults)

    # Supprimer des colonnes
    to_remove = ask("Numéros des colonnes à supprimer (ex: 3,7,12) ou ENTRÉE pour passer", "")
    if to_remove.strip():
        try:
            indices = [int(x.strip()) - 1 for x in to_remove.split(",")]
            cols = [c for i, c in enumerate(cols) if i not in indices]
            print(f"  {GREEN}✓ {len(indices)} colonne(s) supprimée(s){RESET}")
        except ValueError:
            print(f"  {YELLOW}Format invalide — aucune suppression{RESET}")

    # Ajouter des colonnes
    print("  Ajouter des colonnes (tapez ENTRÉE sans rien pour terminer) :")
    while True:
        new_col = ask("  Nom de la nouvelle colonne", "").strip()
        if not new_col:
            break
        width = ask(f"  Largeur de la colonne '{new_col}' (défaut: 30)", "30")
        try:
            cols.append({"name": new_col, "width": int(width)})
            print(f"  {GREEN}✓ Colonne '{new_col}' ajoutée{RESET}")
        except ValueError:
            cols.append({"name": new_col, "width": 30})

    print(f"  {GREEN}✓ {len(cols)} colonne(s) configurée(s){RESET}")
    return cols

# ── Sauvegarde config ────────────────────────────────────────────────────────
def save_config(config, config_path):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n  {GREEN}✓ Configuration sauvegardée dans {config_path}{RESET}")

# ── Installation des dépendances Python ──────────────────────────────────────
def install_requirements():
    print_step("9", "Installation des dépendances Python")
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
    language = configure_language()
    print(f"\n  {t('welcome')}")
    print(f"  {t('edit_later')}\n")

    if not check_dependencies():
        print(f"\n  {YELLOW}{t('continue_anyway')} {RESET}")
        if not ask_bool(t("continue_q"), False):
            sys.exit(1)

    paths     = configure_paths()
    domains   = configure_domains()
    combos    = configure_combinations(domains)
    ollama    = configure_ollama()
    zotero    = configure_zotero()
    scheduler = configure_scheduler()
    pubmed    = configure_pubmed()
    excel_columns = configure_excel_columns()

    config = {
        "version":      "1.0.0",
        "language":     language,
        "paths":        paths,
        "domains":      domains,
        "combinations": combos,
        "ollama":       ollama,
        "zotero":       zotero,
        "scheduler":    scheduler,
        "pubmed":       pubmed,
        "excel_columns": excel_columns,
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
