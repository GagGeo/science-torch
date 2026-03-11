"""
utils/i18n.py — Internationalisation (FR/EN)
Usage : from utils.i18n import t
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
from pathlib import Path

# Langue par défaut
_lang = "en"

STRINGS = {
    # Setup wizard
    "app_name":            {"fr": "Veille Scientifique", "en": "Science Watch"},
    "config_title":        {"fr": "Veille Scientifique — Configuration", "en": "Science Watch — Configuration"},
    "step":                {"fr": "Étape", "en": "Step"},
    "welcome":             {"fr": "Bienvenue ! Ce script va configurer votre outil de veille scientifique.",
                            "en": "Welcome! This script will configure your Science Watch tool."},
    "edit_later":          {"fr": "Vous pourrez modifier ces paramètres à tout moment dans config.json",
                            "en": "You can modify these settings at any time in config.json"},
    "check_prereqs":       {"fr": "Vérification des prérequis", "en": "Checking prerequisites"},
    "detected":            {"fr": "détecté", "en": "detected"},
    "not_found":           {"fr": "non trouvé", "en": "not found"},
    "storage_folders":     {"fr": "Dossiers de stockage", "en": "Storage folders"},
    "root_folder":         {"fr": "Dossier racine du projet", "en": "Project root folder"},
    "folders_created":     {"fr": "Dossiers créés dans", "en": "Folders created in"},
    "domains_title":       {"fr": "Domaines de recherche et mots-clés PubMed",
                            "en": "Research domains and PubMed keywords"},
    "domain_instructions": {"fr": "Entrez vos domaines un par un.",
                            "en": "Enter your domains one by one."},
    "domain_n":            {"fr": "Domaine", "en": "Domain"},
    "abbreviation":        {"fr": "Abréviation (ex: ME)", "en": "Abbreviation (e.g. ME)"},
    "full_name":           {"fr": "Nom complet (ex: Mémoire Épisodique)", "en": "Full name (e.g. Episodic Memory)"},
    "keywords":            {"fr": "Mots-clés PubMed (séparés par des virgules)",
                            "en": "PubMed keywords (comma-separated)"},
    "press_enter_done":    {"fr": "Tapez ENTRÉE sans rien écrire pour terminer.",
                            "en": "Press ENTER without typing to finish."},
    "domain_added":        {"fr": "Domaine ajouté avec", "en": "Domain added with"},
    "keywords_label":      {"fr": "mot(s)-clé(s)", "en": "keyword(s)"},
    "at_least_one":        {"fr": "Au moins un domaine est requis.", "en": "At least one domain is required."},
    "combinations_title":  {"fr": "Onglets de combinaisons inter-domaines",
                            "en": "Cross-domain combination tabs"},
    "activate_tab":        {"fr": "Activer l'onglet", "en": "Activate tab"},
    "combos_activated":    {"fr": "combinaison(s) activée(s)", "en": "combination(s) activated"},
    "ollama_title":        {"fr": "Modèle Ollama (LLM local)", "en": "Ollama model (local LLM)"},
    "available_models":    {"fr": "Modèles disponibles", "en": "Available models"},
    "no_model":            {"fr": "Aucun modèle trouvé. Installer avec", "en": "No model found. Install with"},
    "model_to_use":        {"fr": "Modèle à utiliser", "en": "Model to use"},
    "zotero_title":        {"fr": "Intégration Zotero (optionnelle)", "en": "Zotero integration (optional)"},
    "enable_zotero":       {"fr": "Activer la synchronisation Zotero?", "en": "Enable Zotero sync?"},
    "zotero_port":         {"fr": "Port API locale Zotero", "en": "Zotero local API port"},
    "library_type":        {"fr": "Type de bibliothèque (user/group)", "en": "Library type (user/group)"},
    "collection_name":     {"fr": "Nom de la collection Zotero (laisser vide = racine)",
                            "en": "Zotero collection name (leave empty for root)"},
    "scheduler_title":     {"fr": "Planification de la recherche automatique",
                            "en": "Automatic search scheduling"},
    "search_day":          {"fr": "Jour de la recherche hebdomadaire", "en": "Day of weekly search"},
    "search_time":         {"fr": "Heure de lancement (format HH:MM)", "en": "Launch time (HH:MM format)"},
    "enable_notifs":       {"fr": "Activer les notifications macOS?", "en": "Enable macOS notifications?"},
    "pubmed_title":        {"fr": "Configuration PubMed", "en": "PubMed configuration"},
    "ncbi_email":          {"fr": "Votre email (pour l'API NCBI, optionnel)",
                            "en": "Your email (for NCBI API, optional)"},
    "max_results":         {"fr": "Nombre max d'articles par recherche hebdomadaire",
                            "en": "Max articles per weekly search"},
    "config_saved":        {"fr": "Configuration sauvegardée dans", "en": "Configuration saved to"},
    "install_deps":        {"fr": "Installer les dépendances Python maintenant?",
                            "en": "Install Python dependencies now?"},
    "deps_installed":      {"fr": "Dépendances installées", "en": "Dependencies installed"},
    "setup_done":          {"fr": "Configuration terminée !", "en": "Configuration complete!"},
    "launch_with":         {"fr": "Pour lancer l'application :", "en": "To launch the app:"},
    "icon_appears":        {"fr": "L'icône 🔬 apparaîtra dans votre barre de menu macOS.",
                            "en": "The 🔬 icon will appear in your macOS menu bar."},
    # Menu bar
    "menu_search":         {"fr": "🔍 Lancer une recherche maintenant", "en": "🔍 Run a search now"},
    "menu_add_pdf":        {"fr": "📥 Ajouter un PDF manuellement", "en": "📥 Add a PDF manually"},
    "menu_excel":          {"fr": "📊 Ouvrir le fichier Excel", "en": "📊 Open Excel file"},
    "menu_summary":        {"fr": "📋 Voir le dernier résumé", "en": "📋 View last summary"},
    "menu_zotero":         {"fr": "📚 Ouvrir Zotero", "en": "📚 Open Zotero"},
    "menu_settings":       {"fr": "⚙️  Paramètres", "en": "⚙️  Settings"},
    "menu_pdfs":           {"fr": "📁 Ouvrir le dossier PDFs", "en": "📁 Open PDFs folder"},
    "menu_quit":           {"fr": "Quitter", "en": "Quit"},
    "notif_searching":     {"fr": "Recherche en cours…", "en": "Search in progress…"},
    "notif_pubmed":        {"fr": "PubMed est interrogé pour vos domaines.",
                            "en": "PubMed is being searched for your domains."},
    "notif_error":         {"fr": "Erreur", "en": "Error"},
    "notif_failed":        {"fr": "La recherche a échoué", "en": "Search failed"},
    "notif_done":          {"fr": "Recherche terminée", "en": "Search complete"},
    "notif_new_articles":  {"fr": "nouveaux articles ajoutés", "en": "new article(s) added"},
    "notif_no_articles":   {"fr": "Aucun nouvel article cette semaine.", "en": "No new articles this week."},
    "notif_pdf_processing":{"fr": "Traitement du PDF…", "en": "Processing PDF…"},
    "notif_pdf_added":     {"fr": "Article ajouté avec succès !", "en": "Article added successfully!"},
    "notif_pdf_exists":    {"fr": "Article déjà présent dans la base.", "en": "Article already in the database."},
    "notif_pdf_imported":  {"fr": "PDF importé", "en": "PDF imported"},
    "notif_pdf_invalid":   {"fr": "PDF invalide ou non lisible", "en": "Invalid or unreadable PDF"},
    "notif_no_excel":      {"fr": "Lancez d'abord une recherche pour créer le fichier Excel.",
                            "en": "Run a search first to create the Excel file."},
    "notif_no_summary":    {"fr": "Lancez une recherche pour générer le premier résumé.",
                            "en": "Run a search to generate the first summary."},
    "select_pdf":          {"fr": "Sélectionnez un article PDF", "en": "Select a PDF article"},
}

def set_language(lang: str):
    """Définit la langue globale ('fr' ou 'en')."""
    global _lang
    if lang in ("fr", "en"):
        _lang = lang

def load_language_from_config():
    """Charge la langue depuis config.json."""
    try:
        config_paths = [
            Path.home() / "Documents" / "VeilleScientifique" / "config.json",
            Path(__file__).parent.parent / "config.json",
        ]
        for p in config_paths:
            if p.exists():
                with open(p) as f:
                    cfg = json.load(f)
                set_language(cfg.get("language", "en"))
                return
    except Exception:
        pass

def t(key: str) -> str:
    """Retourne la chaîne traduite pour la langue courante."""
    entry = STRINGS.get(key, {})
    return entry.get(_lang, entry.get("en", key))

# Charger la langue au démarrage
load_language_from_config()
