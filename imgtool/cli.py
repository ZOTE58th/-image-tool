"""命令行入口：解析参数、分发子命令、统一处理错误。"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .errors import ImgToolError
from .info import describe, read_info


def cmd_info(args: argparse.Namespace) -> None:
    """打印图片基础信息。"""
    print(describe(read_info(args.input)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imgtool",
        description="查看图片信息，并对图片做缩放、裁剪、旋转、翻转、灰度化和格式转换。",
        epilog="示例: imgtool info demo.jpg",
    )
    parser.add_argument(
        "--version", action="version", version=f"imgtool {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="命令")

    info_parser = subparsers.add_parser("info", help="查看图片基础信息")
    info_parser.add_argument("input", help="图片路径，例如 demo.jpg")
    info_parser.set_defaults(func=cmd_info)

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
