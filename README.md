# 🔬 Science Torch — Automated Scientific Literature Monitor

*[Français ci-dessous](#français)*

---

## English

**Science Torch** is a free, privacy-first tool for researchers who want to stay up to date with scientific literature — without spending hours on PubMed every week.

### Features

- 🔍 **Automatic weekly PubMed search** across your research domains
- 🤖 **Local LLM analysis** via [Ollama](https://ollama.ai) — free, offline, private
- 📊 **Modular Excel database** with thematic tabs (experimental articles + literature reviews)
- 📚 **Zotero sync** with automatic BibTeX key generation
- 📥 **Manual PDF import** with drag-and-drop
- 📋 **Weekly Markdown summaries**
- 🖥️ **macOS menu bar app** — discreet, always running in the background
- 🔔 **macOS notifications** when new articles are found
- 📄 **Maximized PDF access** via 5 open-access sources (PMC, Europe PMC, Unpaywall, Semantic Scholar, OpenAlex)

### Platform support

| Platform | Status | Installer |
|---|---|---|
| macOS | ✅ Full support | `.app` + `.dmg` via `bash build.sh` |
| Linux | ✅ Full support | Run `python3 main.py` directly |
| Windows | ✅ Full support | `.exe` via `build_windows.bat` |

### How it works

1. You define your research domains and PubMed keywords
2. Every Monday morning, the app searches PubMed automatically
3. Articles are immediately added to your Excel file (**Phase 1** — fast, <1 min)
4. Each article is then analyzed by a local LLM in the background (**Phase 2** — silent, no slowdown)
5. A weekly summary report is generated
6. You receive macOS notifications at the end of each phase

### Choosing your Ollama model

Science Torch works with any model installed on your machine via Ollama. Two recommended options depending on your hardware:

| Model | Quality | GPU usage | Best for |
|---|---|---|---|
| `mistral` | ⭐⭐⭐⭐ | ~90% | Mac with dedicated GPU / Apple Silicon M2+ |
| `gemma3:1b` | ⭐⭐⭐ | ~30–40% | Older machines or if slowdowns are an issue |

To switch models, simply edit `config.json`:
```json
"ollama": { "model": "gemma3:1b" }
```

Any model available via `ollama list` can be used. Larger models (e.g. `llama3`, `mistral`) produce richer summaries; smaller models (`gemma3:1b`, `phi3:mini`) are faster and lighter.

### Requirements

- macOS
- Python 3.9+
- [Ollama](https://ollama.ai) with at least one model installed:
  - High quality: `ollama pull mistral`
  - Lightweight: `ollama pull gemma3:1b`
- [Zotero](https://zotero.org) + [Better BibTeX](https://retorque.re/zotero-better-bibtex/) (optional)

### Installation

**macOS / Linux:**
```bash
git clone https://github.com/GagGeo/science-torch.git
cd science-torch
bash install.sh   # installs dependencies + runs configuration wizard
bash build.sh     # creates Science Torch.app on your desktop (macOS)
```

**Windows:**
```
git clone https://github.com/GagGeo/science-torch.git
cd science-torch
build_windows.bat
```

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) (macOS/Linux) or [INSTALLATION_GUIDE_WINDOWS.md](INSTALLATION_GUIDE_WINDOWS.md) (Windows) for detailed instructions.

### Built with

- [PubMed E-utilities API](https://www.ncbi.nlm.nih.gov/home/develop/api/) — free, no key required
- [Ollama](https://ollama.ai) — local LLM inference
- [Unpaywall](https://unpaywall.org) — open access PDFs
- [Semantic Scholar API](https://api.semanticscholar.org) — additional PDF sources
- [OpenAlex](https://openalex.org) — large-scale open access coverage
- [Europe PMC](https://europepmc.org) — European research archive
- [rumps](https://github.com/jaredks/rumps) — macOS menu bar
- [openpyxl](https://openpyxl.readthedocs.io) — Excel generation
- [pyzotero](https://pyzotero.readthedocs.io) — Zotero integration
- [pypdf](https://pypdf.readthedocs.io) — PDF parsing

### License

Apache 2.0 — free to use, modify and distribute, with attribution and patent protection.

---

## Français

**Science Torch** est un outil gratuit et respectueux de la vie privée pour les chercheurs qui souhaitent assurer leur veille bibliographique sans passer des heures sur PubMed chaque semaine.

### Fonctionnalités

- 🔍 **Recherche PubMed hebdomadaire automatique** sur vos domaines de recherche
- 🤖 **Analyse par LLM local** via [Ollama](https://ollama.ai) — gratuit, hors ligne, privé
- 📊 **Fichier Excel modulaire** avec onglets thématiques (articles expérimentaux + revues de littérature)
- 📚 **Synchronisation Zotero** avec génération automatique des clés BibTeX
- 📥 **Import manuel de PDFs** par drag-and-drop
- 📋 **Résumés hebdomadaires** en Markdown
- 🖥️ **App barre de menu macOS** — discrète, tourne en arrière-plan
- 🔔 **Notifications macOS** à chaque nouveaux articles trouvés
- 📄 **Accès PDF maximisé** via 5 sources open access (PMC, Europe PMC, Unpaywall, Semantic Scholar, OpenAlex)

### Comment ça marche

1. Vous définissez vos domaines de recherche et mots-clés PubMed
2. Chaque lundi matin, l'app interroge PubMed automatiquement
3. Les articles sont immédiatement ajoutés à votre Excel (**Phase 1** — rapide, <1 min)
4. Chaque article est ensuite analysé par un LLM local en arrière-plan (**Phase 2** — silencieuse, sans ralentissement)
5. Un résumé hebdomadaire est généré
6. Vous recevez des notifications macOS à la fin de chaque phase

### Choisir votre modèle Ollama

Science Torch fonctionne avec n'importe quel modèle installé sur votre machine via Ollama. Deux options recommandées selon votre matériel :

| Modèle | Qualité | Utilisation GPU | Idéal pour |
|---|---|---|---|
| `mistral` | ⭐⭐⭐⭐ | ~90% | Mac avec GPU dédié / Apple Silicon M2+ |
| `gemma3:1b` | ⭐⭐⭐ | ~30–40% | Machines plus anciennes ou si ralentissements |

Pour changer de modèle, modifiez simplement `config.json` :
```json
"ollama": { "model": "gemma3:1b" }
```

Tout modèle disponible via `ollama list` peut être utilisé. Les modèles plus grands (`mistral`, `llama3`) produisent des résumés plus riches ; les modèles plus légers (`gemma3:1b`, `phi3:mini`) sont plus rapides et moins gourmands.

### Prérequis

- macOS
- Python 3.9+
- [Ollama](https://ollama.ai) avec au moins un modèle installé :
  - Haute qualité : `ollama pull mistral`
  - Léger : `ollama pull gemma3:1b`
- [Zotero](https://zotero.org) + [Better BibTeX](https://retorque.re/zotero-better-bibtex/) (optionnel)

### Installation

```bash
git clone https://github.com/GagGeo/science-torch.git
cd science-torch
bash install.sh
bash build.sh
```

Voir [GUIDE_INSTALLATION.md](GUIDE_INSTALLATION.md) pour les instructions détaillées.

### Licence

Apache 2.0 — libre d'utilisation, modification et distribution, avec attribution et protection des brevets.
