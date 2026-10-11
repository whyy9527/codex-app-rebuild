# 主页动作、前端覆盖与反馈音

本批从倒计时局部修正转向主页入口与实际结果：个人档案、登录、宝石小店、“更多”，逐一从原版进入并返回。历史探索回放按文本/几何事实数量偏好长指南页，却没有发现原生入口仍回落旧原型；本轮在在线采集前保存三种策略候选，选择优先检查缺失消费者的策略。当前Codex会话生成并执行，未另开模型worker。这是有真实反馈与在线行动的探索迭代，不是完整Dream-RSI，也未证明策略因果收益。[事前选择](strategy-seal.json)、[实际反馈及下一选择](exploration-feedback.json)连接历史原始实验与本批证据。

## 模具补齐

`capture-visible-state.mjs`补采普通链接和输入框等全部可见动作，保留重复控件的状态内身份；后续采集增加实际中心点hit-test，避免把遮挡背景当作可点击入口。修复默认checkVisibility把CSS隐藏错误文字当成事实的问题，保留旧观察，不改写其历史结果。动作库存不能只从已有测试生成。

`capabilities.rebuild.coverage`将真实动作→已观察旅程→实际前端验证结果连接起来。未建立场景的动作显示unmodeled，执行过的检查继续分别显示pass/fail/not_run/unavailable。最终库存中183条控件状态记录未建模，四个已建模入口仍fail；其中有浮层背后的背景控件和重复上下文，不是183项独立产品功能，也不构成完整产品探索。后续hit-test信息缺失的旧记录仍未知，不能推断可点。

v49原样保留v48全部2495项，新增92项，合计2587项；包含真实目标页面/浮层、控件角色/启用状态/几何、文案、整图和真实返回状态。四条旅程的原版/Swift共用场景身份和进度夹具，原生驱动按实际AX操作并保存每条失败，不因为先前已存在按钮就判完成。声音未取得原版应用输出的部分保持pending，不用播放器事件替代声学验收。

初次新标签没有显式视口，元数据viewport为null、PNG为2384×1410，比较器拒绝1200×732契约。初始冻结与源图保留于`source-viewport-uncontrolled`等文件；随后显式1200×732重新采集，冻结函数现在拒绝视口不一致。这次是实施开始后的模具修复，不能包装为事前盲验。其它失败包括同名侧栏/页脚Shop和菜单/主页Login选择器歧义；改用已观察data-test身份。重入旧页还曾重复安装音频钩子，最终采集用新页和幂等钩子，不把重复事件当多次提示音。[失败记录](collection-failures.json)。

## 实际实现与剩余差异

根入口接入年龄注册页与独立登录表单，登录可切换注册、打开忘记密码展示页，关闭返回学习页；“更多”改为原版中文菜单与位置。宝石小店接原版客态遮罩、奖励文案、原心形/激冻资源及建档入口；原生观察发现外层LearningView未将Shop路由给该视图，随后修复，不能只看组件源码就认为集成完成。Apple/商店/菜单图形来自原版实际公开资源，URL与SHA见[resources.json](resources.json)。修复了文字也被下投影的实现错误。

旧二进制6状态、两条返回不可用，按修复后共同模具为15pass/25fail/2505not_run/42unavailable。第一次集成8状态无驱动失败，但Shop仍是旧页面，58pass/27fail/2499not_run/3unavailable；修外层路由后65pass/23fail/2499not_run/0unavailable，四个声音pending仍未执行。所有整图继续失败，几何/字体/颜色和主页动效相位尚未对齐。角色和可点击不代表真实服务已接通：登录提交、OAuth、找回邮件服务、帮助及排行榜等仍有未建模/未实施行为，前端壳不能当作完整功能。

探索已完成课程节点另发现“练习 +5 经验”和“晋升传奇 +40 经验”的弹层，原生旧重复开课逻辑尚未补齐。练习先遇建档中断；合并Later与重试的动作发生遮挡/节点脱离超时，精确关闭行为仍未知，未强制点击或推断规则。随后沿历史已观察`/practice`换入口，进入真正听音配对。[实际新节点及当前练习](discoveries)。这些额外探索独立于四动作pilot预算，不作为其留出收益。

## 真正触发的反馈音

在当前`/practice`点击语音2再配“再见”，原版两次调用`https://simg-ssl.duolingo.com/videos/sound/Match_Incorrect.mp3`。播放promise成功、音量1、未静音；自有浏览器PID启动参数无mute-audio。但同步自有浏览器loopback仍为零，具体输出/过滤原因未确定，因此原版声学证据为unavailable，不认定静音。第一次录音因动作发生在12秒窗口之后而无效，失败原因保留；新的`capture-source-pairing-audio.mjs`在收到READY后自动触发实际源动作，记录开始/结束时间，不录麦克风或其它应用。

原音按实际URL下载且记录SHA；默认独立练习v4原样保留v3内容，只将该原版listenMatch错误提示音绑定至两个已冻结的同组件问题。这是从当前实例到历史同组件的明确复用推断，主课程其它类型及完整源输出一致性仍未验证。原生录音包含实际错误配对AX动作，波形与源文件相关性0.999999883、拟合增益1.000000776、残差RMS0.0000174，确认播放了原音；时间/增益拟合只是诊断，不是端到端1:1。详见[source-sound](source-sound)、[原生声音比较](sound-analysis.json)。

最终主页8状态无驱动失败；独立练习47状态无驱动失败，严格前端74pass/53fail/2457not_run/3unavailable；开箱6状态，严格前端19pass/12fail/2556not_run。它们是实际执行结果，不是视觉完成。构建、30核心、61 Python、主页往返、默认独立练习与开箱回归的最终记录见[verification-summary.json](verification-summary.json)。完整Goal仍active；原始Dream-RSI/Cordis及既有无收益/不可归因实验见[研究来源](../../../../docs/RESEARCH.md)。

## 复跑

从仓库根使用全新输出目录，原生UI任务顺序执行：

```sh
python3 projects/duolingo-web/freeze-home-journey.py --out-dir artifacts/home-journey-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/home-journey-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/home-journey-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v49.json --observed artifacts/home-journey-native-new/observed.json --out artifacts/home-journey-native-new/validation.json
python3 -m capabilities.rebuild.coverage --inventory projects/duolingo-web/evidence/english-home-journey-v1/action-inventory.json --contract projects/duolingo-web/frontend-english-v49.json --validation artifacts/home-journey-native-new/validation.json --out artifacts/home-journey-native-new/coverage.json
swift projects/duolingo-web/observe-frontend.swift artifacts/home-matching-audio-new projects/duolingo-web/fixture-reference-en-zh-v14.json --reference-color-scheme light --exercise-matching-audio /absolute/path/to/capture-owned-audio
```

原版探索使用`capture-home-journey.mjs --cli <playwright_cli.sh> --session <实际源会话> --seal <strategy-seal.json> --out <全新目录>`。原版应用录音使用`capture-source-pairing-audio.mjs --pid <经核实自有浏览器PID> --recorder <capture-owned-audio> --cli <playwright_cli.sh> --session <实际源会话> --left <当前可见语音标签> --right <当前可见文字标签> --out <全新目录>`。不要猜PID或把新自适应题目当旧题。前端比较因真实失败返回1。

[实际原版／Swift 对照](comparison.html)与[下一轮探索队列](frontier.json)由本批原始证据生成。
