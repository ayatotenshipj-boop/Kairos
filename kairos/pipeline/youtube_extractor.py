import logging
import re
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_TIMESTAMP_RE = re.compile(r'^\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->')
_TAG_RE = re.compile(r'<[^>]+>')
_SKIP_PREFIXES = ('WEBVTT', 'Kind:', 'Language:', 'NOTE', 'STYLE', 'REGION')


def _extract_video_id(url: str) -> str | None:
    m = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    if m:
        return m.group(1)
    m = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if m:
        return m.group(1)
    m = re.search(r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})', url)
    if m:
        return m.group(1)
    return None


def _parse_vtt(content: str) -> str:
    """Extrai texto limpo de um arquivo VTT, sem timestamps nem tags."""
    lines = []
    last = None
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in _SKIP_PREFIXES):
            continue
        if _TIMESTAMP_RE.match(line):
            continue
        # Linhas de metadado de posição (ex: "align:start position:0%")
        if re.match(r'^[a-z-]+(:[^>]+)?$', line) and '-->' not in line:
            continue
        clean = _TAG_RE.sub('', line).strip()
        if not clean:
            continue
        if clean != last:
            lines.append(clean)
            last = clean
    return ' '.join(lines)


def _find_vtt(directory: Path) -> Path | None:
    vtts = list(directory.glob('*.vtt'))
    if not vtts:
        return None
    for lang in ('pt', 'en'):
        for vtt in vtts:
            if f'.{lang}.' in vtt.name:
                return vtt
    return vtts[0]


def _extract_via_yt_dlp(url: str) -> str:
    with tempfile.TemporaryDirectory(prefix='kairos_yt_') as tmp_dir:
        tmp_path = Path(tmp_dir)
        cmd = [
            'yt-dlp',
            '--write-auto-sub',
            '--skip-download',
            '--sub-langs', 'pt,en',
            '-o', str(tmp_path / '%(id)s.%(ext)s'),
            '--quiet',
            url,
        ]
        logger.info(f"Executando yt-dlp para {url}")
        # Timeout reduzido: yt-dlp baixa apenas legendas (texto pequeno)
        # 30s é suficiente mesmo para conexões lentas
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"yt-dlp falhou (código {result.returncode}): {result.stderr[:200]}")
            raise RuntimeError("yt-dlp falhou ao baixar as legendas do vídeo")

        vtt = _find_vtt(tmp_path)
        if not vtt:
            raise RuntimeError("Nenhum arquivo de legenda gerado pelo yt-dlp")

        logger.info(f"Lendo legenda: {vtt.name}")
        content = vtt.read_text(encoding='utf-8')
        text = _parse_vtt(content)
        if not text.strip():
            raise RuntimeError("Legenda gerada está vazia após limpeza")
        return text


def extract(url: str) -> str:
    """Extrai transcrição de um vídeo do YouTube.

    Nível 1: youtube-transcript-api.
    Nível 2 (fallback): yt-dlp com legendas automáticas.

    Raises:
        RuntimeError: Se ambos os métodos falharem (mensagem PT-BR).
    """
    video_id = _extract_video_id(url)

    if video_id:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            logger.info(f"Buscando transcrição via youtube-transcript-api (id={video_id})")
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=['pt', 'pt-BR', 'en']
            )
            text = ' '.join(seg['text'] for seg in transcript)
            if text.strip():
                logger.info(f"Transcrição obtida: {len(text)} caracteres")
                return text
            logger.warning("Transcrição retornou vazia — tentando yt-dlp")
        except Exception as e:
            logger.warning(f"youtube-transcript-api falhou: {e} — tentando yt-dlp")
    else:
        logger.warning(f"ID do vídeo não encontrado em '{url}' — tentando yt-dlp diretamente")

    try:
        text = _extract_via_yt_dlp(url)
        logger.info(f"Transcrição obtida via yt-dlp: {len(text)} caracteres")
        return text
    except Exception as e:
        logger.error(f"yt-dlp também falhou: {e}")
        raise RuntimeError(
            "Não foi possível extrair a transcrição do vídeo. "
            "Verifique se o vídeo tem legendas disponíveis e tente novamente."
        ) from e
