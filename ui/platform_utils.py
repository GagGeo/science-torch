"""
ui/platform_utils.py — Utilitaires multi-plateformes
Abstrait les différences macOS / Linux / Windows pour :
  - Ouvrir des fichiers/dossiers
  - Sélecteur de fichier natif
  - Notifications système
  - Dialogues de saisie
"""
import sys
import os
import subprocess
import platform
from pathlib import Path
from typing import Optional

SYSTEM = platform.system()  # "Darwin" | "Linux" | "Windows"


# ── Ouvrir un fichier ou dossier ──────────────────────────────────────────────

def open_path(path: str):
    """Ouvre un fichier ou dossier avec l'application par défaut."""
    if SYSTEM == "Darwin":
        subprocess.run(["open", path])
    elif SYSTEM == "Linux":
        subprocess.run(["xdg-open", path])
    elif SYSTEM == "Windows":
        os.startfile(path)


def open_app(app_name: str):
    """Ouvre une application par son nom."""
    if SYSTEM == "Darwin":
        subprocess.run(["open", "-a", app_name])
    elif SYSTEM == "Linux":
        subprocess.run([app_name.lower()])
    elif SYSTEM == "Windows":
        subprocess.run(["start", app_name], shell=True)


# ── Sélecteur de fichier PDF ──────────────────────────────────────────────────

def pick_pdf_file(prompt: str = "Select a PDF article") -> Optional[str]:
    """
    Ouvre un sélecteur de fichier natif pour choisir un PDF.
    Retourne le chemin du fichier sélectionné ou None si annulé.
    """
    if SYSTEM == "Darwin":
        return _pick_pdf_macos(prompt)
    else:
        return _pick_pdf_tkinter(prompt)


def _pick_pdf_macos(prompt: str) -> Optional[str]:
    """Sélecteur de fichier natif macOS via osascript."""
    script = f"""
    tell application "Finder"
        activate
    end tell
    set theFile to choose file with prompt "{prompt}" \\
        of type {{"pdf"}} \\
        with invisibles false
    return POSIX path of theFile
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except Exception:
        pass
    return None


def _pick_pdf_tkinter(prompt: str) -> Optional[str]:
    """Sélecteur de fichier via tkinter (Linux/Windows)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title=prompt,
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        root.destroy()
        return path or None
    except Exception:
        return None


# ── Dialogue de saisie ────────────────────────────────────────────────────────

def ask_text_dialog(title: str, prompt: str, default: str = "") -> Optional[str]:
    """
    Affiche un dialogue de saisie de texte natif.
    Retourne le texte saisi ou None si annulé.
    """
    if SYSTEM == "Darwin":
        return _ask_text_macos(title, prompt, default)
    else:
        return _ask_text_tkinter(title, prompt, default)


def _ask_text_macos(title: str, prompt: str, default: str) -> Optional[str]:
    """Dialogue de saisie macOS via osascript."""
    safe_default = default.replace('"', '\\"')
    safe_prompt  = prompt.replace('"', '\\"')
    script = f"""
    tell application "System Events"
        set dialogResult to display dialog ¬
            "{safe_prompt}" ¬
            default answer "{safe_default}" ¬
            with title "{title}" ¬
            buttons {{"Cancel", "Confirm"}} ¬
            default button "Confirm"
        return text returned of dialogResult
    end tell
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except Exception:
        pass
    return None


def _ask_text_tkinter(title: str, prompt: str, default: str) -> Optional[str]:
    """Dialogue de saisie via tkinter (Linux/Windows)."""
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        result = simpledialog.askstring(title, prompt, initialvalue=default, parent=root)
        root.destroy()
        return result
    except Exception:
        return None


# ── Notifications système ─────────────────────────────────────────────────────

def send_notification(title: str, subtitle: str = "", message: str = ""):
    """
    Envoie une notification système native.
    Sur macOS : utilise rumps si disponible, sinon osascript.
    Sur Linux : utilise notify-send.
    Sur Windows : utilise plyer si disponible.
    """
    if SYSTEM == "Darwin":
        _notify_macos(title, subtitle, message)
    elif SYSTEM == "Linux":
        _notify_linux(title, subtitle, message)
    elif SYSTEM == "Windows":
        _notify_windows(title, subtitle, message)


def _notify_macos(title: str, subtitle: str, message: str):
    """Notification macOS via osascript (fallback sans rumps)."""
    body = f"{subtitle} — {message}" if subtitle else message
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{body}" with title "{title}"'
        ], capture_output=True)
    except Exception:
        pass


def _notify_linux(title: str, subtitle: str, message: str):
    """Notification Linux via notify-send."""
    body = f"{subtitle}\n{message}" if subtitle else message
    try:
        subprocess.run(["notify-send", title, body], capture_output=True)
    except Exception:
        pass


def _notify_windows(title: str, subtitle: str, message: str):
    """Notification Windows via plyer."""
    body = f"{subtitle} — {message}" if subtitle else message
    try:
        from plyer import notification
        notification.notify(title=title, message=body, timeout=5)
    except Exception:
        pass


# ── Info plateforme ───────────────────────────────────────────────────────────

def is_macos()   -> bool: return SYSTEM == "Darwin"
def is_linux()   -> bool: return SYSTEM == "Linux"
def is_windows() -> bool: return SYSTEM == "Windows"
