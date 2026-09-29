# anchor-id: boundary2_intro
# 以 Java 语义（UTF-16 计数：CRLF=2、非 BMP 字符=2）推算 read_file 截断点。
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(BASE, "samples", "long-text.log")
raw = open(p, "rb").read().decode("utf-8", errors="replace")


def java_len(s):
    return sum(2 if ord(ch) > 0xFFFF else 1 for ch in s)


def java_offset(py_off):
    return java_len(raw[:py_off])


for tag in ["第 21 次迭代", "第 22 次迭代", "工具 [search_text] 结果: 🔍 找到 3 条"]:
    i = raw.find(tag)
    print("%-30s py=%-7d java=%-7d" % (tag, i, java_offset(i) if i >= 0 else -1))

for target in (49990, 50000, 50010):
    lo, hi = 0, len(raw)
    while lo < hi:
        mid = (lo + hi) // 2
        if java_offset(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    print("java %d -> py %d : %r" % (target, lo, raw[max(0, lo - 40):lo + 20].replace("\n", "\\n")))
