# @anchor: anchor_regex_probe_intro
# D7 探针：源码含「标记+反斜杠」的锚点正则字面量，观察安全扫描是否误报路径穿越
import re

PATTERN = re.compile(r"//\s*@anchor:\s*(\w+)")


def count_anchors(text):
    return len(PATTERN.findall(text))


if __name__ == "__main__":
    print("anchors=", count_anchors("// @anchor: demo_token"))
