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
    """Application barre de menu macOS pour Science Torch."""

    def __init__(self, config: dict):
        if not HAS_RUMPS:
            raise ImportError("rumps non installé. Lancez : pip install rumps")

        super().__init__(
            name="Science Torch",
            title="🔬",
            quit_button="Quit"
        )

        self.config    = config
        self.scheduler = WeeklyScheduler(
            config,
            on_complete=self._on_analysis_complete,
            on_phase1_complete=self._on_phase1_complete
        )
        self.pdf_mgr   = PDFManager(config)
        self.pubmed    = PubMedClient(config)
        self.ollama    = OllamaClient(config)
        self.excel     = ExcelManager(config)
        self.zotero    = ZoteroClient(config)
        self.excel_path = Path(config["paths"]["excel"])
        self._build_menu()

    def _build_menu(self):
        self.menu = [
            rumps.MenuItem("🔍 Run a search now",        callback=self.run_search_now),
            rumps.MenuItem("📥 Add a PDF manually",      callback=self.open_pdf_picker),
            None,
            rumps.MenuItem("📊 Open Excel file",         callback=self.open_excel),
            rumps.MenuItem("📋 View last summary",        callback=self.open_last_summary),
            None,
            rumps.MenuItem("📚 Open Zotero",             callback=self.open_zotero),
            None,
            rumps.MenuItem("⚙️  Settings",               callback=self.open_settings),
            rumps.MenuItem("📁 Open PDFs folder",        callback=self.open_pdfs_folder),
        ]

    # ── Actions du menu ───────────────────────────────────────────────────────

    @rumps.clicked("🔍 Run a search now")
    def run_search_now(self, _):
        """Lance la recherche PubMed immédiatement en arrière-plan."""
        self.title = "⏳"
        rumps.notification(
            title="Science Torch",
            subtitle="Search in progress…",
            message="PubMed is being searched for your domains."
        )
        thread = threading.Thread(target=self._search_worker, daemon=True)
        thread.start()

    def _search_worker(self):
        """Worker thread pour la Phase 1 (ne bloque pas l'UI)."""
        try:
            self.scheduler.run_weekly_search()
        except Exception as e:
            logger.error(f"Erreur recherche : {e}")
            self.title = "🔬"
            rumps.notification(
                title="Science Torch",
                subtitle="Error",
                message=f"Search failed: {str(e)[:80]}"
            )

    def _on_phase1_complete(self, result: dict):
        """Notification après Phase 1 — articles dans Excel, analyse en cours."""
        self.title = "🔬"
        n = result.get("new_articles", 0)
        if n > 0:
            rumps.notification(
                title="Science Torch — Articles found",
                subtitle=f"{n} new article(s) added to Excel",
                message="Analysis running in background… 🔄"
            )
        else:
            rumps.notification(
                title="Science Torch",
                subtitle="Search complete",
                message="No new articles this week."
            )

    def _on_analysis_complete(self, result: dict):
        """Notification après Phase 2 — analyse Ollama terminée."""
        n = result.get("total_analyzed", 0)
        if self.config.get("scheduler", {}).get("notifications", True):
            rumps.notification(
                title="Science Torch — Analysis complete",
                subtitle=f"{n} article(s) fully analyzed",
                message="Excel updated. Summary generated. ✅"
            )

    # ── Import PDF ────────────────────────────────────────────────────────────

    @rumps.clicked("📥 Add a PDF manually")
    def open_pdf_picker(self, _):
        """Ouvre un sélecteur de fichier macOS pour choisir un PDF."""
        script = """
        tell application "Finder"
            activate
        end tell
        set theFile to choose file with prompt "Select a PDF article" \\
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
            subtitle="Processing PDF…",
            message=Path(pdf_path).name
        )

        def worker():
            try:
                metadata = self.pdf_mgr.import_pdf(pdf_path)
                if not metadata:
                    self._notify_error("Invalid or unreadable PDF")
                    return

                metadata = self.pdf_mgr.enrich_from_pubmed(metadata, self.pubmed)

                domains = self.config.get("domains", [])
                if metadata.get("abstract"):
                    metadata = self.ollama.analyze_article(metadata, domains)
                else:
                    self._ask_manual_metadata(metadata)

                self.excel.load_or_create()
                added = self.excel.add_article(metadata)

                if added:
                    self.zotero.add_article_silent(metadata)

                self.title = "🔬"
                msg = "Article added successfully!" if added else "Article already in database."
                rumps.notification(
                    title="Science Torch",
                    subtitle="PDF imported",
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
                "Article title (check/correct):" & return & return & ¬
                "PDF imported but some metadata is missing." ¬
                default answer "{current_title}" ¬
                with title "Science Torch — Metadata" ¬
                buttons {{"Cancel", "Confirm"}} ¬
                default button "Confirm"
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

    # ── Ouvertures ────────────────────────────────────────────────────────────

    @rumps.clicked("📊 Open Excel file")
    def open_excel(self, _):
        if self.excel_path.exists():
            subprocess.run(["open", str(self.excel_path)])
        else:
            rumps.notification(
                title="Science Torch",
                subtitle="File not found",
                message="Run a search first to create the Excel file."
            )

    @rumps.clicked("📋 View last summary")
    def open_last_summary(self, _):
        summary = self.scheduler.get_last_summary_path()
        if summary and summary.exists():
            subprocess.run(["open", str(summary)])
        else:
            rumps.notification(
                title="Science Torch",
                subtitle="No summary",
                message="Run a search to generate the first summary."
            )

    @rumps.clicked("📚 Open Zotero")
    def open_zotero(self, _):
        subprocess.run(["open", "-a", "Zotero"])

    @rumps.clicked("📁 Open PDFs folder")
    def open_pdfs_folder(self, _):
        pdfs_path = Path(self.config["paths"]["pdfs"])
        subprocess.run(["open", str(pdfs_path)])

    @rumps.clicked("⚙️  Settings")
    def open_settings(self, _):
        config_paths = [
            Path.home() / "Documents" / "ScienceTorch" / "config.json",
            Path(__file__).parent.parent / "config.json",
        ]
        for p in config_paths:
            if p.exists():
                subprocess.run(["open", str(p)])
                return
        rumps.notification(
            title="Science Torch",
            subtitle="Config not found",
            message="Run setup.py to configure the app."
        )

    def _notify_error(self, message: str):
        self.title = "🔬"
        rumps.notification(
            title="Science Torch — Error",
            subtitle="An error occurred",
            message=message
        )

    # ── Démarrage ──────────────────────────────────────────────────────────────
    def run_app(self):
        self.scheduler.start()
        logger.info("Application démarrée dans la barre de menu")
        self.run()
