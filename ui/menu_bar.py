"""
ui/menu_bar.py — Application barre de menu macOS
Icône discrète dans la barre de menu avec toutes les fonctionnalités.
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path

try:
    import rumps
    HAS_RUMPS = True
except ImportError:
    HAS_RUMPS = False

from utils.logger import get_logger
from core.scheduler import WeeklyScheduler
from core.pdf_manager import PDFManager
from core.pubmed import PubMedClient
from core.ollama_client import OllamaClient
from core.excel_manager import ExcelManager
from core.zotero_client import ZoteroClient

logger = get_logger(__name__)


class VeilleApp(rumps.App if HAS_RUMPS else object):
    """Application barre de menu macOS pour la veille scientifique."""

    def __init__(self, config: dict):
        if not HAS_RUMPS:
            raise ImportError("rumps non installé. Lancez : pip install rumps")

        super().__init__(
            name="Science Torch",
            title="🔬",
            quit_button="Quitter"
        )

        self.config    = config
        self.scheduler = WeeklyScheduler(config, on_complete=self._on_search_complete)
        self.pdf_mgr   = PDFManager(config)
        self.pubmed    = PubMedClient(config)
        self.ollama    = OllamaClient(config)
        self.excel     = ExcelManager(config)
        self.zotero    = ZoteroClient(config)

        self.excel_path = Path(config["paths"]["excel"])
        self._build_menu()

    def _build_menu(self):
        """Construit le menu de la barre de statut."""
        self.menu = [
            rumps.MenuItem("🔍 Lancer une recherche maintenant",
                           callback=self.run_search_now),
            rumps.MenuItem("📥 Ajouter un PDF manuellement",
                           callback=self.open_pdf_picker),
            None,  # Séparateur
            rumps.MenuItem("📊 Ouvrir le fichier Excel",
                           callback=self.open_excel),
            rumps.MenuItem("📋 Voir le dernier résumé",
                           callback=self.open_last_summary),
            None,
            rumps.MenuItem("📚 Ouvrir Zotero",
                           callback=self.open_zotero),
            None,
            rumps.MenuItem("⚙️  Paramètres",
                           callback=self.open_settings),
            rumps.MenuItem("📁 Ouvrir le dossier PDFs",
                           callback=self.open_pdfs_folder),
        ]

    # ── Actions du menu ───────────────────────────────────────────────────────

    @rumps.clicked("🔍 Lancer une recherche maintenant")
    def run_search_now(self, _):
        """Lance la recherche PubMed immédiatement en arrière-plan."""
        self.title = "⏳"
        rumps.notification(
            title="Science Torch",
            subtitle="Recherche en cours…",
            message="PubMed est interrogé pour vos domaines."
        )
        thread = threading.Thread(target=self._search_worker, daemon=True)
        thread.start()

    def _search_worker(self):
        """Worker thread pour la recherche (ne bloque pas l'UI)."""
        try:
            result = self.scheduler.run_weekly_search()
            self.title = "🔬"
        except Exception as e:
            logger.error(f"Erreur recherche : {e}")
            self.title = "🔬"
            rumps.notification(
                title="Science Torch",
                subtitle="Erreur",
                message=f"La recherche a échoué : {str(e)[:80]}"
            )

    def _on_search_complete(self, result: dict):
        """Callback appelé quand la recherche se termine."""
        n   = result.get("new_articles", 0)
        msg = f"{n} nouvel(s) article(s) ajouté(s)." if n > 0 else "Aucun nouvel article cette semaine."
        if self.config.get("scheduler", {}).get("notifications", True):
            rumps.notification(
                title="Science Torch — Recherche terminée",
                subtitle=result.get("week", ""),
                message=msg
            )

    @rumps.clicked("📥 Ajouter un PDF manuellement")
    def open_pdf_picker(self, _):
        """Ouvre un sélecteur de fichier macOS pour choisir un PDF."""
        script = """
        tell application "Finder"
            activate
        end tell
        set theFile to choose file with prompt "Sélectionnez un article PDF" \\
            of type {"pdf"} \\
            with invisibles false
        return POSIX path of theFile
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                pdf_path = result.stdout.strip()
                if pdf_path:
                    self._process_pdf(pdf_path)
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logger.error(f"Erreur sélecteur PDF : {e}")

    def _process_pdf(self, pdf_path: str):
        """Traite un PDF importé manuellement."""
        self.title = "⏳"
        rumps.notification(
            title="Science Torch",
            subtitle="Traitement du PDF…",
            message=Path(pdf_path).name
        )

        def worker():
            try:
                # Extraction métadonnées du PDF
                metadata = self.pdf_mgr.import_pdf(pdf_path)
                if not metadata:
                    self._notify_error("PDF invalide ou non lisible")
                    return

                # Enrichissement depuis PubMed si DOI/PMID trouvé
                metadata = self.pdf_mgr.enrich_from_pubmed(metadata, self.pubmed)

                # Analyse Ollama
                domains = self.config.get("domains", [])
                if metadata.get("abstract"):
                    metadata = self.ollama.analyze_article(metadata, domains)
                else:
                    # Demander à l'utilisateur via une fenêtre de dialogue
                    self._ask_manual_metadata(metadata)

                # Ajout Excel
                self.excel.load_or_create()
                added = self.excel.add_article(metadata)

                # Zotero
                if added:
                    self.zotero.add_article(metadata)

                self.title = "🔬"
                msg = "Article ajouté avec succès !" if added else "Article déjà présent dans la base."
                rumps.notification(
                    title="Science Torch",
                    subtitle="PDF importé",
                    message=msg
                )
            except Exception as e:
                logger.error(f"Erreur traitement PDF : {e}")
                self._notify_error(str(e)[:100])
                self.title = "🔬"

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _ask_manual_metadata(self, metadata: dict):
        """Affiche une boîte de dialogue pour saisir les métadonnées manquantes."""
        current_title = metadata.get("title", "")
        script = f"""
        tell application "System Events"
            set dialogResult to display dialog ¬
                "Titre de l'article (vérifier/corriger) :" & return & return & ¬
                "Le PDF a été importé mais certaines métadonnées sont manquantes." ¬
                default answer "{current_title}" ¬
                with title "Science Torch — Métadonnées" ¬
                buttons {{"Annuler", "Confirmer"}} ¬
                default button "Confirmer"
            return text returned of dialogResult
        end tell
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                metadata["title"] = result.stdout.strip()
        except Exception:
            pass

    @rumps.clicked("📊 Ouvrir le fichier Excel")
    def open_excel(self, _):
        """Ouvre le fichier Excel dans l'application par défaut."""
        if self.excel_path.exists():
            subprocess.run(["open", str(self.excel_path)])
        else:
            rumps.notification(
                title="Science Torch",
                subtitle="Fichier introuvable",
                message="Lancez d'abord une recherche pour créer le fichier Excel."
            )

    @rumps.clicked("📋 Voir le dernier résumé")
    def open_last_summary(self, _):
        """Ouvre le dernier résumé hebdomadaire."""
        summary = self.scheduler.get_last_summary_path()
        if summary and summary.exists():
            subprocess.run(["open", str(summary)])
        else:
            rumps.notification(
                title="Science Torch",
                subtitle="Aucun résumé",
                message="Lancez une recherche pour générer le premier résumé."
            )

    @rumps.clicked("📚 Ouvrir Zotero")
    def open_zotero(self, _):
        """Ouvre Zotero."""
        subprocess.run(["open", "-a", "Zotero"])

    @rumps.clicked("📁 Ouvrir le dossier PDFs")
    def open_pdfs_folder(self, _):
        """Ouvre le dossier des PDFs dans le Finder."""
        pdfs_path = Path(self.config["paths"]["pdfs"])
        subprocess.run(["open", str(pdfs_path)])

    @rumps.clicked("⚙️  Paramètres")
    def open_settings(self, _):
        """Ouvre le fichier de configuration dans l'éditeur par défaut."""
        config_path = Path(__file__).parent.parent / "config.json"
        if config_path.exists():
            subprocess.run(["open", str(config_path)])
        else:
            rumps.notification(
                title="Science Torch",
                subtitle="Config introuvable",
                message="Lancez setup.py pour configurer l'application."
            )

    def _notify_error(self, message: str):
        """Affiche une notification d'erreur."""
        self.title = "🔬"
        rumps.notification(
            title="Science Torch — Erreur",
            subtitle="Une erreur est survenue",
            message=message
        )

    # ── Démarrage ──────────────────────────────────────────────────────────────
    def run_app(self):
        """Démarre l'application et le scheduler."""
        self.scheduler.start()
        logger.info("Application démarrée dans la barre de menu")
        self.run()
