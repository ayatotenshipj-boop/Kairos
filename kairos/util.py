"""Utilitários puros — sem dependências de UI ou pipeline.

Compartilhados entre camadas (ex.: logger/pipeline e workers/ui) para evitar
duplicação. Nada aqui pode importar de `ui/`, `pipeline/` ou `integrations/`.
"""


def format_duration(seconds: float) -> str:
    """Formata segundos como 'MmSSs' (ex.: 2m14s). Negativo vira 0m00s."""
    total = max(0, int(round(seconds)))
    m, s = divmod(total, 60)
    return f"{m}m{s:02d}s"


def truncate_at_line(text: str, max_chars: int, notice: str) -> str:
    """Corta `text` em fronteira de linha até `max_chars`, anexando `notice`.

    Retorna o texto intacto quando `max_chars` não é inteiro positivo ou o texto
    já cabe. Não colapsa whitespace — quem chama decide isso antes.
    """
    if not (isinstance(max_chars, int) and max_chars > 0 and len(text) > max_chars):
        return text
    cut = text.rfind("\n", 0, max_chars)
    if cut <= 0:
        cut = max_chars
    return text[:cut].rstrip() + notice
