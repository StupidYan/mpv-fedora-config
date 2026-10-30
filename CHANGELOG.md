# Changelog

## 2026-10-30 12:07 - External Player Fedora integration

### Added

- 新增 `External Player Fedora` 油猴脚本 fork，基于上游 1.3.1。
- 新增 Fedora/Linux 原生 `ush://` 协议处理器。
- 新增用户级安装与卸载脚本。
- 新增 `x-scheme-handler/ush` desktop 注册。
- 新增 MPV 应用名到 `/usr/bin/mpv` 的本地安全映射配置。
- 新增 External Player 集成文档和许可证文件。

### Changed

- MPV 播放器标记从 Windows 改为 Linux。
- MPV 参数从 shell 风格字符串改为 gzip + Base64 编码的 JSON 数组。
- 油猴脚本旧配置升级时同步迁移播放器平台和播放事件。
- Origin、Referer 和 Cookie 合并传递给单个 `--http-header-fields` 参数。
- 保留 Bilibili `cid` 参数，继续兼容 `uosc_danmaku` 自动弹幕识别。

### Security

- Fedora handler 不经过 shell 启动程序。
- 网页只能选择本地配置中已存在的应用名，不能指定任意可执行文件路径。
- 配置中的可执行文件必须是绝对路径且具备执行权限。
- 限制 URI、gzip payload 和 argv 数量。
- 桌面通知不包含 URL、Referer、Cookie 或媒体标题。
- 修复部分桌面启动器把 Base64 `+` 错误转换成空格时的解码问题。

### Validated

- JSON payload 参数边界测试通过。
- 上游 legacy payload 解析测试通过。
- 含引号、换行、中文和伪攻击字符串的标题仍保持单一 argv 项。
- 未知应用名会被拒绝。
- Desktop `ush://` 调用链测试通过。
- 默认关联正确指向 `mpv-fedora-ush-handler.desktop`。

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
