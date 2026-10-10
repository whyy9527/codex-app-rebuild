# 第七课接入默认七课：实际回放与保留反例

默认夹具 `fixture-reference-en-zh-v8.json` 已接入七课、102道计分题，以及实际观察的暂缓口语状态。原版第七课先冻结，再编译实际 UI 顺序；初始 API 数组不能替代动态插入、复习及结算的观察。

最终 `seven-final` 来自空进度的同一次完整原生回放：430个状态，`walk_error=null`，七课完成；并未标记未编译的后续课程完成。`verification.json` 绑定候选二进制和夹具 SHA256。Swift构建通过，21项业务检查、48项框架测试通过。

共享前端 v14 保留 v13 全部1480项，新增九项原版控件断言，共1489项：985通过、69失败、435未覆盖、0不可验证。第七课原419项为314通过、27失败、78未覆盖。新增 radio 角色、可用状态和 Skip 零容差几何九项全部通过；这不意味着整页视觉通过。38对同视口截图全部不同，原版 q10 口语只有 AX 证据，没有 PNG，未计入图像比较。

## 复跑

从仓库根目录执行；输出目录应使用新的路径以保存既有回执：

```sh
projects/duolingo-web/run-native-course.sh artifacts/seven-course-new   projects/duolingo-web/fixture-reference-en-zh-v8.json   --walk-course --exercise-input-modes --exercise-source-skip   --exercise-listening-decline --decline-lesson-id lesson-6   --english-first-wrong --english-fifth-mixed-errors   --reference-color-scheme light
```

入口严格在构建成功后运行，观察器记录实际运行二进制及夹具哈希。`seven-final` 保存完整观测、进度、契约结果、配对清单及38张原生截图。`seventh-capture-pairs.py` 明确匹配阶段；q1/q4 原版 before 实际为切换后的空输入，新版初始态另存，不能混比。

## 失败与修正

- `seventh-first-failure`：复习题 AX hint 读取失败；实际可访问提示合并在音频按钮内，后续观察器从实际属性读取。
- `seven01`、`seven02`：保留源阶段错配、反馈意思缺失及普通按钮冒充 radio 的失败。
- `invalid-old-binary`：构建失败后误跑旧二进制，本次明确作废；严格启动脚本修复这一证据污染入口。
- `radio-missing-ax`、`radio-unknown-role`：新原生控件先缺 AX，再暴露 AXUnknown；容器与显式 radio 角色修正后，`radio-role-fixed` 实际点击并接受，最终全程再次验证。

原版旧采集把 aria-disabled 控件误记为 enabled；新增控件契约依据原版 ARIA 快照，原始矛盾记录保留。原生 radio 数字选中值尚未被观察器序列化；不能宣称选中状态的数值断言已覆盖。其位置与原版仍有差异。

## 素材、未知及继续探索

第七课 radio2 的 ice 语音由保留的原版播放事件及 timeOrigin 定位；radio1 语音仍未知。两个波形 PNG 是实际原版截图的静态帧，不是动画等价证明。14个新增公开语音资源已校验哈希及解码，未证明应用实际输出或声学等价。

源生命2→3的触发仍未知，没有注入正确答案加心规则。正常口语、听力暂缓其它分支、偏好跨重启、角色动画、布局、字体和声音差异继续进入探索前沿。第八课目前只观察入口，尚未完成。新 RSI 匹配预算探索消融未运行；原论文与既有负面实验保留，不能将本次修复称作 RSI 收益。完整 Goal 保持 active。
