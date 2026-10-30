# External Player Fedora integration

This directory adapts [External Player](https://github.com/LuckyPuppy514/external-player) for Fedora Linux.

The upstream userscript opens URLs such as:

```text
ush://MPV?base64(gzip(arguments))
```

The upstream `LuckyPuppy514/url-scheme-handler` implements this protocol for Windows by writing registry keys and launching an executable through WinAPI. Fedora therefore needs a separate native handler.

## Components

| File | Purpose |
|---|---|
| `external-player-fedora.user.js` | Fedora fork of the Tampermonkey userscript |
| `fedora-ush-handler.py` | Native Linux `ush://` protocol handler |
| `install-fedora.sh` | Installs and uninstalls the user-local handler |

## Install

Install the mpv configuration first from the repository root:

```bash
cd /path/to/mpv-fedora-config
./install.sh
```

Then install this protocol handler:

```bash
cd integrations/external-player
./install-fedora.sh
```

Installed files:

```text
~/.local/bin/mpv-fedora-ush-handler
~/.local/share/applications/mpv-fedora-ush-handler.desktop
~/.config/mpv/external-player-handler.json
```

The desktop entry registers:

```text
x-scheme-handler/ush
```

Check the association:

```bash
xdg-mime query default x-scheme-handler/ush
```

Expected result:

```text
mpv-fedora-ush-handler.desktop
```

## Install the userscript

1. Open your browser's Tampermonkey dashboard.
2. Disable or remove the original `External Player 1.3.1` script.
3. Create a new script and paste the contents of:

   ```text
   external-player-fedora.user.js
   ```

4. Save and reload the video website.

The Fedora fork is named **External Player Fedora** so it does not silently overwrite the upstream script. Its internal configuration version is also increased, which migrates the existing MPV player entry to the Linux-safe argument encoder.

The first site activation may ask the browser for permission to open an external application. Choose the `mpv Fedora USH Handler`.

## Application mapping

`~/.config/mpv/external-player-handler.json` maps protocol application names to local executables:

```json
{
  "apps": [
    {
      "name": "MPV",
      "path": "/usr/bin/mpv"
    }
  ]
}
```

The installer creates this file with the current `mpv` path. Additional entries may be added manually. Every path must be absolute and executable.

## Fedora-specific changes

Compared with the upstream MPV player event:

- MPV is marked as a Linux player.
- Arguments are encoded as a JSON array rather than a shell-style string.
- URLs, cookies, referers, and titles cannot introduce additional shell tokens.
- Origin, referer, and cookie fields are merged into one `--http-header-fields` option.
- Bilibili's `cid` is retained through `--script-opts-append=cid=...`, allowing `uosc_danmaku` to load the matching danmaku.
- The fallback path used when a site blocks `unsafe-eval` uses the same JSON encoder.
- The userscript's update URLs point to this repository's Fedora fork.

## Handler compatibility and security

The native handler:

- decodes URL percent-encoding;
- decodes Base64 and gzip;
- accepts the Fedora fork's JSON array;
- accepts the upstream script's legacy shell-style string for compatibility;
- converts arguments to an argv list without invoking a shell;
- launches the configured executable directly in a new session;
- permits only application names listed in the local configuration;
- never lets a web page choose an arbitrary executable path;
- limits URI, payload, and argument sizes;
- omits URLs, cookies, headers, and titles from desktop notifications.

For compatibility with launchers that corrupt Base64 `+` characters into spaces, the handler repairs that specific form only if the repaired string is valid Base64.

## Test

A dry-run without launching mpv:

```bash
MPV_USH_HANDLER_DRY_RUN=1 \
MPV_USH_HANDLER_CONFIG="$HOME/.config/mpv/external-player-handler.json" \
~/.local/bin/mpv-fedora-ush-handler 'ush://MPV?YOUR_PAYLOAD'
```

For a real browser test:

1. Open a supported Bilibili video page.
2. Click the External Player Fedora MPV button.
3. Accept the browser's external-protocol prompt if requested.
4. Confirm that mpv starts and `uosc_danmaku` reports the danmaku count.

Expected mpv output includes:

```text
Using hardware decoding (vaapi-copy)
AO: [pipewire]
[uosc_danmaku] 已解析 N 条弹幕
```

## Uninstall

```bash
cd integrations/external-player
./install-fedora.sh --uninstall
```

This removes the handler executable, desktop entry, and `ush://` association. It does not modify `~/.config/mpv` or uninstall the userscript.
