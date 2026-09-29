// @anchor: app_ts_intro
// TypeScript 语料：接口 + 类型标注方法/字段，验证 .ts 走 JavaScript 解析器
export interface Item {
  id: number;
  name: string;
}

// @anchor: app_ts_store
// 存储服务类
export class Store {
  private items: Item[] = [];

  // @anchor: app_ts_add
  // 新增条目
  add(item: Item): void {
    this.items.push(item);
  }

  // @anchor: app_ts_count
  // 统计条目数
  count(): number {
    return this.items.length;
  }
}
