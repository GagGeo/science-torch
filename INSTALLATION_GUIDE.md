# 🔬 Science Watch — Installation Guide

## What this app does

Science Watch is an automated scientific literature monitoring tool. Every week, it:
- Automatically searches **PubMed** for new articles matching your research domains
- Analyzes and summarizes each article using a **local LLM** (Ollama — free, private, no data sent online)
- Updates a structured **Excel file** with all key information
- Syncs references with **Zotero** (optional)
- Generates a **weekly summary** in Markdown
- Sends you a **macOS notification**

---

## Prerequisites

### 1. Python 3.9 or higher
Check in Terminal:
```
python3 --version
```
If missing: download from [python.org](https://python.org)

### 2. Ollama (required)
Ollama runs the article analysis model locally on your Mac — free and private, no data ever leaves your machine.

1. Download and install from [ollama.ai](https://ollama.ai)
2. Open Terminal and download the mistral model (~4 GB):
```
ollama pull mistral
```
> ⏱ Download takes a few minutes depending on your connection.

### 3. Zotero + Better BibTeX (optional)
If you want Zotero sync:
1. Install [Zotero](https://zotero.org)
2. Install the [Better BibTeX](https://retorque.re/zotero-better-bibtex/) plugin

---

## Installation

### Step 1 — Get the project folder
Place the project folder wherever you like on your Mac, e.g. in `Documents/`.

### Step 2 — Run the installer
Open Terminal, navigate to the project folder and run:
```
bash install.sh
```
The script will:
- Create an isolated Python environment (`.venv`)
- Install all dependencies automatically
- Launch the configuration wizard

### Step 3 — Configuration
The wizard will ask you a few questions:
- **Storage folder**: where your Excel file, PDFs and summaries will be saved (press Enter to accept the default)
- **Research domains**: enter your domains one by one with their PubMed keywords
- **Combinations**: activate tabs combining multiple domains (optional)
- **Ollama**: choose `mistral` as the model
- **Zotero**: enable if you use it, otherwise answer `n`
- **Schedule**: choose the day and time for the weekly search

### Step 4 — Build the app
```
bash build.sh
```
This creates **Science Watch.app** directly on your desktop.

---

## Launching

Double-click **Science Watch.app** on your desktop.

> ⚠️ If macOS shows "unidentified developer" on first launch:
> **Right-click → Open → Open anyway**

The 🔬 icon appears in the **menu bar** at the top right of your screen.

---

## Usage

Click the 🔬 icon to access the menu:

| Option | Description |
|---|---|
| 🔍 Run a search now | Immediately triggers a PubMed search |
| 📥 Add a PDF manually | Import an article you found yourself |
| 📊 Open Excel file | Opens your article database |
| 📋 View last summary | Opens the weekly summary |
| 📚 Open Zotero | Opens Zotero |
| 📁 Open PDFs folder | Quick access to downloaded PDFs |
| ⚙️ Settings | Edit settings (config.json) |

---

## Your files

All your files are stored in `Documents/ScienceWatch/`:
```
Documents/ScienceWatch/
├── veille.xlsx          ← main Excel file
├── pdfs/
│   ├── auto/            ← open access PDFs downloaded automatically
│   └── manual/          ← PDFs added manually
├── resumes/             ← weekly summaries in Markdown
└── logs/                ← application logs
```

---

## Troubleshooting

**🔬 icon does not appear**
→ Check that Ollama is installed and a model is available: `ollama list`

**Search is very slow**
→ Normal on first launch — Ollama needs to load the model into memory.
→ Subsequent searches are faster (~2–3 min for 20 articles).

**"Unidentified developer" on launch**
→ Right-click → Open → Open anyway.

**No articles found**
→ Check your internet connection.
→ Check your keywords in ⚙️ Settings (config.json).

**Zotero not syncing**
→ Make sure Zotero is open before launching a search.

---

## Editing your research domains

Open `config.json` via ⚙️ Settings and edit the `"domains"` section:
```json
{
  "short": "SHORT_NAME",
  "name": "Full domain name",
  "keywords": ["keyword 1", "keyword 2"]
}
```
Save and relaunch the app.
