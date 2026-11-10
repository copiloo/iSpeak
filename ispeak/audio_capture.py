# ispeak/audio_capture.py

import logging

import numpy as np
import pyaudio

_log = logging.getLogger("iSpeak")

# Pseudo-devices that just mean "whatever Windows' default is" — we offer our
# own "System default" entry instead.
_PSEUDO_DEVICE_MARKERS = ("Sound Mapper", "Primary Sound Capture")


def _fix_name(name: str) -> str:
    """PyAudio decodes Windows' UTF-8 device names as Windows-1252, so a
    curly apostrophe (U+2019) shows up as the three characters U+00E2 U+20AC
    U+2122, and Romanian letters get mangled the same way.  Undo that when the
    name round-trips cleanly; otherwise it was decoded correctly - keep it."""
    try:
        return name.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


class AudioCapture:
    def __init__(self,
                 rate=16000,       # Whisper expects 16kHz
                 chunk_size=1024,  # Process in small chunks
                 channels=1,       # Mono audio
                 device_name=""):  # "" = Windows default recording device

        self.rate = rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_name = device_name or ""
        self.audio_buffer = []  # Unbounded — recording limited by key hold duration
        self.is_recording = False
        # Name of the mic actually used for the last recording, and whether the
        # selected mic was missing so we fell back to the default.
        self.active_device_name = ""
        self.used_fallback = False

        self.stream = None
        self.p = pyaudio.PyAudio()

    # ------------------------------------------------------------------
    # Device enumeration / selection
    # ------------------------------------------------------------------

    def _rescan(self):
        """Re-enumerate devices.  PortAudio only scans at initialisation, so
        this is what picks up a headset plugged in (or a Windows default
        changed) after the app started.  Cheap (~25ms)."""
        if self.stream is not None:
            return  # never while a stream is open
        try:
            self.p.terminate()
        except Exception:
            pass
        self.p = pyaudio.PyAudio()

    def _input_devices(self):
        """[(mme_index, full_name)] for real input devices, one entry each.

        Streams are opened through MME (the default host API, which resamples
        to 16kHz for us), but MME truncates names to 31 characters, so the
        full name is taken from the matching DirectSound entry when there is one.
        """
        mme = self.p.get_default_host_api_info()["index"]
        mme_devices, other_names = [], []
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) <= 0:
                continue
            name = _fix_name(info.get("name", ""))
            if any(marker in name for marker in _PSEUDO_DEVICE_MARKERS):
                continue
            if info.get("hostApi") == mme:
                mme_devices.append((i, name))
            else:
                other_names.append(name)

        result = []
        for index, short in mme_devices:
            longer = [n for n in other_names if n.startswith(short) and "\n" not in n]
            result.append((index, min(longer, key=len) if longer else short))
        return result

    def list_input_devices(self):
        """Full names of the currently connected microphones."""
        self._rescan()
        try:
            return [name for _, name in self._input_devices()]
        except Exception as e:
            _log.warning(f"Could not list input devices: {e}")
            return []

    def default_device_name(self) -> str:
        try:
            return _fix_name(self.p.get_default_input_device_info().get("name", ""))
        except Exception:
            return ""

    def set_device(self, device_name: str):
        """Select the mic for future recordings ("" = Windows default)."""
        self.device_name = device_name or ""

    def _resolve_device(self):
        """(MME index, full name) of the selected mic, or (None, None) for the
        Windows default / when the selected mic isn't connected."""
        if not self.device_name:
            return None, None
        devices = self._input_devices()
        for index, name in devices:
            if name == self.device_name:
                return index, name
        # Fall back to prefix matching (MME's truncated names / renamed endpoints)
        for index, name in devices:
            if self.device_name.startswith(name) or name.startswith(self.device_name):
                return index, name
        return None, None

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _open_stream(self, device_index):
        """Open a PyAudio stream on the given device index (None = system default)."""
        return self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )

    def _open_selected_or_default(self):
        index, name = self._resolve_device()
        self.used_fallback = bool(self.device_name) and index is None
        if self.used_fallback:
            _log.warning(f"Selected microphone '{self.device_name}' not found — using the Windows default")
        self.active_device_name = name if index is not None else self.default_device_name()
        self.stream = self._open_stream(index)
        self.stream.start_stream()

    def start_recording(self):
        """Start capturing audio from the selected (or default) microphone."""
        self.is_recording = True
        self.audio_buffer.clear()

        try:
            self._rescan()
            self._open_selected_or_default()
        except Exception as e:
            _log.warning(f"Could not open microphone '{self.device_name or 'default'}': {e}")
            if self.stream is not None:  # opened but failed to start
                try:
                    self.stream.close()
                except Exception:
                    pass
            self.stream = None
            # Last resort: the Windows default device
            try:
                self._rescan()
                self.active_device_name = self.default_device_name()
                self.used_fallback = bool(self.device_name)
                self.stream = self._open_stream(None)
                self.stream.start_stream()
            except Exception as e2:
                _log.error(f"Failed to open any microphone: {e2}")
                self.stream = None
                self.is_recording = False
                raise

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Called continuously while recording."""
        if self.is_recording:
            audio_chunk = np.frombuffer(in_data, dtype=np.int16)
            self.audio_buffer.append(audio_chunk)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        """Stop and return accumulated audio as float32."""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if len(self.audio_buffer) == 0:
            print("[Audio] ⚠️  No audio data captured")
            return np.array([], dtype=np.float32)

        audio_float = np.concatenate(list(self.audio_buffer)).astype(np.float32) / 32768.0

        audio_level = np.abs(audio_float).max()
        audio_rms = np.sqrt(np.mean(audio_float ** 2))

        if audio_level < 0.001:
            _log.warning(f"Audio from '{self.active_device_name}' is silent (max level {audio_level:.6f})")
        else:
            print(f"[Audio] Audio captured: max={audio_level:.3f}, rms={audio_rms:.3f}")

        return audio_float

    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            try:
                self.stream.close()
            except Exception as e:
                print(f"[Audio] Warning: Error closing stream: {e}")
            self.stream = None
        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                print(f"[Audio] Warning: Error terminating PyAudio: {e}")
            self.p = None
