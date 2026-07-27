"""Compatibility helpers for TorchAudio's 2.8 to 2.10 I/O transition."""
from __future__ import annotations

from typing import NamedTuple


class AudioMetaData(NamedTuple):
    """TorchAudio 2.8-compatible metadata shape used by pyannote 3.x."""

    sample_rate: int
    num_frames: int
    num_channels: int
    bits_per_sample: int
    encoding: str


def _soundfile_info(file, **_kwargs) -> AudioMetaData:
    """Implement removed ``torchaudio.info`` with the existing SoundFile dep."""
    import soundfile

    info = soundfile.info(file)
    subtype = info.subtype or ""
    bits_per_sample = {
        "PCM_S8": 8,
        "PCM_U8": 8,
        "PCM_16": 16,
        "PCM_24": 24,
        "PCM_32": 32,
        "FLOAT": 32,
        "DOUBLE": 64,
        "ULAW": 8,
        "ALAW": 8,
    }.get(subtype, 0)
    if subtype == "PCM_U8":
        encoding = "PCM_U"
    elif subtype.startswith("PCM_"):
        encoding = "PCM_S"
    elif subtype in {"FLOAT", "DOUBLE"}:
        encoding = "PCM_F"
    else:
        encoding = subtype
    return AudioMetaData(
        sample_rate=info.samplerate,
        num_frames=info.frames,
        num_channels=info.channels,
        bits_per_sample=bits_per_sample,
        encoding=encoding,
    )


def install_legacy_io_compat(torchaudio) -> set[str]:
    """Restore I/O symbols removed in TorchAudio 2.9+ for pyannote 3.x."""
    installed: set[str] = set()
    if not hasattr(torchaudio, "AudioMetaData"):
        torchaudio.AudioMetaData = AudioMetaData
        installed.add("AudioMetaData")
    if not callable(getattr(torchaudio, "list_audio_backends", None)):
        torchaudio.list_audio_backends = lambda: ["soundfile"]
        installed.add("list_audio_backends")
    if not callable(getattr(torchaudio, "info", None)):
        torchaudio.info = _soundfile_info
        installed.add("info")
    return installed


def select_soundfile_backend(torchaudio) -> bool:
    """Select SoundFile on legacy TorchAudio; 2.9+ removed this no-op API."""
    setter = getattr(torchaudio, "set_audio_backend", None)
    if not callable(setter):
        return False
    try:
        setter("soundfile")
        return True
    except Exception:
        return False


__all__ = ["AudioMetaData", "install_legacy_io_compat", "select_soundfile_backend"]
