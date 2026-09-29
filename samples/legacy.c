// @anchor: legacy_c_intro
// 预期: .c 既不在锚点扫描白名单，也未注册结构解析器（走 GenericParser 兜底）
#include <stdio.h>

int legacy_add(int a, int b) {
    return a + b;
}
