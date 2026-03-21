"""
core/scheduler.py — Tâche hebdomadaire automatique
Pipeline en deux phases :
  Phase 1 (rapide) : PubMed → Excel (métadonnées uniquement)
  Phase 2 (fond)   : Ollama analyse chaque article + Zotero silencieux
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import schedule
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from utils.logger import get_logger
from core.pubmed import PubMedClient
from core.ollama_client import OllamaClient
from core.excel_manager import ExcelManager
from core.zotero_client import ZoteroClient

logger = get_logger(__name__)

# Pause entre chaque analyse Ollama pour ne pas saturer le CPU
OLLAMA_THROTTLE_SECONDS = 5


class WeeklyScheduler:
    """Gestion de la tâche hebdomadaire de veille."""

    def __init__(self, config: dict, on_complete: Optional[Callable] = None,
                 on_phase1_complete: Optional[Callable] = None):
        self.config             = config
        self.on_complete        = on_complete
        self.on_phase1_complete = on_phase1_complete
        self.pubmed             = PubMedClient(config)
        self.ollama             = OllamaClient(config)
        self.excel              = ExcelManager(config)
        self.zotero             = ZoteroClient(config)
        self.summaries_path     = Path(config["paths"]["summaries"])
        self.summaries_path.mkdir(parents=True, exist_ok=True)
        self._scheduler_thread  = None
        self._analysis_thread   = None
        self._running           = False
        self._analysis_queue    = []
        self._queue_lock        = threading.Lock()

    # ── Planification ─────────────────────────────────────────────────────────
    def start(self):
        sched_cfg = self.config.get("scheduler", {})
        day       = sched_cfg.get("day", "monday")
        time_str  = sched_cfg.get("time", "08:00")

        day_map = {
            "lundi": "monday", "mardi": "tuesday", "mercredi": "wednesday",
            "jeudi": "thursday", "vendredi": "friday",
            "samedi": "saturday", "dimanche": "sunday",
        }
        day_en = day_map.get(day.lower(), day.lower())
        getattr(schedule.every(), day_en).at(time_str).do(self.run_weekly_search)
        logger.info(f"Scheduler planifié : chaque {day} à {time_str}")

        self._running          = True
        self._scheduler_thread = threading.Thread(target=self._loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self):
        self._running = False
        schedule.clear()

    def _loop(self):
        while self._running:
            schedule.run_pending()
            time.sleep(60)

    # ── Phase 1 : PubMed → Excel (rapide) ────────────────────────────────────
    def run_weekly_search(self, days_back: int = 7) -> dict:
        """Phase 1 rapide : PubMed → Excel sans Ollama."""
        logger.info("=" * 60)
        logger.info("PHASE 1 — RECHERCHE PUBMED")
        logger.info("=" * 60)

        self.excel.load_or_create()
        domains      = self.config.get("domains", [])
        new_articles = []

        for domain in domains:
            logger.info(f"Recherche domaine : {domain['short']} — {domain['name']}")
            articles = self.pubmed.search_domain(domain, days_back=days_back)
            logger.info(f"  → {len(articles)} article(s) trouvé(s)")
            for article in articles:
                is_new = self.excel.add_article(article)
                if is_new:
                    new_articles.append(article)

        logger.info(f"Phase 1 terminée : {len(new_articles)} nouveaux articles dans Excel")

        result_phase1 = {"new_articles": len(new_articles)}
        if self.on_phase1_complete:
            self.on_phase1_complete(result_phase1)

        if new_articles:
            self._start_background_analysis(new_articles)

        return result_phase1

    # ── Phase 2 : Ollama en arrière-plan (basse priorité) ────────────────────
    def _start_background_analysis(self, articles: list):
        with self._queue_lock:
            self._analysis_queue = list(articles)

        self._analysis_thread = threading.Thread(
            target=self._analysis_worker,
            daemon=True,
            name="ollama-background"
        )
        self._analysis_thread.start()
        logger.info(f"Phase 2 démarrée — {len(articles)} articles à analyser")

    def _analysis_worker(self):
        """Worker basse priorité : pause entre chaque article."""
        logger.info("=" * 60)
        logger.info("PHASE 2 — ANALYSE OLLAMA (arrière-plan)")
        logger.info("=" * 60)

        domains  = self.config.get("domains", [])
        analyzed = []
        total    = len(self._analysis_queue)

        for i, article in enumerate(self._analysis_queue):
            if not self._running:
                break
            logger.info(f"Analyse {i+1}/{total} : {article.get('cite_key', '?')}")
            try:
                analyzed_article = self.ollama.analyze_article(article, domains)
                self.excel.load_or_create()
                self.excel.update_article_analysis(analyzed_article)
                # Zotero silencieux — API uniquement, sans ouvrir l'UI
                self.zotero.add_article_silent(analyzed_article)
                analyzed.append(analyzed_article)
            except Exception as e:
                logger.error(f"Erreur analyse {article.get('pmid', '?')}: {e}")

            # Pause pour ne pas saturer le CPU
            time.sleep(OLLAMA_THROTTLE_SECONDS)

        if analyzed:
            week_str     = datetime.now().strftime("Semaine du %d %B %Y")
            summary      = self._generate_summary(analyzed, week_str)
            summary_path = self._save_summary(summary, week_str)
            result = {
                "total_analyzed": len(analyzed),
                "summary_path":   str(summary_path),
                "week":           week_str,
            }
            logger.info(f"Phase 2 terminée : {len(analyzed)} articles analysés")
            if self.on_complete:
                self.on_complete(result)

    # ── Résumé ────────────────────────────────────────────────────────────────
    def _generate_summary(self, articles: list, week_str: str) -> str:
        lang = self.config.get("language", "en")
        if not articles:
            if lang == "fr":
                return f"# Résumé hebdomadaire — {week_str}\n\nAucun nouvel article cette semaine.\n"
            return f"# Weekly Summary — {week_str}\n\nNo new articles this week.\n"

        summary = self.ollama.generate_weekly_summary(articles, week_str)
        header  = "## 📋 Liste des nouveaux articles" if lang == "fr" else "## 📋 New Articles"
        summary += f"\n\n---\n\n{header}\n\n"

        for i, art in enumerate(articles, 1):
            analysis     = art.get("analysis", {})
            thm          = analysis.get("take_home_message", "")
            domains      = " | ".join(art.get("domains", []))
            pdf_icon     = "📄" if art.get("pdf_available") else "🔒"
            first_author = art.get("authors", "?").split(",")[0]
            summary += (
                f"### {i}. {first_author} et al. ({art.get('year', '?')})\n"
                f"**{art.get('title', '')}**  \n"
                f"*{art.get('journal', '')}*  \n"
                f"Domains: `{domains}` | {pdf_icon}  \n"
                f"Key: `{art.get('cite_key', '')}` | PMID: {art.get('pmid', '')}  \n"
            )
            if thm:
                summary += f"> 💡 {thm}\n"
            summary += "\n"
        return summary

    def _save_summary(self, content: str, week_str: str) -> Path:
        filename = f"summary_{datetime.now().strftime('%Y_%m_%d')}.md"
        path     = self.summaries_path / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Résumé sauvegardé : {path}")
        return path

    def get_last_summary_path(self) -> Optional[Path]:
        summaries = sorted(self.summaries_path.glob("summary_*.md"), reverse=True)
        if not summaries:
            summaries = sorted(self.summaries_path.glob("resume_*.md"), reverse=True)
        return summaries[0] if summaries else None
