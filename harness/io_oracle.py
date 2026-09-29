# @anchor: io_oracle_intro
# read_file / write_file 差分校验器：从只读源码抽规格 → 与沙箱事实和实测基线比对 → 报告落盘 lab-out/io-report.txt。
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parents[1]
LABOUT = BASE / "lab-out"
WF = BASE.parent / "workflow-read-only"


class _Tee:
    def __init__(self, fp):
        self.fp = fp

    def write(self, text):
        sys.stdout.write(text)
        self.fp.write(text)

    def flush(self):
        sys.stdout.flush()
        self.fp.flush()


# @anchor: io_oracle_spec
# 规格抽取：正则解析只读源码里的常量与消息模板（纯文本匹配，不执行任何代码）
def extract_spec():
    fo = (WF / "src/main/java/com/myagent/workflow/tools/FileOperator.java").read_text(encoding="utf-8")
    te = (WF / "src/main/java/com/myagent/workflow/tools/ToolExecutor.java").read_text(encoding="utf-8")
    td = (WF / "src/main/java/com/myagent/workflow/tools/ToolDefinitions.java").read_text(encoding="utf-8")
    spec = {}
    spec["max_length"] = int(re.search(r"final int MAX_LENGTH = (\d+);", fo).group(1))
    spec["trunc_note"] = "文件过长，已截断。如需完整内容请告知" in fo
    spec["read_header_fmt"] = "📄 文件 " in fo
    spec["read_absent_msg"] = "文件不存在或是一个目录: " in fo
    spec["write_ok_fmt"] = '"✅ " + filename' in fo
    spec["write_err_prefix"] = "写入文件失败: " in fo
    spec["write_atomic"] = "ATOMIC_MOVE" in fo and "REPLACE_EXISTING" in fo
    spec["delete_dir_msg"] = "不能删除目录" in fo
    spec["update_md_read_refusal"] = "❌ UPDATE.md 不支持完整读取。请使用 read_between_anchors 按锚点读取。" in te
    spec["update_md_delete_refusal"] = "❌ UPDATE.md 不允许删除。" in te
    spec["dot_refusal"] = "❌ 不允许访问以 . 开头的文件/目录：" in te
    spec["dotdot_refusal"] = "路径中不允许出现" in te
    spec["declared_read_limit"] = int(re.search(r"读取大小限制为 (\d+) 字符", td).group(1))
    return spec


# @anchor: io_oracle_known_diffs
# 已知差异白名单：已记录在 PROJECT.md 台账，出现即不算回归
KNOWN_DIFFS = {
    "io-01": "read_file 声明阈值 5000 与实现阈值 50000 不符（描述陈旧）",
    "d4": "点开头路径一律拒绝（write_file/read_file 均如此）",
    "d8": "文档/字符串里的锚点写法字面量被收录（假阳性）",
    "io-02": "write_file 即时刷新不套用排除目录规则，条目须等 rebuild 清理",
}


# @anchor: io_oracle_helpers
# 工具函数：UTF-16 计数（对齐 Java String.length）与索引读取
def java_len(text):
    return sum(2 if ord(ch) > 0xFFFF else 1 for ch in text)


def read_raw(rel):
    return open(BASE / rel, "rb").read().decode("utf-8", errors="replace")


