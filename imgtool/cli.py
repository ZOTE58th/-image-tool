"""命令行入口：解析参数、分发子命令、统一处理错误。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .edits import crop, flip, resize, rotate, to_grayscale
from .errors import ImgToolError
from .imageio import (
    EXT_TO_FORMAT,
    default_output,
    format_size,
    load_image,
    save_image,
)
from .info import describe, read_info


def _save_result(
    img, args: argparse.Namespace, source: Path, tag: str, ext: str | None = None
) -> None:
    """按 -o 或默认命名保存结果，并告诉使用者文件位置。

    ext 用于格式转换：默认沿用原扩展名，转换时显式传入目标扩展名。
    """
    out_path = (
        Path(args.out).expanduser()
        if args.out
        else default_output(source, tag, ext=ext)
    )
    saved_path, size = save_image(img, str(out_path), source_path=source)
    print(f"已保存: {saved_path}")
    print(f"文件大小: {format_size(size)}    尺寸: {img.width} x {img.height} 像素")


def cmd_info(args: argparse.Namespace) -> None:
    """打印图片基础信息。"""
    print(describe(read_info(args.input)))


def cmd_resize(args: argparse.Namespace) -> None:
    """缩放图片。"""
    img, source = load_image(args.input)
    _save_result(resize(img, args.width, args.height), args, source, "resize")


def cmd_crop(args: argparse.Namespace) -> None:
    """按矩形区域裁剪图片。"""
    img, source = load_image(args.input)
    _save_result(
        crop(img, args.left, args.top, args.right, args.bottom), args, source, "crop"
    )


def cmd_rotate(args: argparse.Namespace) -> None:
    """旋转图片。"""
    img, source = load_image(args.input)
    _save_result(rotate(img, args.angle), args, source, f"rotate{args.angle}")


def cmd_flip(args: argparse.Namespace) -> None:
    """翻转图片。"""
    img, source = load_image(args.input)
    tag = "flip_h" if args.direction in ("horizontal", "h") else "flip_v"
    _save_result(flip(img, args.direction), args, source, tag)


def cmd_gray(args: argparse.Namespace) -> None:
    """转灰度图。"""
    img, source = load_image(args.input)
    _save_result(to_grayscale(img), args, source, "gray")


def cmd_convert(args: argparse.Namespace) -> None:
    """转换图片格式。"""
    img, source = load_image(args.input)
    target_ext = "." + args.to.lower().lstrip(".")
    if target_ext not in EXT_TO_FORMAT:
        raise ImgToolError(
            f"不支持转换为 {args.to}，可选: "
            + "、".join(sorted(ext.lstrip('.') for ext in EXT_TO_FORMAT))
        )
    _save_result(img, args, source, target_ext.lstrip("."), ext=target_ext)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imgtool",
        description="查看图片信息，并对图片做缩放、裁剪、旋转、翻转、灰度化和格式转换。",
        epilog="所有编辑都另存为新文件，不会覆盖原图。用 -o 指定输出路径。",
    )
    parser.add_argument(
        "--version", action="version", version=f"imgtool {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="命令")

    info_parser = subparsers.add_parser("info", help="查看图片基础信息")
    info_parser.add_argument("input", help="图片路径，例如 demo.jpg")
    info_parser.set_defaults(func=cmd_info)

    resize_parser = subparsers.add_parser(
        "resize", help="缩放图片（只给一边时按比例缩放）"
    )
    resize_parser.add_argument("input", help="图片路径")
    resize_parser.add_argument("-w", "--width", type=int, help="目标宽度（像素）")
    resize_parser.add_argument("-H", "--height", type=int, help="目标高度（像素）")
    resize_parser.add_argument("-o", "--out", help="输出文件路径")
    resize_parser.set_defaults(func=cmd_resize)

    crop_parser = subparsers.add_parser("crop", help="按左、上、右、下坐标裁剪")
    crop_parser.add_argument("input", help="图片路径")
    crop_parser.add_argument("--left", type=int, required=True, help="左边界 x 坐标")
    crop_parser.add_argument("--top", type=int, required=True, help="上边界 y 坐标")
    crop_parser.add_argument("--right", type=int, required=True, help="右边界 x 坐标")
    crop_parser.add_argument("--bottom", type=int, required=True, help="下边界 y 坐标")
    crop_parser.add_argument("-o", "--out", help="输出文件路径")
    crop_parser.set_defaults(func=cmd_crop)

    rotate_parser = subparsers.add_parser("rotate", help="顺时针旋转 90 / 180 / 270 度")
    rotate_parser.add_argument("input", help="图片路径")
    rotate_parser.add_argument(
        "-a", "--angle", type=int, required=True, choices=(90, 180, 270),
        help="旋转角度，只支持 90、180、270",
    )
    rotate_parser.add_argument("-o", "--out", help="输出文件路径")
    rotate_parser.set_defaults(func=cmd_rotate)

    flip_parser = subparsers.add_parser("flip", help="水平或垂直翻转")
    flip_parser.add_argument("input", help="图片路径")
    flip_parser.add_argument(
        "-d", "--direction", required=True, choices=("horizontal", "vertical"),
        help="翻转方向",
    )
    flip_parser.add_argument("-o", "--out", help="输出文件路径")
    flip_parser.set_defaults(func=cmd_flip)

    gray_parser = subparsers.add_parser("gray", help="彩色图转灰度图")
    gray_parser.add_argument("input", help="图片路径")
    gray_parser.add_argument("-o", "--out", help="输出文件路径")
    gray_parser.set_defaults(func=cmd_gray)

    convert_parser = subparsers.add_parser(
        "convert", help="转换图片格式，例如 png 转 jpg"
    )
    convert_parser.add_argument("input", help="图片路径")
    convert_parser.add_argument(
        "-t", "--to", required=True,
        help="目标格式，例如 jpg、png、bmp、webp",
    )
    convert_parser.add_argument("-o", "--out", help="输出文件路径")
    convert_parser.set_defaults(func=cmd_convert)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        parser.print_help()
        return 1

    try:
        args.func(args)
    except ImgToolError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n已取消", file=sys.stderr)
        return 130
    return 0
