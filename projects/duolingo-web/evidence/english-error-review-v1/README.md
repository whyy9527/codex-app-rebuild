# 错误首答、课末更正与18卡成绩单

2026-10-11。接续[17卡历史实现](../english-result-review-native-v1/README.md)。完整运行 Goal 保持 active；原始 Dream-RSI、Cordis 论文和负面消融仍在[RESEARCH](../../../../docs/RESEARCH.md)。本批是实际探索与修复，没有模型消融或 RSI 收益证明。

## 原版新证据

实际重练先完成听音配对，再在“热”选择题故意选 `coffee`。原版拒绝并显示正确答案 `hot`；随后继续，实际暂缓 `More milk?` 口语，观察到插入翻译，完成后续题与挑战引导。课末错题引导后再次出现相同公开题内容和选择顺序，实际选择 `hot` 获接受。源结算为“你莫不是特工？”及完成6项听力挑战；动画数字不当作可靠成绩。

成绩单有18张卡：16次接受、1次拒绝、1次暂缓展示。第1号卡保留首答 `coffee`，红底红叉；第17号卡另保留改答 `hot`，绿底绿勾。两张同题卡没有去重或覆盖。点击分别展示各自答案及正确答案。原版最后一行实际滚动387点后可见；不是把布局存在当作已在视口。详见 `source/start.json`、`wrong-assist.json`、`after-wrong.json`、`after-speech.json` 及三张 `review-*.png/json`。

短答案浮层实际99×136，15点padding加2点边框，标签13粗体，两组41点高且间隔20点。顶部错误卡及滚动后的更正卡浮层均在卡顶下78点；此前靠近底部的口语卡浮层在上方。源码CSS和实际矩形保存在 `wrong-tooltip-css.json`、`correction-tooltip-css.json`。这些短答案样本不证明所有长答案/多行浮层规则。

本次仍未遇到 `listenIsolation`。重复重练此前也没有发现其回顾卡，不能把重复执行既有题型当作探索充分；[frontier](frontier.json)明确改从不同入口/已保留状态继续，并保存正常口语、默认回顾和其余未访分支。

## 模具与实现

`compile-error-review.py`核验错误回执、改答身份、实际18卡顺序及红绿CSS，生成16评分题的独立实例夹具（课末多一次改答）和49项原资源清单。与旧实例共用 `review_instance_compiler.py`，旧夹具和资源清单输出逐字节不变。缺失评分、奖励公式、自适应选题和声学一致性继续记未知。原红叉SVG与实际原音导入，49项资源回执的落盘SHA全部验证。

v35原样保留v34全部2027项，追加181项：三状态54张卡的几何/角色/enabled、实际答案文字、整图和真实背景采样，共2208。源自检395pass/0fail/1799not_run/14unavailable，其中新增181全pass；源自检不能代表Swift通过。`sample-frontend-colors.py`仅从实测内容区、backing scale和ICC→sRGB后的截图采样契约位置，不复制期望颜色或生成通过标记。

Swift错误卡按实际拒绝状态选择红底/红字与原红叉；暂缓评分仍nil。短答案浮层改用内容宽度、13点标签与根据实际滚动位置选择上下方向。27核心检查验证错误首答和改答保留不同attempt ID、同题ID，原始答案不覆盖、暂缓不评分和重练清空。

## 真实验证与负结果

- 原版首错回执的首次本地解析使用错误cwd，虽然解析失败，后续Continue已执行一次。恢复正确文件确认拒绝，没有重答或把恢复当新动作。一次采集命名撞已有raw文件，被防覆盖保护拦住；另用新文件名读取当前状态。
- 首次冻结器错误要求DOM text-run逐条出现标题，实际标题在AX snapshot中存在；修正证据读取，不改期望文本，保留旧需求。
- native-baseline-01：驱动误用 `option-coffee`，真实失败；当前实例实际选项ID为1。修驱动后 baseline-02真实48状态，含一次错答、更正、18卡、展开、387点滚动、关闭、重新练习。
- final-01同样48状态无驱动失败。三整图RGB均差分别从 `[3.390,2.693,3.414]`→`[2.055,1.719,2.226]`、`[3.300,2.640,3.956]`→`[2.119,1.784,2.277]`、`[2.477,1.233,3.090]`→`[1.362,0.829,1.457]`。均下降但仍fail，没有放宽容差。
- 新增181项仍 **176pass/5fail**：三整图及两红底采样。红底实际由旧绿 `[215,255,184]` 修成 `[255,223,223]`，原版为 `[255,223,224]`，色彩转换后仍差1级，不能算通过。全契约210pass/10fail/1988not_run；其它5失败为既有主页4文本和任务页整图。
- 同一最终二进制回归旧17卡实例，44状态无驱动失败，147pass/7fail/2054not_run；未展开图误差不变，展开图下降仍fail。不同轨迹的通过数不累加。

构建、27核心、56 Python、12 Node通过，旧编译输出字节一致。默认练习真正重启回归结果见 `verification-summary.json`；此显式实例没有替换默认练习，默认回顾及未知题型仍未完成。仅导入原音不证明实际声学一致，没有麦克风或环境录音。资源哈希、二进制身份和原生失败完整保留。

## 复跑

```sh
python3 projects/duolingo-web/compile-current-review.py
python3 projects/duolingo-web/compile-error-review.py
python3 projects/duolingo-web/freeze-error-review.py --out-dir artifacts/error-review-freeze-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/error-review-native-new projects/duolingo-web/fixture-reference-en-zh-v11.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-quests --exercise-error-review
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v35.json --observed artifacts/error-review-native-new/observed.json --out artifacts/error-review-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v35.json --observed artifacts/error-review-native-new/observed-colors.json --out artifacts/error-review-native-new/validation.json
```

下一步先改变寻找听音填空的探索路径，再按实际源证据推广默认回顾；修复颜色/字体/整图与实际声音差异，继续未访导航。所有范围继续由完整Goal管理，不以本批新增行为宣称探索充分、1:1完成或RSI有效。
