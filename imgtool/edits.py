"""图片编辑算法：缩放、裁剪、旋转、翻转、灰度化。

每个函数都只做一件事：接收 Image 对象和已经校验过的参数，返回新的 Image。
输入校验（宽高是否小于等于 0、坐标是否越界）在这里完成，失败抛 ImgToolError，
这样命令行层不必重复写判断。
"""

from __future__ import annotations

from typing import Optional

from PIL import Image

from .errors import ImgToolError

# Pillow 的旋转是逆时针的，这里按"顺时针"的直觉对外约定
VALID_ANGLES = (90, 180, 270)


def resize(
    img: Image.Image, width: Optional[int] = None, height: Optional[int] = None
) -> Image.Image:
    """缩放图片。

    同时给出宽高时按指定尺寸缩放（不保持比例）；
    只给出其中一个时，另一边按原始比例自动计算。
    """
    if width is None and height is None:
        raise ImgToolError("缩放需要至少指定宽度或高度之一（--width / --height）")

    if width is not None and width <= 0:
        raise ImgToolError(f"宽度必须大于 0，当前为 {width}")
    if height is not None and height <= 0:
        raise ImgToolError(f"高度必须大于 0，当前为 {height}")

    original_w, original_h = img.size

    if width is None:
        # 只给高度：按比例算宽度
        width = round(original_w * height / original_h)
    elif height is None:
        height = round(original_h * width / original_w)

    # 极端比例下四舍五入可能得到 0 像素，这里兜底成 1
    width = max(1, int(width))
    height = max(1, int(height))

    return img.resize((width, height), Image.LANCZOS)


def crop(
    img: Image.Image, left: int, top: int, right: int, bottom: int
) -> Image.Image:
    """按左、上、右、下坐标裁剪，坐标基于原图像素。"""
    width, height = img.size

    if right <= left:
        raise ImgToolError(
            f"裁剪区域无效：右坐标 {right} 必须大于左坐标 {left}"
        )
    if bottom <= top:
        raise ImgToolError(
            f"裁剪区域无效：下坐标 {bottom} 必须大于上坐标 {top}"
        )
    if left < 0 or top < 0:
        raise ImgToolError(
            f"裁剪区域越界：左/上坐标不能为负数，当前 left={left}, top={top}"
        )
    if right > width or bottom > height:
        raise ImgToolError(
            f"裁剪区域超出图片范围：图片为 {width} x {height}，"
            f"但右坐标 {right}、下坐标 {bottom} 超出了边界"
        )

    return img.crop((left, top, right, bottom))


def rotate(img: Image.Image, angle: int) -> Image.Image:
    """顺时针旋转 90 / 180 / 270 度，画布自动扩展。"""
    if angle not in VALID_ANGLES:
        raise ImgToolError(f"旋转角度仅支持 90、180、270 度，当前为 {angle}")
    # Pillow 的 rotate 是逆时针，取负号换成顺时针
    return img.rotate(-angle, expand=True)


def flip(img: Image.Image, direction: str) -> Image.Image:
    """水平或垂直翻转。"""
    if direction in ("horizontal", "h"):
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    if direction in ("vertical", "v"):
        return img.transpose(Image.FLIP_TOP_BOTTOM)
    raise ImgToolError(f"翻转方向仅支持 horizontal 或 vertical，当前为 {direction}")


def to_grayscale(img: Image.Image) -> Image.Image:
    """转灰度图。带透明通道时只对颜色通道灰度化，alpha 原样保留。"""
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        gray = rgba.convert("L")
        return Image.merge("LA", (gray, rgba.getchannel("A")))
    return img.convert("L")
