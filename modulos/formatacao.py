"""Regras de escrita aplicadas na interface e antes de salvar no banco."""


def maiusculas(valor):
    return str(valor or "").upper()


def iniciais_maiusculas(valor):
    return str(valor or "").title()


def iniciais_maiusculas_funcao(valor):
    """Mantém conectivos minúsculos e siglas comuns em setor/cargo."""
    palavras = iniciais_maiusculas(valor).split(" ")
    for indice, palavra in enumerate(palavras):
        if indice > 0 and palavra.lower() in {"de", "da", "do", "das", "dos", "e"}:
            palavras[indice] = palavra.lower()
        elif palavra.upper() in {"TI", "RH", "T.I", "GLPI"}:
            palavras[indice] = palavra.upper()
    return " ".join(palavras)
