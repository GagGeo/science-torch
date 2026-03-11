"""
core/pubmed.py — Moteur de recherche PubMed
Recherche automatique, récupération des métadonnées, téléchargement PDFs open access.
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PMC_OA_BASE = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"
UNPAYWALL   = "https://api.unpaywall.org/v2/"


class PubMedClient:
    """Client pour l'API PubMed (NCBI E-utilities)."""

    def __init__(self, config: dict):
        self.email       = config["pubmed"].get("email", "")
        self.max_results = config["pubmed"].get("max_results", 50)
        self.pdfs_auto   = Path(config["paths"]["pdfs_auto"])
        self.session     = requests.Session()
        self.session.headers.update({"User-Agent": "VeilleScientifique/1.0"})

    # ── Paramètres de base ────────────────────────────────────────────────────
    def _base_params(self):
        params = {"tool": "VeilleScientifique", "retmode": "json"}
        if self.email:
            params["email"] = self.email
        return params

    def _throttle(self):
        """Respecte la limite de 3 req/s de NCBI."""
        time.sleep(0.34)

    # ── Construction de la requête PubMed ────────────────────────────────────
    def build_query(self, keywords: list[str], days_back: int = 7) -> str:
        """
        Construit une requête PubMed à partir d'une liste de mots-clés.
        Filtre sur les N derniers jours.
        """
        date_end   = datetime.now()
        date_start = date_end - timedelta(days=days_back)
        date_filter = (
            f"{date_start.strftime('%Y/%m/%d')}:{date_end.strftime('%Y/%m/%d')}[dp]"
        )
        kw_query = " OR ".join(f'"{kw}"[tiab]' for kw in keywords)
        return f"({kw_query}) AND {date_filter}"

    # ── Recherche : récupération des PMIDs ───────────────────────────────────
    def search(self, query: str) -> list[str]:
        """Retourne la liste des PMIDs correspondant à la requête."""
        params = self._base_params()
        params.update({
            "db":         "pubmed",
            "term":       query,
            "retmax":     self.max_results,
            "sort":       "pub date",
            "usehistory": "y",
        })
        try:
            r = self.session.get(EUTILS_BASE + "esearch.fcgi", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            logger.info(f"PubMed — {len(pmids)} résultat(s) pour : {query[:80]}…")
            self._throttle()
            return pmids
        except Exception as e:
            logger.error(f"Erreur recherche PubMed : {e}")
            return []

    # ── Récupération des métadonnées ─────────────────────────────────────────
    def fetch_details(self, pmids: list[str]) -> list[dict]:
        """Récupère les métadonnées complètes pour une liste de PMIDs."""
        if not pmids:
            return []

        params = self._base_params()
        params.update({
            "db":      "pubmed",
            "id":      ",".join(pmids),
            "retmode": "xml",
        })
        try:
            r = self.session.get(EUTILS_BASE + "efetch.fcgi", params=params, timeout=60)
            r.raise_for_status()
            self._throttle()
            return self._parse_xml(r.text)
        except Exception as e:
            logger.error(f"Erreur fetch détails : {e}")
            return []

    # ── Parsing XML PubMed ────────────────────────────────────────────────────
    def _parse_xml(self, xml_text: str) -> list[dict]:
        """Parse le XML PubMed et retourne une liste de dicts structurés."""
        articles = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"Erreur parsing XML : {e}")
            return []

        for article in root.findall(".//PubmedArticle"):
            try:
                art = self._parse_article(article)
                if art:
                    articles.append(art)
            except Exception as e:
                logger.warning(f"Erreur parsing article : {e}")
                continue

        return articles

    def _parse_article(self, node) -> Optional[dict]:
        """Parse un nœud PubmedArticle."""
        # PMID
        pmid_node = node.find(".//PMID")
        pmid = pmid_node.text if pmid_node is not None else ""

        # Titre
        title_node = node.find(".//ArticleTitle")
        title = "".join(title_node.itertext()) if title_node is not None else ""

        # Abstract
        abstract_parts = node.findall(".//AbstractText")
        abstract = " ".join("".join(p.itertext()) for p in abstract_parts)

        # Auteurs
        authors = []
        for author in node.findall(".//Author"):
            last  = author.findtext("LastName", "")
            first = author.findtext("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())
        authors_str = ", ".join(authors) if authors else "Auteurs inconnus"

        # Journal
        journal = node.findtext(".//Journal/Title", "")
        if not journal:
            journal = node.findtext(".//MedlineTA", "")

        # Année
        year = (
            node.findtext(".//PubDate/Year")
            or node.findtext(".//PubDate/MedlineDate", "")[:4]
            or ""
        )

        # Volume / Numéro / Pages
        volume = node.findtext(".//Volume", "")
        issue  = node.findtext(".//Issue", "")
        pages  = node.findtext(".//MedlinePgn", "")

        # DOI
        doi = ""
        for id_node in node.findall(".//ArticleId"):
            if id_node.get("IdType") == "doi":
                doi = id_node.text or ""
                break

        # PMC ID (pour open access)
        pmc_id = ""
        for id_node in node.findall(".//ArticleId"):
            if id_node.get("IdType") == "pmc":
                pmc_id = id_node.text or ""
                break

        # Publication type
        pub_types = [pt.text for pt in node.findall(".//PublicationType") if pt.text]

        # Type d'article (expérimental ou revue)
        article_type = self._classify_article_type(pub_types, title, abstract)

        # Clé citable
        first_author_last = authors[0].split()[0] if authors else "Unknown"
        cite_key = f"@{first_author_last}{year}"

        # Référence formatée
        vol_issue = f"{volume}({issue})" if volume and issue else volume or ""
        reference = f"{authors_str} ({year}). {title}. {journal}"
        if vol_issue:
            reference += f", {vol_issue}"
        if pages:
            reference += f", {pages}"
        if doi:
            reference += f". https://doi.org/{doi}"

        # BibTeX
        bibtex = self._build_bibtex(
            cite_key.lstrip("@"), first_author_last, authors, year,
            title, journal, volume, issue, pages, doi
        )

        return {
            "pmid":         pmid,
            "pmc_id":       pmc_id,
            "doi":          doi,
            "title":        title,
            "authors":      authors_str,
            "journal":      journal,
            "year":         year,
            "abstract":     abstract,
            "pub_types":    pub_types,
            "article_type": article_type,
            "cite_key":     cite_key,
            "reference":    reference,
            "bibtex":       bibtex,
            "pdf_path":     "",
            "pdf_available": False,
        }

    def _classify_article_type(self, pub_types: list, title: str, abstract: str) -> str:
        """Classifie l'article comme expérimental ou revue."""
        review_types = {
            "Review", "Systematic Review", "Meta-Analysis",
            "Literature Review", "Narrative Review"
        }
        if any(pt in review_types for pt in pub_types):
            return "review"

        review_keywords = [
            "systematic review", "meta-analysis", "literature review",
            "narrative review", "scoping review", "revue systématique",
            "méta-analyse"
        ]
        text_lower = (title + " " + abstract[:200]).lower()
        if any(kw in text_lower for kw in review_keywords):
            return "review"

        return "experimental"

    def _build_bibtex(self, key, first_author, authors, year, title,
                      journal, volume, issue, pages, doi) -> str:
        """Génère une entrée BibTeX."""
        author_bib = " and ".join(authors[:6])
        if len(authors) > 6:
            author_bib += " and others"

        fields = [
            f"  author  = {{{author_bib}}}",
            f"  title   = {{{title}}}",
            f"  journal = {{{journal}}}",
            f"  year    = {{{year}}}",
        ]
        if volume:
            fields.append(f"  volume  = {{{volume}}}")
        if issue:
            fields.append(f"  number  = {{{issue}}}")
        if pages:
            fields.append(f"  pages   = {{{pages}}}")
        if doi:
            fields.append(f"  doi     = {{{doi}}}")

        inner = ",\n".join(fields)
        return f"@article{{{key}{year},\n{inner}\n}}"

    # ── Téléchargement PDF open access ───────────────────────────────────────
    def try_download_pdf(self, article: dict) -> bool:
        """
        Tente de télécharger le PDF via PubMed Central ou Unpaywall.
        Retourne True si succès.
        """
        pmid   = article.get("pmid", "")
        pmc_id = article.get("pmc_id", "")
        doi    = article.get("doi", "")

        # Nom de fichier basé sur la clé citable
        safe_key = article["cite_key"].lstrip("@").replace("/", "_")
        pdf_path = self.pdfs_auto / f"{safe_key}.pdf"

        # 1. PubMed Central (open access garanti)
        if pmc_id:
            if self._download_pmc(pmc_id, pdf_path):
                article["pdf_path"]      = str(pdf_path)
                article["pdf_available"] = True
                return True

        # 2. Unpaywall (open access via DOI)
        if doi and self.email:
            if self._download_unpaywall(doi, pdf_path):
                article["pdf_path"]      = str(pdf_path)
                article["pdf_available"] = True
                return True

        logger.info(f"PDF non disponible en open access pour PMID {pmid}")
        return False

    def _download_pmc(self, pmc_id: str, dest: Path) -> bool:
        """Télécharge via PubMed Central OA."""
        # Récupère le lien FTP/HTTPS du PDF
        params = {
            "verb":           "GetRecord",
            "identifier":     f"oai:pubmedcentral.nih.gov:{pmc_id.replace('PMC', '')}",
            "metadataPrefix": "pmc",
        }
        try:
            r = self.session.get(PMC_OA_BASE, params=params, timeout=30)
            self._throttle()
            # Cherche un lien PDF dans la réponse OAI
            if "pdf" in r.text.lower():
                pdf_url = self._extract_pdf_url_from_oai(r.text, pmc_id)
                if pdf_url:
                    return self._save_pdf(pdf_url, dest)
        except Exception as e:
            logger.debug(f"PMC OAI échoué pour {pmc_id} : {e}")

        # Fallback : lien direct PMC
        direct_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
        return self._save_pdf(direct_url, dest)

    def _extract_pdf_url_from_oai(self, xml_text: str, pmc_id: str) -> Optional[str]:
        """Extrait l'URL du PDF depuis la réponse OAI-PMH."""
        try:
            root = ET.fromstring(xml_text)
            for elem in root.iter():
                if elem.text and elem.text.strip().endswith(".pdf"):
                    return elem.text.strip()
        except Exception:
            pass
        return None

    def _download_unpaywall(self, doi: str, dest: Path) -> bool:
        """Télécharge via Unpaywall si open access."""
        try:
            url = f"{UNPAYWALL}{doi}?email={self.email}"
            r   = self.session.get(url, timeout=15)
            self._throttle()
            data = r.json()
            oa_url = data.get("best_oa_location", {})
            if oa_url:
                pdf_url = oa_url.get("url_for_pdf") or oa_url.get("url")
                if pdf_url:
                    return self._save_pdf(pdf_url, dest)
        except Exception as e:
            logger.debug(f"Unpaywall échoué pour DOI {doi} : {e}")
        return False

    def _save_pdf(self, url: str, dest: Path) -> bool:
        """Télécharge et sauvegarde un PDF depuis une URL."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 VeilleScientifique/1.0"}
            r = self.session.get(url, headers=headers, timeout=60, stream=True)
            if r.status_code == 200 and "pdf" in r.headers.get("content-type", "").lower():
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"PDF téléchargé : {dest.name}")
                return True
        except Exception as e:
            logger.debug(f"Échec téléchargement PDF ({url}) : {e}")
        return False

    # ── Recherche complète pour un domaine ───────────────────────────────────
    def search_domain(self, domain: dict, days_back: int = 7) -> list[dict]:
        """
        Recherche complète pour un domaine :
        retourne la liste d'articles enrichis avec tentative de téléchargement PDF.
        """
        query = self.build_query(domain["keywords"], days_back)
        pmids = self.search(query)
        if not pmids:
            return []

        articles = self.fetch_details(pmids)

        for art in articles:
            self.try_download_pdf(art)

        return articles
