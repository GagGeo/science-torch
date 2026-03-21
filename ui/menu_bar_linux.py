"""
ui/menu_bar_linux.py — Application barre de menu Linux
Utilise pystray pour l'icône système (system tray).
Même fonctionnalités que la version macOS.
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import threading
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

from utils.logger import get_logger
from core.scheduler import WeeklyScheduler
from core.pdf_manager import PDFManager
from core.pubmed import PubMedClient
from core.ollama_client import OllamaClient
from core.excel_manager import ExcelManager
from core.zotero_client import ZoteroClient
from ui.platform_utils import (
    open_path, open_app, pick_pdf_file,
    ask_text_dialog, send_notification
)

logger = get_logger(__name__)


def _create_icon_image(size: int = 64) -> "Image":
    """Crée une icône simple 🔬 en pixels pour la barre système."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Fond bleu foncé
    draw.ellipse([4, 4, size-4, size-4], fill="#2C3E50")
    # Cercle intérieur bleu
    draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], fill="#3498DB")
    return img


class VeilleAppLinux:
    """Application barre système Linux pour Science Torch."""

    def __init__(self, config: dict):
        if not HAS_PYSTRAY:
            raise ImportError(
                "pystray ou Pillow non installé.\n"
                "Lancez : pip install pystray pillow"
            )

        self.config     = config
        self.scheduler  = WeeklyScheduler(
            config,
            on_complete=self._on_analysis_complete,
            on_phase1_complete=self._on_phase1_complete
        )
        self.pdf_mgr    = PDFManager(config)
        self.pubmed     = PubMedClient(config)
        self.ollama     = OllamaClient(config)
        self.excel      = ExcelManager(config)
        self.zotero     = ZoteroClient(config)
        self.excel_path = Path(config["paths"]["excel"])
        self.icon       = None

    def _build_menu(self) -> "pystray.Menu":
        """Construit le menu système."""
        return pystray.Menu(
            pystray.MenuItem("🔍 Run a search now",   self._run_search_now),
            pystray.MenuItem("📥 Add a PDF manually", self._open_pdf_picker),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📊 Open Excel file",    self._open_excel),
            pystray.MenuItem("📋 View last summary",  self._open_last_summary),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📚 Open Zotero",        self._open_zotero),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️  Settings",          self._open_settings),
            pystray.MenuItem("📁 Open PDFs folder",   self._open_pdfs_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit",                  self._quit),
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _run_search_now(self, icon, item):
        send_notification(
            "Science Torch",
            "Search in progress…",
            "PubMed is being searched for your domains."
        )
        thread = threading.Thread(target=self._search_worker, daemon=True)
        thread.start()

    def _search_worker(self):
        try:
            self.scheduler.run_weekly_search()
        except Exception as e:
            logger.error(f"Erreur recherche : {e}")
            send_notification("Science Torch — Error", "Search failed", str(e)[:80])

    def _on_phase1_complete(self, result: dict):
        n = result.get("new_articles", 0)
        if n > 0:
            send_notification(
                "Science Torch — Articles found",
                f"{n} new article(s) added to Excel",
                "Analysis running in background… 🔄"
            )
        else:
            send_notification("Science Torch", "Search complete", "No new articles this week.")

    def _on_analysis_complete(self, result: dict):
        n = result.get("total_analyzed", 0)
        if self.config.get("scheduler", {}).get("notifications", True):
            send_notification(
                "Science Torch — Analysis complete",
                f"{n} article(s) fully analyzed",
                "Excel updated. Summary generated. ✅"
            )

    def _open_pdf_picker(self, icon, item):
        pdf_path = pick_pdf_file("Select a PDF article")
        if pdf_path:
            thread = threading.Thread(
                target=self._process_pdf, args=(pdf_path,), daemon=True
            )
            thread.start()

    def _process_pdf(self, pdf_path: str):
        send_notification("Science Torch", "Processing PDF…", Path(pdf_path).name)
        try:
            metadata = self.pdf_mgr.import_pdf(pdf_path)
            if not metadata:
                send_notification("Science Torch — Error", "Invalid or unreadable PDF", "")
                return

            metadata = self.pdf_mgr.enrich_from_pubmed(metadata, self.pubmed)
            domains  = self.config.get("domains", [])

            if metadata.get("abstract"):
                metadata = self.ollama.analyze_article(metadata, domains)
            else:
                title = ask_text_dialog(
                    "Science Torch — Metadata",
                    "Article title (check/correct):\n\nPDF imported but some metadata is missing.",
                    metadata.get("title", "")
                )
                if title:
                    metadata["title"] = title

            self.excel.load_or_create()
            added = self.excel.add_article(metadata)
            if added:
                self.zotero.add_article_silent(metadata)

            msg = "Article added successfully!" if added else "Article already in database."
            send_notification("Science Torch", "PDF imported", msg)

        except Exception as e:
            logger.error(f"Erreur traitement PDF : {e}")
            send_notification("Science Torch — Error", "Processing failed", str(e)[:80])

    def _open_excel(self, icon, item):
        if self.excel_path.exists():
            open_path(str(self.excel_path))
        else:
            send_notification("Science Torch", "File not found",
                              "Run a search first to create the Excel file.")

    def _open_last_summary(self, icon, item):
        summary = self.scheduler.get_last_summary_path()
        if summary and summary.exists():
            open_path(str(summary))
        else:
            send_notification("Science Torch", "No summary",
                              "Run a search to generate the first summary.")

    def _open_zotero(self, icon, item):
        open_app("zotero")

    def _open_pdfs_folder(self, icon, item):
        open_path(self.config["paths"]["pdfs"])

    def _open_settings(self, icon, item):
        config_paths = [
            Path.home() / "Documents" / "ScienceTorch" / "config.json",
            Path(__file__).parent.parent / "config.json",
        ]
        for p in config_paths:
            if p.exists():
                open_path(str(p))
                return
        send_notification("Science Torch", "Config not found",
                          "Run setup.py to configure the app.")

    def _quit(self, icon, item):
        self.scheduler.stop()
        icon.stop()

    # ── Démarrage ─────────────────────────────────────────────────────────────
    def run_app(self):
        """Démarre l'application dans la barre système."""
        self.scheduler.start()
        logger.info("Application démarrée dans la barre système (Linux)")

        img        = _create_icon_image()
        self.icon  = pystray.Icon(
            name="science-torch",
            icon=img,
            title="Science Torch",
            menu=self._build_menu()
        )
        self.icon.run()
