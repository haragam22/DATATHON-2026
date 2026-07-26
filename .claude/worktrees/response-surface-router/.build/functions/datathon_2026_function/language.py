"""Phase 18 — Kannada/Voice, text-only scope. Zia's installed SDK (v1.4.0)
has no STT/TTS/translation method (confirmed by reading the module, not
assumed) despite technical.md/implementation.md describing "Zia Services
STT/TTS" — that's a doc/reality gap, flagged rather than built against a
nonexistent API. Scoped down (confirmed with the user) to text-in/text-out:
detect the question's language, translate Kannada/code-switched input to
English before it hits Stage 1, and translate the final answer back to
Kannada when the input was Kannada/mixed — via QuickML chat() (the only
confirmed-working LLM surface), not a dedicated translation API.

Audio capture/STT/TTS remain out of scope until a real Zia (or other
Catalyst-native) speech API is confirmed to exist.
"""

from __future__ import annotations

from typing import Literal

import quickml_client

Language = Literal["en", "kn", "mixed"]

_DETECT_SYSTEM_PROMPT = (
    "Identify the language of the user's message. Respond with ONLY one "
    'word: "en" if entirely English, "kn" if entirely Kannada (Kannada '
    'script or romanized), "mixed" if it code-switches between English and '
    "Kannada in the same message. No punctuation, no explanation."
)

_TRANSLATE_TO_EN_SYSTEM_PROMPT = (
    "Translate the user's message to English. If it is already partly or "
    "fully English, keep the English parts as-is and translate only the "
    "Kannada parts. Respond with ONLY the translated text, no explanation, "
    "no quotes."
)

_TRANSLATE_TO_KN_SYSTEM_PROMPT = (
    "Translate the given English text to Kannada. Respond with ONLY the "
    "Kannada translation, no explanation, no quotes, no English."
)


def detect_language(text: str) -> Language:
    raw = quickml_client.chat(
        [
            {"role": "system", "content": _DETECT_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        max_tokens=10, temperature=0.0,
    ).strip().lower()
    if raw not in ("en", "kn", "mixed"):
        return "en"  # unrecognized detector output -> treat as English, safest no-op default
    return raw  # type: ignore[return-value]


def translate_to_english(text: str) -> str:
    return quickml_client.chat(
        [
            {"role": "system", "content": _TRANSLATE_TO_EN_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        max_tokens=400, temperature=0.0,
    ).strip()


def translate_to_kannada(text: str) -> str:
    return quickml_client.chat(
        [
            {"role": "system", "content": _TRANSLATE_TO_KN_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        max_tokens=400, temperature=0.0,
    ).strip()


def preprocess_question(question: str) -> tuple[str, Language]:
    """Returns (english_question, detected_language). english_question is
    the original text unchanged when already English."""
    language = detect_language(question)
    if language == "en":
        return question, language
    return translate_to_english(question), language


def postprocess_answer(answer: str, language: Language) -> str:
    """Translates the English pipeline answer back to Kannada when the
    original question was Kannada/mixed, per the user's request that
    Kannada-in gets Kannada-out."""
    if language == "en":
        return answer
    return translate_to_kannada(answer)


def _demo() -> None:
    """ponytail self-check: routing logic (which branch calls translate),
    with quickml_client.chat mocked out — no live LLM call."""
    import quickml_client as _qc

    calls: list[str] = []

    def _fake_chat(messages, **kwargs):
        system = messages[0]["content"]
        calls.append(system)
        if system is _DETECT_SYSTEM_PROMPT:
            return "kn" if any(ord(ch) > 0x0C80 and ord(ch) < 0x0CFF for ch in messages[1]["content"]) else "en"
        if system is _TRANSLATE_TO_EN_SYSTEM_PROMPT:
            return "How many cases in Mysuru?"
        if system is _TRANSLATE_TO_KN_SYSTEM_PROMPT:
            return "ಕನ್ನಡ ಉತ್ತರ"
        raise AssertionError(f"unexpected system prompt: {system!r}")

    original_chat = _qc.chat
    _qc.chat = _fake_chat
    try:
        english_q, lang = preprocess_question("Murder cases in Bengaluru")
        assert lang == "en" and english_q == "Murder cases in Bengaluru", (english_q, lang)

        kannada_q, lang = preprocess_question("ಮೈಸೂರಿನಲ್ಲಿ ಎಷ್ಟು ಪ್ರಕರಣಗಳಿಲ್ಲ")
        assert lang == "kn" and kannada_q == "How many cases in Mysuru?", (kannada_q, lang)

        assert postprocess_answer("3 cases found.", "en") == "3 cases found."
        assert postprocess_answer("3 cases found.", "kn") == "ಕನ್ನಡ ಉತ್ತರ"
    finally:
        _qc.chat = original_chat

    print("language._demo: all assertions passed")


if __name__ == "__main__":
    _demo()
