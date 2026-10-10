# 实际跳过与重练：原生分支接入

原版证据来自 secondary-reset-q0、secondary-q0-skipped、seventh-review-intro 和 seventh-review-q0-answer；不是候选实现推导需求。原版空答案跳过显示“正确答案：/茶和咖啡”，生命保持2；整课末重练原题，最后完美100%。源轨迹同时发生2→3生命刷新，触发机制仍未知。

先冻结 compile-skip-probe 及 v1 契约，再接入 Question 的可选 skipLabel/skipCorrectText、独立 skip 状态和重练队列。跳过不调用答错评分、不扣心、不计错误、不重复入队；普通答错原有扣心仍通过回归。中文纠正文本取源字串，不把词块空格拼入答案。未把未知跳过音效替换成答错音效。

真实 owned Swift 子窗口已走完：空答案→跳过→反馈→重练引导→原题→正确反馈→完成→回主页；native02 无 walk_error。20项核心检查、Swift构建、47项框架测试通过。四题键盘/难度偏好原生回归仍45pass/9fail/4not_run，既有几何失败没有放宽。

初次跳过按钮AX为[139,640,152,48]，与源[140,639,150,50]不符；v2补充源DOM零容差几何断言，native01失败保留。修正strokeBorder及50点点击框后native02精确通过。v2共59项，源事实回放49pass/0fail/10not_run，原生43pass/6fail/10not_run，整体仍fail。六个失败为源生命2/3和连对15题：这个压缩探针从五心开始，只有一道题，无法替代整课及生命刷新。没有改动原版计数断言来掩盖差异。

五对同视口截图均different。角色仍为静态裁切，气泡缺原版播放/提示样式、反馈图标/字体/布局不同；review词库未恢复原版重排顺序。q0语音尚未编入此探针，真实输出/跳过音效仍未验证。组件通过不代表像素、声音或整课通过。完整第七课、listenIsolation遗漏选项、新结算/主页、产品全部差异仍待补齐；默认五课和显式六课冻结夹具保持，未用单题探针冒充默认产品更新。

新证据再次说明：业务效果“不扣心”不足以验收前端，必须保留按钮实际边界和源反馈文本；压缩探针可定位机制缺口，却不能验证完整状态连续性。没有执行新的RSI匹配预算消融，Dream-RSI/Cordis及旧负面结果仍在 docs/RESEARCH.md。完整运行Goal保持active。

## 复跑

仓库根、新输出目录、既有macOS辅助功能权限；比较因已知失败/未覆盖返回非零。图像比较的轨迹/limitations必须使用native02/pairs.json完整结构，初次漏填两字段的诊断命令失败未运行UI动作，也没有重试原版操作。

```sh
python3 projects/duolingo-web/compile-skip-probe.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-source-skip
artifacts/observe-source-skip artifacts/source-skip-review projects/duolingo-web/fixture-reference-en-zh-skip-v1.json --walk-course --exercise-source-skip --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-skip-v2.json --observed artifacts/source-skip-review/observed.json --out artifacts/source-skip-review/frontend-result.json
```
