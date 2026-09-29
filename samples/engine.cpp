/* @anchor: engine_cpp_intro */
/* C++ 语料：块注释锚点、类与成员方法结构、#include 收集 */
#include <string>

// @anchor: engine_cpp_class
// 引擎类
class Engine {
public:
    // @anchor: engine_cpp_ctor
    // 构造函数
    Engine();

    // @anchor: engine_cpp_run
    // 运行方法
    void run();

private:
    int rpm;
};

// @anchor: engine_cpp_free_fn
// 自由函数
int computeRpm(int base) {
    return base * 2;
}
