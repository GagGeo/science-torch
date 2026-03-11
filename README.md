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

### How it works

1. You define your research domains and PubMed keywords
2. Every Monday morning, the app searches PubMed automatically
3. Each article is analyzed by a local LLM (Mistral) — hypothesis, population, methods, results, take-home message
4. Articles are added to your Excel file and Zotero library
5. A summary report is generated
6. You receive a macOS notification

### Requirements

- macOS
- Python 3.9+
- [Ollama](https://ollama.ai) with `mistral` model (`ollama pull mistral`)
- [Zotero](https://zotero.org) + [Better BibTeX](https://retorque.re/zotero-better-bibtex/) (optional)

### Installation

```bash
git clone https://github.com/GagGeo/science-torch.git
cd science-torch
bash install.sh   # installs dependencies + runs configuration wizard
bash build.sh     # creates Science Torch.app on your desktop
```

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed instructions.

### Built with

- [PubMed E-utilities API](https://www.ncbi.nlm.nih.gov/home/develop/api/) — free, no key required
- [Ollama](https://ollama.ai) — local LLM inference
- [rumps](https://github.com/jaredks/rumps) — macOS menu bar
- [openpyxl](https://openpyxl.readthedocs.io) — Excel generation
- [pyzotero](https://pyzotero.readthedocs.io) — Zotero integration
- [pypdf](https://pypdf.readthedocs.io) — PDF parsing

### License

MIT — free to use, modify and distribute.

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

### Comment ça marche

1. Vous définissez vos domaines de recherche et mots-clés PubMed
2. Chaque lundi matin, l'app interroge PubMed automatiquement
3. Chaque article est analysé par un LLM local (Mistral) — hypothèse, population, méthode, résultats, take-home message
4. Les articles sont ajoutés à votre fichier Excel et à Zotero
5. Un résumé hebdomadaire est généré
6. Vous recevez une notification macOS

### Prérequis

- macOS
- Python 3.9+
- [Ollama](https://ollama.ai) avec le modèle `mistral` (`ollama pull mistral`)
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

MIT — libre d'utilisation, modification et distribution.
