# 🔬 Science Torch — Windows Installation Guide

## Prerequisites

### 1. Python 3.9 or higher
Download from [python.org](https://python.org).

> ⚠️ During installation, check **"Add Python to PATH"**.

### 2. Ollama (required)
1. Download from [ollama.ai](https://ollama.ai)
2. Install and open **Ollama**
3. Open **Command Prompt** and run:
```
ollama pull mistral
```
Or for a lighter model:
```
ollama pull gemma3:1b
```

### 3. Zotero + Better BibTeX (optional)
1. Install [Zotero](https://zotero.org)
2. Install [Better BibTeX](https://retorque.re/zotero-better-bibtex/)

---

## Installation

### Step 1 — Get the project folder
Place the project folder anywhere on your PC, e.g. `Documents\ScienceTorch\`.

### Step 2 — First run (configuration)
Double-click **`setup.bat`** to launch the configuration wizard.

It will ask you:
- Data folder name and location
- Your research domains and PubMed keywords
- Ollama model to use
- Weekly search schedule

### Step 3 — Launch the app
Double-click **`ScienceTorch.exe`**.

The 🔬 icon appears in the **system tray** (bottom right, near the clock).

> ⚠️ If Windows shows "Windows protected your PC":
> Click **"More info" → "Run anyway"**

---

## Usage

Right-click the 🔬 icon in the system tray:

| Option | Description |
|---|---|
| 🌐 Open dashboard | Opens the web interface in your browser |
| 🔍 Run a search now | Immediately triggers a PubMed search |
| 📥 Add a PDF manually | Import an article you found yourself |
| 📊 Open Excel file | Opens your article database |
| 📋 View last summary | Opens the weekly summary |
| ⚙️ Settings | Edit settings |
| Quit | Exit the app |

---

## Choosing your Ollama model

| Model | Quality | GPU usage | Best for |
|---|---|---|---|
| `mistral` | ⭐⭐⭐⭐ | High | Gaming PCs / dedicated GPU |
| `gemma3:1b` | ⭐⭐⭐ | Low | Office PCs / integrated GPU |

To switch models, open **Settings** and edit `config.json`:
```json
"ollama": { "model": "gemma3:1b" }
```

---

## Troubleshooting

**🔬 icon does not appear**
→ Check that Ollama is running (look for it in the system tray)
→ Try: open Command Prompt and run `ollama list`

**"Windows protected your PC" warning**
→ Click "More info" → "Run anyway" — this is normal for unsigned apps

**Search is slow**
→ Normal on first launch — Ollama loads the model into memory
→ Consider switching to `gemma3:1b` for better performance

**No articles found**
→ Check your internet connection
→ Check your keywords in Settings

**Zotero not syncing**
→ Make sure Zotero is open before running a search
