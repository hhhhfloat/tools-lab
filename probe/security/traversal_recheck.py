# @anchor: traversal_recheck_intro
# D7 复测语料：源码中出现「锚点标记 + 反斜杠」（如 r"@anchor:\s*(\w+)"）是否仍被安全扫描
# 判为盘符路径（期望：能正常写入，不再报 FILE_PATH_TRAVERSAL）
import re

PATTERNS = [
    r"//\s*@anchor:\s*(\w+)",
    r"#\s*@anchor:\s*(\w+)",
]


# @anchor: traversal_recheck_count
# 反向自检：用上面的正则统计本文件自身的锚点数量（含本锚点共 2 个）
def count_anchors(text):
    total = 0
    for p in PATTERNS:
        total += len(re.findall(p, text))
    return total
