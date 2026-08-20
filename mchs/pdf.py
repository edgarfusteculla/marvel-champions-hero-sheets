"""Exporta las hojas a PDF usando el modo headless de un navegador Chromium."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

WINDOWS_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)

COMMAND_CANDIDATES = ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser")


class PdfExportError(RuntimeError):
    pass


def find_browser() -> str | None:
    for path in WINDOWS_CANDIDATES:
        if Path(path).exists():
            return path
    for command in COMMAND_CANDIDATES:
        found = shutil.which(command)
        if found:
            return found
    return None


def export(html_path: Path, pdf_path: Path) -> None:
    browser = find_browser()
    if browser is None:
        raise PdfExportError(
            "No he encontrado Edge ni Chrome para generar el PDF. "
            "Genera el HTML y usa Imprimir > Guardar como PDF en tu navegador."
        )

    result = subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if not pdf_path.exists():
        raise PdfExportError(f"El navegador no generó el PDF: {result.stderr.strip()}")
