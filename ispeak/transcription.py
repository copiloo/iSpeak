# ispeak/transcription.py

import os
import sys
import time

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
        self.backend = None
        self.mlx_model_path = None

        os.makedirs(models_dir, exist_ok=True)
        self._load_model(model_size)
        self.current_language = "ro"

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
            language: language code ('ro', 'en', …) or None for auto-detect

        Returns:
            dict: text, language, confidence, segments, transcribe_time, backend
        """
        if language is None:
            language = self.current_language

        start_time = time.time()

        if self.backend == "mlx":
            result = self._transcribe_mlx(audio_data, language)
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
        segments, info = self.model.transcribe(
            audio_data,
            language=language,
            beam_size=1,           # greedy decoding — much faster, fine for dictation
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
        )
        segments_list = list(segments)
        text = " ".join(s.text for s in segments_list).strip()
        return {
            "text": text,
            "language": info.language,
            "confidence": self._calculate_confidence_fw(segments_list),
            "segments": segments_list,
        }

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
