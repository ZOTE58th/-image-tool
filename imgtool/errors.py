"""统一的错误类型。

所有"用户输入有问题"的情况都抛 ImgToolError，由命令行入口统一捕获，
打印一行中文提示后以非零状态码退出，避免把 traceback 甩给使用者。
"""


class ImgToolError(Exception):
    """可展示给使用者的错误，消息本身即完整的提示文案。"""
