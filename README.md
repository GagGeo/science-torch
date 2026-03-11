# 🔬 Veille Scientifique Automatisée

Application de veille scientifique automatisée pour chercheurs, avec recherche PubMed, analyse par LLM local (Ollama), intégration Zotero et interface barre de menu macOS.

## Fonctionnalités

- 🔍 Recherche automatique hebdomadaire sur PubMed
- 🤖 Analyse et résumé structuré via Ollama (LLM local, gratuit)
- 📊 Export Excel avec onglets thématiques modulaires
- 📚 Synchronisation automatique avec Zotero + Better BibTeX
- 📥 Téléchargement automatique des PDFs open access
- 🖥️ Application barre de menu macOS discrète
- 🔔 Notifications macOS
- 📋 Résumés hebdomadaires automatiques
- 📄 Support articles expérimentaux ET revues de littérature

## Prérequis

- macOS (Tahoe ou supérieur recommandé)
- Python 3.9+
- [Ollama](https://ollama.ai) installé avec au moins un modèle (ex: `ollama pull mistral`)
- [Zotero](https://www.zotero.org) + plugin [Better BibTeX](https://retorque.re/zotero-better-bibtex/) (optionnel)

## Installation

```bash
git clone https://github.com/votre-compte/veille-scientifique.git
cd veille-scientifique
python setup.py
```

Le script `setup.py` guidera la configuration initiale.

## Utilisation

```bash
python main.py
```

L'application apparaît dans la barre de menu (icône 🔬). Cliquer pour :
- Lancer une recherche manuelle
- Ajouter un PDF manuellement
- Voir le dernier résumé hebdomadaire
- Accéder aux paramètres

## Structure du projet

```
veille_scientifique/
├── main.py                  # Point d'entrée principal
├── setup.py                 # Configuration initiale interactive
├── config.json              # Configuration utilisateur (généré par setup.py)
├── core/
│   ├── pubmed.py            # Moteur de recherche PubMed
│   ├── ollama_client.py     # Interface Ollama (LLM local)
│   ├── excel_manager.py     # Gestion du fichier Excel
│   ├── zotero_client.py     # Intégration Zotero
│   ├── pdf_manager.py       # Téléchargement et gestion des PDFs
│   └── scheduler.py         # Tâche hebdomadaire automatique
├── ui/
│   ├── menu_bar.py          # Application barre de menu macOS
│   └── pdf_drop.py          # Fenêtre drag-and-drop PDF
├── utils/
│   ├── logger.py            # Logging
│   └── helpers.py           # Fonctions utilitaires
└── output_templates/
    └── weekly_summary.md    # Template résumé hebdomadaire
```

## Configuration

Editer `config.json` pour modifier :
- Domaines et mots-clés
- Fréquence de recherche
- Dossier de stockage des PDFs
- Modèle Ollama utilisé

## Distribution

Pour partager avec un collègue :
1. Cloner le dépôt GitHub
2. Lancer `python setup.py` pour une nouvelle configuration personnalisée
3. S'assurer qu'Ollama est installé sur la machine cible
