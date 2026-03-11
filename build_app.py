"""
build_app.py — Packaging de Veille Scientifique en application macOS (.app)
Usage : python build_app.py py2app
"""

from setuptools import setup

APP = ["main.py"]

DATA_FILES = [
    ("", ["config.json"]),
    ("core", [
        "core/__init__.py",
        "core/pubmed.py",
        "core/ollama_client.py",
        "core/excel_manager.py",
        "core/zotero_client.py",
        "core/pdf_manager.py",
        "core/scheduler.py",
    ]),
    ("ui", [
        "ui/__init__.py",
        "ui/menu_bar.py",
    ]),
    ("utils", [
        "utils/__init__.py",
        "utils/logger.py",
    ]),
]

OPTIONS = {
    "argv_emulation": False,  # Désactivé pour les apps barre de menu
    "plist": {
        "CFBundleName":               "Veille Scientifique",
        "CFBundleDisplayName":        "Veille Scientifique",
        "CFBundleIdentifier":         "com.veillescientifique.app",
        "CFBundleVersion":            "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable":    True,
        "LSUIElement":                True,   # App barre de menu (pas de dock)
        "NSHumanReadableCopyright":   "Veille Scientifique — Open Source",
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName":       "PDF Document",
                "CFBundleTypeRole":       "Viewer",
                "LSHandlerRank":          "Alternate",
                "LSItemContentTypes":     ["com.adobe.pdf"],
                "CFBundleTypeExtensions": ["pdf"],
            }
        ],
    },
    "packages": [
        "rumps", "openpyxl", "requests", "pypdf",
        "schedule", "pyzotero", "questionary",
    ],
    "excludes": [
        "tkinter", "matplotlib", "numpy", "scipy",
        "PIL", "PyQt5", "wx", "gi",
    ],
    "iconfile": "assets/icon.icns",  # Créé par build.sh si absent
}

setup(
    app=APP,
    name="Veille Scientifique",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
