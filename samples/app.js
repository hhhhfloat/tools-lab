// @anchor: app_js_intro
// JavaScript 语料：类/方法结构、字符串内假锚点、重复 ID、单行块注释锚点
import { helper } from "./helper.js";

// @anchor: app_js_helper_use
// 顶层函数（锚点在 function 之上）
export function useHelper(v) {
  return helper(v);
}

// @anchor: app_js_class
// 视图类
export class View {
  // @anchor: app_js_member
  // 类字段区
  count = 0;

  constructor(name) {
    this.name = name;
  }

  // @anchor: app_js_render
  // 渲染方法
  render() {
    const fake = "// @anchor: app_js_fake_in_string";
    return `<div>${this.name}${fake}</div>`;
  }

  /* @anchor: app_js_block_style */
  /* 单行块注释锚点（JS 解析器与扫描器均支持） */
  clear() {
    this.count = 0;
  }
}

// @anchor: app_js_dup
// 重复 ID 第一次
const dupOne = () => 1;

// @anchor: app_js_dup
// 重复 ID 第二次（预期 app_js_dup_2）
const dupTwo = () => 2;
