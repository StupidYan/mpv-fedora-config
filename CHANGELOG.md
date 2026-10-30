# Changelog

## 2026-10-30 11:32 - Initial Fedora 44 release

### Added

- Fedora 44 / KDE Wayland / AMD Radeon 680M 基础配置。
- 官方 uosc 5.13.0。
- 官方 uosc_danmaku 2.2.0。
- 官方 thumbfast。
- MediaInfo 面板。
- 官方 uosc 原生菜单和精选 shader 菜单。
- PipeWire 音频配置。
- `vaapi-copy` 硬件解码配置。
- yt-dlp B 站弹幕伪字幕排除配置。
- 独立安装脚本 `install.sh`。
- Fedora mpv Lua 5.1 位运算兼容补丁及独立 patch 文件。

### Migrated

以下弹幕偏好来自旧 Windows `mpv-lazy` 配置：

```ini
fontsize=40
displayarea=0.1
merge_tolerance=3
fps=60/1.001
vf_fps=yes
```

旧弹幕默认开启状态由 `install.sh` 写入运行时历史文件：

```json
{"show_danmaku":true}
```

### Fixed

- 修复 `uosc_danmaku` 在 Fedora mpv Lua 5.1 下因缺失 `bit` / `bit32` 导致的启动崩溃。
- 修复纯 Lua `bxor` 实现中因进位导致的 CRC32 错误。
- 修正 Linux 下 MediaInfo 可执行文件名大小写。

### Validated

- Fedora 44 KDE Wayland 实机播放。
- `gpu-next` 输出。
- PipeWire 音频。
- AMD VA-API 硬件解码。
- B 站在线播放。
- uosc_danmaku 解析 946 条弹幕。
- thumbfast 缩略图脚本加载。
- MediaInfo 脚本加载。
- 所有菜单引用的 shader 路径存在。
