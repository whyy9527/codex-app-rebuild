# 第三课：从探索遗漏回到真实前端与声音

原版中文母语→英语，第2阶段第2部分，续接既有第3课首题跳过后的现场。真实执行15道判题题目、1道口语拒绝、首题错题重练、结算、补心、建档提示和主页。首题原跳过及重练各有成绩记录，成绩单语义库存17卡；当前视口行动采集只收16个主卡，不能误报全部可见。源页面1200×732；较旧首题采集没有新版截图一致性元数据，不补造通过。

发现了旧模具缺的两种三行表格填空、五组文字配对的两次实例，以及结算中间的红心奖励。它们不是上一课的换词题：表格需要示例、强调、边框、分隔线和填写位置；文字配对左列显示中文，不能复用音频波形。Swift接第三课主页入口、真实课程内容、原版公开素材、表格组件、文字配对及补心/回主页。原版结算为15XP/100%，回主页5心、505宝石、Lesson4of6；它们是该实例观察，不是推导出的评分公式。

## 探索、RSI与未完成

上一批真实模型 deployment05/06 的反馈指向未完成课程、声音和故事/电台。本批沿该反馈继续，发现新题型和中间奖励，而非重复日历。新需求追加v78，旧v77的20903项逐项保留；[探索反馈](exploration-feedback.json)区分本批主代理人工引导与此前真实模型调用。不能据此宣称RSI有因果收益；真实匹配预算对照仍未完成，论文及原机制证据继续见[研究说明](../../../../docs/RESEARCH.md)。

[源码编译器](../../compile-unit12-lesson3.py)仅消费真实UI、实际选择和播放回执，不读未来答案或用候选证明原版。原网络回放器对patternTapComplete仍报告未支持；当前新增的是UI证据编译与原生执行消费者，不冒充旧网络回放器已有覆盖。

未访问的第四课、故事/电台解锁、其它作答/键盘/悬停方式、人物动画来源与完整声学一致性继续留在探索队列。当前整图仍有差异，不能称1:1完成。第四课真实入口已打开，尚未开始作答。

## 声音与实际失败

原版观察器包装原HTMLMediaElement.play并调用原方法，记录call和playing；早期空URL调用保留，不能当静音证明。正确反馈原MP3音量0.35，配对Match_Correct_A_A_01…05音量1，结算音量0.5。没有录制浏览器声学输出。

原生基线实际记录左词合成点击声和右词语音；修复为文字配对左词不插入合成声、右词播放原语音，同时播放原配对音效，末对另触发原正确反馈。自有应用录音只录显式PID，麦克风关闭，动作在录音启动后执行。实际输出与原MP3的相关性只说明该素材出现，不证明全程声音/时序等价。

`native-before`保留31状态基线；`native-first`保留35状态及旧驱动寻找review-continue失败，不回填为通过。后续最终回执、严格结果、音频测量和差异图在本目录分别保存。三轮构建/执行不是独立实验样本，也不是RSI消融。

## 复跑

从仓库根运行，输出目录须新建。先编译真实证据，再构建与实际UI执行：

```sh
python3 projects/duolingo-web/compile-unit12-lesson3.py --out-dir artifacts/lesson3-compiled-new
PYTHONPATH=. python3 projects/duolingo-web/freeze-unit12-lesson3.py --out-dir artifacts/lesson3-contract-new
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/capture-owned-audio
projects/duolingo-web/run-native-course.sh artifacts/lesson3-ui-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit12-frontend-repair-v1/native-final/progress.json --seed-preferences projects/duolingo-web/evidence/english-unit12-frontend-repair-v1/native-final/progress.json.preferences.json --exercise-home-journey projects/duolingo-web/evidence/english-unit12-lesson3-v1/journey.json --audio-recorder artifacts/capture-owned-audio
```

编译器输出与已保存Swift bundle/共同夹具须一致，不能拿未安装的编译产物当实际候选。严格比较命令见本目录逐项结果；几何零容差，整图不加遮罩。旧失败、未覆盖、不可用继续显示。

最终同二进制41状态无驱动失败、37 Swift核心/67 Python/24 Node检查通过。v78保留20903旧项，共23444项；本轨迹633pass/546fail/21487not_run/778unavailable，前端仍失败。209状态/104边/5920待探索控制记录不是完成率。[逐项验收](frontend-v78.json)、[实际检查](validation.json)、[原始失败及几何审计](reference-image-audit.json)。

严格图像门禁发现本批40张原版PNG实际2384×1410，独立测量却应为2400×1464。没有用PNG反推比例或缩放凑齐：对应原整图断言保存在v78的`unavailable_reference_requirement`，本批图像比较未执行，须重采同一原版状态。修复CDP显式clip并在采集器增加PNG对独立几何一致性检查；新原版采集真实得到2400×1464，回归使用真实旧失败/新成功PNG。新采集时宝石已变155，属于另一个状态，变更原因尚不明，不能替换旧505参考冒充同状态。人物/字体/题面仍有明显差异。

声音混合中语音和配对音效重叠，整段对单独音效的相关性仅0.338；不能因此报音效等价。进一步使用原语音拟合并减去后，修复后残差信号与原配对音效相关性0.999955、拟合增益0.99994；基线增益约0.00000136。左词实际录音由非零变为零。[直接比较](matching-audio.json)、[重叠音频诊断](matching-audio-decomposition.json)。这些是一次真实触发的素材出现证据，不是全声音/时序等价，也不是消融效果。
