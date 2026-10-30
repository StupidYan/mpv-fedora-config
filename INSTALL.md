# 安装与回滚

## 1. 安装系统依赖

```bash
sudo dnf install mpv mediainfo yt-dlp
```

如需使用 ffmpeg 相关功能：

```bash
sudo dnf install ffmpeg
```

## 2. 安装配置

在项目根目录执行：

```bash
./install.sh
```

默认目标：

```text
~/.config/mpv
```

自定义目标：

```bash
MPV_CONFIG_DIR=/path/to/mpv ./install.sh
```

## 3. 验证

本地视频：

```bash
mpv --force-window=yes /tmp/mpv-fedora44-test.mp4
```

检查：

1. uosc 底部控制栏；
2. 时间线缩略图；
3. `F4` MediaInfo；
4. 右键 `视频 > 着色器`；
5. 硬件解码日志中出现 `Using hardware decoding (vaapi-copy)`。

B 站弹幕：

```bash
mpv "https://www.bilibili.com/video/BV11bxF6CEvi/"
```

检查：

1. `Ctrl+d` 打开搜索；
2. 选择对应剧集；
3. 终端出现 `已解析 N 条弹幕`；
4. `j` 可开关弹幕。

## 4. 回滚

`install.sh` 不会删除旧配置，而是移动到：

```text
~/.config/mpv.backup-YYYYmmdd-HHMMSS
```

回滚示例：

```bash
mv ~/.config/mpv ~/.config/mpv.clean
mv ~/.config/mpv.backup-YYYYmmdd-HHMMSS ~/.config/mpv
```

确认恢复后，可删除 `.clean` 目录。

## 5. 常用调整

弹幕字号：

```ini
fontsize=40
```

弹幕显示区域：

```ini
displayarea=0.1
```

关闭弹幕平滑 fps 滤镜：

```ini
vf_fps=no
```

关闭硬件解码：

```ini
hwdec=no
```
