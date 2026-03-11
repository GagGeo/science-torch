"""
core/zotero_client.py — Intégration Zotero via API locale
Synchronise automatiquement les articles avec Zotero + Better BibTeX.
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import json
import requests
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ZoteroClient:
    """Client pour l'API locale Zotero."""

    def __init__(self, config: dict):
        cfg = config.get("zotero", {})
        self.enabled      = cfg.get("enabled", False)
        self.base_url     = cfg.get("base_url", "http://localhost:23119")
        self.library_type = cfg.get("library_type", "user")
        self.collection   = cfg.get("collection", "")
        self.session      = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self._collection_key = None

    def _is_available(self) -> bool:
        """Vérifie que Zotero tourne avec l'API locale activée."""
        if not self.enabled:
            return False
        try:
            r = self.session.get(f"{self.base_url}/better-bibtex/cayw", timeout=2)
            return True  # Si on arrive ici, Zotero répond
        except Exception:
            try:
                r = self.session.get(f"{self.base_url}/", timeout=2)
                return True
            except Exception:
                return False

    def _get_collection_key(self) -> Optional[str]:
        """Récupère la clé de la collection Zotero cible."""
        if self._collection_key:
            return self._collection_key
        if not self.collection:
            return None

        try:
            r = self.session.get(
                f"{self.base_url}/zotero/collections",
                timeout=5
            )
            collections = r.json()
            for col in collections:
                if col.get("name") == self.collection:
                    self._collection_key = col.get("key")
                    return self._collection_key
        except Exception as e:
            logger.debug(f"Zotero — collection non trouvée : {e}")
        return None

    # ── Ajout d'un article ────────────────────────────────────────────────────
    def add_article(self, article: dict) -> Optional[str]:
        """
        Ajoute un article dans Zotero.
        Retourne la clé BibTeX générée par Better BibTeX.
        """
        if not self.enabled:
            return None

        if not self._is_available():
            logger.warning("Zotero non disponible — synchronisation ignorée")
            return None

        # Construction de l'item Zotero
        item = self._build_zotero_item(article)
        collection_key = self._get_collection_key()
        if collection_key:
            item["collections"] = [collection_key]

        try:
            # API Zotero locale (connector)
            r = self.session.post(
                f"{self.base_url}/connector/saveItems",
                json={"items": [item], "uri": ""},
                timeout=5
            )
            if r.status_code in (200, 201):
                logger.info(f"Zotero — article ajouté : {article.get('cite_key', '')}")
                # Attacher le PDF si disponible
                if article.get("pdf_available") and article.get("pdf_path"):
                    self._attach_pdf(article["pdf_path"])
                return article.get("cite_key", "")
            else:
                logger.warning(f"Zotero — réponse inattendue : {r.status_code}")
                # Fallback : import via BibTeX
                return self._import_bibtex(article)
        except Exception as e:
            logger.error(f"Zotero — erreur ajout : {e}")
            return self._import_bibtex(article)

    def _build_zotero_item(self, article: dict) -> dict:
        """Construit un item au format Zotero."""
        # Auteurs
        authors_raw = article.get("authors", "")
        creators = []
        for author_str in authors_raw.split(", "):
            parts = author_str.strip().split(" ")
            if len(parts) >= 2:
                creators.append({
                    "creatorType": "author",
                    "lastName":    parts[0],
                    "firstName":   " ".join(parts[1:])
                })
            elif parts:
                creators.append({
                    "creatorType": "author",
                    "name":        parts[0]
                })

        item_type = "journalArticle"
        pub_types = article.get("pub_types", [])
        if any(pt in pub_types for pt in ["Book", "Book Chapter"]):
            item_type = "bookSection"

        return {
            "itemType":          item_type,
            "title":             article.get("title", ""),
            "creators":          creators,
            "abstractNote":      article.get("abstract", ""),
            "publicationTitle":  article.get("journal", ""),
            "date":              article.get("year", ""),
            "DOI":               article.get("doi", ""),
            "extra":             f"PMID: {article.get('pmid', '')}",
            "tags":              [{"tag": d} for d in article.get("domains", [])],
            "accessDate":        "",
            "url":               f"https://pubmed.ncbi.nlm.nih.gov/{article.get('pmid', '')}/",
        }

    def _import_bibtex(self, article: dict) -> Optional[str]:
        """Importe un article via BibTeX (fallback)."""
        bibtex = article.get("bibtex", "")
        if not bibtex:
            return None

        try:
            r = self.session.post(
                f"{self.base_url}/connector/import",
                data=bibtex.encode("utf-8"),
                headers={"Content-Type": "application/x-bibtex"},
                timeout=5
            )
            if r.status_code in (200, 201):
                logger.info("Zotero — import BibTeX réussi")
                return article.get("cite_key", "")
        except Exception as e:
            logger.error(f"Zotero — erreur import BibTeX : {e}")
        return None

    def _attach_pdf(self, pdf_path: str):
        """Attache un PDF au dernier item ajouté dans Zotero."""
        try:
            path = Path(pdf_path)
            if not path.exists():
                return
            # L'API locale Zotero ne supporte pas directement l'attachement de fichiers
            # via le connector — on log pour info
            logger.info(f"PDF à attacher manuellement dans Zotero : {path.name}")
        except Exception as e:
            logger.debug(f"Attachement PDF Zotero : {e}")

    # ── Récupération de la clé BibTeX via Better BibTeX ──────────────────────
    def get_bibtex_key(self, pmid: str) -> Optional[str]:
        """
        Demande à Better BibTeX la clé citable d'un article via son PMID.
        """
        if not self.enabled or not self._is_available():
            return None
        try:
            r = self.session.get(
                f"{self.base_url}/better-bibtex/export/item",
                params={"translator": "biblatex", "pmid": pmid},
                timeout=5
            )
            if r.status_code == 200:
                bibtex_text = r.text
                # Extraire la clé du BibTeX retourné
                import re
                match = re.search(r"@\w+\{([^,]+),", bibtex_text)
                if match:
                    return f"@{match.group(1)}"
        except Exception as e:
            logger.debug(f"Better BibTeX clé non récupérée : {e}")
        return None
