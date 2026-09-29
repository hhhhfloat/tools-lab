# anchor-id: boundary_intro
# 推算 read_file 截断点：按「原始字符（CRLF 计 2）」定位第 N 个字符的上下文。
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(BASE, "samples", "long-text.log")
raw = open(p, "rb").read().decode("utf-8", errors="replace")
print("raw_chars=%d crlf=%d" % (len(raw), raw.count("\r\n")))

for n in (49900, 50000, 50100):
    seg = raw[n - 60:n + 60].replace("\r", "\\r").replace("\n", "\\n")
    print("  around %d: %s" % (n, seg))

tail = raw[:50000].replace("\r", "")
print("tail_after_cut_120: %s" % tail[-120:].replace("\n", "\\n"))
