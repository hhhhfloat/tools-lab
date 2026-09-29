// search 语料：与 dup/util.js 同名，含同名符号 sharedFn
// 预期: 与 dup/util.js 一起在结果中体现「同名不同目录」
function sharedFn(a) {
  return a * sharedFn(a);
}

module.exports = { sharedFn };
