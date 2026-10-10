# 探索与前端模具修正 · 2026-10-10

用户指出探索不足、E2E遗漏前端要求、自定限制干扰1:1。此目录记录实际修正，不宣布复刻完成。

## 首轮实际发现

从自有匿名浏览器当前 `/learn` 状态（西语课、一课完成）悬停 More，显示 English Test、Create a profile、Settings、Help、Sign in。点击 Settings 进入 Preferences，出现音效、动画、鼓励信息、听力练习开关及 Dark mode；进入 Privacy 看见两个隐私开关与未改动时禁用的 Save changes；从此打开 Help Center 看见 FAQ 分类。以上页面均保存原始快照；没有执行的开关效果仍未知。

- `history.json`：5个真实状态、4次实际转移及观察到的操作。
- `frontier.json`：从历史推导22项未访问动作，已观察结果才消去动作；不可用不算完成。不是完整需求清单，也不证明探索充分。
- `home-layout.json`：1200×732视口，实际 duolingo-sans 字体、控件几何、32个图片资源路径。路径去除查询参数，仅用于需求追踪；资源路径的首次采集记录，后续实际资源见 reference-assets.json 和 choice-assets.json。

## 历史首轮失败基线

`combined-result.json`：同一源码期间，冻结业务12/12通过；`candidate-frontend.json` 的10项原版文案全部失败，另有3项 pending；整体返回失败。`candidate-observed.json` 是真实隔离 Swift 进程的 AX 文本，不是手填候选结果。`reference-observed.json` 来自实际浏览器 DOM；`reference-frontend.json` 同10项通过、3项未验证，因此原版的初始契约也没有整体完成。

原来的12项测试检查抽象动作语义，无法因课程/内容改变而失败；现在统一入口会暴露前端文案缺口。这只是第一步。视觉、原版音色/时序、More悬停及消失仍显式未验证；不以文案一致证明1:1。历史原版1200×732与Swift2624×1744图像尚未对齐采样和窗口装饰，不作为视觉通过证据。

## 当前实际进展

- `curriculum-first.json`：原版第一节12题完整观察；`curriculum-second-01.json`保留第二节最后一题因未知短语配对而停止的失败；`curriculum-second-02.json`记录随后在原版确认全部配对和完成。不是重复修旧测试，发现了 `my + noun` 组合及词块翻译要求。
- `compile-observed-course.py`把实际题面、选项顺序、正确反馈、配对列顺序和词库编成 `fixture-reference-v4.json`，没有用候选答案证明原版。默认客户端已切换为这两节西语课24题。
- `reference-assets.json`和`choice-assets.json`记录公开加载的原版字体/图形来源与摘要。题图实际来自CSS背景，早先在radio下找到的inline SVG是反馈装饰，已纠正来源。Duo只取一个实际动画帧，不能算完成动画。
- `settings-sound-reload.json`确认关闭Sound effects后同访客reload仍关闭；`more-hover-dismiss.json`确认菜单展开和移出关闭。当前探索历史11状态、11转移、23待访问动作；新增分支使队列增加，不能用队列长度衡量探索收益。
- 第一个星节点包含三节课，两个已观察课时不是两个路径节点。第三节第一题及三张图已实际观察，后续仍待探索；不把现有数据量当成需求上限。

## v4 课程修正回执（88a9f72）

`product-current-result.json`及同前缀文件来自同一验证期间：源码与资源摘要未改变，冻结业务12/12通过，24题的144项文案通过；主页/More契约12通过、Settings 7失败，视觉/音频2项未验证，产品整体失败。实际原生观察与五张窗口截图一并保留。该业务回归仍使用历史v2题库；原版西语数据另由课程前端契约检查，不能混为全部业务1:1。

`course-hint-failure.json`保留此前141通过、3失败的文案回执；词块提示原本没正确暴露给AX，修复后144通过。`native-hover-unavailable.json`保留采集不到自有窗口的真实失败，根因未确认。`product-hover-failure.json`保留整体验证时悬停未触发的结果；当前驱动在截图后明确先移出再移入More，重跑可读到实际菜单与Settings页，未放宽原版断言。