def load_index(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


# @anchor: io_oracle_baseline
# 实测基线：每条为一次真实工具调用观察到的结果，逐条与源码规格判定
BASELINE = [
    ("io-r1", "read_file(13775 字符无锚点文件) 完整返回，无截断提示",
     "阈值 > 13775", "完整返回 300 行，无提示", "io-01"),
    ("io-r2", "read_file(samples/long-text.log) 截断并附提示",
     "截断点 = MAX_LENGTH(UTF-16)", "截断点≈java 50000，附标准提示", None),
    ("io-r3", "read_file(UPDATE.md) 拒绝",
     "按 checkPath 拒绝", "❌ UPDATE.md 不支持完整读取…", None),
    ("io-r4", "read_file(点开头路径) 拒绝",
     "按 checkPath 拒绝", "❌ 不允许访问以 . 开头的文件/目录…", "d4"),
    ("io-r5", "read_file(缺失/目录/目录带尾斜杠)",
     "统一回「文件不存在或是一个目录: X」", "三种输入同一文案", None),
    ("io-r6", "read_file(0 字节文件)",
     "只回头部无内容", "📄 文件 empty.txt 内容已阅读", None),
    ("io-w1", "write_file 新建 + 多级目录自动创建",
     "返回 ✅ filename 并建目录", "✅ 4 级目录 + 文件落地", None),
    ("io-w2", "write_file 覆盖已存在文件",
     "整文件替换", "VERSION-1 → VERSION-2 生效", None),
    ("io-w3", "write_file 无结尾换行内容",
     "逐字写入，不补换行", "nonl.txt bytes=14 无 LF", None),
    ("io-w4", "write_file 含 CRLF 内容",
     "不归一化，原样落盘", "crlf=2 / lf=3", None),
    ("io-w5", "write_file(点开头路径)",
     "按 checkPath 拒绝", "❌ 不允许访问以 . 开头的文件/目录…", "d4"),
    ("io-w6", "write_file(目标是已存在目录)",
     "IOException → 写入文件失败", "写入文件失败: <abs>/samples", None),
    ("io-w7", "write_file(父路径是文件)",
     "IOException → 写入文件失败", "写入文件失败: <abs>/probe/io/noext", None),
    ("io-w8", "write_file(尾斜杠 + 不存在路径)",
     "Path 归一化 → 落成普通文件", "dir_target 为文件（22 字节）", None),
    ("io-w9", "write_file(名字含反斜杠)",
     "反斜杠当分隔符 → 建子目录", "bsep/name.txt", None),
    ("io-w10", "write_file(排除目录 dist/)", "写入成功但索引应排除",
     "写入成功；即时刷新进了索引，rebuild 后被清理", "io-02"),
]


# @anchor: io_oracle_checks
# 自动校验：沙箱事实 + 两份索引，逐条给 PASS/FAIL
def run_checks(spec):
    results = []

    def check(cid, desc, ok, detail):
        results.append((cid, desc, ok, detail))

    check("C1", "源码 MAX_LENGTH 抽取", spec["max_length"] == 50000,
          "MAX_LENGTH=%d" % spec["max_length"])
    check("C2", "read_file 描述阈值 vs 实现阈值",
          spec["declared_read_limit"] == spec["max_length"],
          "描述=%d 实现=%d → io-01" % (spec["declared_read_limit"], spec["max_length"]))

    log = read_raw("samples/long-text.log")
    check("C3", "long-text.log 超阈值（应触发截断路径）",
          java_len(log) > spec["max_length"],
          "java_len=%d > %d" % (java_len(log), spec["max_length"]))

    probe_len = java_len(read_raw("probe/io/trunc_probe.txt"))
    check("C4", "13775 字符探针在声明阈值之上、实现阈值之下",
          spec["declared_read_limit"] < probe_len <= spec["max_length"],
          "java_len=%d" % probe_len)

    nonl = (BASE / "probe/io/nonl.txt").read_bytes()
    check("C5", "write_file 不追加结尾换行", b"\n" not in nonl and len(nonl) == 14,
          "bytes=%d" % len(nonl))

    crlf = (BASE / "probe/io/crlf.txt").read_bytes()
    check("C6", "write_file 保留 CRLF 不归一化", crlf.count(b"\r\n") == 2,
          "crlf=%d lf=%d" % (crlf.count(b"\r\n"), crlf.count(b"\n")))

    a = load_index(".anchors.json")
    d = load_index(".project_index.json")
    check("C7", "两份索引文件集一致（D1 哨兵）", sorted(a) == sorted(d),
          "A=%d P=%d only_A=%s" % (len(a), len(d), sorted(set(a) - set(d))))

    check("C8", "排除目录条目已被 rebuild 清理",
          "probe/dist/inside_write.js" not in a and "probe/dist/inside_write.js" not in d,
          "dist 条目不在索引中")

    tmpjunk = [k for k in a if k.startswith("tmp/")]
    check("C9", "tmp 脚本不得污染索引（约定：不写锚点字面量）", not tmpjunk, "tmp=%s" % tmpjunk)

    rp = d.get("probe/io/refresh_probe.js")
    check("C10", "新写入文件经轮末 flush 后可见且带 symbol",
          bool(rp) and rp[0].get("symbol") == "refreshProbe",
          "entry=%s" % rp)

    fake = [x["id"] for x in a.get("samples/md_anchor_example.md", [])]
    check("C11", "D8 假锚点行为冻结",
          "mirror_js_style" in fake and "mirror_html_style" in fake,
          "ids=%s" % fake)

    check("C12", "无锚点长文件不入索引",
          "samples/long-text.log" not in a and "probe/io/trunc_probe.txt" not in a,
          "long-text.log/trunc_probe.txt 缺席")

    return results


# @anchor: io_oracle_main
# 入口：输出规格、基线判定、自动校验与最终 RESULT，并落盘报告
def main():
    LABOUT.mkdir(exist_ok=True)
    with open(LABOUT / "io-report.txt", "w", encoding="utf-8") as fp:
        out = _Tee(fp)
        spec = extract_spec()
        print("== io oracle ==", file=out)
        print("[spec] %s" % json.dumps(spec, ensure_ascii=False, sort_keys=True), file=out)

        print("\n[baseline] 实测条目 vs 源码规格", file=out)
        flagged = []
        for bid, item, expect, observed, known in BASELINE:
            tag = "KNOWN(%s)" % known if known else "OK"
            if known:
                flagged.append(known)
            print("  %-6s %-9s %s\n         期望: %s\n         实测: %s"
                  % (bid, tag, item, expect, observed), file=out)

        print("\n[checks] 自动校验", file=out)
        fails = []
        for cid, desc, ok, detail in run_checks(spec):
            print("  %-4s %-6s %s | %s" % (cid, "PASS" if ok else "FAIL", desc, detail), file=out)
            if not ok:
                fails.append((cid, desc, detail))

        unknown = sorted(set(flagged) - set(KNOWN_DIFFS))
        print("\n[known diffs] %s" % ", ".join(sorted(set(flagged))), file=out)
        for k in sorted(set(flagged)):
            print("  %-7s %s" % (k, KNOWN_DIFFS.get(k, "未登记")), file=out)

        bad = [f for f in fails if f[0] not in ("C2",)]
        verdict = "PASS" if not bad and not unknown else "CHECK"
        print("\n[unexpected failures] %s" % (bad if bad else "none"), file=out)
        print("RESULT=%s" % verdict, file=out)


if __name__ == "__main__":
    main()
