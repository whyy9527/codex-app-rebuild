# 真实成绩历史、17卡回顾与滚动反例

2026-10-11。接续[原版成绩单漏采](../english-current-walk-v1/README.md)。完整Goal仍active，原始RSI论文与无收益/不可归因实验继续保留在[RESEARCH](../../../../docs/RESEARCH.md)。本批没有新模型调用、消融或RSI收益结论。

## 先补真实交互证据

原版重练实例的口语卡悬停不展开，点击后移开指针仍展示答案，第二次点击收起；见`source-probe/trigger.json`、`second-click.json`和两张PNG。它的口语句为`Good morning, I'd like water and tea.`，与之前17卡实例的`Hot, please.`不同；两者均实际暂缓，没有正常口语评分。DOM给出勾号12×9置于25点白圆、关闭图标16点置于35点白圆/2点边框、标题100点宽、播放控件39×39等事实，见`control-css.json`。不是从候选反推原版。

源滚轮命令返回时立即读取仍为原位；后续稳定采集才测到387点位移：首卡y194→-193，末卡y895→508，关闭按钮随内容上移到-380.5，不能假设它固定在视口。`scrolled-stable.json/png`保留实际事实。两个实例内容不同，不能把它们当同状态整图配对。

## 实际实现与共同数据

`compile-current-review.py`按前批逐题当前renderer回执、真实接受反馈和原版17卡顺序编译显式`fixture-reference-en-zh-current-review-v1.json`。16评分题加暂缓口语，包含实际插入翻译、键盘挑战和引导页。编译器核对translate/speak原句、assist提示、听力卡类型及实际接受身份；不采用未来/初始题单补缺。资源45项，包含实际记录的配对反馈、原音与原版勾/关闭SVG；14份新原音及两幅原SVG/透明渲染图导入应用，哈希全部核验。没有播放事件的声音不据此补成已观察声音。

LearningCore新增可选`ResultReviewPresentation`与运行时`ResultReviewEntry`，在实际继续前保留答案、接受状态和题目身份；暂缓口语使用源展示原句，但`accepted=nil, declined=true`，不冒充评分正确。重开练习创建空历史。26核心检查包含实际17卡顺序、暂缓与插题、输入清除后答案保留和重练隔离，既有25项仍执行。

Swift回顾接实际记录，展示卡片/音频入口、点击展开、关闭和滚动。源已知句子与原音进入模板，不硬写17条页面内容。**这份显式实例尚未替换默认练习**：默认通用夹具没有回顾元数据，仍是静态回顾文字；其听音填空卡、错误卡颜色/去重等源规则继续探索，不能以这一实例宣称全产品回顾完成。候选重练目前重新启动显式夹具，原版则生成了另一套题；自适应选择仍未实现。

v34原样保留v33全部2023项，追加4项原版关闭DIV的几何/enabled，总2027；不凭可点击就替它杜撰ARIA button角色。源新增4全pass，全集214pass/0fail/1799not_run/14unavailable。源自检仍不是候选通过。

## 原生验证与负结果

- native-01：驱动错用只存在于配对题的`question-prompt`等待普通题，真实失败保留；按原生实际标题标识修复后续跑。
- native-02：实际42状态，包括16题、暂缓、引导、结算、17卡、展开、关闭和重练。卡片102个几何/角色/enabled检查通过，但两张整图失败；勾/关闭缺白圆被实际截图揭示。
- native-03：按源CSS修白圆/图标尺寸、标题宽度和音频控件。整图RGB均差从未展开`[2.962,2.027,3.056]`降到`[2.074,1.615,2.082]`，展开从`[3.113,2.220,3.182]`降到`[2.253,1.818,2.252]`；仍fail，不当1:1。
- native-04：补源底部20点空间后驱动记录44状态，却发现`postToPid`滚轮没有移动任何卡。其退出0不能证明滚动；几何反例原样保存。
- native-05：确认自有窗口激活、指针命中后发送实际滚轮事件，等待几何变化。真实44状态、无驱动失败；首卡y-193、末卡y508，与源387点位移相同，滚回首卡y194，再关闭并重练。

最终共同v34为 **147pass／7fail／1873not_run／0unavailable**；本批关联的115项为 **113pass／2fail**，两项均整图。其它5项失败来自实际访问的主页4项和任务页整图，不隐藏旧失败。字体、speaker栅格、气泡和底下结算仍有差异，卡片几何通过不能替代像素一致。所有图像比较仅使用ICC→sRGB、实测标题栏和backing scale，无平移搜索、屏蔽或容差。

同一最终二进制另跑默认练习47状态，包含一次错误/重练、结算/奖励、返回和真正终止重启，无驱动失败。共同计数仍94pass/56fail/1874not_run/3unavailable，新增回顾状态未访问；不能与显式实例累计。主六课保持，默认v3与主课v11未修改。26核心、56 Python、12 Node通过，编译器和冻结器逐字节复现；归档重绑定PNG后重新比较计数相同。没有环境或麦克风录音，没有新增声学一致性证据。

## 复跑与下一步

```sh
python3 projects/duolingo-web/compile-current-review.py
python3 projects/duolingo-web/freeze-result-review-controls.py --out-dir artifacts/review-freeze-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
node --test projects/duolingo-web/*.test.mjs
swift projects/duolingo-web/observe-frontend.swift artifacts/review-native-new projects/duolingo-web/fixture-reference-en-zh-v11.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-quests --exercise-current-review
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v34.json --observed projects/duolingo-web/evidence/english-result-review-native-v1/native-05/observed.json --out artifacts/review-validation-new.json
```

摘要、图像差异、二进制身份和未完成项见[verification-summary](verification-summary.json)。下一批优先探索真实错误后的回顾卡和重复重练语义、听音填空回顾/暂缓，从源证据推广到默认课程；继续修字体/播放图形/声学及其它未访问分支。当前仅全对与暂缓卡的绿色展示已获源证据，错误卡颜色/去重未验证，完整Goal不收窄或完成。
