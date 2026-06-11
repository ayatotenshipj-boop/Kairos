import logging
import re
import subprocess
import tempfile
from pathlib import Path

from kairos.config import config as cfg
from kairos.util import truncate_at_line

logger = logging.getLogger(__name__)

# Modelo Whisper carregado sob demanda e reaproveitado entre chamadas.
_whisper_model = None

_TRANSCRIPT_NOTICE = (
    "\n\n[Transcrição truncada para caber no limite do backend de IA. "
    "Conteúdo além deste ponto foi omitido.]"
)


def _normalize_transcript(text: str) -> str:
    """Limpa e limita a transcrição antes de enviar ao backend.

    Colapsa espaços, quebra em sentenças (uma por linha) e corta no limite
    configurável (`transcript_max_chars`), anexando aviso PT-BR quando truncar.
    Um blob cru gigante estoura o limite/timeout do backend; isto evita o
    fallback desnecessário.
    """
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?<=[.!?])\s+", "\n", text)

    max_chars = cfg.load().get("transcript_max_chars", 30000)
    return truncate_at_line(text, max_chars, _TRANSCRIPT_NOTICE)


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


def _try_captions(video_id: str) -> str | None:
    """Atalho rápido: usa legenda já existente, se houver. Nunca lança."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        logger.info(f"Tentando legenda pronta (id={video_id})")
        transcript = YouTubeTranscriptApi().fetch(
            video_id, languages=['pt', 'pt-BR', 'en']
        )
        text = ' '.join(snippet.text for snippet in transcript)
        if text.strip():
            logger.info(f"Legenda obtida: {len(text)} caracteres")
            return text
    except Exception as e:
        logger.info(f"Sem legenda pronta ({e}) — usará áudio + Whisper")
    return None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        size = cfg.load().get("whisper_model", "small")
        logger.info(f"Carregando modelo Whisper '{size}' (CPU/int8) — pode baixar no 1º uso")
        _whisper_model = WhisperModel(size, device="cpu", compute_type="int8")
    return _whisper_model


def _download_audio(url: str, dest_dir: Path) -> Path:
    out_template = str(dest_dir / '%(id)s.%(ext)s')
    cmd = [
        'yt-dlp',
        '-f', 'bestaudio',
        '-x', '--audio-format', 'mp3',
        '--no-playlist',
        '-o', out_template,
        '--quiet',
        url,
    ]
    logger.info(f"Baixando áudio via yt-dlp: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        logger.error(f"yt-dlp falhou (código {result.returncode}): {result.stderr[:200]}")
        raise RuntimeError("Falha ao baixar o áudio do vídeo")

    audio_files = list(dest_dir.glob('*.mp3'))
    if not audio_files:
        # Fallback: yt-dlp pode ter salvo noutro container. Filtra por sufixo de
        # áudio para não pegar restos (.part, .json) como se fossem o áudio.
        _audio_ext = ('.mp3', '.m4a', '.webm', '.opus', '.ogg', '.wav', '.aac')
        audio_files = [
            p for p in dest_dir.iterdir()
            if p.is_file() and p.suffix.lower() in _audio_ext
        ]
    if not audio_files:
        raise RuntimeError("Nenhum arquivo de áudio gerado pelo yt-dlp")
    return audio_files[0]


def _transcribe_whisper(audio: Path) -> str:
    model = _get_whisper_model()
    logger.info(f"Transcrevendo áudio com Whisper: {audio.name}")
    # language=None → detecção automática (suporta vídeos PT e EN)
    segments, _info = model.transcribe(str(audio), language=None)
    text = ' '.join(seg.text.strip() for seg in segments)
    text = text.strip()
    if not text:
        raise RuntimeError("Transcrição retornou vazia")
    return text


def _extract_via_whisper(url: str) -> str:
    with tempfile.TemporaryDirectory(prefix='kairos_yt_') as tmp_dir:
        audio = _download_audio(url, Path(tmp_dir))
        return _transcribe_whisper(audio)


def extract(url: str) -> str:
    """Extrai transcrição de um vídeo do YouTube.

    Atalho: legenda já existente (rápido, quando há).
    Principal: yt-dlp baixa o áudio e faster-whisper transcreve (funciona em
    qualquer vídeo, não exige legenda).

    Raises:
        RuntimeError: Se a transcrição falhar (mensagem PT-BR).
    """
    video_id = _extract_video_id(url)

    if video_id:
        captions = _try_captions(video_id)
        if captions is not None:
            return _normalize_transcript(captions)

    try:
        text = _extract_via_whisper(url)
        logger.info(f"Transcrição obtida via Whisper: {len(text)} caracteres")
        return _normalize_transcript(text)
    except Exception as e:
        logger.error(f"Transcrição por áudio falhou: {e}")
        raise RuntimeError(
            "Não foi possível transcrever o vídeo. "
            "Verifique a URL e a conexão e tente novamente."
        ) from e
