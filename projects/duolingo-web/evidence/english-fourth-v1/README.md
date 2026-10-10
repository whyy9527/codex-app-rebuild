# 英语第四课：挑战入口、听力身份和结算链

实际观察跨越2026-10-10/11，来源为自有匿名 en/zh 原版标签。第四课是首节点的第4/4课，启动奖励显示+20经验；不能用前三课的普通开始/结算流程代替。本目录只记录这一条真实轨迹，完整产品和分支覆盖仍未知。

## 新需求与原始反例

第三课完成→建档稍后→主页后，实际出现通知提醒遮罩，选择“下次再说”关闭。主页已有青铜等级、查看排行榜、宝石505。候选完成三课却显示锁定排行榜、宝石515；同状态需求比较明确报4项fail。原版并非每课增加5宝石，不能继续使用自定公式。

第四课开始先显示“来复习一下这个等级，完成后有惊喜哦！”（下次再说/开始挑战+20经验），再显示复习说明，然后进入“错题重练”首题。前一次入口点击失败后误启动了采集，使主页重载；后两次等待challenge超时分别停在挑战入口和说明页。不是原版不可用。保存现场后再继续，不重启浏览器或强制绕过遮罩。`failures.json`保存已验证错误类别，原始本机日志留在忽略目录。

捕获工具新增未完成课程前置检查、响应等待超时和finally监听器清理；当前主页误用前置检查已实际拒绝。成功捕获12题公开字段，`session.json.initial`只是加载中，随后真正入口由`reloaded-entry.json`记录。没有将加载页伪称题目。新幂等媒体初始化避免以后重复包裹play；本批旧初始化已经重复，所以原始media内重复调用保留，不当成多次用户播放或声音质量证据。

`replay-02.json`实际接受0–4题，在第5题listenTap停止，动作为空。原因是原检查错误要求听力转录文字可见。`audio-identity.json`保留实际点击当前正常播放按钮后的源音频调用，确认为API该题tts；改为当前显式播放地址匹配后，`replay-03.json`实际接受5–11题。文字题的可见题面/完整词库核对继续保留，缺音频/错音频仍拒绝。播放URL一致不是录音或声学等价。

第四课没有观测到前三课的三个追加翻译题，不能给它强加15题模板。题5起出现挑战题及“来试试这个等级里最有挑战性的练习吧！”题间页。12题最终都得到原版正向反馈，完成后实际链为：挑战完成→英语分数进度→连胜页→15分钟双倍经验奖励→传奇挑战邀请→稍后建档→主页。传奇+80经验入口、回顾本单元等分支尚未访问。完成后第二路径节点为Lesson1of4，仍未进入，不推断其题库。

主页采样跨午夜，连胜由1变2，排行榜倒计时18→17小时；这是本次现场值，不把日期/时钟变化写成每课固定规则。结算滚动数字的AX包含全部0–9，已直接读保存的原版PNG确认总经验20、正确率100%，独立保存在completion-visual-reading.json，未从AX列表编造数值。

公开character字段首次保留了Junior/Lucy/Eddy的url/name及idle/correct/incorrectAnimation。它们明确关联本会话角色，解决了之前字段裁剪造成的素材来源缺失；仍需绑定实际DOM/动画状态、确认完整角色素材和Swift表现。不能将上一课任意Duo Lottie映射成Junior。

## 冻结与复跑

`freeze-english-fourth.py`从本目录实际回执生成147项增量前端需求，累计v5为519项；当前三课候选221pass、4fail、294not_run，整体fail。`candidate-before.json`只消费上轮同一构建的真实原生观察，没有伪造第四课候选执行。原版截图24张题目/反馈及新增入口/结算保留；Swift本批尚未接入第四课。

`history.json`记录34状态、38转移；frontier有37个动作取得观察结果、24待探索。失败尝试保留，不是策略自改进或RSI收益。原始研究及负结果继续见[研究来源](../../../../docs/RESEARCH.md)；后续要用相同起点/预算的真实探索机制消融验证收益，不能拿本次驱动修复当消融。

```bash
node projects/duolingo-web/check-reference-identity.mjs
python3 projects/duolingo-web/freeze-english-fourth.py
python3 -m capabilities.rebuild.discovery --workspace . --history projects/duolingo-web/evidence/english-fourth-v1/history.json --out artifacts/fourth-frontier.json
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v5.json --observed projects/duolingo-web/evidence/english-third-native-v1/final-observed.json --out artifacts/fourth-before.json
```

最后一项预期fail，不能为绿色状态降低断言。原版当前已到第四课后主页；接续先读现场。下一批按已冻结第四课和结算链实现，修复青铜/宝石差异，绑定原版角色与动画，补同状态视觉/实际声音验收，并继续访问第二节点及其它前沿。完整Goal保持active。
