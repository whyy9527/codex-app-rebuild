# 指南实际探针与前端模具反馈

真实模型04的语义代理计分0／0不代表没有遗漏。独立后续探针实际聚焦Hi，再按Tab，到welcome，focus-visible=true；[操作回执](source/tab-welcome.raw.txt)及[焦点画面／事实](source/guide-keyboard.json)保留。原版词语是aria-label命名的透明DIV，不能伪造button语义。Swift目前只有下划线路径，缺对应焦点控件；尚未实现，不称完成。click is仍未执行，其他词语/输入模式/声音分支继续未知。

## 共同前端验收

新采集器保存实测CSS窗口／DPR和activeElement／focus-visible／焦点CSS。此次产品源实测1200×732、DPR1；旧04截图缺这些元数据，不逆推、不回填。图像比较支持声明的实测reference_capture，与原生窗口按各自scale裁剪／降采样到共同CSS尺寸，继续严格逐像素、无掩码／放宽／对齐搜索。两项反例检查拒绝伪造源scale、尺寸和错误内容。

[v73](../../frontend-english-v73.json)完整保留17092条v72要求，新增343，共17435。新增两状态区分普通指南和实际键盘焦点；包括整图、文字、控件几何／状态以及焦点交互要求。未访问的键盘状态不计通过。现有原生指南与主页共2状态、0驱动失败，[严格结果](native-matched/frontend-v73.json)61pass／30fail／17265not_run／79unavailable；整图失败，不合并历史其他旅程结果当通过率。

首遍误用pending发音引导偏好，原生出现原版当前没有的遮罩；保留[native失败夹具回执](native/observed.json)，不将其用作同状态视觉结论。重跑明确使用上一批真实dismissed偏好＋相同进度，保存[native-matched回执](native-matched/observed.json)。没有修改产品逻辑来隐藏引导。

65Python／21Node检查通过；新图像机制对原有v72的全部状态及图像差异数值逐项不变，仍716pass／243fail／15042not_run／1091unavailable，见[回归](regression.json)。本批没有Swift产品修复或声音等价收益；缺口仍为失败／不可验证，不把模具改善称作复刻改善。

## 探索续跑

[历史](history.json)146状态、69条已有可追溯边，[frontier](frontier.json)3963待探索动作。04的8次实际分组探针另记[procedures](experiment-procedures.json)，因其包含reload／focus／Enter等程序，不冒充一条源pointer动作已覆盖。四次训练、四次在线及重复Enter均保留；两个后续源状态也保留。状态数／待探索数不是独立业务数，也不是充分性证明。

[反馈](exploration-feedback.json)要求后续策略读取主页／前端失败和未知，改变观察维度，优先发音完整练习及音频、主页下层／故事／电台、第三课后续和恢复，再验证词语焦点。不能继续只奖励文字数量，也不能围绕时钟字段优化而搁置这些消费者。真实RSI因果收益未观察到，[04报告](../../../exploration-ablation/REPORT04.md)保留负面结果与成本；原论文继续在研究文档中。

## 复跑

从仓库根使用新输出目录。现有源数据为真实观察，不等于可随意重置在线访客账号。原生二进制摘要保存在回执，本批未改Swift。

```sh
python3 -m projects.duolingo-web.freeze-guide-probes --out-dir artifacts/guide-freeze-new
swift projects/duolingo-web/observe-frontend.swift artifacts/guide-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit12-frontend-repair-v1/native-final/progress.json --seed-preferences projects/duolingo-web/evidence/english-unit12-frontend-repair-v1/native-final/progress.json.preferences.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/evidence/english-guide-probes-v1/journey.json
python3 projects/duolingo-web/bind-frontend-aliases.py --observed artifacts/guide-native-new/observed.json --aliases projects/duolingo-web/evidence/english-guide-probes-v1/aliases.json --out artifacts/guide-native-new/observed-bound.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v73.json --observed artifacts/guide-native-new/observed-bound.json --out artifacts/guide-native-new/frontend-v73.json
```

[归档审计](archive-audit.json)区分原始／归档摘要。PNG字节不变，日志仅归一化本机路径；04模型与源动作证据不被后续探针替换。完整1:1 Goal active。
