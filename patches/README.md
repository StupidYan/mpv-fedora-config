# Patches

## 0001-uosc_danmaku-Lua51-inflate-bit-ops.patch

Purpose:

- add pure Lua unsigned 32-bit bit operations for Fedora mpv Lua 5.1;
- keep `uosc_danmaku` 2.2.0 loadable when `bit` and `bit32` are unavailable.

Apply to this repository from its root:

```bash
git apply -p1 patches/0001-uosc_danmaku-Lua51-inflate-bit-ops.patch
```

Dry-run against the upstream repository root:

```bash
git -C /path/to/uosc_danmaku apply -p3 --check \
  patches/0001-uosc_danmaku-Lua51-inflate-bit-ops.patch
```

The vendored file in `scripts/uosc_danmaku/modules/inflate.lua` already contains
this change. Remove it after upstream officially supports Lua 5.1.
