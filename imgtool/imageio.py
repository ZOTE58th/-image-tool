"""图片读写、格式判定与文件大小格式化。

这一层只负责"把文件变成 Image 对象"和"把 Image 对象安全地写回磁盘"，
真正的编辑逻辑放在 edits.py，读写复用这一层。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, UnidentifiedImageError

from .errors import ImgToolError

# 扩展名 -> Pillow 保存时使用的格式名
EXT_TO_FORMAT = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".bmp": "BMP",
    ".gif": "GIF",
    ".tif": "TIFF",
    ".tiff": "TIFF",
    ".webp": "WEBP",
}

SUPPORTED_EXT_TEXT = "、".join(sorted(EXT_TO_FORMAT))


def format_size(size_bytes: int) -> str:
    """把字节数格式化成 B / KB / MB，KB 及以上保留两位小数。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    kb = size_bytes / 1024
    if kb < 1024:
        return f"{kb:.2f} KB"
    return f"{kb / 1024:.2f} MB"


def target_format(path: Path) -> str:
    """根据扩展名推断保存格式，不支持的扩展名直接报错。"""
    ext = path.suffix.lower()
    if ext not in EXT_TO_FORMAT:
        raise ImgToolError(
            f"不支持保存为 {ext or '无扩展名'} 格式，可选扩展名: {SUPPORTED_EXT_TEXT}"
        )
    return EXT_TO_FORMAT[ext]


def load_image(path: str) -> Tuple[Image.Image, Path]:
    """读取图片并返回 (Image 对象, 绝对路径)。

    任何读取失败都转成 ImgToolError，保证调用方只需要处理一种异常。
    """
    file_path = Path(path).expanduser()

    if not file_path.exists():
        raise ImgToolError(f"文件不存在: {file_path}")
    if not file_path.is_file():
        raise ImgToolError(f"这不是一个文件: {file_path}")
    if file_path.stat().st_size == 0:
        raise ImgToolError(f"文件是空的，无法作为图片读取: {file_path}")

    try:
        with Image.open(file_path) as img:
            img.load()  # 强制解码，避免"能打开但读不出像素"的情况被漏掉
            # copy() 会丢掉 .format，手动带回真实格式（扩展名可能与内容不一致）
            snapshot = img.copy()
            snapshot.format = img.format
            return snapshot, file_path.resolve()
    except UnidentifiedImageError:
        raise ImgToolError(f"无法识别为图片，可能不是有效的图片文件: {file_path}")
    except OSError as exc:
        raise ImgToolError(f"读取图片失败: {file_path}（{exc}）")


def prepare_for_save(img: Image.Image, fmt: str) -> Image.Image:
    """按目标格式调整颜色模式，重点处理透明通道。"""
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (
        img.mode == "P" and "transparency" in img.info
    )

    if fmt == "JPEG":
        # JPEG 不支持透明通道，先铺白底再转 RGB，否则保存会直接失败
        if has_alpha:
            base = img.convert("RGBA")
            canvas = Image.new("RGBA", base.size, (255, 255, 255, 255))
            return Image.alpha_composite(canvas, base).convert("RGB")
        return img.convert("RGB")

    if fmt == "GIF":
        # GIF 只支持调色板模式
        return img.convert("P", palette=Image.ADAPTIVE)

    if img.mode == "P":
        return img.convert("RGBA" if has_alpha else "RGB")

    return img


def save_image(
    img: Image.Image,
    out_path: str,
    source_path: Optional[Path] = None,
    quality: int = 95,
) -> Tuple[Path, int]:
    """把图片保存到新路径，返回 (绝对路径, 字节数)。

    约定：绝不覆盖原图。若输出路径与源文件相同则直接报错。
    """
    target = Path(out_path).expanduser()
    if not target.suffix:
        raise ImgToolError(f"输出路径缺少扩展名，无法判断格式: {target}")

    fmt = target_format(target)

    if source_path is not None:
        try:
            same = target.resolve() == source_path.resolve()
        except OSError:
            same = False
        if same:
            raise ImgToolError(
                f"输出路径不能与原图相同（不覆盖原图）: {target}\n"
                f"请用 -o 指定一个新的文件，例如 {target.with_name(target.stem + '_out' + target.suffix)}"
            )

    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)

    data = prepare_for_save(img, fmt)
    save_kwargs = {}
    if fmt in ("JPEG", "WEBP"):
        save_kwargs["quality"] = quality
    if fmt == "JPEG":
        save_kwargs["optimize"] = True

    try:
        data.save(target, format=fmt, **save_kwargs)
    except OSError as exc:
        raise ImgToolError(f"保存图片失败: {target}（{exc}）")

    resolved = target.resolve()
    return resolved, os.path.getsize(resolved)


def default_output(input_path: Path, tag: str, ext: Optional[str] = None) -> Path:
    """生成默认输出文件名，例如 demo.jpg -> demo_resize.png。"""
    suffix = ext if ext else input_path.suffix
    return input_path.with_name(f"{input_path.stem}_{tag}{suffix}")