## 原始视觉差异

`reference-home-1200.png`为真实原版一课完成的主页；`visual-progress.json`用于候选对应初态。`visual-window.png`和`visual-window-metadata.json`记录实际原生窗口；只按contentLayoutRect裁去32pt窗口装饰、按2x Retina采样归一，得到`visual-candidate-content.png`。两端内容1200×732，未对产品内容做平移、遮罩或局部裁切。

`visual-result.json`只给原始RGB差异诊断；`visual-difference.png`保留差异。可直接看到正文粗细、锁定节点透明度、开始提示/环位置、图形及Duo动画帧等差异，不能用低平均差异宣布通过。原版语音身份、反馈音效和时序尚未对齐；系统西语发音不是原版音频验收。

## 继续方向

继续探索待访问动作，将真实结果变成业务和前端契约；同时对齐比较状态、视口及采样，修复实际布局、字体、素材、内容和声音。历史反馈用于调整探索策略，随后用真实任务消融检验效果；当前未访问优先只是起点，没有宣称 RSI 收益。原生 Goal 保持 active。


## v4.1：偏好页、实际保存反例与跨课探索

原生已接入Preferences页面的四个开关、三项外观选择和账户/支持导航卡；四个开关独立保存，Sound effects控制音效，不代替旧的全局静音。`sound-effects-speech-green.json`记录原版关音效时仍调用未静音的verde语音，并给出实际公开语音资源；没有将媒体调用当成输出录音。

`frontend-preferences-v4.1.json`增加4项控件几何与5项重启恢复检查。原生9项通过，另1项课程效果仍未验证；实际布局截图与1200×732的原始差异均保留。几何通过只覆盖这些开关，不证明整页视觉。Animations/Motivational messages/Listening exercises目前只保存偏好，其课程效果还未实现和验证。

原版使用同一契约复跑，出现了新的反例。`preferences-reference-verdict.json`为立即刷新时8通过、1失败、1未验证；`preferences-reference-ack-03.json`虽然9项通过，但最初的Sound effects并非开启，不能声称完全匹配初态。`preferences-reference-ack-04.json`先恢复并刷新验证四项均开启，再关闭、等待对应保存请求200、刷新读状态，结果7项通过、Sound effects和Animations两项持久化失败，另1项未验证。没有改低断言来通过。

`preferences-save-network.json`记录只含已去除用户ID的接口路径、状态码与布尔字段：普通偏好与Motivational messages使用不同保存路径。`observe-reference-preferences.mjs`提供可复跑的真实采集，分别等待对应接口，并验证初态；回执只报告实际事实。保存200仍不足以证明最终状态稳定，缓存、页面水合与保存时序的关系尚未定位。统一入口也比较这份原版事实，因此原版反例会直接出现在产品结果中，不能只看候选通过。

`preferences-product-*`保存当前同一源码、资源及参考输入未改变的验收。原生主页/菜单/设置文案19项通过，视觉/音频2项未验证；课程文案144项通过；原生偏好9项通过、1未验证；原版偏好7通过、2失败、1未验证，整体仍失败。核心5项、Python47项、音效开关与全局静音分离的播放传输检查通过，不能替代原版音频身份/输出或产品完成。

`compile-reference-knowledge.py`从原版正确反馈提取10个词义映射，包含本轮新确认的green→verde；不会读取候选答案。`explore-curriculum.mjs --lessons 3`自动从新访客完成前两课，实际回答第三课green后，保存未知blue题并停止。`multi-lesson-knowledge-01.json`保留26个题目现场（25个有反馈、最后1个未回答）及运行时知识快照；metadata保存代码/知识/结果摘要。第三课内容并未因此完成。数据复用不是RSI策略自改进，探索策略消融仍待进行。

当前历史17状态、18转移、24待探索动作。接下来继续定位原版保存反例、探索第三课与原版课程数据来源，减少逐词手工推断，并补原版语音、导航、反馈、动画及探索策略实验；Goal仍active。
