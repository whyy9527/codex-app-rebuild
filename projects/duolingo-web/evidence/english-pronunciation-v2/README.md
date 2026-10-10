# Swift 发音页与实际播放 · v2

实现原版发音页39个音标、词例、分组、零进度条、蓝色开始按钮和导航选中态。第一次候选仍落到旧通用页面：顶层LearningView的路由白名单缺Pronunciation；`route-failure`保留失败，已将它接入ReferenceHome。第二次LazyVGrid未暴露全部离屏词例，`lazy-failure`保留结果，已改为完整Grid。没有把这些失败改成通过。

`source-audio-completion.json`通过实际按钮逐项等待play及ended，再等待500ms完成边界，39项均只有一次对应资源调用，无失败。此前快速采样把上一按钮的延迟调用归入下一窗口的问题已实测排除；旧v1保留。原始39个公开MP3按实际URL下载并捆绑，摘要见`../../reference-pronunciation-audio-v1.json`；没有用系统TTS代替。每项源事件结束不证明Swift全部输出等价。

v10保留v9全部七课102题和历史文件，仅给真实六课主页快照加入连胜2及当时倒计时12小时；匹配进度`progress-source.json`为原六课seed的生命3，直接来自v1源截图，未推断生命刷新机制。新增可选streak元数据供主页显示，不改业务结算规则。该状态用于固定参考比较，不代表自动计时/连胜规则已完成。

构建、21核心业务检查及52框架检查通过。`matched`实际点击原生导航，新页59pass/15fail/4not_run；完整v18为78pass/19fail/1492not_run。15按钮几何仍零容差失败：候选AX位置/尺寸与浏览器分数坐标不完全相同，保留原始矩形，不放宽。整体1200×732、sRGB同空间、仅裁原生标题栏/2x降采样的整图仍different；字体、边框/计时颜色等尚有差异，不以平均差小宣称1:1。

`matched/phoneme.wav`仅录本次owned子应用，无麦克风及其他应用；录音开始后0.120秒实际AX点击sound-0，peak0.4824，RMS0.02492，记录见wav.json。它证明该按钮确实输出声音，不证明全部39按钮、音效、音量或原版实际声波等价。

源开始链接已真实进入/alphabets/en/pronunciation；首次只出现加载中，`practice-start.json`保留，后续`practice-ready.json/png`显示“你听到了什么？”，dock/deck两项radio、跳过和禁用检查。未作答，不推断正确选项。**候选开始仍进入旧通用destination，练习链未实现**，不能把本页通过当成练习通过；下一轮从该真实挑战续跑。

## 复跑

```sh
swift build --package-path projects/education-swift
mkdir -p artifacts/pronunciation-recorder
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/pronunciation-recorder/capture-owned-audio
swift projects/duolingo-web/observe-frontend.swift artifacts/pronunciation-new \
  projects/duolingo-web/fixture-reference-en-zh-v10.json \
  --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json \
  --reference-color-scheme light --observe-pronunciation \
  --pronunciation-audio-recorder "$PWD/artifacts/pronunciation-recorder/capture-owned-audio"
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v18.json \
  --observed artifacts/pronunciation-new/observed.json --out artifacts/pronunciation-new/result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/pronunciation-new \
  --pairs projects/duolingo-web/evidence/english-pronunciation-v2/pairs.json --out artifacts/pronunciation-new/visual.json
```

前端命令预期返回fail；图像命令零退出仅表示诊断成功，结果仍different。首个图像诊断缺trajectory清单字段而失败，补全清单后重新执行，未改像素或评价。完整Goalactive；优先继续实际练习链、视觉和声音差异，不用扩大验收文档代替实现。
