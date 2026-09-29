# 生成 io-01 复核用的中等长度探针文件（约 5.3k 字符：> 旧描述阈值 5000，<< 实现阈值 50000）
# 约定：tmp/ 下脚本不写锚点字面量，避免污染索引
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path(__file__).resolve().parents[1]  # tools-lab

target = BASE / "probe" / "io" / "mid_probe.txt"
lines = ["MP%03d %s" % (i, "m" * 92) for i in range(1, 54)]
text = "\n".join(lines) + "\n"
target.write_text(text, encoding="utf-8")
java_len = sum(2 if ord(c) > 0xFFFF else 1 for c in text)
print("wrote %s" % target)
print("chars=%d java_len=%d lines=%d" % (len(text), java_len, len(lines)))
