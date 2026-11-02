# External Player Fedora integration

This directory adapts [External Player](https://github.com/LuckyPuppy514/external-player) for Fedora Linux.

Target environment: Fedora 44 with KDE Plasma (Wayland), as declared in the repository root README. The integration was developed and verified on this combination only (Plasma 6.8.2, xdg-desktop-portal 1.22.1, Chromium 156.0.8078.73). GNOME and every other desktop are untested, and no support is claimed for them. For orientation only: the handler is a plain Python 3 executable, the installer uses the XDG user directories (`~/.local/bin`, `~/.local/share/applications`) and `gio`/`xdg-mime` associations, and the desktop entry's `X-KDE-Protocols` key is a KDE-specific hint — none of this is a cross-desktop compatibility statement.

The upstream userscript opens URLs such as:

```text
ush://MPV?base64(gzip(arguments))
```

The upstream `LuckyPuppy514/url-scheme-handler` implements this protocol for Windows by writing registry keys and launching an executable through WinAPI. Fedora therefore needs a separate native handler.

## Components

| File | Purpose |
|---|---|
| `external-player-fedora.user.js` | Fedora fork of the Violentmonkey userscript |
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

1. Open the raw script URL:

   ```text
   https://raw.githubusercontent.com/StupidYan/mpv-fedora-config/main/integrations/external-player/external-player-fedora.user.js
   ```

2. Let Violentmonkey install or update the script.
3. If you prefer a manual update, paste the repository file over the existing `External Player` script and save.
4. Reload the video website.

The fork keeps the upstream script name and namespace so Violentmonkey treats it as an update to your existing installation. Its internal configuration version is increased, which migrates the existing MPV player entry to the Linux-safe argument encoder.

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
- launches MPV in `--player-operation-mode=pseudo-gui` mode;
- fills in the standard user Wayland runtime environment when a browser activation omits it;
- writes launch diagnostics and mpv output to a user-private state log.

The private log is:

```text
~/.local/state/mpv-fedora/external-handler.log
```

The file is mode `0600`, belongs only to the current user, and is truncated when it grows beyond 1 MiB. It can contain mpv terminal output, which may include media URLs, headers, cookies, or titles. Do not paste the full file publicly without redacting it.

For compatibility with launchers that corrupt Base64 `+` characters into spaces, the handler repairs that specific form only if the repaired string is valid Base64.

## Chromium and the XDG desktop portal

Recent Chromium releases do not run `xdg-open` for external protocols. They call the XDG desktop portal (`org.freedesktop.portal.OpenURI`) instead, and the portal keeps its own "latest choice" memory for each scheme in the permission store (`desktop-used-apps` table).

Everything in this section was observed on this machine via D-Bus tracing: Chromium 156 called `org.freedesktop.portal.OpenURI`, and the request was served by the `xdg-desktop-portal` service (1.22.1) alone, which consulted the permission store and launched the desktop file itself; `xdg-desktop-portal-kde` (6.8.2) was not involved. Fedora 44 also packages `xdg-desktop-portal-gnome`, but GNOME was not tested and it is unknown whether it is affected in the same way; the commands below document what was verified on KDE Plasma, not cross-desktop support.

That memory takes priority over the `mimeapps.list` default. If a portal app chooser ever appeared for `ush://` and the plain `mpv` player was selected, the portal forever forwards the raw `ush://...` URL to `/usr/share/applications/mpv.desktop`. mpv cannot open such a URL and exits silently, so the browser reports a successful launch while nothing appears.

The installer prevents and repairs this by seeding the permission store with this handler as the latest choice for `x-scheme-handler/ush`, with a usage count already at the portal's threshold, which also suppresses the portal's app chooser:

```bash
busctl --user call \
    org.freedesktop.impl.portal.PermissionStore \
    /org/freedesktop/impl/portal/PermissionStore \
    org.freedesktop.impl.portal.PermissionStore \
    SetPermission sbssas \
    "desktop-used-apps" true "x-scheme-handler/ush" "" \
    3 "mpv-fedora-ush-handler.desktop" "3" "3"
```

Inspect the current state with:

```bash
busctl --user call \
    org.freedesktop.impl.portal.PermissionStore \
    /org/freedesktop/impl/portal/PermissionStore \
    org.freedesktop.impl.portal.PermissionStore \
    Lookup ss "desktop-used-apps" "x-scheme-handler/ush"
```

An entry that does not name `mpv-fedora-ush-handler.desktop` first means the portal will bypass this handler; rerun the installer or the `SetPermission` command above to repair it.

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

## Troubleshooting

If clicking the webpage button does not open mpv, first open the webpage console:

```text
F12 → Console
```

A line such as:

```text
Opening MPV with N arguments
Launched external handler for 'ush://MPV?...'
```

means Violentmonkey and the browser successfully dispatched the URL. Continue with:

```bash
less ~/.local/state/mpv-fedora/external-handler.log
```

Look for:

```text
launch app='MPV' payload=json
running pid=...
exited pid=... return_code=...
```

- `running pid=...` means mpv stayed alive for at least two seconds.
- `exited ... return_code=...` means mpv exited immediately; inspect the mpv output lines immediately above it.
- No new `launch` line means Chromium/KDE did not invoke the handler. Check:

  ```bash
  xdg-mime query default x-scheme-handler/ush
  ```

  It must return:

  ```text
  mpv-fedora-ush-handler.desktop
  ```

- A correct `xdg-mime` result plus browser console lines such as `Launched external handler for 'ush://...'`, but still no `launch` log line, means the XDG portal forwarded the URL to a different application. Verify the portal's stored choice as shown in [Chromium and the XDG desktop portal](#chromium-and-the-xdg-desktop-portal); on Chromium-based browsers you can also watch the actual target with `dbus-monitor --session | grep -A2 Launched` while clicking the play button.

After changing the protocol handler, fully restart the browser. A browser process that started before handler installation can retain an older external-protocol activation path.

## Uninstall

```bash
cd integrations/external-player
./install-fedora.sh --uninstall
```

This removes the handler executable, desktop entry, and `ush://` association. It does not modify `~/.config/mpv` or uninstall the userscript.
