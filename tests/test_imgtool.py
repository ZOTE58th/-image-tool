"""imgtool 的功能测试，覆盖编辑算法与命令行错误提示两条路径。

运行: uv run pytest -q
"""

from __future__ import annotations

import pytest
from PIL import Image

from imgtool.cli import main
from imgtool.edits import crop, flip, resize, rotate, to_grayscale
from imgtool.errors import ImgToolError
from imgtool.imageio import format_size, save_image
from imgtool.info import read_info


@pytest.fixture()
def rgb_image(tmp_path):
    """生成一张 80x60 的纯色图，四角颜色不同，方便验证翻转方向。"""
    img = Image.new("RGB", (80, 60), (10, 20, 30))
    img.putpixel((0, 0), (255, 0, 0))  # 左上角红色
    path = tmp_path / "demo.png"
    img.save(path)
    return path


@pytest.fixture()
def alpha_image(tmp_path):
    """生成带透明度的 RGBA 图。"""
    img = Image.new("RGBA", (40, 40), (255, 0, 0, 0))
    img.putpixel((20, 20), (0, 128, 255, 200))
    path = tmp_path / "alpha.png"
    img.save(path)
    return path


def test_format_size_units():
    assert format_size(512) == "512 B"
    assert format_size(2048) == "2.00 KB"
    assert format_size(5 * 1024 * 1024) == "5.00 MB"


def test_info_reads_basic_fields(rgb_image):
    info = read_info(str(rgb_image))
    assert info.width == 80 and info.height == 60
    assert info.mode == "RGB"
    assert info.format_name == "PNG"
    assert info.has_alpha is False
    assert "真彩色" in info.mode_text
    assert info.size_bytes > 0


def test_resize_keeps_ratio_when_only_width(rgb_image):
    img = Image.open(rgb_image)
    out = resize(img, width=40, height=None)
    assert out.size == (40, 30)  # 80x60 等比缩小一半


def test_resize_rejects_non_positive(rgb_image):
    img = Image.open(rgb_image)
    with pytest.raises(ImgToolError):
        resize(img, width=0)
    with pytest.raises(ImgToolError):
        resize(img, width=10, height=-1)


def test_crop_rejects_out_of_bounds(rgb_image):
    img = Image.open(rgb_image)
    with pytest.raises(ImgToolError, match="超出图片范围"):
        crop(img, 0, 0, 100, 100)


def test_crop_returns_requested_size(rgb_image):
    img = Image.open(rgb_image)
    out = crop(img, 10, 10, 50, 40)
    assert out.size == (40, 30)


def test_rotate_swaps_dimensions(rgb_image):
    img = Image.open(rgb_image)
    assert rotate(img, 90).size == (60, 80)
    assert rotate(img, 180).size == (80, 60)


def test_flip_horizontal_moves_corner_pixel(rgb_image):
    img = Image.open(rgb_image)
    flipped = flip(img, "horizontal")
    assert flipped.getpixel((79, 0)) == (255, 0, 0)


def test_grayscale_mode(rgb_image):
    img = Image.open(rgb_image)
    assert to_grayscale(img).mode == "L"


def test_grayscale_jpeg_keeps_single_channel(rgb_image, tmp_path):
    """灰度图存 JPG 后仍应是单通道，而不是被撑成三通道彩图。"""
    img = Image.open(rgb_image)
    out_path = tmp_path / "gray.jpg"
    saved, _ = save_image(to_grayscale(img), str(out_path))
    assert Image.open(saved).mode == "L"


def test_grayscale_keeps_alpha(alpha_image):
    img = Image.open(alpha_image)
    assert to_grayscale(img).mode == "LA"


def test_alpha_to_jpeg_gets_white_background(alpha_image, tmp_path):
    img = Image.open(alpha_image)
    out_path = tmp_path / "flat.jpg"
    saved, _ = save_image(img, str(out_path))
    result = Image.open(saved)
    assert result.mode == "RGB"
    # 完全透明处被铺成白色，而不是变成黑色或保存失败
    assert result.getpixel((0, 0)) == (255, 255, 255)


def test_save_refuses_to_overwrite_source(rgb_image):
    img = Image.open(rgb_image)
    with pytest.raises(ImgToolError, match="不覆盖原图"):
        save_image(img, str(rgb_image), source_path=rgb_image)


def test_cli_info_output(rgb_image, capsys):
    assert main(["info", str(rgb_image)]) == 0
    out = capsys.readouterr().out
    assert "80 x 60 像素" in out
    assert "PNG" in out


def test_cli_missing_file_exits_nonzero(capsys):
    assert main(["info", "no_such_file.png"]) == 1
    assert "文件不存在" in capsys.readouterr().err


def test_cli_resize_writes_new_file(rgb_image, tmp_path):
    out_path = tmp_path / "small.jpg"
    assert main(["resize", str(rgb_image), "-w", "20", "-o", str(out_path)]) == 0
    assert out_path.exists()
    assert Image.open(out_path).size == (20, 15)
