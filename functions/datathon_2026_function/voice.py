"""Bilingual (English/Kannada) speech-to-text — local, open-source HF
model, no external API calls, no per-request cost (idea.md feature 1's
hard constraint). TTS deliberately out of scope for now (skipped per user
instruction) — MMS-TTS needs torch, adding real deploy-size risk on top of
STT's; revisit as a separate, explicitly-scoped decision later.

STT: faster-whisper (ctranslate2 backend, NOT torch) — one multilingual
model handles English, Kannada, and code-switched audio, so no separate
per-language STT model is needed. Model weights are pulled from the HF hub
lazily on first use and cached to local disk by faster-whisper itself, not
vendored into the deploy package — keeps the deploy package itself small
even though the cached weights are not.

UNCONFIRMED, flagged per CLAUDE.md rather than assumed: whether a Catalyst
Function's writable /tmp persists across warm invocations (so the
lazy-downloaded weights are only fetched once) or is wiped every cold
start (so every cold start re-downloads ~150-500MB from the HF hub before
the first request completes, adding real latency). Needs empirical
confirmation via an actual deploy — the model is loaded lazily and cached
at module level here specifically so a warm invocation is fast regardless
of which behavior turns out to be true; cold-start latency is the open
risk, not correctness.
"""

from __future__ import annotations

import io
from typing import Any, Literal

Language = Literal["en", "kn"]

_WHISPER_MODEL_SIZE = "small"  # multilingual — covers en + kn in one model

# Module-level cache: a Catalyst Function process may serve several warm
# invocations, so load the model at most once per process rather than once
# per request — mirrors the lazy-singleton pattern quickml_client.py
# already uses for its client object.
_whisper_model = None


class VoiceError(Exception):
    pass


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise VoiceError(
                "faster-whisper not installed — add it to requirements.txt"
            ) from e
        _whisper_model = WhisperModel(_WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper_model


def transcribe(audio_bytes: bytes, hint_language: Language | None = None) -> dict[str, Any]:
    """Returns {"text": str, "detected_language": "en"|"kn"|other}.
    hint_language is passed straight to faster-whisper's `language=` param
    when given — skips its own language-ID pass and is slightly faster;
    omit it to let the model auto-detect (needed for code-switched audio)."""
    model = _get_whisper_model()
    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),
        language=hint_language,
        vad_filter=True,  # trims silence, faster + fewer hallucinated segments on quiet audio
    )
    text = " ".join(seg.text.strip() for seg in segments).strip()
    if not text:
        raise VoiceError("no speech detected in audio")
    return {"text": text, "detected_language": info.language}


def _demo() -> None:
    """ponytail self-check: error path only — no live model load/download,
    since that needs the real (heavy, network-dependent) dependency which
    isn't assumed present in every environment this runs in."""
    import voice as _v

    original = _v._get_whisper_model
    def _raise_missing():
        raise VoiceError("faster-whisper not installed — add it to requirements.txt")
    _v._get_whisper_model = _raise_missing
    try:
        transcribe(b"")
        raise AssertionError("expected VoiceError")
    except VoiceError:
        pass
    finally:
        _v._get_whisper_model = original

    print("voice._demo: all assertions passed (error path only — model load not exercised)")


if __name__ == "__main__":
    _demo()
