// @anchor: module_mjs_intro
// 预期: .mjs 不在锚点扫描白名单（TEXT_EXTENSIONS）内，anchor 不被索引；
//       但注册表里有 JavaScriptParser，所以 get_file_structure 仍能解析结构
export function mjsFn(a) {
  return a + 1;
}

export class MjsClass {
  run() {
    return 1;
  }
}
