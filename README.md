# mpv-fedora-config

适用于 Fedora 44 KDE Wayland 的轻量 mpv 配置。目标是保持标准 Linux mpv 目录结构，避免深度整合包带来的维护成本：新增插件时只需要放入对应的 `scripts/`、`script-opts/` 和 `input.conf` 条目。

创建时间：2026-10-30 11:32

## 目标环境

| 项目 | 值 |
|---|---|
| 系统 | Fedora 44 KDE Plasma |
| 显示协议 | Wayland |
| GPU | AMD Radeon 680M |
| mpv | Fedora 官方包，验证版本 0.41.0 |
| 音频 | PipeWire |
| 视频输出 | `gpu-next` |
| 硬件解码 | `vaapi-copy` |

## 功能

- 官方 [uosc](https://github.com/tomasklaen/uosc) 5.13.0
- 官方 [uosc_danmaku](https://github.com/Tony15246/uosc_danmaku) 2.2.0
- 官方 [thumbfast](https://github.com/po5/thumbfast) 缩略图
- MediaInfo 面板与 uosc 菜单
- 官方 uosc 原生右键菜单
- 精选 GLSL 着色器菜单
- B 站、巴哈姆特等弹幕源支持
- AMD VA-API 硬件解码
- PipeWire 音频
- yt-dlp 在线视频播放，并排除 B 站弹幕伪字幕轨
- 可选 External Player Fedora 浏览器油猴集成和原生 `ush://` 协议处理器

## 安装

先安装系统依赖：

```bash
sudo dnf install mpv mediainfo yt-dlp
```

可选依赖：

```bash
sudo dnf install ffmpeg
```

进入本项目目录并执行：

```bash
./install.sh
```

安装脚本会先备份现有 `~/.config/mpv`，再安装新配置。备份目录格式如下：

```text
~/.config/mpv.backup-YYYYmmdd-HHMMSS
```

也可以显式指定目标目录：

```bash
MPV_CONFIG_DIR=/path/to/mpv ./install.sh
```

## External Player Fedora

可选安装浏览器外部播放器集成：

```bash
cd integrations/external-player
./install-fedora.sh
```

然后在 Tampermonkey 中导入：

```text
integrations/external-player/external-player-fedora.user.js
```

详细说明见：

```text
integrations/external-player/README.md
```

## 快捷键

| 键 | 功能 |
|---|---|
| 鼠标右键 | uosc 菜单 |
| 鼠标左键双击 | 全屏 |
| `Space` | 暂停/继续 |
| `q` | 退出 |
| `Q` | 退出并记住位置 |
| `Ctrl+d` | 搜索并加载弹幕 |
| `j` | 弹幕开/关 |
| `F4` | MediaInfo 菜单 |
| `Alt+i` | MediaInfo 常驻面板 |

## 着色器菜单

鼠标右键打开：

```text
视频 > 着色器
```

当前包含：

- 关闭全部
- SSim 超分/降采样
- Krig 色度放大
- SMAA 抗锯齿
- LumaSharpen
- Unsharp
- FSRCNNX x2
- RAVU Zoom r2
- 去隔行 SWA

本项目刻意不携带 mpv_PlayKit 的 140MB 全量着色器库，只收录菜单实际使用的精选文件。新增 shader 时：

1. 将 `.glsl` 文件加入 `shaders/`；
2. 在 `input.conf` 增加一个 `change-list glsl-shaders ...` 菜单项；
3. 重启 mpv。

## 弹幕配置

弹幕选项位于：

```text
script-opts/uosc_danmaku.conf
```

以下偏好已从旧 Windows `mpv-lazy` 配置迁移：

```ini
fontsize=40
displayarea=0.1
merge_tolerance=3
fps=60/1.001
vf_fps=yes
```

同时迁移了：

```ini
ytdl-raw-options-append=sub-langs=-danmaku
```

用于避免 yt-dlp 把 B 站弹幕 XML 当作普通字幕轨。

旧配置中的 `bilibiliAssert` 是已被 `uosc_danmaku` 取代的独立旧脚本，本项目未迁移，避免两套弹幕系统同时工作。

## Fedora Lua 5.1 兼容补丁

Fedora mpv 0.41 链接 Lua 5.1，没有 `bit` / `bit32` 库。上游 `uosc_danmaku 2.2.0` 的 `modules/inflate.lua` 无条件依赖 bit 操作，会导致脚本启动失败。

本项目在 vendored 文件中加入了纯 Lua 的无符号 32 位位运算兜底实现，覆盖：

- `band`
- `bxor`
- `bnot`
- `lshift`
- `rshift`

独立补丁位于：

```text
patches/0001-uosc_danmaku-Lua51-inflate-bit-ops.patch
```

补丁已在 mpv 的 Lua 5.1 环境中验证：

- ZIP 解压内容正确；
- CRC32 校验正确；
- `uosc_danmaku` 可正常启动；
- B 站视频实测解析 946 条弹幕。

## 已验证结果

以下结果来自 Fedora 44 实机测试：

```text
Using hardware decoding (vaapi-copy).
VO: [gpu-next] 1920x1080 nv12
AO: [pipewire] 44100Hz stereo 2ch floatp
[uosc_danmaku] 已解析 946 条弹幕
```

自动化回归还确认：

- uosc 5.13.0 加载成功；
- uosc_danmaku 2.2.0 加载成功；
- thumbfast 加载成功；
- MediaInfo 面板加载成功；
- 配置解析无错误；
- Lua 脚本无崩溃；
- 输入键位无重复；
- 所有菜单引用的 shader 文件存在。

## 目录结构

```text
.
├── mpv.conf
├── input.conf
├── install.sh
├── fonts/
├── shaders/
├── scripts/
│   ├── uosc/
│   ├── uosc_danmaku/
│   ├── thumbfast.lua
│   └── stats_mediainfo.lua
├── script-opts/
│   ├── uosc.conf
│   ├── uosc_danmaku.conf
│   ├── thumbfast.conf
│   └── stats_mediainfo.conf
├── integrations/
│   └── external-player/
├── patches/
├── licenses/
├── CHANGELOG.md
├── INSTALL.md
└── SOURCES.md
```

## 已知限制

1. 官方 uosc 的 `ziggy-linux` 辅助二进制未包含。

   影响：

   - uosc 内置在线字幕下载；
   - mpv 原生剪贴板不可用时的 uosc 剪贴板兜底。

   不影响：

   - uosc UI；
   - uosc_danmaku；
   - thumbfast；
   - MediaInfo；
   - 着色器菜单。

2. VapourSynth 补帧未包含。mpv 已支持 VapourSynth bridge，但仍需要额外安装 VapourSynth、K7sfunc、插件与模型，后续应单独项目化。

3. `vf_fps=yes` 可能增加高分辨率视频的滤镜开销。如 4K 播放卡顿，可在 `script-opts/uosc_danmaku.conf` 中改为：

   ```ini
   vf_fps=no
   ```

4. `displayarea=0.1` 来自旧 Windows 配置。如弹幕区域过窄，可改为上游默认：

   ```ini
   displayarea=0.85
   ```

## 维护原则

- 保持标准 Linux mpv 目录；
- 每个插件独立位于 `scripts/`；
- 每个插件选项独立位于 `script-opts/`；
- 不使用大型 `script-opts.conf` 聚合所有插件；
- 不迁移 Windows 安装器、命名管道和 D3D11 专用配置；
- 只收录当前使用的 shader，避免仓库膨胀；
- 本地兼容补丁必须保存在 `patches/`，方便上游修复后移除。

## External Player Fedora 限制

- 上游 `url-scheme-handler` 是 Windows 程序，本项目不使用它。
- Fedora 使用 `integrations/external-player/fedora-ush-handler.py` 注册用户级 `ush://` 协议。
- 浏览器第一次调用时会显示外部协议确认窗口。
- 浏览器中的原版 External Player 脚本应禁用，避免同时显示两套按钮。

## 来源与许可证

见 [SOURCES.md](SOURCES.md) 和 `licenses/` 目录。

上游组件分别保留其原许可证。本仓库自身的配置文件和安装脚本未声明独立开源许可证；如需公开分发，请先完成第三方资产许可证审查。
