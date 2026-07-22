"""Placeholder Evidence files: images + audio, no external APIs.

CLAUDE.md hard constraints this module respects:
- Placeholder/stock content only — never real forensic content, never
  photorealistic photos of synthetic people. Images are flat text/noise
  cards, not renderings of people or scenes.
- No TTS/gTTS/pyttsx3 — audio is a synthesized tone/noise burst via numpy +
  stdlib `wave`, not fake speech.
- FileURL is a local csv_out/evidence_files/ path at generation time.
  TODO: swap for a real Catalyst Stratus URL once an upload step exists —
  do not fabricate a Stratus URL now.
"""

from __future__ import annotations

import os
import random
import wave

import numpy as np
from PIL import Image, ImageDraw

random.seed(46)

EVIDENCE_FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "csv_out", "evidence_files")

CARD_COLORS = [(60, 60, 70), (70, 55, 55), (55, 65, 60), (65, 60, 75)]


def generate_placeholder_image(evidence_id: int, case_no: str, out_dir: str = EVIDENCE_FILES_DIR) -> str:
    os.makedirs(out_dir, exist_ok=True)
    w, h = 480, 320
    img = Image.new("RGB", (w, h), random.choice(CARD_COLORS))
    draw = ImageDraw.Draw(img)

    # procedural noise texture — clearly synthetic, never photorealistic
    noise = (np.random.rand(h, w, 3) * 25).astype(np.uint8)
    base = np.array(img)
    noisy = np.clip(base.astype(int) + noise.astype(int) - 12, 0, 255).astype(np.uint8)
    img = Image.fromarray(noisy)
    draw = ImageDraw.Draw(img)

    draw.rectangle([10, 10, w - 10, h - 10], outline=(200, 200, 200), width=2)
    draw.text((24, 24), "SYNTHETIC EVIDENCE PLACEHOLDER", fill=(230, 230, 230))
    draw.text((24, 50), f"Case No: {case_no}", fill=(200, 200, 200))
    draw.text((24, 70), f"Evidence ID: {evidence_id}", fill=(200, 200, 200))
    draw.text((24, h - 40), "No real content — demo data only", fill=(180, 180, 180))

    path = os.path.join(out_dir, f"evidence_{evidence_id}.png")
    img.save(path)
    return path


def generate_placeholder_audio(evidence_id: int, out_dir: str = EVIDENCE_FILES_DIR, duration_s: float = 2.0) -> str:
    os.makedirs(out_dir, exist_ok=True)
    sample_rate = 22050
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    freq = random.choice([220, 330, 440, 550])
    tone = 0.3 * np.sin(2 * np.pi * freq * t)
    noise = 0.02 * np.random.randn(len(t))
    signal = np.clip(tone + noise, -1.0, 1.0)
    pcm = (signal * 32767).astype(np.int16)

    path = os.path.join(out_dir, f"evidence_{evidence_id}.wav")
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return path
