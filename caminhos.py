"""Pastas da aplicação, tanto em Python quanto no executável do Windows."""

import sys
from pathlib import Path


def pasta_aplicacao():
    """Local dos modelos, da configuração e dos arquivos gerados."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent
