# ispeak/transcription.py

import os
import sys
import time

# Try to import MLX-Whisper first (fastest on Apple Silicon)
MLX_AVAILABLE = False
if sys.platform == "darwin":
    try:
        import mlx_whisper
        MLX_AVAILABLE = True
        print("[Transcription] MLX-Whisper available - using optimized Apple Silicon backend")
    except ImportError:
        print("[Transcription] MLX-Whisper not available, falling back to faster-whisper")

# Fallback to faster-whisper
from faster_whisper import WhisperModel


class TranscriptionEngine:
    """
    High-performance transcription engine with MLX-Whisper (Apple Silicon)
    and faster-whisper fallback.

    MLX-Whisper is 30-40% faster on Apple Silicon due to unified memory architecture.
    """

    # Model mapping for MLX (uses HuggingFace repos)
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
        """
        Initialize Whisper model

        Args:
            model_size: "tiny", "base", "small", "medium", "large", "large-v3-turbo", "turbo"
            models_dir: directory to store/cache models
            use_mlx: Try to use MLX-Whisper on Apple Silicon (default: True)

        Note: "small" is recommended for Romanian - significantly better accuracy than "base"
              "turbo" (large-v3-turbo) offers best speed/accuracy tradeoff
        """
        self.model_size = model_size
        self.models_dir = models_dir
        self.use_mlx = use_mlx and MLX_AVAILABLE
        self.model = None
        self.backend = None

        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)

        # Load the model
        self._load_model(model_size)

        self.current_language = "ro"  # Default Romanian

    def _load_model(self, model_size):
        """Load the appropriate model based on available backends."""
        start_time = time.time()

        if self.use_mlx and model_size in self.MLX_MODELS:
            try:
                print(f"[Transcription] Loading MLX model: {model_size}...")
                # MLX-Whisper uses HuggingFace model paths
                self.mlx_model_path = self.MLX_MODELS[model_size]
                self.backend = "mlx"
                load_time = time.time() - start_time
                print(f"[Transcription] MLX backend ready: {model_size} ({load_time:.2f}s)")

                # Always load faster-whisper as fallback, even when using MLX
                print(f"[Transcription] Loading faster-whisper as fallback...")
                fw_start = time.time()
                fw_model = model_size
                if model_size == "turbo":
                    fw_model = "large-v3-turbo"

                self.model = WhisperModel(
                    fw_model,
                    device="auto",
                    compute_type="int8",
                    download_root=self.models_dir
                )
                fw_time = time.time() - fw_start
                print(f"[Transcription] Fallback model loaded ({fw_time:.2f}s)")
                return
            except Exception as e:
                print(f"[Transcription] MLX load failed: {e}, falling back to faster-whisper")

        # Fallback to faster-whisper
        print(f"[Transcription] Loading faster-whisper model: {model_size}...")

        # Map turbo models to faster-whisper names
        fw_model = model_size
        if model_size == "turbo":
            fw_model = "large-v3-turbo"

        self.model = WhisperModel(
            fw_model,
            device="auto",
            compute_type="int8",  # Faster, minimal accuracy loss
            download_root=self.models_dir
        )
        self.backend = "faster-whisper"
        load_time = time.time() - start_time
        print(f"[Transcription] Model loaded: {model_size} via {self.backend} ({load_time:.2f}s)")

    def transcribe(self, audio_data, language=None):
        """
        Transcribe audio to text using the fastest available backend.

        Args:
            audio_data: numpy array of audio samples (float32, 16kHz)
            language: language code ('ro', 'en', etc.) or None for auto-detect

        Returns:
            dict with 'text', 'language', 'confidence', 'segments'
        """
        if language is None:
            language = self.current_language

        start_time = time.time()

        if self.backend == "mlx":
            result = self._transcribe_mlx(audio_data, language)
        else:
            result = self._transcribe_faster_whisper(audio_data, language)

        transcribe_time = time.time() - start_time
        result["transcribe_time"] = transcribe_time
        result["backend"] = self.backend

        return result

    def _transcribe_mlx(self, audio_data, language):
        """Transcribe using MLX-Whisper (Apple Silicon optimized)."""
        try:
            # MLX-Whisper transcribe function
            result = mlx_whisper.transcribe(
                audio_data,
                path_or_hf_repo=self.mlx_model_path,
                language=language,
                verbose=False,            # Disable verbose output
                # Speed optimizations - single pass, no retries
                temperature=0.0,          # Fixed temperature, no fallback retries
                compression_ratio_threshold=None,  # Disable quality-based retries
                logprob_threshold=None,   # Disable quality-based retries
                condition_on_previous_text=False,  # Faster for short dictation
                word_timestamps=False,    # Don't need word-level timestamps
            )

            text = result.get("text", "").strip()
            detected_lang = result.get("language", language)
            segments = result.get("segments", [])

            # Calculate confidence from segments if available
            confidence_score = self._calculate_confidence(segments)

            return {
                "text": text,
                "language": detected_lang,
                "confidence": confidence_score,
                "segments": segments
            }
        except Exception as e:
            print(f"[Transcription] MLX transcription failed: {e}, falling back to faster-whisper")
            # Fallback to faster-whisper for this transcription
            return self._transcribe_faster_whisper(audio_data, language)

    def _transcribe_faster_whisper(self, audio_data, language):
        """Transcribe using faster-whisper."""
        # Optimized transcription parameters
        segments, info = self.model.transcribe(
            audio_data,
            language=language,
            beam_size=3,                  # Reduced from 5 (~30% faster, minimal accuracy loss)
            vad_filter=True,              # Filter out silence
            vad_parameters=dict(
                min_silence_duration_ms=300  # Reduced from 500ms for faster response
            ),
            condition_on_previous_text=False,  # Faster for short dictation
            no_speech_threshold=0.6,      # Skip segments with high no-speech probability
        )

        # Combine all segments and calculate confidence
        segments_list = list(segments)
        text = " ".join([segment.text for segment in segments_list])

        confidence_score = self._calculate_confidence_fw(segments_list)

        return {
            "text": text.strip(),
            "language": info.language,
            "confidence": confidence_score,
            "segments": segments_list
        }

    def _calculate_confidence(self, segments):
        """Calculate confidence score from MLX segments."""
        if not segments:
            return 0.0

        # MLX segments may have different structure
        try:
            if isinstance(segments[0], dict):
                # Try to get avg_logprob if available
                logprobs = [s.get("avg_logprob", -0.5) for s in segments if "avg_logprob" in s]
                if logprobs:
                    avg_confidence = sum(logprobs) / len(logprobs)
                    return min(1.0, max(0.0, 1.0 + avg_confidence))
        except Exception:
            pass

        return 0.7  # Default confidence if we can't calculate

    def _calculate_confidence_fw(self, segments_list):
        """Calculate confidence score from faster-whisper segments."""
        if not segments_list:
            return 0.0

        # avg_logprob is typically in range [-1, 0], closer to 0 = higher confidence
        avg_confidence = sum(segment.avg_logprob for segment in segments_list) / len(segments_list)
        # Convert log probability to a 0-1 scale (approximate)
        return min(1.0, max(0.0, 1.0 + avg_confidence))

    def set_language(self, lang_code):
        """Switch language: 'ro', 'en', etc."""
        self.current_language = lang_code
        print(f"[Transcription] Language set to: {lang_code}")

    def switch_model(self, model_size):
        """Switch to a different model size."""
        if model_size == self.model_size:
            return

        print(f"[Transcription] Switching model from {self.model_size} to {model_size}...")
        self.model_size = model_size
        self._load_model(model_size)

    def transcribe_interim(self, audio_data, language=None):
        """
        Fast transcription for interim/streaming results.

        Uses faster settings (lower beam size, no VAD) for quick feedback.
        Quality may be slightly lower than full transcribe().

        Args:
            audio_data: numpy array of audio samples (float32, 16kHz)
            language: language code or None

        Returns:
            str: transcribed text (just the text, no metadata)
        """
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
                # faster-whisper with speed-optimized settings
                segments, _ = self.model.transcribe(
                    audio_data,
                    language=language,
                    beam_size=1,  # Fastest
                    vad_filter=False,  # Skip VAD for speed
                    condition_on_previous_text=False,
                    without_timestamps=True,  # Skip timestamp calculation
                )
                text = " ".join([segment.text for segment in segments])
                return text.strip()
        except Exception as e:
            print(f"[Transcription] Interim transcription error: {e}")
            return ""

    def get_backend_info(self):
        """Get information about the current backend."""
        return {
            "backend": self.backend,
            "model_size": self.model_size,
            "mlx_available": MLX_AVAILABLE,
            "using_mlx": self.backend == "mlx"
        }
