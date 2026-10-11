# 当前发音入口、实际语音与共同前端验收

核对当前实现后纠正旧报告阶段判断：Swift已有发音页面及三套观察顺序的练习，不能再称缺专用页面。缺口是后续加载、自适应选题、正常口语、音标进度及完整视觉／声学等价。本批从前端反馈选择重访发音入口，不再围绕时钟或指南文字新增计数打转；不是新的同预算RSI消融。

## 原版与实现

新开原版tab保留两个未完课程和指南。当前访客音标进度全0，实际开始仍为dock／deck；这不是同访客完成三套后的第四次，也不能据此推断自适应选题。开始前的[策略记录](strategy-before.json)、[原版入口](source/entry.json)、[实际点击及media.play](source/start.raw.txt)和[首题](source/first-question.json)保存，CSS尺寸1200×732／DPR1实测。

原版“开始 +10 经验”是264×48链接，Swift原先是44点按钮。修为真实可点击AXLink、264×48命中，44点面＋4点底边；保持后续卡片的总布局高度。构建后真实主页→发音→首题，3状态0驱动失败，[检查](validation.json)确认链接语义、尺寸及dock／deck到达。完整矩形仍不等：源y150.7890625，候选151，严格断言继续fail；没有放宽容差。

[v74](../../frontend-english-v74.json)完整保留v73的17435项，新增当前入口和首题217项，共17652；[同二进制结果](native/frontend-v74.json)69pass／41fail／17437not_run／105unavailable，两张整图均fail。新访客状态不顶替旧非零音标进度夹具；未运行旧状态不算通过。148状态／70条真实边及[待探索分支](frontier.json)继续累积，重复观察不冒充新独立需求或RSI收益。

## 实际声音

原版此次media.play事件明确指向oscaren/1476c4713ac5bd75a4808ea547208a1d；已入库同URL资源摘要验证一致。另跑实际UI入口，仅录自有应用PID、不录麦克风，[输出测量](native-audio/audio-measurement.json)与该资源归一化相关0.99997426、拟合增益0.99985205。保留[录音](native-audio/pronunciation-entry-speech.wav)、动作／时序及源事件；不能把它说成原版浏览器声学输出等价、完成音效或全课程声音通过。

Swift构建及35核心检查通过；前一提交65Python／21Node与旧v72逐项回归通过，本次Swift改动另以真实UI点击和应用输出验证。完整1:1 Goal active。后续继续实际后续发音／正常口语与进度、主页下层／故事／电台、第三课后续；策略同时消费视觉、交互、声音和未知分支，避免再次只优化一个代理分数。

## 复跑

```sh
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m projects.duolingo-web.freeze-pronunciation-current --out-dir artifacts/pronunciation-freeze-new
swift projects/duolingo-web/observe-frontend.swift artifacts/pronunciation-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit12-frontend-repair-v1/native-final/progress.json --seed-preferences projects/duolingo-web/evidence/english-unit12-frontend-repair-v1/native-final/progress.json.preferences.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/evidence/english-pronunciation-current-v1/journey.json
python3 projects/duolingo-web/bind-frontend-aliases.py --observed artifacts/pronunciation-native-new/observed.json --aliases projects/duolingo-web/evidence/english-pronunciation-current-v1/aliases.json --out artifacts/pronunciation-native-new/observed-bound.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v74.json --observed artifacts/pronunciation-native-new/observed-bound.json --out artifacts/pronunciation-native-new/frontend-v74.json
```

声音复跑另编译capture-owned-audio.swift，使用audio-journey.json与--audio-recorder，再执行measure-pronunciation-entry-audio.py，--source指向保存的source/start.raw.txt。源采样是日期限定的观察，不冒充可重置在线账号。[归档审计](archive-audit.json)保留原始／归档摘要，PNG/WAV字节不变，日志本机路径归一化。
