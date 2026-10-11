# 当前显示题目、动态插入与 Eddy 原版动画

2026-10-11，中文母语→英语访客 `/practice`。本批由已有缺失角色和暂缓替换失败继续探索，不是自主 RSI 效果实验。完整目标继续；原始论文及负面实验仍见 [RESEARCH](../../../../docs/RESEARCH.md)。

## 实际发现与驱动修正

从原版任务页“去学个单元”进入练习，刷新得到新的16题实例。前五题真实接受，驱动在第六题 `listenTap` 停止。原版听力暂缓显示“听力题已跳过／将在15分钟后恢复”，继续后插入 `Good morning!` 翻译，词库是“而且／早上好”；初始列表这一位置却仍是听力题，不能通过初始索引恢复当前内容。

新增 `capture-current-challenge.mjs`，从当前唯一可见 challenge 的 React renderer 读取公共题目字段。它与原有 session 采集器共用 `public-reference-challenge.mjs` 白名单；不读取 challengeState 或未来序列，DOM 题型不匹配时保留现场。`replay-reference-session.mjs --current-only` 用这一当前题实际回放单步，然后执行原版继续。原先按初始 session 回放的模式保留；本模式不改写它，也不声称实现了自适应出题。

实际单步答题获得“好棒！”反馈，继续到 `speak`：“Good morning, I'd like more tea, please.”。未支持正常口语的回放保存 `Uncovered type: speak`、answered=0；显式 `--stop-before-type speak` 则保存 requested boundary、answered=0。二者都没有提交、暂缓或录音，原版停在该题；最终代码再次实际停在同一口语边界，回执在 `source-final-boundary/`。逐份结果见 [回放摘要](replay-summary.json)，完整原始公共字段、前后PNG、实际反馈在 `source/`。

公共题目可能包含参考答案，适合复刻规格和验证回放，**不是盲探索评分**。本批只验证实际插入题及单步续接；新实例其余分支、15分钟后恢复和通用自适应选题仍未覆盖。新插入题也还没有独立 Swift 实例及共同前端契约，不能用当前题回放成功算候选完成。

## 原版资源与实际应用输出

当前翻译题的 Eddy renderer 绑定与公开 Rive 下载逐字节一致：236733 bytes，SHA256 `eb9eac9f5724ef9af410eeb552549c695f1f35c630803945ffee1886055abffa`。`import-current-character.py` 验证实际缓冲摘要后，导入 `en-character-eddy.riv`，按原版 artboard、state machine、正确/错误/reset trigger、缩放及位移参数绑定既有 image key。这个 key 已被主课和默认独立练习使用；没有用替代绘图冒充原角色。

源12个buffer帧有6个不同帧。原生默认独立练习实际完成47状态、错误复习、奖励与真实终止重启，驱动无失败；q5待机和正确反馈分别捕获12个自有窗口帧，角色区域各有12种像素内容。见 [实际运动诊断](motion-diagnostic.json)。这证明候选实际输出在动；源捕获是另一道翻译题，不能证明与原版 isolation 的姿态、时序或触发完全一致。q12 虽引用同一资源，其布局仍没有渲染角色。

## 负面前端结果保留

共同 v31 原生回执重定位到字节一致 PNG 后重新执行，仍为 **89 pass／55 fail／1759 not_run／0 unavailable**，没有放宽旧断言。q5整图 RGB 平均绝对差从约 `[3.036, 2.123, 3.142]` 增到 `[3.051, 2.300, 3.325]`；反馈也略增。见 [逐项结果](native-01/frontend-v31-validation.json) 和 [前后诊断](image-delta.json)。动画时刻未对齐，不能声称资源接入改善了整体还原。

旧源 q5 canvas 是 `[301.0861,184.75,129.8,192.5]`，当前候选角色 AX 是 `[285.1,180.75,129.8,192.5]`；radio 的 y 仅差0.5点。PNG还显示缺气泡尖角、文字虚线、分隔线及该题暂缓入口。需要按各自源证据修布局，不能移动整个内容区或篡改原版 Rive 内部参数掩盖包装层问题。新资源绑定不等于这些前端需求已完成。

9 Node／56 Python／Swift构建／25核心检查通过，日志随批保留。归档重验第一次误给 CLI 传了不存在的 `--reference` 参数，在执行验证前退出；去掉该参数后得到以上失败结果，是调用错误而非产品回归。`copy-manifest.json`记录137份PNG/Rive及其他逐字节复制件；观测JSON只重定位capture路径，浏览器raw日志不入库。

## 复跑与继续探索

从仓库根执行，`PLAYWRIGHT_CLI` 指向已安装 Playwright skill 的 wrapper；`OWNED_SESSION` 必须是实际原版当前题会话。示例是单步作答，会改变原版题目；采集命令只读。输出使用新目录。

```sh
node --test projects/duolingo-web/public-reference-challenge.test.mjs projects/duolingo-web/reference-challenge-identity.test.mjs
node projects/duolingo-web/capture-current-challenge.mjs --cli "$PLAYWRIGHT_CLI" --session "$OWNED_SESSION" --out artifacts/current-next/visible
node projects/duolingo-web/replay-reference-session.mjs --cli "$PLAYWRIGHT_CLI" --session "$OWNED_SESSION" --ui-language zh --current-only --stop-before-type speak --out artifacts/current-next/replay.json --screenshot-prefix current-next/replay
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/current-native-next projects/duolingo-web/fixture-reference-en-zh-v11.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-quests --exercise-general-practice --capture-character-frames --character-frame-resource en-image-2185ab058ad2813ae3aa
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v31.json --observed projects/duolingo-web/evidence/english-current-challenge-v1/native-01/observed.json --out artifacts/current-next/validation.json
```

继续队列：从实际口语边界探索评分和暂缓后的题目；把当前插入实例编译进共享前端/业务模具；补 q5/q12 的实际角色、气泡及交互缺口；验证声学/动画时序；继续未访导航与真实探索机制效果。没有新增原创素材或页面子集限制。
