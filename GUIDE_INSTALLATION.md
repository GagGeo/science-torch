# 🔬 Science Torch — Guide d'installation

## Ce que fait cette application

Science Torch est un outil de veille bibliographique automatisée. Chaque semaine, elle :
- Recherche automatiquement les nouveaux articles sur **PubMed** selon vos domaines d'intérêt
- Analyse et résume chaque article grâce à un **LLM local** (Ollama — gratuit, privé, sans internet)
- Met à jour un **fichier Excel** structuré avec toutes les informations clés
- Synchronise les références avec **Zotero** (optionnel)
- Génère un **résumé hebdomadaire** en Markdown
- Vous notifie par une **notification macOS**

---

## Prérequis

### 1. Python 3.9 ou supérieur
Vérifiez dans le Terminal :
```
python3 --version
```
Si absent : télécharger sur https://python.org

### 2. Ollama (obligatoire)
Ollama fait tourner le modèle d'analyse localement sur votre Mac, gratuitement et sans envoyer vos données sur internet.

1. Télécharger et installer depuis https://ollama.ai
2. Ouvrir le Terminal et télécharger le modèle mistral (~4 Go) :
```
ollama pull mistral
```
Le téléchargement prend quelques minutes selon votre connexion.

### 3. Zotero + Better BibTeX (optionnel)
Si vous voulez synchroniser avec Zotero :
1. Installer Zotero depuis https://zotero.org
2. Installer le plugin Better BibTeX depuis https://retorque.re/zotero-better-bibtex/

---

## Installation

### Étape 1 — Récupérer le dossier projet
Placez le dossier reçu où vous voulez sur votre Mac, par exemple dans Documents/.

### Étape 2 — Lancer l'installation
Ouvrir le Terminal, naviguer jusqu'au dossier projet :
```
cd chemin/vers/le/dossier
bash install.sh
```
Le script installe toutes les dépendances et lance le wizard de configuration.

### Étape 3 — Configuration
Le wizard vous posera quelques questions :
- **Dossier de stockage** : appuyez sur Entrée pour accepter le dossier par défaut
- **Domaines de recherche** : entrez vos domaines un par un avec leurs mots-clés PubMed
- **Combinaisons** : activez les onglets croisant plusieurs domaines (optionnel)
- **Ollama** : choisissez `mistral` comme modèle
- **Zotero** : activez si vous l'utilisez, sinon répondez `n`
- **Planning** : choisissez le jour et l'heure de la recherche hebdomadaire

### Étape 4 — Créer l'application
```
bash build.sh
```
Cela crée **Science Torch.app** directement sur votre bureau.

---

## Lancement

Double-cliquez sur **Science Torch.app** sur votre bureau.

Si macOS affiche "développeur non identifié" la première fois :
→ Clic droit sur l'app → Ouvrir → Ouvrir quand même.

L'icône 🔬 apparaît dans la **barre de menu** en haut à droite de l'écran.

---

## Utilisation

Cliquer sur l'icône 🔬 pour accéder au menu :

| Option | Description |
|---|---|
| 🔍 Lancer une recherche maintenant | Lance immédiatement la recherche PubMed |
| 📥 Ajouter un PDF manuellement | Importer un article trouvé vous-même |
| 📊 Ouvrir le fichier Excel | Ouvre votre base d'articles |
| 📋 Voir le dernier résumé | Ouvre le résumé hebdomadaire |
| 📚 Ouvrir Zotero | Ouvre Zotero |
| 📁 Ouvrir le dossier PDFs | Accès rapide aux PDFs téléchargés |
| ⚙️ Paramètres | Modifie les réglages (config.json) |

---

## Vos fichiers

Tous vos fichiers sont dans Documents/ScienceTorch/ :
```
Documents/ScienceTorch/
├── veille.xlsx          ← fichier Excel principal
├── pdfs/
│   ├── auto/            ← PDFs open access téléchargés automatiquement
│   └── manual/          ← PDFs ajoutés manuellement
├── resumes/             ← résumés hebdomadaires en Markdown
└── logs/                ← logs de l'application
```

---

## Dépannage

**L'icône 🔬 n'apparaît pas**
→ Vérifier qu'Ollama est installé et qu'un modèle est disponible : `ollama list`

**La recherche est très lente**
→ Normal au premier lancement — Ollama charge le modèle en mémoire.
→ Les recherches suivantes sont plus rapides (~2-3 min pour 20 articles).

**"Développeur non identifié"**
→ Clic droit → Ouvrir → Ouvrir quand même.

**Aucun article trouvé**
→ Vérifier la connexion internet et les mots-clés dans ⚙️ Paramètres.

**Zotero non synchronisé**
→ S'assurer que Zotero est ouvert avant de lancer une recherche.

---

## Modifier vos domaines de recherche

Ouvrez config.json via ⚙️ Paramètres et modifiez la section "domains" :
```json
{
  "short": "NOM_COURT",
  "name": "Nom complet du domaine",
  "keywords": ["mot-clé 1", "mot-clé 2"]
}
```
Sauvegardez et relancez l'application.
