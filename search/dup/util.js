// search 语料：与 dup2/util.js 同名，含同名符号 sharedFn
// 预期: 'sharedFn' 跨文件命中 4 条（两份同名文件各 定义+调用）
function sharedFn(a) {
  return sharedFn(a - 1);
}

module.exports = { sharedFn };
