# 排行榜状态与练习入口：实际补漏

历史动作清单只收按钮和 ARIA 控件，漏掉原版悬停才显示的无 role `SPAN`“清除”。本批实际选择、清除并刷新原版，再冻结 v51 后实施 Swift；采集器现在也记录最外层 pointer 候选及中心命中情况。pointer 只是探索线索，不能自动证明可点击或覆盖完整。该控件已实际点击，但语义角色仍未分类，没有虚构 button 角色。

Swift 补悬停清除并将状态选择放入持久化偏好。旧二进制真实运行在清除处失败，重启也丢失选择；新二进制实际完成选择、清除、重启检查。原版刷新与原生重启分别执行，不推断服务器存储等价。

继续换到排行榜练习入口，发现当前原版首题是“热／咖啡／欢迎／茶”，而默认 Swift 仍是历史实例。v52 将题目、11 个控件及初始未作答退出转成共同前端验收，保留真实失败；本批没有改练习题单。原版该状态直接返回主页，没有确认；不能外推到已作答的退出路径。完整当前实例、后续题目及声音继续进入 frontier。

| 实际运行 | 状态 | 通过 | 失败 | 未运行 | 不可验证 |
| --- | ---: | ---: | ---: | ---: | ---: |
| v51 旧二进制 | 3 | 11 | 10 | 2767 | 6 |
| v51 修复后状态／重启 | 5 | 35 | 10 | 2749 | 0 |
| v51 既有节点／传奇／排行榜回归 | 10 | 119 | 23 | 2652 | 0 |
| v52 当前练习入口／初始退出 | 2 | 38 | 12 | 2798 | 0 |
| v52 同一二进制两次独立会话合并 | 7 | 73 | 22 | 2753 | 0 |

最后一行来自两次实际隔离会话，不是一条连续七状态旅程。五个状态页整图全部失败，清除控件严格小数几何也失败；练习入口四个右侧词不同，练习及返回整图仍失败。未把这些差异降阈值或计作通过。构建成功，30 项 Swift 核心业务检查通过；不能替代前端验收。

v51 原样保留 v50 的2739项并增加55项；v52 再增加54项，共2848项。source-validation 只检验源证据自洽，不是产品通过。原版访客 URL 的数值标识在 JSON 中显式脱敏；原始文本不提交。完整后端／账户状态未克隆，当前只复用已观察的八课完成进度及可见状态。

本批历史反馈实际引导换入口并发现遗漏；没有独立工作者、匹配资源实验或 RSI 因果收益证明。原始论文继续由 docs/RESEARCH.md 管理。剩余状态图标、建档嵌套、整页像素、当前练习完整实例、原版声学输出及真实机制消融见 frontier.json。音频三配置负结果及原生阳性对照见相邻 english-source-audio-filter-v1。

## 复跑

在仓库根使用新的输出目录；运行前端验收后必须检查逐项结果，不只看驱动退出码。原生驱动使用 AX 操作，不能代替鼠标命中验证。

```sh
python3 projects/duolingo-web/freeze-leaderboard-state.py --out-dir artifacts/leaderboard-state-freeze-new
python3 projects/duolingo-web/freeze-leaderboard-practice.py --out-dir artifacts/leaderboard-practice-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/leaderboard-state-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/leaderboard-state-scenarios-v1.json
swift projects/duolingo-web/observe-frontend.swift artifacts/leaderboard-practice-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/leaderboard-practice-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v52.json --observed artifacts/leaderboard-practice-native-new/observed.json --out artifacts/leaderboard-practice-native-new/validation.json
```

[实际截图并排对照](comparison.html)。原始运行回执、二进制摘要、失败和覆盖分开保存在本目录，不累加历史构建充当当前整体通过率。
