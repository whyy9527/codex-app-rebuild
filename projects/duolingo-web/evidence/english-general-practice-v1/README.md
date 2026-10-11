# 独立练习的实际轨迹与前端模具补漏

2026-10-11，真实中文→英语匿名页面，从特别任务“去学个单元”进入 `/practice`。采集器显式支持该路由，取得公共 `GLOBAL_PRACTICE` 内容；仅保留白名单，不保存原始会话或用户标识。原版页面是需求来源。当前 Swift 的该入口仍是通用 Practice 占位页，本批没有改 Swift，也没有把这条练习换成主课程。

## 这次实际发现

最初响应列出16题，实际执行包含16道评分题、口语暂缓，以及一次故意错误后的同题更正，共17次评分提交。前五题实际通过；第六题听音填空的选项不显示单词，逐项播放把实际音频 URL 与选项对应，再提交，原版接受。听音配对同样通过实际左侧播放确定左右对应，不能照 API 的数组顺序假定屏幕顺序。

第七题 API 为 listenTap，原版因输入模式显示“键入你听到的内容”和文本框。驱动按完整词库检查而停止；保存键盘态，实际切换“使用词库”，保存切换回执，才继续按真实词库作答。输入偏好的长期保存规则尚未确认。这次故障是发现一个前端状态，不是把空词库放宽成通过。

随后出现口语“Tea, please.”，实际选择“现在不做口语题”，显示“麦克风已关闭／将在15分钟后恢复”。没有触发录音。继续后插入同句中文翻译题；提交“茶／谢谢”被接受。后续听写、缺词输入经过真实反馈验证。

挑战题过渡后，原计划最后三题依次变成“我想要咖啡加冰，谢谢。”“不要冰，不要水，谢谢。”“早上好，我想要咖啡加牛奶。”的英语输入题。原 API 的图片命名题没有实际出现，保持 unknown，不能宣称已探索它。最后一题故意提交 water，显示正确答案 `Good morning, I'd like coffee with milk.`；继续到复习过渡，同题“错题重练”，输入反馈给出的答案被接受。

实际结算截图显示“你莫不是特工？”、“完成了8项听力挑战”、5 XP、94%。AX 动画数字包含全部0–9，不能直接用 AX 字符串读成显示分数；`settlement-visual.json`明确为截图人工读数。结算有“回顾本单元／重新练习／继续”。继续出现“你又获取了一颗红心！”，再到建档提示，稍后返回 `/learn`。前一任务页快照红心3，返回主页红心4、宝石510、连胜2；奖励画面确实观察到，但自然恢复与通用奖励上限/触发条件没有做独立因果对照。不能把它实现为普通主课程扣生命和解锁下一课的流程。

## 冻结与真实缺口

`freeze-general-practice.py`读取实际已反馈回执生成40个状态、88项新增要求；v28保留v27全部1747项不变，总1835。新增覆盖实际题目及反馈整图、标题、配对8个矩形、键盘输入矩形、口语暂缓入口、复习、奖励和结算/建档控件。`trace.json`按实际顺序记录已接受/拒绝提交，独立标识插入题和替换题，不伪装成初始 API 列表。

源投影检查88/88通过，只证明原版证据与规格一致，其中图片检查为源帧自身校验，不证明候选完成。用上一轮实际 Swift 归档观察比较完整v28：34pass／6fail／1795not_run／0unavailable；88项新状态全部尚未访问。原来的练习标题失败仍在，不删除旧断言。本批没有新的 Swift 构建或原生运行。

回放工具新增听音配对、听音填空、听写和缺词输入支持；变题先比较 DOM type，再执行题型专用播放，避免按旧题型操作新页面。完整选项集合、当前播放URL和填空上下文共同检查；未支持题型与真实内容替换分开记录。驱动因未支持题型、键盘模式及实际替换停止的所有回执保留。这是本次实际续跑修正，不是自主探索或 RSI 收益证明，原论文及负面消融仍见仓库研究文档。

两个旧作答工具没有截图预检，complete-before.png 和 replacement-before.png 被其后对同状态的作答前截图覆盖；较早DOM到这些帧的时间对应关系 unavailable。原JSON保留，不追认其原始帧；第10题较早的回放截图另有 `after-inserted-question-10-before.png`。新增规格引用现存的真实作答前/反馈帧，不用它们声称动画时间一致。两个工具现在在任何浏览器动作前检查回执、intent和所有预定截图；实际文件碰撞反例测试确认既有帧内容不变且不会调用浏览器。原始碰撞的较早字节无法恢复。

4个Node回归检查通过（配对集合、同选项异句、听写媒体/填空上下文、截图碰撞），完整56个Python测试通过。原版正常口语、图片命名、结算重新练习/回顾、听力暂缓续题、精确进度权重、奖励规则、原音实际输出等继续进入 frontier。下一实施批次从本轨迹编译独立 Swift 练习及共同夹具，接真实任务页入口，逐状态比较；整个Goal仍active。

## 复跑

仓库根执行，输出须为新的目录/文件：

```sh
python3 projects/duolingo-web/freeze-general-practice.py --out-dir artifacts/general-practice-recompiled
node --test projects/duolingo-web/reference-challenge-identity.test.mjs
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/evidence/english-general-practice-v1/frontend-subset.json --observed projects/duolingo-web/evidence/english-general-practice-v1/reference.json --out artifacts/general-practice-source-check.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v28.json --observed projects/duolingo-web/evidence/english-quests-v1/native-final/observed-portable.json --out artifacts/general-practice-candidate-baseline.json
```

最后命令预期退出1；它是旧候选证据的重评估。重新采集原版会生成新的自适应实例，必须重新观察身份、模式和插入/替换，不能把这次顺序当选题规则。
