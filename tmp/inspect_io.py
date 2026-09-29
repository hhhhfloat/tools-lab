# anchor-id: inspect_io_intro
# 临时检查器：报告文件字节数/字符数/行数/BOM/换行风格，用于对照 read_file 的输出。
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    "samples/long-text.log",
    "samples/notes.txt",
    "UPDATE.md",
    "PROJECT.md",
    "harness/anchor_oracle.py",
    "probe/io/trunc_probe.txt",
]

for rel in TARGETS:
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print("%-34s MISSING" % rel)
        continue
    raw = open(p, "rb").read()
    text = raw.decode("utf-8", errors="replace")
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n")
    print("%-34s bytes=%-7d chars=%-7d lines=%-5d crlf=%-4d lf=%-5d bom=%s"
          % (rel, len(raw), len(text), lf + 1, crlf, lf, raw[:3] == b"\xef\xbb\xbf"))
    tail = text[-120:].replace("\n", "\\n")
    print("    tail: %s" % tail)
