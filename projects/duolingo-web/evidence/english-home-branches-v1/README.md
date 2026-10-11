# 完成节点、传奇与排行榜

沿上一轮未建模动作和真实路由失败继续探索，事前选择见[selection-seal.json](selection-seal.json)。本轮逐步点击原版，不把已有测试当需求全集，新增发现反馈到[下一选择](exploration-feedback.json)。这是当前模型依据历史反馈选择分支并实际执行；没有独立模型worker、受控消融或可归因的RSI收益。

## 实际发现与实现

- 已完成节点有“练习 +5 经验”和“晋升传奇 +40 经验”。原生旧版只是两段文字，负基线无法执行练习动作；现在是实际链接／按钮。
- 练习触发建档提示，“稍后创建帐户”返回原完成节点弹层。源码原有该提示组件，但入口没有接通。
- 传奇先进入独立深色挑战页，显示原版金色Duo、红心、“开始 +40 经验”和“下次再说”。开始后出现建档提示；稳定采集时传奇页已关闭，稍后返回完成节点弹层。下次再说也返回该弹层。原生现按这些观察接通。
- 排行榜是独立青铜等级页、占位榜单、客态行和状态面板，不是旧英文原型。实际选择第一个墨镜图标后出现对应状态图像；原生接入该展示和选择。其它十一按钮结果、清除、重载保存及客态行目的地仍待探索，不宣称服务端已接通。“去学个单元”使用既有独立练习消费者，实际新入口与自适应题目尚未共同验收。

原版观测在[source](source)，均1200×732。观察包含可操作性hit-test、状态内控件身份、DOM/AX、几何、图形和CSS；遮挡背景不作为当前可操作层。源站临时guest数字档案URL已明确脱敏，未改动视觉事实。原版图形来自公开实际资源，[resources.json](resources.json)记录URL、响应／解压SVG／PNG摘要。HTTP gzip解码后用CairoSVG2.9.1三倍渲染，保留内嵌位图；ImageMagick失败记录保留，没有替代角色。

## 共享模具与真实失败

实施前冻结v50，原样保留v49全部2587项，新增152项，合计2739项。新10状态包含完整整图、文案、动作角色／启用状态／严格几何、可操作层的建档提示／传奇页／完成节点弹层出现与消失，以及未验证音频。冻结可复跑且字节一致；原版自校验909pass/0fail仅说明一致性，不是Swift验收或完整覆盖。

`home-branches-scenarios-v1.json`将单步推进串成同状态路径，原生驱动实际AX执行并捕获结果，动作库存连到每个已观察后继。未建模动作继续保留，库存行数不是独立业务功能数。

原版“稍后”保留弹层。初次探索错误地再次点节点、收起弹层，随后传奇点击超时；失败保留后按实际状态单独重开、点击，未强制点击。原生第一次AX动作成功却出现传奇按钮落在内容区之外，整图与几何捕获这个问题；修正ZStack定尺寸容器的顶部对齐后，开始按钮几何与原版一致。AX成功不等于用户能看到／点击，仍需前端验证。

首次三个PNG为1020×648，元数据为2400×1528，比较器判unavailable。新多步采集主动激活自有应用并有界核对实际PNG尺寸，失败图和每次尝试保留；最终10图在第一次尝试均匹配。未确定OS缩放原因，不宣称已证明具体根因或重试效果。驱动旅程失败现在保存记录后返回非零；故意缺失控件的负例实际exit1、0状态，是采集器验证，不是产品缺陷注入或RSI消融。

| 实际运行 | 状态 | pass | fail | not_run | unavailable |
|---|---:|---:|---:|---:|---:|
| 旧二进制负基线 | 2 | 11 | 8 | 2708 | 12 |
| 首次集成 | 10 | 116 | 23 | 2597 | 3 |
| 修复布局／采集后 | 10 | 119 | 23 | 2597 | 0 |
| 既有主页四入口往返回归 | 8 | 65 | 23 | 2651 | 0 |
| 开箱及练习建档往返回归 | 8 | 27 | 17 | 2695 | 0 |

新10状态驱动无失败，所有整图仍fail；完成节点约4pt位置差、建档提示和传奇退出控件小数几何等仍未对齐。旧负基线两旅程缺控件，不能只比较断言通过数量或称为RSI提升。声学验证保持pending，继承上一批原版浏览器输出unavailable；没有新增声音一致性结论。

[完整摘要](verification-summary.json)、[实际图像对照](comparison.html)、[原始失败](collection-failures.json)、[后续探索与修复队列](frontier.json)。Swift构建和30核心检查通过；本批没有修改Python核心，原始RSI论文和历史无收益实验继续保留在[RESEARCH](../../../../docs/RESEARCH.md)。完整Goal仍active。

## 复跑

从仓库根执行，输出目录必须全新，原生UI运行顺序执行：

```sh
python3 projects/duolingo-web/freeze-home-branches.py --out-dir artifacts/home-branches-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/home-branches-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/home-branches-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v50.json --observed artifacts/home-branches-native-new/observed.json --out artifacts/home-branches-native-new/validation.json
python3 -m capabilities.rebuild.coverage --inventory projects/duolingo-web/evidence/english-home-branches-v1/action-inventory.json --contract projects/duolingo-web/frontend-english-v50.json --validation artifacts/home-branches-native-new/validation.json --out artifacts/home-branches-native-new/coverage.json
```

前端比较因保留的真实差异返回1。原版采集用`capture-visible-state.mjs`在当前可见页面逐步记录，路径／角色／控件来源见各source快照；没有把外站guest状态当可任意重置的本地夹具。状态清除、服务端保存及新练习入口仍需后续探索和共同数据准备。
