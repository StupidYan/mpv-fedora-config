#!/usr/bin/env python3
"""Fedora/Linux handler for External Player's ush:// URLs.

Payload format:
    ush://APP_NAME?base64(gzip(JSON array))

For compatibility with the upstream Windows userscript, a legacy shell-style
string is accepted as input, but it is parsed into argv without a shell.
"""

from __future__ import annotations

import base64
import gzip
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

MAX_URI_LENGTH = 32_768
MAX_PAYLOAD_LENGTH = 65_536
MAX_ARGV_LENGTH = 256
MAX_LOG_SIZE = 1_048_576


class HandlerError(Exception):
    """An expected user-facing handler error."""


def config_path() -> Path:
    override = os.environ.get("MPV_USH_HANDLER_CONFIG")
    if override:
        return Path(override).expanduser()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser()
    return config_home / "mpv" / "external-player-handler.json"


def load_apps() -> dict[str, str]:
    path = config_path()
    apps: dict[str, str] = {}

    if path.is_file():
        try:
            data: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise HandlerError(f"Invalid handler configuration: {path}") from error

        entries = data.get("apps") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            raise HandlerError(f"Configuration must contain an 'apps' array: {path}")

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            executable = entry.get("path")
            if isinstance(name, str) and isinstance(executable, str):
                apps[name] = executable

    # A default is useful immediately after cloning the repository. Users can
    # add more entries, but a web page can never choose an arbitrary executable.
    if "MPV" not in apps:
        mpv = shutil.which("mpv") or "/usr/bin/mpv"
        apps["MPV"] = mpv
    return apps


def decode_payload(encoded: str) -> str:
    if len(encoded) > MAX_PAYLOAD_LENGTH:
        raise HandlerError("Encoded payload is too large")

    # urdecode() intentionally does not treat '+' as a space. Some desktop
    # launchers nevertheless convert Base64 '+' to a literal space. Accept that
    # damaged form only when replacing spaces back to '+' yields valid Base64.
    candidates = [encoded]
    repaired = encoded.replace(" ", "+")
    if repaired != encoded:
        candidates.append(repaired)

    last_error: Exception | None = None
    compressed: bytes | None = None
    for candidate in candidates:
        try:
            padded = candidate + ("=" * ((-len(candidate)) % 4))
            compressed = base64.b64decode(padded, validate=True)
            break
        except (ValueError, base64.binascii.Error) as error:
            last_error = error

    if compressed is None:
        raise HandlerError("Payload is not valid Base64") from last_error

    try:
        raw = gzip.decompress(compressed)
    except (OSError, EOFError) as error:
        raise HandlerError("Payload is not valid gzip data") from error

    if len(raw) > MAX_PAYLOAD_LENGTH:
        raise HandlerError("Decoded payload is too large")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HandlerError("Decoded payload is not UTF-8") from error


def payload_to_argv(payload: str) -> list[str]:
    try:
        data: Any = json.loads(payload)
    except json.JSONDecodeError:
        # Compatibility with the upstream Windows userscript.
        try:
            argv = shlex.split(payload, posix=True)
        except ValueError as error:
            raise HandlerError("Legacy payload contains unbalanced quoting") from error
    else:
        if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
            raise HandlerError("JSON payload must be an array of strings")
        argv = data

    if not argv or len(argv) > MAX_ARGV_LENGTH:
        raise HandlerError("Payload has an invalid argument count")
    if any("\x00" in item for item in argv):
        raise HandlerError("Payload contains a NUL character")
    return argv


def parse_ush_url(uri: str) -> tuple[str, list[str], str]:
    if len(uri) > MAX_URI_LENGTH:
        raise HandlerError("URI is too large")

    parsed = urlsplit(uri)
    if parsed.scheme.lower() != "ush" or not parsed.netloc or not parsed.query:
        raise HandlerError("URI must have the form ush://APP?PAYLOAD")

    app_name = unquote(parsed.netloc).strip()
    encoded_payload = unquote(parsed.query).strip()
    if not app_name or not encoded_payload:
        raise HandlerError("URI application name or payload is empty")

    payload = decode_payload(encoded_payload)
    payload_kind = "json" if payload.lstrip().startswith("[") else "legacy"
    return app_name, payload_to_argv(payload), payload_kind


