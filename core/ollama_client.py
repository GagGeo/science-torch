"""
core/ollama_client.py — Interface Ollama pour l'extraction structurée d'articles
Utilise un LLM local (mistral, llama3, etc.) pour analyser les abstracts.
"""
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import json
import requests
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Prompts ───────────────────────────────────────────────────────────────────

PROMPT_EXPERIMENTAL = """Tu es un assistant de recherche scientifique expert en neurosciences cognitives.
Analyse cet abstract d'article scientifique et extrais les informations suivantes en JSON.
Réponds UNIQUEMENT avec du JSON valide, sans texte avant ou après.

Abstract :
\"\"\"
{abstract}
\"\"\"

Format JSON attendu :
{{
  "hypotheses": "Les hypothèses principales de l'étude (1-3 phrases)",
  "population": "Description générale de la population étudiée",
  "n_per_group": "Nombre de participants par groupe (ex: 'HC=30, MCI=25')",
  "group_type": "Type de groupes (ex: 'Contrôles sains, patients MCI')",
  "inclusion_criteria": "Critères d'inclusion/exclusion principaux",
  "methods": "Outils et méthodes utilisés",
  "results": "Résultats principaux (2-4 phrases)",
  "effect_size": "Taille d'effet si mentionnée (Cohen's d, eta², etc.), sinon vide",
  "conclusion": "Conclusion des auteurs (1-2 phrases)",
  "take_home_message": "Message principal à retenir (1 phrase simple)",
  "article_type_confidence": "experimental ou review"
}}"""

PROMPT_REVIEW = """Tu es un assistant de recherche scientifique expert en neurosciences cognitives.
Analyse cet abstract de revue de littérature et extrais les informations suivantes en JSON.
Réponds UNIQUEMENT avec du JSON valide, sans texte avant ou après.

Abstract :
\"\"\"
{abstract}
\"\"\"

Format JSON attendu :
{{
  "review_objective": "Quelle question la revue cherche-t-elle à répondre ? (1-2 phrases)",
  "corpus": "Description du corpus (bases de données, période, critères de sélection)",
  "n_articles": "Nombre d'articles inclus si mentionné, sinon vide",
  "period_covered": "Période temporelle couverte si mentionnée, sinon vide",
  "main_themes": "Les 3-5 grands thèmes organisateurs de la revue",
  "consensus": "Points de consensus identifiés dans la littérature",
  "debates": "Débats, controverses ou questions ouvertes identifiés",
  "limitations": "Limites identifiées par les auteurs ou dans la littérature",
  "global_effect_size": "Taille d'effet globale si méta-analyse (ex: d=0.7), sinon vide",
  "heterogeneity": "I² ou autre mesure d'hétérogénéité si méta-analyse, sinon vide",
  "take_home_message": "Message principal à retenir (1 phrase simple)",
  "article_type_confidence": "review"
}}"""

PROMPT_CLASSIFY_DOMAINS = """Tu es un assistant de recherche scientifique.
Analyse ce titre et cet abstract et détermine à quels domaines de recherche ils appartiennent.

Titre : {title}
Abstract : {abstract}

Domaines disponibles :
{domains_list}

Réponds UNIQUEMENT avec du JSON valide :
{{
  "domains": ["CODE1", "CODE2"],
  "confidence": "high/medium/low",
  "rationale": "Brève justification (1 phrase)"
}}

Sélectionne TOUS les domaines pertinents (minimum 1, maximum tous si vraiment pertinents).
"""


