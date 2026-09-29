// @anchor: app_java_intro
// Java 语料：验证 // 锚点、块注释锚点、无描述锚点、字符串内假锚点、符号归属
package samples;

/**
 * 预期: 本块注释内的 @anchor 不被索引（正则要求 /* 后紧跟空白，`*` 不满足）
 * @anchor: app_java_block_comment_anchor
 * 预期: 应查不到该 ID
 */
public class App {

    private int count = 0;

    // @anchor: app_java_field_area
    // 字段与构造区（锚点在方法定义之上，符号应落到下一个方法）
    public App() {
        this.count = 0;
    }

    // @anchor: app_java_method_sum
    // 求和方法（锚点位于方法定义上方）
    public int sum(int a, int b) {
        return a + b;
    }

    // @anchor: app_java_inline_desc
    /* 单行块注释作为描述 */
    public void logWithInlineDesc(String msg) {
        System.out.println(msg);
    }

    // @anchor: app_java_no_desc

    public void noDesc() {
        String fake = "// @anchor: app_java_fake_in_string";
        System.out.println(fake);
    }

    // @anchor: app_java_dup
    // 重复 ID 第一次出现
    public void dupOne() {}

    // @anchor: app_java_dup
    // 重复 ID 第二次出现，预期被重命名为 app_java_dup_2
    public void dupTwo() {}
}
