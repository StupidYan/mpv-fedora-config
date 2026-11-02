# External Player Fedora 集成

语言：简体中文 | [English](README.md)

本目录将 [External Player](https://github.com/LuckyPuppy514/external-player) 移植到 Fedora Linux。

上游用户脚本会打开如下形式的 URL：

```text
ush://MPV?base64(gzip(arguments))
```

上游的 `LuckyPuppy514/url-scheme-handler` 通过写注册表和 WinAPI 调用在 Windows 上实现该协议，Fedora 因此需要一个独立的原生处理器。

目标环境：Fedora 44 + KDE Plasma（Wayland），与仓库根 README 声明一致。本集成仅在这一组合上开发与验证（实测版本：Plasma 6.8.2、xdg-desktop-portal 1.22.1、Chromium 156.0.8078.73）；GNOME 及其他桌面未测试，不承诺支持。以下仅为组件本身的客观描述：处理器是纯 Python 3 可执行文件，安装使用 XDG 用户目录（`~/.local/bin`、`~/.local/share/applications`）和 `gio`/`xdg-mime` 关联，desktop 文件中的 `X-KDE-Protocols` 是 KDE 专属提示——以上均不构成跨桌面兼容性结论。

## 组件

| 文件 | 用途 |
|---|---|
| `external-player-fedora.user.js` | 暴力猴（Violentmonkey）用户脚本的 Fedora 分支 |
| `fedora-ush-handler.py` | 原生 Linux `ush://` 协议处理器 |
| `install-fedora.sh` | 用户级安装与卸载脚本 |

## 安装

先从仓库根目录安装 mpv 配置：

```bash
cd /path/to/mpv-fedora-config
./install.sh
```

然后安装本协议处理器：

```bash
cd integrations/external-player
./install-fedora.sh
```

安装的文件：

```text
~/.local/bin/mpv-fedora-ush-handler
~/.local/share/applications/mpv-fedora-ush-handler.desktop
~/.config/mpv/external-player-handler.json
```

desktop 文件注册：

```text
x-scheme-handler/ush
```

检查关联：

```bash
xdg-mime query default x-scheme-handler/ush
```

预期结果：

```text
mpv-fedora-ush-handler.desktop
```

## 安装用户脚本

1. 打开脚本原始地址：

   ```text
   https://raw.githubusercontent.com/StupidYan/mpv-fedora-config/main/integrations/external-player/external-player-fedora.user.js
   ```

2. 让暴力猴完成安装或更新。
3. 也可以手动更新：把仓库中的脚本文件内容粘贴覆盖现有的 `External Player` 脚本并保存。
4. 重新加载视频网站。

分支保留了上游脚本的名称和命名空间，暴力猴会将其识别为对现有安装的更新。其内部配置版本号已提升，会把已有的 MPV 播放器条目迁移到 Linux 安全的参数编码器。

首次在某网站触发时，浏览器可能询问是否允许打开外部应用，选择 `mpv Fedora USH Handler` 即可。

## 应用映射

`~/.config/mpv/external-player-handler.json` 将协议中的应用名映射到本地可执行文件：

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

安装器会使用当前 `mpv` 的路径创建该文件，可手动添加更多条目。每个路径必须是绝对路径且可执行。

## Fedora 专属改动

与上游 MPV 播放器事件相比：

- MPV 被标记为 Linux 播放器。
- 参数使用 JSON 数组编码，而非 shell 风格字符串。
- URL、Cookie、Referer 和标题无法注入额外的 shell 词元。
- Origin、referer、cookie 字段合并为一个 `--http-header-fields` 选项。
- 通过 `--script-opts-append=cid=...` 保留 B 站的 `cid`，使 `uosc_danmaku` 能加载对应的弹幕。
- 站点封锁 `unsafe-eval` 时使用的回退路径同样使用 JSON 编码器。
- 用户脚本的更新地址指向本仓库的 Fedora 分支。

## 处理器兼容性与安全性

原生处理器：

- 解码 URL 百分号编码；
- 解码 Base64 和 gzip；
- 接受 Fedora 分支的 JSON 数组；
- 为兼容起见，也接受上游脚本的旧版 shell 风格字符串；
- 将参数转换为 argv 列表，全程不调用 shell；
- 在新会话中直接启动配置的可执行文件；
- 只允许本地配置中列出的应用名；
- 网页永远无法指定任意可执行文件路径；
- 限制 URI、载荷和参数的大小与数量；
- 桌面通知不包含 URL、Cookie、请求头和标题。
- 以 `--player-operation-mode=pseudo-gui` 模式启动 MPV；
- 浏览器激活缺少会话环境时，补全标准的用户 Wayland 运行时环境；
- 将启动诊断和 mpv 输出写入用户私有的状态日志。

私有日志位于：

```text
~/.local/state/mpv-fedora/external-handler.log
```

该文件权限为 `0600`，仅属于当前用户，超过 1 MiB 时截断。其中可能包含 mpv 终端输出（含媒体 URL、请求头、Cookie 或标题），公开粘贴前务必先脱敏。

为兼容会把 Base64 `+` 字符损坏成空格的启动器，处理器仅在该替换结果确为合法 Base64 时修复这一种损坏形式。

## Chromium 与 XDG 桌面门户

较新的 Chromium 对外部协议不再调用 `xdg-open`，而是调用 XDG 桌面门户（`org.freedesktop.portal.OpenURI`）；portal 会在权限库（`desktop-used-apps` 表）中为每种协议保存自己的"上次选择"记忆。

本节全部内容均来自本机的 D-Bus 追踪实测：Chromium 156 调用了 `org.freedesktop.portal.OpenURI`，请求由 `xdg-desktop-portal` 服务（1.22.1）独立完成——它查询权限库并自行启动 desktop 文件，`xdg-desktop-portal-kde`（6.8.2）未参与。Fedora 44 仓库中也打包了 `xdg-desktop-portal-gnome`，但 GNOME 未测试、是否同样受影响未知；下文命令仅代表在 KDE Plasma 上验证过的操作，不代表跨桌面支持。

该记忆的优先级高于 `mimeapps.list` 默认值。如果 `ush://` 曾在 portal 应用选择器中被选成 mpv 播放器本体，portal 就会一直把原始 `ush://...` URL 转发给 `/usr/share/applications/mpv.desktop`。mpv 无法打开这种 URL，静默退出——浏览器报告"已启动外部处理器"，实际什么都没发生。

安装器通过向权限库种入本处理器作为 `x-scheme-handler/ush` 的最新选择来预防并修复该问题；种入的使用次数直接达到 portal 阈值，同时也会让 portal 跳过其应用选择器：

```bash
busctl --user call \
    org.freedesktop.impl.portal.PermissionStore \
    /org/freedesktop/impl/portal/PermissionStore \
    org.freedesktop.impl.portal.PermissionStore \
    SetPermission sbssas \
    "desktop-used-apps" true "x-scheme-handler/ush" "" \
    3 "mpv-fedora-ush-handler.desktop" "3" "3"
```

查看当前状态：

```bash
busctl --user call \
    org.freedesktop.impl.portal.PermissionStore \
    /org/freedesktop/impl/portal/PermissionStore \
    org.freedesktop.impl.portal.PermissionStore \
    Lookup ss "desktop-used-apps" "x-scheme-handler/ush"
```

如果记录的第一项不是 `mpv-fedora-ush-handler.desktop`，portal 就会绕过本处理器；重新运行安装器或上面的 `SetPermission` 命令即可修复。

## 测试

不启动 mpv 的空跑测试：

```bash
MPV_USH_HANDLER_DRY_RUN=1 \
MPV_USH_HANDLER_CONFIG="$HOME/.config/mpv/external-player-handler.json" \
~/.local/bin/mpv-fedora-ush-handler 'ush://MPV?YOUR_PAYLOAD'
```

真实浏览器测试：

1. 打开一个受支持的 B 站视频页面。
2. 点击 External Player Fedora 的 MPV 按钮。
3. 如浏览器弹出外部协议确认框，允许。
4. 确认 mpv 启动，且 `uosc_danmaku` 报告弹幕数量。

mpv 预期输出包含：

```text
Using hardware decoding (vaapi-copy)
AO: [pipewire]
[uosc_danmaku] 已解析 N 条弹幕
```

## 故障排查

点击网页按钮后 mpv 未打开时，先打开网页控制台：

```text
F12 → Console
```

如果看到类似：

```text
Opening MPV with N arguments
Launched external handler for 'ush://MPV?...'
```

说明暴力猴和浏览器已成功派发 URL。接着查看：

```bash
less ~/.local/state/mpv-fedora/external-handler.log
```

重点找：

```text
launch app='MPV' payload=json
running pid=...
exited pid=... return_code=...
```

- `running pid=...`：mpv 至少存活了两秒。
- `exited ... return_code=...`：mpv 立即退出，查看其上方紧邻的 mpv 输出行。
- 没有新的 `launch` 行：Chromium/KDE 没有调用处理器。检查：

  ```bash
  xdg-mime query default x-scheme-handler/ush
  ```

  必须返回：

  ```text
  mpv-fedora-ush-handler.desktop
  ```

- `xdg-mime` 结果正确、浏览器控制台也有 `Launched external handler for 'ush://...'`，但仍没有 `launch` 日志行：XDG portal 把 URL 转给了别的应用。按 [Chromium 与 XDG 桌面门户](#chromium-与-xdg-桌面门户) 一节检查 portal 记录；Chromium 系浏览器还可以在点击播放按钮时用 `dbus-monitor --session | grep -A2 Launched` 观察实际启动目标。

更换协议处理器后请完全重启浏览器。处理器安装之前启动的浏览器进程可能保留旧的外部协议激活路径。

## 卸载

```bash
cd integrations/external-player
./install-fedora.sh --uninstall
```

该操作会移除处理器可执行文件、desktop 文件和 `ush://` 关联，不会改动 `~/.config/mpv`，也不会卸载用户脚本。