def resolve_executable(app_name: str) -> Path:
    apps = load_apps()
    # xdg-open and some desktop portals normalize the URI host to lower case,
    # turning `ush://MPV?...` into `ush://mpv?...`. Match configured names
    # case-insensitively while still allowing only locally configured apps.
    requested_name = app_name.casefold()
    executable = None
    for configured_name, configured_path in apps.items():
        if configured_name.casefold() == requested_name:
            executable = configured_path
            break
    if not executable:
        supported = ", ".join(sorted(apps))
        raise HandlerError(f"Application is not configured: {app_name} (configured: {supported})")

    path = Path(executable).expanduser()
    if not path.is_absolute():
        raise HandlerError(f"Configured executable must be an absolute path: {path}")
    if not path.is_file() or not os.access(path, os.X_OK):
        raise HandlerError(f"Configured executable is unavailable: {path}")
    return path


def notify_error(message: str) -> None:
    # Keep notification text generic: URLs, headers, cookies, and media titles
    # are intentionally never copied into desktop notifications.
    command = shutil.which("notify-send")
    if not command:
        return
    try:
        subprocess.run(
            [command, "--app-name=External Player Fedora", "External Player failed", message],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def handler_log_path() -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")).expanduser()
    return state_home / "mpv-fedora" / "external-handler.log"


def write_log(message: str) -> Path:
    path = handler_log_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.touch(mode=0o600, exist_ok=True)

    # Keep debug data bounded. Do not retain a compressed old copy because mpv
    # output can contain URLs, headers, cookies, or media titles.
    if path.stat().st_size > MAX_LOG_SIZE:
        path.unlink(missing_ok=True)
        path.touch(mode=0o600)

    timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
    with path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(f"[{timestamp}] {message}\n")
    return path


def build_launch_environment() -> dict[str, str]:
    environment = os.environ.copy()
    runtime_dir = f"/run/user/{os.getuid()}"

    # Desktop activations normally inherit these values. Some browser and
    # portal combinations do not, so provide the standard user-session values.
    environment.setdefault("XDG_RUNTIME_DIR", runtime_dir)
    environment.setdefault("WAYLAND_DISPLAY", "wayland-0")
    environment.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path={runtime_dir}/bus")
    return environment


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: mpv-fedora-ush-handler 'ush://APP?PAYLOAD'", file=sys.stderr)
        return 2

    try:
        app_name, argv, payload_kind = parse_ush_url(sys.argv[1])
        executable = resolve_executable(app_name)

        if os.environ.get("MPV_USH_HANDLER_DRY_RUN") == "1":
            print(json.dumps({"app": app_name, "executable": str(executable), "argv": argv}, ensure_ascii=False, indent=2))
            return 0

        launch_argv = list(argv)
        if app_name.casefold() == "mpv" and not any(arg.startswith("--player-operation-mode=") for arg in launch_argv):
            launch_argv.insert(0, "--player-operation-mode=pseudo-gui")

        environment = build_launch_environment()
        log_path = write_log(
            f"launch app={app_name!r} executable={executable!s} "
            f"payload={payload_kind} args={len(argv)} "
            f"wayland={environment.get('WAYLAND_DISPLAY', '')!r} "
            f"runtime={environment.get('XDG_RUNTIME_DIR', '')!r}"
        )

        # Detach from the browser's activation process. mpv is launched directly
        # with an argv list; no shell is involved. Keep mpv output in a
        # user-private state file because silent launch failures are otherwise
        # invisible when the browser discards desktop activation output.
        with log_path.open("a", encoding="utf-8", newline="\n") as output_log:
            timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
            print(f"[{timestamp}] mpv output begin", file=output_log, flush=True)
            process = subprocess.Popen(
                [str(executable), *launch_argv],
                cwd=Path.home(),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=output_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        # Most invalid URLs, refused headers, and display initialization errors
        # happen immediately. Wait briefly so quick failures are captured.
        time.sleep(2)
        return_code = process.poll()
        if return_code is None:
            write_log(f"running pid={process.pid}")
        else:
            write_log(f"exited pid={process.pid} return_code={return_code}")
        return 0 if return_code is None or return_code == 0 else 1
    except HandlerError as error:
        print(f"External Player Fedora: {error}", file=sys.stderr)
        write_log(f"handler error: {error}")
        notify_error(str(error))
        return 1
    except OSError as error:
        # Do not include the OS error string if it can contain a path/URL.
        print("External Player Fedora: failed to launch the configured application", file=sys.stderr)
        write_log(f"launch exception: {error}")
        notify_error("Failed to launch the configured application")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
