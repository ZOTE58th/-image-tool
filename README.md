# imgtool — 图片信息查看与简单编辑工具

一个用 Python 编写的**命令行**图片工具。它可以读取一张图片的基础信息（文件名、格式、
宽高、颜色模式、文件大小），并对图片做缩放、裁剪、旋转、翻转、灰度化和格式转换。

所有编辑结果都**另存为新文件**，绝不会覆盖原图，保存后会打印结果文件的绝对路径。

## 1. 项目介绍

### 程序做什么

给定一张图片，`imgtool` 提供两组能力：

1. **读取信息**：文件名、图片格式、宽高（像素）、颜色模式、文件大小（KB/MB，保留两位小数）、
   是否带透明通道、DPI（若图片中有记录）。
2. **简单编辑**：缩放、裁剪、旋转、翻转、灰度化、格式转换。

### 支持的功能

| 命令 | 功能 | 说明 |
| --- | --- | --- |
| `info` | 读取图片信息 | 展示 6 项以上元信息 |
| `resize` | 缩放 | 同时给宽高则按指定尺寸；只给一边则按原比例换算 |
| `crop` | 裁剪 | 指定左、上、右、下坐标，越界时提示并退出 |
| `rotate` | 旋转 | 顺时针 90 / 180 / 270 度，画布自动扩展 |
| `flip` | 翻转 | `horizontal` 水平、`vertical` 垂直 |
| `gray` | 灰度化 | 彩色图转灰度图，带透明度时保留透明通道 |
| `convert` | 格式转换 | 支持 jpg / png / bmp / gif / tif / webp 互转 |

### 程序形式

**命令行（CLI）程序**，基于 `argparse` 实现子命令，无图形界面依赖，可在服务器上直接运行。

> 关于图像库：作业推荐 OpenCV，本项目选用 **Pillow**。原因是本项目要展示"颜色模式"
> （RGB / RGBA / L / P 等）并处理透明通道，Pillow 的 `mode` 与 alpha 语义更直接；
> OpenCV 读图默认丢 alpha、通道顺序为 BGR，还需要额外转换才能满足 3.4 的透明通道要求。
> 作业原文为"推荐"，非强制。

## 2. 环境配置

### Python 版本

- 要求：**Python >= 3.9**
- 开发与测试环境：**Python 3.11.6**（Linux x86_64）

### 安装依赖（推荐 uv）

项目用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境与依赖，仓库内提供
`pyproject.toml` 和 `uv.lock`，可复现安装。

```bash
# 1. 安装 uv（已安装可跳过）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 进入项目目录
cd image-tool

# 3. 按 uv.lock 创建 .venv 并安装依赖
uv sync
```

`uv sync` 会自动创建 `.venv/` 并装好 Pillow。之后用 `uv run` 运行程序即可，
无需手动激活虚拟环境。

### 安装依赖（不使用 uv 的备选方案）

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

### 依赖清单

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| Pillow | >= 10.0 | 图片读取、编辑、保存 |
| pytest | >= 8.4 | 仅开发测试用（`dev` 组） |

## 3. 运行方式

以下命令都在项目根目录执行。`uv run` 会自动使用 `.venv` 里的依赖。

```bash
# 查看帮助
uv run imgtool --help
uv run imgtool info --help
```

> 等价写法：激活虚拟环境后直接用 `imgtool ...`；或不安装入口脚本，
> 用 `uv run python -m imgtool ...`。

### 3.1 查看图片信息

```bash
uv run imgtool info demo.jpg
```

预期输出：

```
文件名     : demo.jpg
图片格式   : JPEG
宽度和高度 : 800 x 600 像素
颜色模式   : RGB（真彩色）
文件大小   : 37.74 KB
透明通道   : 无
完整路径   : /home/user/demo.jpg
```

带透明通道的 PNG 会显示：

```
颜色模式   : RGBA（真彩色 + 透明通道）
透明通道   : 有
```

### 3.2 缩放

只给宽度，高度按比例自动计算（800x600 → 400x300）：

```bash
uv run imgtool resize demo.jpg -w 400 -o out_400.jpg
```

```
已保存: /home/user/out_400.jpg
文件大小: 16.56 KB    尺寸: 400 x 300 像素
```

同时给宽高，按指定尺寸缩放（不保持比例）：

```bash
uv run imgtool resize demo.jpg -w 200 -H 500 -o out_200x500.png
```

只给高度同理：`-H 300`。

> 不写 `-o` 时，自动存为 `demo_resize.jpg`，与输入文件放在同一目录。
> 注意高度参数是大写 `-H`，小写 `-h` 是帮助。

### 3.3 裁剪

四个坐标都必填，坐标系以图片左上角为原点：

```bash
uv run imgtool crop demo.jpg --left 100 --top 50 --right 500 --bottom 400 -o out_crop.jpg
```

