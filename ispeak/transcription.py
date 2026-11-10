# ispeak/transcription.py

import os
import sys
import time

import short_window

# Try MLX-Whisper first (Apple Silicon only)
MLX_AVAILABLE = False
if sys.platform == "darwin":
    try:
        import mlx_whisper
        MLX_AVAILABLE = True
        print("[Transcription] MLX-Whisper available - using optimized Apple Silicon backend")
    except ImportError:
        print("[Transcription] MLX-Whisper not available, falling back to faster-whisper")

# Import faster-whisper — graceful failure if not installed
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("[Transcription] WARNING: faster-whisper not installed. Install: pip install faster-whisper")


# Languages "auto" mode chooses between.  Restricting detection matters:
# Whisper sometimes guesses a related language (e.g. Italian/Portuguese for
# Romanian) on short clips, and forcing the WRONG language makes Whisper
# translate instead of transcribe.
AUTO_LANGUAGES = ("ro", "en")

# Large models get a separate small model for language detection (see
# TranscriptionEngine._detect_language).
DETECTOR_MODEL = "small"
MODELS_USING_DETECTOR = ("medium", "large", "turbo")


class TranscriptionEngine:
    """
    High-performance transcription engine.
    Uses MLX-Whisper on Apple Silicon, falls back to faster-whisper everywhere else.
    """

    MLX_MODELS = {
        "tiny": "mlx-community/whisper-tiny-mlx",
        "base": "mlx-community/whisper-base-mlx",
        "small": "mlx-community/whisper-small-mlx",
        "medium": "mlx-community/whisper-medium-mlx",
        "large": "mlx-community/whisper-large-v3-mlx",
        "large-v3": "mlx-community/whisper-large-v3-mlx",
        "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
        "turbo": "mlx-community/whisper-large-v3-turbo",
    }

    def __init__(self, model_size="small", models_dir="./models", use_mlx=True):
        self.model_size = model_size
        self.models_dir = models_dir
        self.use_mlx = use_mlx and MLX_AVAILABLE
        self.model = None       # faster-whisper model (None when using MLX)
        self.detector = None    # optional small model used only for language detection
        self.fast_mode = True   # short encoder window for short clips (see short_window.py)
        self.backend = None
        self.mlx_model_path = None

        os.makedirs(models_dir, exist_ok=True)
        self._load_model(model_size)
        self.current_language = "ro"

    @classmethod
    def from_loaded(cls, model_size, backend_info, language="en", models_dir="./models"):
        """Wrap a model that was already loaded (e.g. by a background thread)
        without triggering another load in __init__."""
        engine = cls.__new__(cls)
        engine.model_size = model_size
        engine.models_dir = models_dir
        engine.current_language = language
        engine.backend = backend_info.get("backend", "faster-whisper")
        engine.model = backend_info.get("model")
        engine.detector = backend_info.get("detector")
        engine.fast_mode = True
        engine.mlx_model_path = backend_info.get("mlx_model_path")
        engine.use_mlx = engine.backend == "mlx"
        return engine

    def _load_model(self, model_size):
        """Load only the model needed for the selected backend."""
        start_time = time.time()

        if self.use_mlx and model_size in self.MLX_MODELS:
            try:
                print(f"[Transcription] Loading MLX model: {model_size}...")
                self.mlx_model_path = self.MLX_MODELS[model_size]
                self.backend = "mlx"
                # MLX models load lazily on first transcribe — nothing to download here
                load_time = time.time() - start_time
                print(f"[Transcription] MLX backend ready: {model_size} ({load_time:.2f}s)")
                return  # ← do NOT also load faster-whisper
            except Exception as e:
                print(f"[Transcription] MLX setup failed: {e}, falling back to faster-whisper")

        # faster-whisper path
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError(
                "faster-whisper is not installed and MLX is unavailable. "
                "Install: pip install faster-whisper"
            )

        print(f"[Transcription] Loading faster-whisper model: {model_size}...")
        fw_model = "large-v3-turbo" if model_size == "turbo" else model_size

        self.model = WhisperModel(
            fw_model,
            device="auto",
            compute_type="int8",
            download_root=self.models_dir
        )
        self.backend = "faster-whisper"
        load_time = time.time() - start_time
        print(f"[Transcription] Model loaded: {model_size} via {self.backend} ({load_time:.2f}s)")

    def transcribe(self, audio_data, language=None):
        """
        Transcribe audio to text.

        Args:
            audio_data: numpy float32 array at 16kHz
            language: 'ro', 'en', 'auto' (detect among AUTO_LANGUAGES),
                      or None to use self.current_language

        NOTE: do not pass faster-whisper `hotwords` / `initial_prompt` with
        English terms — it measurably degrades Romanian (diacritics dropped).

        Returns:
            dict: text, language, confidence, segments, transcribe_time, backend
        """
        if language is None:
            language = self.current_language

        start_time = time.time()

        if self.backend == "mlx":
            result = self._transcribe_mlx(audio_data, None if language == "auto" else language)
        else:
            result = self._transcribe_faster_whisper(audio_data, language)

        result["transcribe_time"] = time.time() - start_time
        result["backend"] = self.backend
        return result

    def _transcribe_mlx(self, audio_data, language):
        try:
            result = mlx_whisper.transcribe(
                audio_data,
                path_or_hf_repo=self.mlx_model_path,
                language=language,
                verbose=False,
                temperature=0.0,
                compression_ratio_threshold=None,
                logprob_threshold=None,
                condition_on_previous_text=False,
                word_timestamps=False,
            )
            text = result.get("text", "").strip()
            detected_lang = result.get("language", language)
            segments = result.get("segments", [])
            return {
                "text": text,
                "language": detected_lang,
                "confidence": self._calculate_confidence_mlx(segments),
                "segments": segments,
            }
        except Exception as e:
            print(f"[Transcription] MLX transcription failed: {e}, falling back to faster-whisper")
            # On-demand fallback: load faster-whisper if not already loaded
            if self.model is None:
                if not FASTER_WHISPER_AVAILABLE:
                    return {"text": "", "language": language, "confidence": 0.0, "segments": []}
                fw_model = "large-v3-turbo" if self.model_size == "turbo" else self.model_size
                self.model = WhisperModel(fw_model, device="auto", compute_type="int8",
                                          download_root=self.models_dir)
            return self._transcribe_faster_whisper(audio_data, language)

    def _transcribe_faster_whisper(self, audio_data, language):
        options = dict(
            beam_size=1,           # greedy decoding — much faster, fine for dictation
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
        )
        if self.fast_mode:
            try:
                fast = short_window.transcribe(self.model, audio_data, language, AUTO_LANGUAGES,
                                               detect_fallback=self._detect_language)
            except Exception as e:
                print(f"[Transcription] Fast path failed: {e}")
                fast = None
            if fast is not None:
                return {
                    "text": fast["text"],
                    "language": fast["language"],
                    "confidence": fast["confidence"],
                    "segments": [],
                    "mode": f"fast {fast['window']}s window",
                }
            mode = "full 30s window (fast path fell back)"
        else:
            mode = "full 30s window"

        if language == "auto":
            language = self._detect_language(audio_data)

        segments, info = self.model.transcribe(audio_data, language=language, **options)
        segments_list = list(segments)
        text = " ".join(s.text for s in segments_list).strip()
        return {
            "text": text,
            "language": info.language,
            "confidence": self._calculate_confidence_fw(segments_list),
            "segments": segments_list,
            "mode": mode,
        }

    def _detect_language(self, audio_data) -> str:
        """Pick the most likely of AUTO_LANGUAGES for this clip.

        Uses the small helper `detector` model when one is loaded: with large
        models (turbo/medium/large) detection costs a full extra encoder pass
        (~5s for turbo on CPU), while small does it in ~1s just as reliably.
        """
        model = self.detector or self.model
        try:
            _, _, all_probs = model.detect_language(audio_data, vad_filter=True)
            probs = dict(all_probs or [])
        except Exception as e:  # e.g. VAD found no speech at all
            print(f"[Transcription] Language detection failed: {e}")
            probs = {}
        return max(AUTO_LANGUAGES, key=lambda lang: probs.get(lang, 0.0))

    def _calculate_confidence_mlx(self, segments):
        if not segments:
            return 0.0
        try:
            if isinstance(segments[0], dict):
                logprobs = [s["avg_logprob"] for s in segments if "avg_logprob" in s]
                if logprobs:
                    return min(1.0, max(0.0, 1.0 + sum(logprobs) / len(logprobs)))
        except Exception:
            pass
        return 0.7

    def _calculate_confidence_fw(self, segments_list):
        if not segments_list:
            return 0.0
        avg = sum(s.avg_logprob for s in segments_list) / len(segments_list)
        return min(1.0, max(0.0, 1.0 + avg))

    def set_language(self, lang_code):
        self.current_language = lang_code
        print(f"[Transcription] Language set to: {lang_code}")

    def switch_model(self, model_size):
        if model_size == self.model_size:
            return
        print(f"[Transcription] Switching model from {self.model_size} to {model_size}...")
        self.model_size = model_size
        self.model = None  # release old model before loading new one
        self._load_model(model_size)

    def transcribe_interim(self, audio_data, language=None):
        """Fast transcription for streaming/interim results (lower quality, higher speed)."""
        if language is None:
            language = self.current_language
        try:
            if self.backend == "mlx":
                result = mlx_whisper.transcribe(
                    audio_data,
                    path_or_hf_repo=self.mlx_model_path,
                    language=language,
                    verbose=False,
                    temperature=0.0,
                    compression_ratio_threshold=None,
                    logprob_threshold=None,
                    condition_on_previous_text=False,
                    word_timestamps=False,
                )
                return result.get("text", "").strip()
            else:
                segments, _ = self.model.transcribe(
                    audio_data,
                    language=language,
                    beam_size=1,
                    vad_filter=False,
                    condition_on_previous_text=False,
                    without_timestamps=True,
                )
                return " ".join(s.text for s in segments).strip()
        except Exception as e:
            print(f"[Transcription] Interim transcription error: {e}")
            return ""

    def get_backend_info(self):
        return {
            "backend": self.backend,
            "model_size": self.model_size,
            "mlx_available": MLX_AVAILABLE,
            "using_mlx": self.backend == "mlx",
        }
