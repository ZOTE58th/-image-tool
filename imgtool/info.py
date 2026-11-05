"""读取并描述图片的基础信息。"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .imageio import format_size, load_image

# Pillow 的模式代号 -> 便于阅读的说明
MODE_DESCRIPTION = {
    "1": "二值图（1 位黑白）",
    "L": "灰度图（8 位）",
    "LA": "灰度图 + 透明通道",
    "P": "调色板模式",
    "PA": "调色板模式 + 透明通道",
    "RGB": "真彩色",
    "RGBA": "真彩色 + 透明通道",
    "CMYK": "印刷四色",
    "YCbCr": "亮度色度分量",
    "I": "32 位整数灰度图",
    "F": "32 位浮点灰度图",
}


@dataclass
class ImageInfo:
    """一张图片的元信息快照。"""

    path: Path
    file_name: str
    format_name: str
    width: int
    height: int
    mode: str
    size_bytes: int
    has_alpha: bool
    dpi: str | None = None

    @property
    def mode_text(self) -> str:
        """颜色模式的展示文案，例如 'RGBA（真彩色 + 透明通道）'。"""
        meaning = MODE_DESCRIPTION.get(self.mode)
        return f"{self.mode}（{meaning}）" if meaning else self.mode

    @property
    def size_text(self) -> str:
        return format_size(self.size_bytes)


def read_info(path: str) -> ImageInfo:
    """读取图片信息，失败时抛 ImgToolError。"""
    img, resolved = load_image(path)

    dpi_value = None
    raw_dpi = img.info.get("dpi")
    if raw_dpi:
        # Pillow 返回 (x, y) 浮点元组，取整展示
        dpi_value = "{:.0f} x {:.0f}".format(*raw_dpi)

    has_alpha = img.mode in ("RGBA", "LA", "PA") or (
        img.mode == "P" and "transparency" in img.info
    )

    return ImageInfo(
        path=resolved,
        file_name=resolved.name,
        format_name=img.format or resolved.suffix.lstrip(".").upper(),
        width=img.width,
        height=img.height,
        mode=img.mode,
        size_bytes=resolved.stat().st_size,
        has_alpha=has_alpha,
        dpi=dpi_value,
    )


def _display_width(text: str) -> int:
    """计算终端显示宽度：中日韩全角字符占 2 列。"""
    return sum(
        2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text
    )


def _pad(text: str, width: int) -> str:
    """按显示宽度右补空格，保证中英文混排时冒号能对齐。"""
    return text + " " * max(0, width - _display_width(text))


def describe(info: ImageInfo) -> str:
    """把 ImageInfo 渲染成多行文本，供命令行直接打印。"""
    rows: List[tuple[str, str]] = [
        ("文件名", info.file_name),
        ("图片格式", info.format_name),
        ("宽度和高度", f"{info.width} x {info.height} 像素"),
        ("颜色模式", info.mode_text),
        ("文件大小", info.size_text),
        ("透明通道", "有" if info.has_alpha else "无"),
    ]
    if info.dpi:
        rows.append(("分辨率（DPI）", info.dpi))

    rows.append(("完整路径", str(info.path)))

    label_width = max(_display_width(label) for label, _ in rows)
    return "\n".join(
        f"{_pad(label, label_width)} : {value}" for label, value in rows
    )
