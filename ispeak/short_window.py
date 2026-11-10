# ispeak/short_window.py
"""
Fast path for short dictations.

Whisper always encodes a fixed 30-second window: a 2-second dictation is
padded with silence to 30s, and the encoder (93% of the work for turbo on
CPU, ~4.6s) costs the same no matter how little was said.  CTranslate2 can
encode a shorter window, which is ~4x faster (10s window: ~1.1s).

Whisper was trained on 30s windows, so used naively a short window makes it
repeat itself.  Two things keep it reliable in testing:
  * windows in 10-second steps with >= 2s of trailing silence
  * timestamp mode, and stopping at the first timestamp past the real audio
and as a safety net, any suspicious result (repetition, too much text for the
amount of speech) returns None so the caller falls back to the normal path.
"""

import math
import re
import zlib

import numpy as np

SAMPLE_RATE = 16000
MAX_FAST_SECONDS = 27      # longer clips use the normal 30s path
MIN_TRAILING_SILENCE = 2   # seconds of padding kept after the speech
VAD_MARGIN = 0.2           # seconds kept around detected speech
DETECTION_CONFIDENCE = 0.8 # below this, auto language detection uses detect_fallback

_RE_REPEATED_WORD = re.compile(r"\b(\w+)\b(?:[\s.,!?;:]+\1\b){2,}", re.IGNORECASE | re.UNICODE)


def _trim_silence(audio):
    """Cut leading/trailing silence (keeps pauses inside the speech).
    Returns None if there is no speech at all."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    speech = get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=300))
    if not speech:
        return None
    margin = int(VAD_MARGIN * SAMPLE_RATE)
    start = max(0, speech[0]["start"] - margin)
    end = min(len(audio), speech[-1]["end"] + margin)
    return audio[start:end]


def _looks_suspicious(text, speech_seconds):
    if not text:
        return True
    data = text.encode("utf-8")
    if len(data) > 40 and len(data) / len(zlib.compress(data)) > 2.0:
        return True                                   # repeated sentences
    if _RE_REPEATED_WORD.search(text):
        return True                                   # "commit. Commit. Commit."
    if len(text) / max(speech_seconds, 0.5) > 25:
        return True                                   # far more text than speech
    return False


def transcribe(model, audio, language, auto_languages=("ro", "en"), detect_fallback=None):
    """Transcribe `audio` (float32, 16kHz) with a short encoder window.

    model:    faster_whisper.WhisperModel
    language: language code, or "auto" to pick among `auto_languages`
    detect_fallback: callable(audio) -> language, used in auto mode when the
              short-window detection is not confident (very short clips)
    Returns {"text", "language", "confidence", "window"} or None when the
    fast path isn't suitable / the result looks unreliable (caller falls back).
    """
    import ctranslate2

    if len(audio) / SAMPLE_RATE > MAX_FAST_SECONDS + 3:
        return None
    speech = _trim_silence(audio)
    if speech is None:
        return {"text": "", "language": language, "confidence": 0.0, "window": 0}
    seconds = len(speech) / SAMPLE_RATE
    if seconds > MAX_FAST_SECONDS:
        return None

    window = min(30, 10 * math.ceil((seconds + MIN_TRAILING_SILENCE) / 10))
    fe = model.feature_extractor
    features = fe(speech, padding=fe.n_samples - len(speech))[..., : window * 100]
    encoded = model.model.encode(
        ctranslate2.StorageView.from_array(np.ascontiguousarray(features[None])),
        to_cpu=False)

    tok = model.hf_tokenizer
    if language == "auto":
        # Reuses the encoder output — no extra encoder pass.  Reliable (p≈1.0)
        # from ~2s of speech; on shorter clips it can be confidently WRONG
        # (a 1.5s Romanian clip came out as English and got translated), so
        # below the threshold we defer to the full-window detector.
        probs = {t[2:-2]: p for t, p in model.model.detect_language(encoded)[0]}
        language = max(auto_languages, key=lambda lang: probs.get(lang, 0.0))
        if probs.get(language, 0.0) < DETECTION_CONFIDENCE and detect_fallback is not None:
            language = detect_fallback(audio)

    prompt = [tok.token_to_id("<|startoftranscript|>"),
              tok.token_to_id(f"<|{language}|>"),
              tok.token_to_id("<|transcribe|>")]
    result = model.model.generate(encoded, [prompt], beam_size=1, max_length=448,
                                  suppress_blank=True, return_scores=True,
                                  return_no_speech_prob=True)[0]

    ts_begin = tok.token_to_id("<|0.00|>")
    eot = tok.token_to_id("<|endoftext|>")
    text_ids = []
    for t in result.sequences_ids[0]:
        if t >= ts_begin:
            if (t - ts_begin) * 0.02 > seconds + 0.5:   # past the real audio
                break
        elif t < eot:
            text_ids.append(t)
    text = tok.decode(text_ids).strip()

    if result.no_speech_prob > 0.6 or _looks_suspicious(text, seconds):
        return None

    avg_logprob = result.scores[0] if result.scores else -1.0
    return {
        "text": text,
        "language": language,
        "confidence": min(1.0, max(0.0, 1.0 + avg_logprob)),
        "window": window,
    }
