# 原版英语发音页与原生缺漏 · v1

原版实际中文→英语、1200×732、六课进度，从主页真实点击发音并通过正文就绪检查；JSON、PNG、几何、就绪回执与39个音标按钮实际点击记录均保留。顶部两行文案、元音15项、辅音24项，按钮包含词例及零进度。

`hot-audio.json`单独点击ɑ hot 0出现aa.mp3播放调用。`audio-actions.json`随后逐次点击39项，37个窗口各见一个URL，b/n窗口还出现空URL，部分资源可能来自前一次的延迟播放，归因未验证，不能直接用于实现映射。`phonemes.json`保留原始窗口URL列表并明确unverified。旧探针有重复包装，同一调用的相同日志不能解释为重复播放多次；资源身份和muted=false不证明实际声波等价。下一步用播放结束边界逐项重测，不能过滤异常凑唯一映射。

`text-geometry.json`是实际可见DOM读取，`phonemes.json`绑定来源哈希、顺序、组别和按钮矩形。点击不进入课程，路径仍/characters；练习开始链、进度增长和恢复尚待探索，不能按主课程推断。音标按钮后半部分需要滚动，初始截图不含所有39项。

前端v18保留v17全部1511项并新增78项，共1589项；文字44项，首屏15个按钮的语义角色/零容差几何30项，整图/交互/练习链/音频与恢复4项待验证。没有以240个原始事实代理数量冒充240项需求。

实际原生AX导航检查使用现有v9构建及归档六课进度，不修改App代码。`native-before`显示导航点击成功，但页面仍是学习路径。仅新页：44fail、30unavailable、4not_run；完整v18：19pass、48fail、30unavailable、1492not_run。19通过属于本次观察的既有主页要求，不能写成发音页通过。初次命令误填不存在的seed文件，在启动前失败；修正为下面已存在的进度后使用新输出目录，保留本地失败日志。

```sh
swift projects/duolingo-web/observe-frontend.swift artifacts/pronunciation-new \
  projects/duolingo-web/fixture-reference-en-zh-v9.json \
  --seed-progress projects/duolingo-web/evidence/english-seventh-native-v1/radio-missing-ax/progress.json \
  --reference-color-scheme light --observe-pronunciation
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v18.json \
  --observed artifacts/pronunciation-new/observed.json --out artifacts/pronunciation-new/result.json
```

下一步根据这些已冻结原版事实实现Swift发音页，重测音频归因后接真实播放，实际点击/录音及整图比较；继续探索练习链。不得以新增导航或本契约替代实现。完整Goal保持active。