```
已保存: /home/user/out_crop.jpg
文件大小: 16.41 KB    尺寸: 400 x 350 像素
```

区域越界时不会崩溃，而是提示后退出：

```bash
uv run imgtool crop demo.jpg --left 0 --top 0 --right 2000 --bottom 800
# 错误: 裁剪区域超出图片范围：图片为 800 x 600，但右坐标 2000、下坐标 800 超出了边界
```

### 3.4 旋转

```bash
uv run imgtool rotate demo.jpg -a 90 -o out_90.jpg
# 已保存: /home/user/out_90.jpg
# 文件大小: 45.03 KB    尺寸: 600 x 800 像素   ← 宽高互换
```

`-a` 只接受 `90`、`180`、`270`，其他值会报错。

### 3.5 翻转

```bash
uv run imgtool flip demo.jpg -d horizontal -o out_flip_h.jpg   # 左右镜像
uv run imgtool flip demo.jpg -d vertical   -o out_flip_v.jpg   # 上下镜像
```

### 3.6 灰度化

```bash
uv run imgtool gray demo.jpg
# 已保存: /home/user/demo_gray.jpg
# 颜色模式变为 L（灰度图）
```

对带透明通道的图（如 PNG 图标），灰度化后会保留透明通道（`LA` 模式），
透明区域不会变成黑色块。

### 3.7 格式转换

```bash
# PNG 转 JPG（默认输出 demo_jpg.jpg）
uv run imgtool convert demo.png -t jpg

# JPG 转 PNG，并指定输出路径
uv run imgtool convert photo.jpg -t png -o photo.png
```

带透明通道的 PNG 转 JPG 时，程序会先铺**白色背景**再转成 RGB，避免保存失败或出现黑底。
转换后可以用 `imgtool info` 验证：

```bash
uv run imgtool info demo_jpg.jpg
# 图片格式   : JPEG
# 颜色模式   : RGB（真彩色）
```

### 3.8 通用说明

- **不覆盖原图**：如果 `-o` 指向的正是输入文件，程序会拒绝执行并提示换一个路径。
- **输出目录**：`-o` 的父目录不存在时会自动创建。
- **支持扩展名**：`.jpg .jpeg .png .bmp .gif .tif .tiff .webp`。

## 4. 错误提示

所有异常都会转成一行中文提示，程序以状态码 `1` 退出，不会打印 traceback。

| 情况 | 提示 |
| --- | --- |
| 文件不存在 | `错误: 文件不存在: xxx.jpg` |
| 不是有效图片 | `错误: 无法识别为图片，可能不是有效的图片文件: xxx.jpg` |
| 空文件 | `错误: 文件是空的，无法作为图片读取: xxx.png` |
| 宽高 <= 0 | `错误: 宽度必须大于 0，当前为 0` |
| 缩放未给参数 | `错误: 缩放需要至少指定宽度或高度之一（--width / --height）` |
| 裁剪越界 | `错误: 裁剪区域超出图片范围：图片为 800 x 600，但右坐标 2000、下坐标 800 超出了边界` |
| 输出与原图相同 | `错误: 输出路径不能与原图相同（不覆盖原图）: xxx.jpg` |
| 不支持的格式 | `错误: 不支持转换为 xyz，可选: bmp、gif、jpeg、jpg、png、tif、tiff、webp` |

## 5. 项目结构

```
image-tool/
├── imgtool/
│   ├── __init__.py      版本号
│   ├── __main__.py      支持 python -m imgtool
│   ├── cli.py           命令行入口，定义子命令与参数
│   ├── edits.py         编辑算法：resize / crop / rotate / flip / gray
│   ├── imageio.py       读图、存图、格式判定、大小格式化
│   ├── info.py          图片信息采集与排版输出
│   └── errors.py        统一的 ImgToolError
├── tests/
│   └── test_imgtool.py  16 个单元测试
├── pyproject.toml       项目元数据与依赖
├── uv.lock              依赖锁定文件
├── .gitignore           排除 .venv、__pycache__、输出目录
└── README.md
```

## 6. 开发与测试

```bash
# 运行全部测试
uv run pytest -q

# 只跑命令行相关的测试
uv run pytest -q -k cli
```

测试覆盖：信息读取、等比缩放、越界裁剪、旋转后尺寸、翻转后像素位置、灰度模式、
透明图转 JPG 白底、拒绝覆盖原图、CLI 退出码。

## 7. 提交说明（Git）

| 分支 | 用途 |
| --- | --- |
| `main` | 稳定分支，代码可直接运行 |
| `dev` | 功能开发分支，所有功能提交都在这里 |

提交信息统一采用 `type: 摘要` 的形式（`feat` / `test` / `chore`），每次提交对应一个
完整改动：初始化骨架 → 读取信息 → 缩放裁剪 → 旋转翻转灰度转换 → 测试与错误处理 →
完善 README，最后把 `dev` 合并回 `main`。
