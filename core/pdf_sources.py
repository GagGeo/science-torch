"""
core/pdf_sources.py — Sources multiples pour maximiser l'accès aux PDFs
APIs intégrées (ordre de tentative) :
  1. PubMed Central (PMC)     — articles NIH-funded
  2. Europe PMC               — articles européens + archive ouverte
  3. Unpaywall                — meilleur lien OA via DOI
  4. Semantic Scholar         — métadonnées + liens PDFs alternatifs
  5. OpenAlex                 — grande couverture, liens OA
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# ── URLs des APIs ─────────────────────────────────────────────────────────────
PMC_OA_BASE        = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"
PMC_DIRECT         = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
EUROPE_PMC_BASE    = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UNPAYWALL_BASE     = "https://api.unpaywall.org/v2/"
SEMANTIC_BASE      = "https://api.semanticscholar.org/graph/v1/paper/"
OPENALEX_BASE      = "https://api.openalex.org/works/"

# ── Délai entre requêtes (ms) pour respecter les limites ─────────────────────
THROTTLE = 1.0  # secondes


class PDFSourceManager:
    """
    Gestionnaire de sources PDF multiples.
    Essaie chaque source dans l'ordre jusqu'à trouver un PDF.
    """

    def __init__(self, config: dict):
        self.config    = config
        self.pdfs_auto = Path(config["paths"]["pdfs_auto"])
        self.pdfs_auto.mkdir(parents=True, exist_ok=True)
        self.email     = config.get("pubmed", {}).get("email", "")
        self.session   = requests.Session()
        self.session.headers.update({
            "User-Agent": f"ScienceTorch/1.0 (mailto:{self.email})" if self.email
                          else "ScienceTorch/1.0"
        })

    def try_download_pdf(self, article: dict) -> bool:
        """
        Tente de télécharger le PDF via toutes les sources disponibles.
        Retourne True dès qu'un PDF est trouvé et sauvegardé.
        Met à jour article['pdf_path'] et article['pdf_available'].
        """
        pmid   = article.get("pmid", "")
        pmc_id = article.get("pmc_id", "")
        doi    = article.get("doi", "")
        title  = article.get("title", "")

        safe_key = article.get("cite_key", pmid).lstrip("@").replace("/", "_")
        pdf_path = self.pdfs_auto / f"{safe_key}.pdf"

        # Ne pas retélécharger si déjà présent
        if pdf_path.exists():
            article["pdf_path"]      = str(pdf_path)
            article["pdf_available"] = True
            return True

        sources_tried = []

        # ── 1. PubMed Central ─────────────────────────────────────────────────
        if pmc_id:
            sources_tried.append("PMC")
            if self._download_pmc(pmc_id, pdf_path):
                self._mark_found(article, pdf_path)
                logger.info(f"PDF trouvé via PMC : {safe_key}")
                return True
            time.sleep(THROTTLE)

        # ── 2. Europe PMC ─────────────────────────────────────────────────────
        if pmid or pmc_id:
            sources_tried.append("EuropePMC")
            if self._download_europe_pmc(pmid, pmc_id, pdf_path):
                self._mark_found(article, pdf_path)
                logger.info(f"PDF trouvé via Europe PMC : {safe_key}")
                return True
            time.sleep(THROTTLE)

        # ── 3. Unpaywall ──────────────────────────────────────────────────────
        if doi:
            sources_tried.append("Unpaywall")
            if self._download_unpaywall(doi, pdf_path):
                self._mark_found(article, pdf_path)
                logger.info(f"PDF trouvé via Unpaywall : {safe_key}")
                return True
            time.sleep(THROTTLE)

        # ── 4. Semantic Scholar ───────────────────────────────────────────────
        if doi or pmid:
            sources_tried.append("SemanticScholar")
            if self._download_semantic_scholar(doi, pmid, pdf_path):
                self._mark_found(article, pdf_path)
                logger.info(f"PDF trouvé via Semantic Scholar : {safe_key}")
                return True
            time.sleep(THROTTLE)

        # ── 5. OpenAlex ───────────────────────────────────────────────────────
        if doi:
            sources_tried.append("OpenAlex")
            if self._download_openalex(doi, pdf_path):
                self._mark_found(article, pdf_path)
                logger.info(f"PDF trouvé via OpenAlex : {safe_key}")
                return True
            time.sleep(THROTTLE)

        logger.info(f"PDF non disponible (PMID {pmid}) — sources essayées : {', '.join(sources_tried)}")
        return False

    def _mark_found(self, article: dict, pdf_path: Path):
        article["pdf_path"]      = str(pdf_path)
        article["pdf_available"] = True

    # ── Source 1 : PubMed Central ─────────────────────────────────────────────
    def _download_pmc(self, pmc_id: str, dest: Path) -> bool:
        """Télécharge via PubMed Central OA."""
        # Tentative OAI-PMH
        try:
            params = {
                "verb":           "GetRecord",
                "identifier":     f"oai:pubmedcentral.nih.gov:{pmc_id.replace('PMC', '')}",
                "metadataPrefix": "pmc",
            }
            r = self.session.get(PMC_OA_BASE, params=params, timeout=20)
            if r.status_code == 200 and "pdf" in r.text.lower():
                pdf_url = self._extract_url_from_oai(r.text)
                if pdf_url and self._save_pdf(pdf_url, dest):
                    return True
        except Exception as e:
            logger.debug(f"PMC OAI échoué : {e}")

        # Fallback : lien direct PMC
        direct_url = PMC_DIRECT.format(pmc_id=pmc_id)
        return self._save_pdf(direct_url, dest)

    def _extract_url_from_oai(self, xml_text: str) -> Optional[str]:
        try:
            root = ET.fromstring(xml_text)
            for elem in root.iter():
                if elem.text and elem.text.strip().endswith(".pdf"):
                    return elem.text.strip()
        except Exception:
            pass
        return None

    # ── Source 2 : Europe PMC ────────────────────────────────────────────────
    def _download_europe_pmc(self, pmid: str, pmc_id: str, dest: Path) -> bool:
        """
        Télécharge via Europe PMC — couvre articles EU + archive ouverte.
        Supporte PMID et PMC ID.
        """
        try:
            # Chercher l'article dans Europe PMC
            search_id = pmc_id if pmc_id else f"MED:{pmid}"
            r = self.session.get(
                f"{EUROPE_PMC_BASE}/article/{search_id}/fullTextXML",
                timeout=20
            )
            if r.status_code == 200 and len(r.content) > 1000:
                # Chercher le lien PDF dans la réponse
                pdf_url = self._extract_europe_pmc_pdf_url(pmid, pmc_id)
                if pdf_url:
                    return self._save_pdf(pdf_url, dest)

            # Tentative directe via le endpoint PDF
            if pmc_id:
                pdf_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmc_id}&blobtype=pdf"
                return self._save_pdf(pdf_url, dest)

        except Exception as e:
            logger.debug(f"Europe PMC échoué : {e}")
        return False

    def _extract_europe_pmc_pdf_url(self, pmid: str, pmc_id: str) -> Optional[str]:
        """Cherche le lien PDF via l'API Europe PMC."""
        try:
            query = pmc_id if pmc_id else pmid
            source = "PMC" if pmc_id else "MED"
            r = self.session.get(
                f"{EUROPE_PMC_BASE}/search",
                params={
                    "query":      f"ext_id:{query} src:{source}",
                    "resultType": "core",
                    "format":     "json",
                    "pageSize":   1,
                },
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                results = data.get("resultList", {}).get("result", [])
                if results:
                    item = results[0]
                    # Chercher un lien PDF dans fullTextUrlList
                    for url_item in item.get("fullTextUrlList", {}).get("fullTextUrl", []):
                        if url_item.get("documentStyle") == "pdf":
                            return url_item.get("url")
        except Exception as e:
            logger.debug(f"Europe PMC URL extraction échouée : {e}")
        return None

    # ── Source 3 : Unpaywall ──────────────────────────────────────────────────
    def _download_unpaywall(self, doi: str, dest: Path) -> bool:
        """
        Télécharge via Unpaywall — meilleure source pour PDFs OA via DOI.
        Email requis pour l'API (recommandé, non bloquant).
        """
        try:
            email_param = self.email if self.email else "sciencetorch@example.com"
            r = self.session.get(
                f"{UNPAYWALL_BASE}{doi}",
                params={"email": email_param},
                timeout=15
            )
            if r.status_code != 200:
                return False

            data    = r.json()
            oa_loc  = data.get("best_oa_location") or {}
            pdf_url = oa_loc.get("url_for_pdf") or oa_loc.get("url")

            if not pdf_url:
                # Chercher dans toutes les locations OA
                for loc in data.get("oa_locations", []):
                    candidate = loc.get("url_for_pdf") or loc.get("url")
                    if candidate:
                        pdf_url = candidate
                        break

            if pdf_url:
                return self._save_pdf(pdf_url, dest)

        except Exception as e:
            logger.debug(f"Unpaywall échoué : {e}")
        return False

    # ── Source 4 : Semantic Scholar ───────────────────────────────────────────
    def _download_semantic_scholar(self, doi: str, pmid: str, dest: Path) -> bool:
        """
        Télécharge via Semantic Scholar — couvre beaucoup d'articles
        avec liens vers versions arXiv, preprints et PDFs institutionnels.
        """
        try:
            # Construire l'ID Semantic Scholar
            if doi:
                paper_id = f"DOI:{doi}"
            elif pmid:
                paper_id = f"PMID:{pmid}"
            else:
                return False

            r = self.session.get(
                f"{SEMANTIC_BASE}{paper_id}",
                params={"fields": "openAccessPdf,externalIds"},
                timeout=15
            )
            if r.status_code != 200:
                return False

            data    = r.json()
            oa_pdf  = data.get("openAccessPdf") or {}
            pdf_url = oa_pdf.get("url")

            if pdf_url:
                return self._save_pdf(pdf_url, dest)

        except Exception as e:
            logger.debug(f"Semantic Scholar échoué : {e}")
        return False

    # ── Source 5 : OpenAlex ───────────────────────────────────────────────────
    def _download_openalex(self, doi: str, dest: Path) -> bool:
        """
        Télécharge via OpenAlex — 250M+ articles, bonne couverture OA.
        """
        try:
            r = self.session.get(
                f"{OPENALEX_BASE}https://doi.org/{doi}",
                params={
                    "select": "open_access,best_oa_location",
                    "mailto": self.email or "sciencetorch@example.com",
                },
                timeout=15
            )
            if r.status_code != 200:
                return False

            data    = r.json()
            oa_loc  = data.get("best_oa_location") or {}
            pdf_url = oa_loc.get("pdf_url")

            if not pdf_url:
                # Chercher dans open_access
                oa = data.get("open_access", {})
                pdf_url = oa.get("oa_url")

            if pdf_url:
                return self._save_pdf(pdf_url, dest)

        except Exception as e:
            logger.debug(f"OpenAlex échoué : {e}")
        return False

    # ── Téléchargement générique ──────────────────────────────────────────────
    def _save_pdf(self, url: str, dest: Path) -> bool:
        """Télécharge et sauvegarde un PDF depuis une URL."""
        try:
            r = self.session.get(url, timeout=60, stream=True, allow_redirects=True)
            content_type = r.headers.get("content-type", "").lower()

            if r.status_code == 200 and ("pdf" in content_type or url.endswith(".pdf")):
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                # Vérifier que c'est bien un PDF (magic bytes)
                with open(dest, "rb") as f:
                    header = f.read(4)
                if header == b"%PDF":
                    logger.info(f"PDF sauvegardé : {dest.name}")
                    return True
                else:
                    dest.unlink(missing_ok=True)
                    logger.debug(f"Fichier téléchargé non valide (pas un PDF) : {url}")

        except Exception as e:
            logger.debug(f"Échec téléchargement ({url[:60]}…) : {e}")
            if dest.exists():
                dest.unlink(missing_ok=True)
        return False

    def get_stats(self) -> dict:
        """Retourne des statistiques sur les PDFs téléchargés."""
        pdfs = list(self.pdfs_auto.glob("*.pdf"))
        total_size = sum(p.stat().st_size for p in pdfs)
        return {
            "count":      len(pdfs),
            "total_mb":   round(total_size / 1024 / 1024, 1),
            "folder":     str(self.pdfs_auto),
        }
