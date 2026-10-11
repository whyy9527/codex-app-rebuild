# 阶段2主页补漏与重载验收

2026-10-12，中文母语→英语、1200×732。延续已解锁的原版自有会话，实际访问课程弹层、阶段列表、锁定小故事、指南、电台入口和重载。探索从主页旧消费者遗漏出发，发现了新的课程内容、交互与前端需求，没有继续围绕倒计时修补。

原版第一课为“购买食品杂货”、第1/5单元、开始+10经验；锁定小故事“篮球运动员”仍可点击入口，打开说明弹层，内层“未解锁”按钮禁用。指南实际是 `/guidebook/en/11` 的购物语句，候选仍是旧西语指南。电台点击没有证明播放器存在：实际发生自动滚动，第二部分标题成为顶部标题，虚拟化控件库存57→75，继续出现第三部分。不要把当前DOM库存当完整App，也不要把没有捕获播放器当静音证据。

立即跳级后任务50/50，后来阶段页及主页重载都为0/50；阶段2、10分、530宝石仍保存。跨午夜可能解释任务变化，但尚未验证，不能按猜测修改规则。原版启动/数据准备仍依赖当前在线会话，没有服务端重置能力。

[反馈与下一步选择](exploration-feedback.json)把上述新发现直接列为下一批探索输入。[历史](history.json)合并43状态、25条实际控制边，[frontier](frontier.json)仍有1453条状态动作记录未解决；重复入口单独保留，数字不是独立需求数或App覆盖率。本批归档动作账本共17次尝试、16次成功动作，包含选择器失败；只读库存采集另记。没有匹配预算的RSI收益或消融结论；Dream-RSI／Cordis原论文继续见[研究文档](../../../../docs/RESEARCH.md)。

## 共同前端模具与实际候选

[v64](../../frontend-english-v64.json)逐项保留v63的9152项，新增1813项，共10965项，新增13个源状态；包含整图、文字、动作几何/角色/可用性和音频未知。新旧状态分别保存，不拿阶段2刷新后的截图覆盖即时结算状态。

Swift记录这一全对跳级实例的实际结果：阶段1完成、阶段2解锁、10分／530宝石／原版阶段卡片。兼容旧进度和旧v1夹具；结果按本次观测写入，不推导未知评分公式。任务仍保留即时50/50，刷新后的0/50差异留作失败。主页路径仍是旧节点、购物课正文及购物指南未实现，阶段1复习回调也尚未接入；不能以正确标题宣称主页已复刻。

- [43状态完整跳级和重启](native-placement/observed.json)：无旅程驱动失败，[48项局部检查](native-placement/outcome-validation.json)通过。独立前端为260 pass／78 fail／10333 not_run／294 unavailable，全部43整图仍fail。此轨迹未配置新控件别名，无法映射的控件如实unavailable。
- [最后卡片边框修正后的3状态重启检查](native-restored/observed.json)：无旅程失败，已显式配置已知原生控件映射；前端147 pass／67 fail／10568 not_run／183 unavailable，3整图仍fail。这次二进制与43状态的摘要不同，不合并计数或宣称全43状态使用最终构建。
- [早先40状态失败](native-failed/observed.json)及日志保留：错误提取卡片文本导致活跃阶段按钮不存在，重新读取原版九卡真实文字后修复。

源参考自检1800项通过，13项音频仍未执行；这只验证新契约可执行。最终构建成功，31项Swift业务／61项Python／17项Node检查通过。原声资源存在不是实际应用输出或音色一致的证明；1:1、完整音效、完整探索闭环和真实机制消融仍未完成。

## 复跑

在仓库根使用新输出目录：

```sh
python3 projects/duolingo-web/compile-section-placement.py
python3 projects/duolingo-web/compile-sections-presentation.py --source-json projects/duolingo-web/evidence/english-stage2-home-v1/stage2-home-source-02-sections-layout-corrected.json --presentation-name sections-unlocked-presentation --manifest-path projects/duolingo-web/reference-assets-en-zh-sections-unlocked-v1.json
python3 projects/duolingo-web/freeze-stage2-home.py --out-dir artifacts/stage2-freeze-new
python3 -m projects.duolingo-web.compile-stage2-frontier --out-dir artifacts/stage2-history-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/stage2-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/section-placement-outcome-scenarios-v1.json
python3 projects/duolingo-web/verify-section-placement.py --with-outcome --native artifacts/stage2-native-new --out artifacts/stage2-native-new/route.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v64.json --observed artifacts/stage2-native-new/observed.json --out artifacts/stage2-native-new/frontend.json
```

最后一条目前应返回fail。旧v1编译使用 `--without-outcome --out-dir`，不覆盖历史实例。三状态检查使用 `stage2-outcome-smoke-scenarios-v1.json` 并以实际完成跳级的进度作种子。资源使用既有 `fetch-english-resources.py` 及v2／unlocked两份manifest；浏览器渲染须显式指定任务会话。原版在线观察器接收 `--cli --session --out`，不会自动选择其他会话。
