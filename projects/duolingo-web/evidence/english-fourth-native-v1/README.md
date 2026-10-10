# 英语第四课原生接入：实际四课运行，产品仍失败

2026-10-11，默认夹具升级为en/zh v4，共15+15+15+12=57题，保留历史v1/v2/v3。第四课内容、选择/词库顺序、12个正向反馈及对话问句来自真实原版，未复制前三课15题模式。对话Coffee or tea?同时在源DOM与PNG确认；角色/源语音按题关联。

## 实现与验证

第四课增加独立挑战入口、开始/稍后动作、初始复习说明与第5题前难题说明。初始说明属于LearningCore状态，会阻止隐藏题目接收输入；首次继续不会跳过题0，之后才自动播放当前题语音。旧夹具/存储兼容仍由核心检查覆盖。新入口尚缺原版动画，现有鼓励图也未对齐。

英语主页使用实际完成1/2/3/4课后的宝石/青铜卡片快照，替换自定每课加5宝石公式。三课后已显示505、青铜等级、查看排行榜及实际源图。快照只用于该冻结现场，不代表后端奖励规则或实时倒计时；跨午夜连胜变化仍未实现。第二路径节点尚未编译，完成第四课后仍有错误的路径呈现，不把四课算整个课程完成。

Swift构建及10项核心检查通过。实际原生从空进度走完全部四课，首课误答/重练、第三课重复词块选择/撤回也执行；walk_error为null，保存四课完成，completedCourses为空。initial-observed/window/progress与initial-*.png来自同一次最终构建运行。完成页state别名只规范该次实际lesson-4-complete的命名，没有伪造额外访问；驱动今后直接输出同一规范名。

共享前端v5的519项：303pass、8fail、208not_run，整体fail。前三课后主页4个明确失败已消除；当前8个失败为第四课完成页7个文案/数字及完成后下一节点1项。分数、连胜、双倍经验、传奇邀请等完整链仍未访问候选。第四课24对同内容视口截图全部different，保留未加遮罩/容差的RGB诊断，不能因文字通过称1:1。

92个公共资源（70语音、22图形）的源及PNG哈希已核对。修复全局mp3忽略导致干净克隆无英语语音的交付缺口，将精确公开en-speech文件纳入默认应用资源；未放开私人音频忽略。播放器资源可得、AX走课和哈希检查不代表实际系统输出/听感与原版一致。没有开展新的RSI机制消融，不据本轮通过数宣称策略收益。

新观察发现先前第四课后主页PNG只拍到路径加载中，后续又出现通知层。原始截图保留，实际选择“下次再说”后才补拍home-uncovered；不能把前两张当无弹层静态主页验收。源证据目录保留三次现场差异。

## 复跑

从仓库根：

```sh
python3 projects/duolingo-web/compile-english-fourth.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
mkdir -p artifacts
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
artifacts/observe-frontend artifacts/my-english-fourth projects/duolingo-web/fixture-reference-en-zh-v4.json --walk-course --english-first-wrong --exercise-duplicate-words --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v5.json --observed artifacts/my-english-fourth/observed.json --out artifacts/my-english-fourth-result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/my-english-fourth --fourth-lesson --out artifacts/my-english-fourth-pixels.json
```

输出目录需尚不存在。前端入口预期失败，不能降低断言；声音文件已包含，重取/核查来源仍可用fetch-english-resources.py和v4资源清单。下一批直接修第四课结算链和完成路径，并补源角色动画/同状态几何与实际声音输出，再继续第二节点探索和真实策略消融。Goal保持active。
