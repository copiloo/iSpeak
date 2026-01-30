# ispeak/transcription.py

from faster_whisper import WhisperModel
import os

class TranscriptionEngine:
    def __init__(self, model_size="small", models_dir="./models"):
        """
        Initialize Whisper model
        model_size: "tiny", "base", "small", "medium", "large"
        models_dir: directory to store/cache models

        Note: "small" is recommended for Romanian - significantly better accuracy than "base"
        """
        self.model_size = model_size
        self.models_dir = models_dir

        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)

        # device: "cpu", "cuda", or "auto"
        # compute_type: "int8" for speed, "float16" for quality
        print(f"Loading {model_size} model...")
        self.model = WhisperModel(
            model_size,
            device="auto",  # Use Metal on M-series Macs
            compute_type="int8",  # Faster, minimal accuracy loss
            download_root=models_dir
        )
        print(f"Model loaded: {model_size}")

        self.current_language = "ro"  # Default Romanian

    def transcribe(self, audio_data, language=None):
        """
        Transcribe audio to text
        Returns: dict with 'text', 'language', 'segments'
        """
        if language is None:
            language = self.current_language

        # Transcribe with options
        segments, info = self.model.transcribe(
            audio_data,
            language=language,
            beam_size=5,          # Quality vs speed tradeoff
            vad_filter=True,      # Filter out silence
            vad_parameters=dict(
                min_silence_duration_ms=500  # 500ms silence = pause
            )
        )

        # Combine all segments
        text = " ".join([segment.text for segment in segments])

        return {
            "text": text.strip(),
            "language": info.language,
            "segments": list(segments)
        }

    def transcribe_realtime(self, audio_data):
        """
        Faster transcription for real-time use
        Lower accuracy but instant feedback
        """
        segments, info = self.model.transcribe(
            audio_data,
            language=self.current_language,
            beam_size=1,      # Fastest beam search
            vad_filter=True,
            without_timestamps=True  # Skip timestamp calculation
        )

        text = " ".join([segment.text for segment in segments])
        return text.strip()

    def set_language(self, lang_code):
        """Switch language: 'ro', 'en', etc."""
        self.current_language = lang_code
        print(f"Language set to: {lang_code}")

    def get_supported_languages(self):
        """Return list of supported languages"""
        return [
            "en", "ro", "es", "fr", "de", "it", "pt", "nl",
            "pl", "ru", "ja", "ko", "zh", "ar", "hi", "tr"
            # Whisper supports 99 languages total
        ]