class OllamaClient:
    """Client pour Ollama — LLM local gratuit."""

    def __init__(self, config: dict):
        cfg = config.get("ollama", {})
        self.model    = cfg.get("model", "mistral")
        self.base_url = cfg.get("base_url", "http://localhost:11434")
        self.timeout  = 60  # Les LLMs locaux peuvent être lents

    def _is_available(self) -> bool:
        """Vérifie qu'Ollama tourne."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def _generate(self, prompt: str) -> Optional[str]:
        """Envoie un prompt à Ollama et retourne la réponse brute."""
        if not self._is_available():
            logger.warning("Ollama non disponible — analyse LLM ignorée")
            return None

        payload = {
            "model":  self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,   # Faible pour des réponses structurées
                "num_predict": 1024,
            }
        }
        try:
            r = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"Erreur Ollama : {e}")
            return None

    def _parse_json_response(self, raw: str) -> Optional[dict]:
        """Parse la réponse JSON d'Ollama (robuste aux préambules)."""
        if not raw:
            return None
        # Cherche le premier { et le dernier }
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            logger.warning("Pas de JSON trouvé dans la réponse Ollama")
            return None
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError as e:
            logger.warning(f"JSON invalide dans réponse Ollama : {e}")
            return None

    # ── Analyse d'un article expérimental ────────────────────────────────────
    def analyze_experimental(self, abstract: str) -> dict:
        """Extrait les infos structurées d'un article expérimental."""
        prompt = PROMPT_EXPERIMENTAL.format(abstract=abstract[:1500])
        raw    = self._generate(prompt)
        result = self._parse_json_response(raw)

        if result:
            logger.info("Ollama — analyse expérimentale réussie")
            return result

        # Fallback vide si Ollama indisponible
        return {
            "hypotheses":             "",
            "population":             "",
            "n_per_group":            "",
            "group_type":             "",
            "inclusion_criteria":     "",
            "methods":                "",
            "results":                "",
            "effect_size":            "",
            "conclusion":             "",
            "take_home_message":      "",
            "article_type_confidence":"experimental"
        }

    # ── Analyse d'une revue de littérature ───────────────────────────────────
    def analyze_review(self, abstract: str) -> dict:
        """Extrait les infos structurées d'une revue de littérature."""
        prompt = PROMPT_REVIEW.format(abstract=abstract[:1500])
        raw    = self._generate(prompt)
        result = self._parse_json_response(raw)

        if result:
            logger.info("Ollama — analyse revue réussie")
            return result

        return {
            "review_objective":       "",
            "corpus":                 "",
            "n_articles":             "",
            "period_covered":         "",
            "main_themes":            "",
            "consensus":              "",
            "debates":                "",
            "limitations":            "",
            "global_effect_size":     "",
            "heterogeneity":          "",
            "take_home_message":      "",
            "article_type_confidence":"review"
        }

    # ── Classification par domaine ────────────────────────────────────────────
    def classify_domains(self, title: str, abstract: str, domains: list[dict]) -> list[str]:
        """
        Détermine à quels domaines appartient un article.
        Retourne la liste des codes de domaines (ex: ['ME', 'MA']).
        """
        domains_list = "\n".join(
            f"- {d['short']} : {d['name']} (mots-clés: {', '.join(d['keywords'][:3])})"
            for d in domains
        )
        prompt = PROMPT_CLASSIFY_DOMAINS.format(
            title=title,
            abstract=abstract[:1500],
            domains_list=domains_list
        )
        raw    = self._generate(prompt)
        result = self._parse_json_response(raw)

        if result and "domains" in result:
            valid_codes = {d["short"] for d in domains}
            classified  = [d for d in result["domains"] if d in valid_codes]
            if classified:
                logger.info(f"Domaines classifiés : {classified}")
                return classified

        # Fallback : tous les domaines (sera revu manuellement)
        logger.warning("Classification Ollama échouée — domaines non assignés")
        return []

    # ── Analyse complète d'un article ────────────────────────────────────────
    def analyze_article(self, article: dict, domains: list[dict]) -> dict:
        """
        Analyse complète d'un article :
        - Extraction structurée selon le type
        - Classification par domaine
        Retourne l'article enrichi.
        """
        abstract = article.get("abstract", "")
        if not abstract:
            logger.warning(f"Pas d'abstract pour PMID {article.get('pmid', '?')}")
            return article

        article_type = article.get("article_type", "experimental")

        # Extraction structurée
        if article_type == "review":
            analysis = self.analyze_review(abstract)
        else:
            analysis = self.analyze_experimental(abstract)

        article["analysis"] = analysis

        # Classification par domaine
        article["domains"] = self.classify_domains(
            article.get("title", ""),
            abstract,
            domains
        )

        return article

    # ── Génération du résumé hebdomadaire ────────────────────────────────────
    def generate_weekly_summary(self, articles: list[dict], week_str: str) -> str:
        """Génère un résumé hebdomadaire narratif à partir des articles."""
        if not articles:
            return f"# Résumé hebdomadaire — {week_str}\n\nAucun nouvel article cette semaine."

        articles_text = ""
        for i, art in enumerate(articles[:20], 1):  # Max 20 articles
            analysis = art.get("analysis", {})
            thm = analysis.get("take_home_message", art.get("abstract", "")[:200])
            domains = ", ".join(art.get("domains", []))
            articles_text += (
                f"\n{i}. [{domains}] {art['authors'].split(',')[0]} et al. "
                f"({art['year']}) — {art['title'][:100]}\n"
                f"   → {thm}\n"
            )

        prompt = f"""Tu es un assistant de recherche scientifique.
Voici les articles scientifiques publiés cette semaine ({week_str}) dans les domaines
de la mémoire épisodique, la conscience/métacognition et la maladie d'Alzheimer.

Articles :
{articles_text}

Génère un résumé hebdomadaire en français, structuré et professionnel, incluant :
1. Un paragraphe d'introduction (tendances générales de la semaine)
2. Les faits saillants par domaine
3. Un paragraphe de conclusion (perspectives)

Longueur : 300-500 mots. Ton scientifique mais accessible."""

        raw = self._generate(prompt)
        if raw:
            return f"# Résumé hebdomadaire — {week_str}\n\n{raw}"
        return f"# Résumé hebdomadaire — {week_str}\n\n{articles_text}"
