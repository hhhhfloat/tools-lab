// @anchor: end_rule_a_intro
// 命名规则探针：验证 `_end` 后缀锚点在项目索引中的可见性差异
export const probe = 1;

// @anchor: end_rule_a_probe_end
// 预期: 以 _end 结尾 → 可能不进 .project_index.json（describe 不可见）
export function endProbe() {
  return 1;
}

// @anchor: end_rule_a_end_middle
// 对照: 含 _end 但非后缀（中间出现）
export function endMiddle() {
  return 2;
}

// @anchor: end_rule_a_probe_start
// 对照: _start 后缀
export function startProbe() {
  return 3;
}
