// search 语料：beta 模块（中间层）
// 预期: 'betaFn' 命中本文件定义行 + alpha.js 调用行 + app.js 调用行
function betaFn(x) {
  return gammaFn(x) * 2;
}

module.exports = { betaFn };
