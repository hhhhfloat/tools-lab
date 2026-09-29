// search 语料：gamma 模块（叶子）
// 预期: 'gammaFn' 命中本文件 1 处定义 + beta.js 1 处 + alpha.js 1 处 + app.js 2 处 = 5 条
function gammaFn(x) {
  return x + 1;
}

module.exports = { gammaFn };
