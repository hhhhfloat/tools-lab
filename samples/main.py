# @anchor: main_py_intro
# Python 语料：验证 # 锚点、缩进结构解析、字符串内假锚点、方法体内锚点
import os
from typing import List


def top_level(x):
    return x


# @anchor: main_py_class
# 数据仓库类
class Repo:
    version = 1

    # @anchor: main_py_init
    # 构造函数（Python 方法 start=end=def 行，锚点在 def 之上）
    def __init__(self, name):
        self.name = name

    def fetch(self):
        # @anchor: main_py_inner
        # 方法体内的锚点（预期符号归属会落到其后最近的方法）
        fake = "# @anchor: main_py_fake_in_string"
        return self.name


def after_class():
    return os.getcwd()
