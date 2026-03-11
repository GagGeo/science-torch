"""
core/pdf_manager.py — Gestion des PDFs (import manuel + analyse)
Traite les PDFs déposés manuellement et en extrait les métadonnées.
Utilise pypdf (100% Python pur, compatible Python 3.14+).
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import re
import shutil
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Import pypdf (100% Python pur, compatible Python 3.14+)
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    logger.warning("pypdf non disponible — extraction PDF désactivée")


class PDFManager:
    """Gestion des fichiers PDF : déplacement, extraction de texte."""

    def __init__(self, config: dict):
        self.pdfs_manual = Path(config["paths"]["pdfs_manual"])
        self.pdfs_auto   = Path(config["paths"]["pdfs_auto"])
        self.pdfs_manual.mkdir(parents=True, exist_ok=True)

    # ── Import d'un PDF déposé manuellement ──────────────────────────────────
    def import_pdf(self, source_path: str) -> dict:
        """
        Importe un PDF déposé par l'utilisateur.
        Retourne un dict avec les métadonnées extraites.
        """
        source = Path(source_path)
        if not source.exists() or source.suffix.lower() != ".pdf":
            logger.error(f"Fichier PDF invalide : {source_path}")
            return {}

        # Extraire le texte
        text = self.extract_text(source)
        if not text:
            logger.warning(f"PDF sans texte extractible : {source.name}")

        # Tenter d'extraire les métadonnées de base
        metadata = self.extract_metadata(source, text)

        # Déplacer dans le dossier manuel
        dest = self.pdfs_manual / source.name
        if dest.exists():
            dest = self.pdfs_manual / f"{source.stem}_1{source.suffix}"
        shutil.copy2(source, dest)
        metadata["pdf_path"]      = str(dest)
        metadata["pdf_available"] = True
        metadata["text"]          = text

        logger.info(f"PDF importé : {dest.name}")
        return metadata

    # ── Extraction du texte ───────────────────────────────────────────────────
    def extract_text(self, pdf_path: Path, max_pages: int = 20) -> str:
        """Extrait le texte brut d'un PDF via pypdf."""
        if not HAS_PYPDF:
            return ""
        try:
            reader = PdfReader(str(pdf_path))
            pages  = min(len(reader.pages), max_pages)
            texts  = []
            for i in range(pages):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    texts.append(page_text)
            return "\n".join(texts)
        except Exception as e:
            logger.error(f"Erreur extraction texte PDF : {e}")
            return ""

    # ── Extraction des métadonnées ────────────────────────────────────────────
    def extract_metadata(self, pdf_path: Path, text: str) -> dict:
        """
        Tente d'extraire les métadonnées d'un PDF :
        DOI, PMID, titre, auteurs, année.
        """
        metadata = {
            "pmid":    "",
            "doi":     "",
            "title":   "",
            "authors": "",
            "year":    "",
            "journal": "",
            "abstract":"",
        }

        # Métadonnées embarquées dans le PDF via pypdf
        if HAS_PYPDF:
            try:
                reader = PdfReader(str(pdf_path))
                info   = reader.metadata
                if info:
                    if info.title:
                        metadata["title"] = info.title
                    if info.author:
                        metadata["authors"] = info.author
            except Exception:
                pass

        if text:
            # DOI
            doi_match = re.search(r'\b(10\.\d{4,}/[^\s"\'<>]+)', text[:3000])
            if doi_match:
                metadata["doi"] = doi_match.group(1).rstrip(".")

            # PMID
            pmid_match = re.search(r'PMID[:\s]+(\d{6,})', text[:3000], re.IGNORECASE)
            if pmid_match:
                metadata["pmid"] = pmid_match.group(1)

            # Année
            year_match = re.search(r'\b(19[9]\d|20[0-3]\d)\b', text[:500])
            if year_match:
                metadata["year"] = year_match.group(1)

            # Abstract
            abstract_match = re.search(
                r'(?:Abstract|Résumé|ABSTRACT)[:\s\n]+(.*?)(?:\n\n|\Z)',
                text[:5000],
                re.DOTALL | re.IGNORECASE
            )
            if abstract_match:
                metadata["abstract"] = abstract_match.group(1).strip()[:3000]

        return metadata

    # ── Complétion depuis PubMed ──────────────────────────────────────────────
    def enrich_from_pubmed(self, metadata: dict, pubmed_client) -> dict:
        """
        Si on a un DOI ou PMID extrait du PDF,
        complète les métadonnées depuis PubMed.
        """
        pmid = metadata.get("pmid", "")
        doi  = metadata.get("doi", "")

        if pmid:
            articles = pubmed_client.fetch_details([pmid])
            if articles:
                pdf_path = metadata.get("pdf_path", "")
                metadata.update(articles[0])
                metadata["pdf_path"]      = pdf_path
                metadata["pdf_available"] = True
                return metadata

        if doi:
            query = f'"{doi}"[aid]'
            pmids = pubmed_client.search(query)
            if pmids:
                articles = pubmed_client.fetch_details(pmids[:1])
                if articles:
                    pdf_path = metadata.get("pdf_path", "")
                    metadata.update(articles[0])
                    metadata["pdf_path"]      = pdf_path
                    metadata["pdf_available"] = True
                    return metadata

        logger.info("PDF — métadonnées complétées depuis le texte uniquement")
        return metadata
