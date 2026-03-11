"""
core/scheduler.py — Tâche hebdomadaire automatique
Lance la recherche PubMed chaque lundi matin et génère le résumé.
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import json
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


class WeeklyScheduler:
    """Gestion de la tâche hebdomadaire de veille."""

    def __init__(self, config: dict, on_complete: Optional[Callable] = None):
        self.config      = config
        self.on_complete = on_complete  # Callback pour la notification macOS
        self.pubmed      = PubMedClient(config)
        self.ollama      = OllamaClient(config)
        self.excel       = ExcelManager(config)
        self.zotero      = ZoteroClient(config)
        self.summaries_path = Path(config["paths"]["summaries"])
        self.summaries_path.mkdir(parents=True, exist_ok=True)
        self._thread     = None
        self._running    = False

    # ── Planification ─────────────────────────────────────────────────────────
    def start(self):
        """Démarre le scheduler en arrière-plan."""
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

        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Arrête le scheduler."""
        self._running = False
        schedule.clear()
        logger.info("Scheduler arrêté")

    def _loop(self):
        """Boucle de vérification (toutes les 60 secondes)."""
        while self._running:
            schedule.run_pending()
            time.sleep(60)

    # ── Recherche hebdomadaire ────────────────────────────────────────────────
    def run_weekly_search(self, days_back: int = 7) -> dict:
        """
        Exécute la recherche hebdomadaire complète :
        1. Recherche PubMed pour chaque domaine
        2. Analyse Ollama de chaque article
        3. Ajout dans Excel
        4. Synchronisation Zotero
        5. Génération du résumé
        6. Notification macOS
        """
        logger.info("=" * 60)
        logger.info("DÉMARRAGE RECHERCHE HEBDOMADAIRE")
        logger.info("=" * 60)

        self.excel.load_or_create()
        domains = self.config.get("domains", [])

        all_articles  = []
        new_articles  = []
        already_known = []

        # ── Recherche par domaine ──────────────────────────────────────────
        for domain in domains:
            logger.info(f"Recherche domaine : {domain['short']} — {domain['name']}")
            articles = self.pubmed.search_domain(domain, days_back=days_back)
            logger.info(f"  → {len(articles)} article(s) trouvé(s)")

            for article in articles:
                # Analyse Ollama
                article = self.ollama.analyze_article(article, domains)

                # Ajout dans Excel (retourne False si doublon)
                is_new = self.excel.add_article(article)
                if is_new:
                    new_articles.append(article)
                    # Synchronisation Zotero
                    self.zotero.add_article(article)
                else:
                    already_known.append(article)

                all_articles.append(article)

        # ── Résumé hebdomadaire ────────────────────────────────────────────
        week_str = datetime.now().strftime("Semaine du %d %B %Y")
        summary  = self._generate_summary(new_articles, week_str)
        summary_path = self._save_summary(summary, week_str)

        result = {
            "total_found":    len(all_articles),
            "new_articles":   len(new_articles),
            "already_known":  len(already_known),
            "summary_path":   str(summary_path),
            "week":           week_str,
        }

        logger.info(f"Recherche terminée : {len(new_articles)} nouveaux articles")
        logger.info("=" * 60)

        # ── Callback (notification macOS) ──────────────────────────────────
        if self.on_complete:
            self.on_complete(result)

        return result

    # ── Génération du résumé ──────────────────────────────────────────────────
    def _generate_summary(self, articles: list, week_str: str) -> str:
        """Génère le résumé hebdomadaire via Ollama."""
        if not articles:
            return f"# Résumé hebdomadaire — {week_str}\n\nAucun nouvel article cette semaine.\n"

        # Résumé via Ollama
        summary = self.ollama.generate_weekly_summary(articles, week_str)

        # Ajout du tableau récapitulatif
        summary += "\n\n---\n\n## 📋 Liste des nouveaux articles\n\n"
        for i, art in enumerate(articles, 1):
            analysis = art.get("analysis", {})
            thm = analysis.get("take_home_message", "")
            domains = " | ".join(art.get("domains", []))
            pdf_icon = "📄" if art.get("pdf_available") else "🔒"
            summary += (
                f"### {i}. {art['authors'].split(',')[0]} et al. ({art['year']})\n"
                f"**{art['title']}**  \n"
                f"*{art['journal']}*  \n"
                f"Domaines : `{domains}` | {pdf_icon} PDF  \n"
                f"Clé : `{art.get('cite_key', '')}` | PMID : {art.get('pmid', '')}  \n"
            )
            if thm:
                summary += f"> 💡 {thm}\n"
            summary += "\n"

        return summary

    def _save_summary(self, content: str, week_str: str) -> Path:
        """Sauvegarde le résumé hebdomadaire en Markdown."""
        filename = f"resume_{datetime.now().strftime('%Y_%m_%d')}.md"
        path = self.summaries_path / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Résumé sauvegardé : {path}")
        return path

    # ── Dernière recherche ────────────────────────────────────────────────────
    def get_last_summary_path(self) -> Optional[Path]:
        """Retourne le chemin du dernier résumé généré."""
        summaries = sorted(self.summaries_path.glob("resume_*.md"), reverse=True)
        return summaries[0] if summaries else None
