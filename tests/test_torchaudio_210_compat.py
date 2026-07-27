"""TorchAudio 2.9+ removed metadata and global backend/info APIs."""
import sys
from types import SimpleNamespace

from core.torchaudio_compat import (
    AudioMetaData,
    install_legacy_io_compat,
    select_soundfile_backend,
)


def test_removed_pyannote_io_symbols_are_restored():
    module = SimpleNamespace()

    assert install_legacy_io_compat(module) == {
        "AudioMetaData", "info", "list_audio_backends",
    }
    metadata = module.AudioMetaData(16000, 32000, 1, 16, "PCM_S")
    assert metadata == AudioMetaData(16000, 32000, 1, 16, "PCM_S")
    assert metadata.sample_rate == 16000
    assert module.list_audio_backends() == ["soundfile"]


def test_existing_pyannote_io_symbols_are_preserved():
    sentinel = object()
    native_info = lambda *_args, **_kwargs: sentinel
    native_backends = lambda: ["ffmpeg"]
    module = SimpleNamespace(
        AudioMetaData=sentinel,
        info=native_info,
        list_audio_backends=native_backends,
    )

    assert install_legacy_io_compat(module) == set()
    assert module.AudioMetaData is sentinel
    assert module.info is native_info
    assert module.list_audio_backends is native_backends


def test_removed_info_uses_soundfile_metadata(monkeypatch):
    soundfile = SimpleNamespace(
        info=lambda _file: SimpleNamespace(
            samplerate=24000,
            frames=48000,
            channels=2,
            subtype="PCM_24",
        )
    )
    monkeypatch.setitem(sys.modules, "soundfile", soundfile)
    module = SimpleNamespace()
    install_legacy_io_compat(module)

    metadata = module.info("reference.wav", backend="soundfile")

    assert metadata == AudioMetaData(24000, 48000, 2, 24, "PCM_S")


def test_removed_set_audio_backend_does_not_break_startup():
    assert select_soundfile_backend(SimpleNamespace()) is False


def test_legacy_set_audio_backend_is_still_selected():
    selected = []
    module = SimpleNamespace(set_audio_backend=selected.append)
    assert select_soundfile_backend(module) is True
    assert selected == ["soundfile"]
