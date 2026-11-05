"""命令行入口：解析参数、分发子命令、统一处理错误。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .edits import crop, resize
from .errors import ImgToolError
from .imageio import default_output, format_size, load_image, save_image
from .info import describe, read_info


def _save_result(img, args: argparse.Namespace, source: Path, tag: str) -> None:
    """按 -o 或默认命名保存结果，并告诉使用者文件位置。"""
    out_path = Path(args.out).expanduser() if args.out else default_output(source, tag)
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
