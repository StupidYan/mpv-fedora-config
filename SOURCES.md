# Sources

## Vendored components

| Component | Version | Source commit | License |
|---|---:|---|---|
| uosc | 5.13.0 | `074b086` | LGPL-2.1-or-later |
| uosc_danmaku | 2.2.0 | `d896f17` | MIT |
| thumbfast | git snapshot | `0f711de` | MPL-2.0 |
| MediaInfo panel | mpv_PlayKit asset | local `mpv_PlayKit-main` archive | See PlayKit license |
| Selected shaders | mpv_PlayKit curated subset | local `mpv_PlayKit-main` archive | See file headers and PlayKit license |

## Original repositories

- uosc: https://github.com/tomasklaen/uosc
- uosc_danmaku: https://github.com/Tony15246/uosc_danmaku
- thumbfast: https://github.com/po5/thumbfast
- mpv_PlayKit: https://github.com/hooke007/mpv_PlayKit

## Local patch

```text
patches/0001-uosc_danmaku-Lua51-inflate-bit-ops.patch
```

Purpose:

- support Fedora mpv's Lua 5.1 runtime;
- provide pure Lua unsigned 32-bit bit operations when `bit` and `bit32` are unavailable;
- keep the change removable after upstream gains Lua 5.1 support.

## License notice

This repository vendors multiple components under different licenses. Their original license documents are kept in:

```text
licenses/
```

The repository root does not apply a single blanket license to all files. If you intend to redistribute this repository publicly, review every vendored file and its applicable license first.
