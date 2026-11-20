"""User-data paths and durable JSON storage for CORRIDOR SLAYER."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def user_data_dir() -> Path:
    """Return the per-user writable data directory without creating it."""
    override = os.environ.get("CS_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "Corridor Slayer"
        return Path.home() / "AppData" / "Roaming" / "Corridor Slayer"
    base = os.environ.get("XDG_DATA_HOME")
    return (Path(base).expanduser() if base else Path.home() / ".local" / "share") \
        / "corridor-slayer"


def data_file(name: str) -> Path:
    return user_data_dir() / name


def legacy_file(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def _copy_legacy_once(target: Path, legacy: Path | None) -> Path:
    """Copy a legacy file into user data without removing or truncating it."""
    if target.exists() or legacy is None or not legacy.is_file():
        return target
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with legacy.open("rb") as src:
            raw = src.read()
        _atomic_write_bytes(target, raw)
    except OSError:
        # Keep old installations playable if the user-data directory is
        # temporarily unavailable. Saving still reports the actual failure.
        return legacy
    return target


def read_text(target: Path, legacy: Path | None = None,
              encoding: str = "utf-8") -> str:
    source = _copy_legacy_once(target, legacy)
    return source.read_text(encoding=encoding)


def read_json(target: Path, legacy: Path | None = None,
              default=None):
    try:
        return json.loads(read_text(target, legacy))
    except FileNotFoundError:
        return default


def write_json(target: Path, payload, *, indent: int = 2) -> None:
    text = json.dumps(payload, indent=indent, ensure_ascii=False)
    _atomic_write_bytes(target, text.encode("utf-8"))


def _atomic_write_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, target)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
