# 主页阶段、当前跳级测试与结算后探索

2026-10-11→12，中文母语→英语，1200×732，原版自有匿名浏览器会话。从上一批 `open-sections` 缺失和三个不同首题继续探索。八阶段加每日巩固的九张卡片取得完整 DOM 几何；实际滚动到下层。阶段2通关测试完成15题，全被原版接受；实际结算为50 XP／100%、英语分数10、每日目标50完成、5宝石、建档提示，返回后阶段1已完成、阶段2解锁，530宝石。继续进入原版阶段2主页，又发现小故事、电台及不同课程路径。

这里没有原版服务端重置能力。旧阶段1准备态、新跳级实例、解锁后的阶段2状态分开保存；不把不同实例首题拼成一套原版序列。公开当前题目评分字段用于建立夹具，不能当盲测或RSI发现得分。

## 探索确实改变了观察器

[事前选择](policy-before-actions.json)来自旧frontier和候选缺失；[八批当前题回执](placement-batch01.json)保留中断。最初未知鼓励页“万事开头难…”、“很不错哦！”及 `tapComplete`、`name` 阻止旧回放继续。改为当前页的进度条、退出、Duo和鼓励气泡结构识别，随后“佩服！”无需再加字面例外就能继续；新图片填空、数字图片输入也经原版实际答题验证。Node测试使用这些真实回执，且结算页不会被当鼓励页自动点击。

这是已验证的观察机制修正，不是资源匹配的RSI因果收益。每批有步数限制，但本批没有集中计量所有继续／滚动／导航，因此不能宣称整体导航预算符合24或把本批充作消融。[反馈、计量缺口和下一步](exploration-feedback.json)，[失败原样及处理](failure-history.json)。Dream-RSI／Cordis论文与机制边界继续见[研究文档](../../../../docs/RESEARCH.md)。

[合并历史](history.json)现在24状态／16真实控制边，519条未解决的状态动作记录；不是519个独立需求，也不是全App覆盖率。下层可达不等于每个动作执行；15题回执另存，不混入盲测分数。下一轮从解锁后主页和实际音频继续，而非回到倒计时修补。

## 共同模具与Swift实际结果

[v63契约](../../frontend-english-v63.json)完整保留v62的8440项，追加712项，共9152。新增包含九卡库存几何、15题前后截图、三个鼓励页、五页结算及返回、下层阶段和阶段2主页。已解锁主页等还未被候选访问，明确 `not_run`。图片题使用原版图片；原始灰底／红心覆盖层都保留，不能只取DOM第一张IMG。当前源计数器的裁剪滚筒会暴露0..9文本，结算依据实际稳定截图50／100，不把所有滚筒数字当可见文字。

Swift增加阶段列表、原版卡片资源、跳级介绍、独立3红心会话、15题固定观察实例、图片填空／图片输入、原声音资源与结算链。阶段3..8完整测试题单、阶段解锁持久化和阶段2主页尚未实现；相应原版需求仍留在模具中。

- [阶段最终4状态](native-sections-final/observed.json)：进入／继续／返回成功，九卡容器库存几何通过；v63为183 pass／43 fail／8680 not_run／246 unavailable，四整图全fail。
- [跳级最终40状态](native-placement-final/observed.json)：15题、三鼓励、结算及返回走通；[33项局部题目／流程检查](native-placement-final/route-validation.json)通过。v63[独立前端验收](native-placement-final/validation.json)为173 pass／62 fail／8917 not_run／0 unavailable；五个输入框实际几何精确通过，40整图全fail。强制原生radio语义后精确文本粒度仍有差异，不能通过放宽旧文本断言清掉失败。
- 返回的候选仍是旧阶段、5分、525宝石、旧任务状态，原版已经阶段2／10分／530／50任务；这是实质失败。原声音文件取得不是实际扬声器输出或声学一致的证据。布局、动画、整体视觉、实际音效继续待补。

两个最终旅程使用同一成功构建，30核心、61 Python、17 Node检查通过。不能把两个轨迹计数相加成全App分数。先前捕获名冲突、错误interlude控件名、红心覆盖层取错、错误指南button等待均保留；源等待失败后独立快照确认实际导航成功。归档JSON只重定位截图路径／移除本机路径，原PNG字节保留。

## 复跑

在仓库根运行，下列原版实例无需读取未来题单；原版在线探索需要显式自有浏览器会话，不自动借用其它会话。

```sh
python3 projects/duolingo-web/compile-sections-presentation.py --out-dir artifacts/sections-assets-repro-new
python3 projects/duolingo-web/compile-section-placement.py
python3 projects/duolingo-web/freeze-sections.py --out-dir artifacts/sections-contract-repro-new
python3 -m projects.duolingo-web.compile-sections-frontier --out-dir artifacts/sections-history-repro-new
swift build --package-path projects/education-swift
swift projects/duolingo-web/observe-frontend.swift artifacts/placement-repro-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/section-placement-native-scenarios-v1.json
python3 projects/duolingo-web/verify-section-placement.py --native artifacts/placement-repro-new --out artifacts/placement-repro-new/route.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v63.json --observed artifacts/placement-repro-new/observed.json --out artifacts/placement-repro-new/frontend.json
```

最后一条当前应该失败，保留真实差异。主页阶段旅程把 `--exercise-home-journey` 换为 `projects/duolingo-web/sections-native-scenarios-v1.json`，并使用新输出目录。资源按两份 `reference-assets-en-zh-sections-v1.json`／`reference-assets-en-zh-section-placement-v1.json` 和原有fetch工具重取；归档receipt含原始与渲染hash。
