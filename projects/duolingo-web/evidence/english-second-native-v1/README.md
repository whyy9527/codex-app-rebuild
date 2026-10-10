# 英语第二课原生接入与差异回执

本批不是1:1完成交付。Goal继续active；RSI原论文及完整消融目标保持。

第二课采用原版实际接受的12道正常题和3道挑战翻译，15题；没有把初始API末尾未出现的match/listenTap/match冒充已执行。新增范例填空的固定前后句段、可撤回词块、源音频关联、挑战标记及三处实测鼓励文字。范例Tea with sugar.使用同句同角色的第7题公开剪辑，原版范例按钮实际音频URL尚未观察，不能宣称声音匹配。挑战题角色资源未知，候选保留空位，列为视觉差异。

默认夹具升级en-zh-v2，两课各15题，首节点总课数仍为原版4；后两课未编造。52项源资源（34语音、18SVG及PNG）哈希在resources.json，v1夹具与清单保持原字节。Swift构建及8项核心检查通过，核心检查包含填空撤回、实际挑战尾部、鼓励阻断/继续及首课解锁第二课。

## 实际原生与前端结果

- home-observed.json：明确种入首课完成/红心4，共同状态；开始弹层第2/4单元可用。home-result.json：27pass、206not_run。
- course-observed.json：新进度开始，首题误选sugar→完成首课→错题重练→回主页→真实第2课全对→三处鼓励→完成。walk_error=null；两课进度均保存。course-result.json：122pass、2fail、109not_run。两条失败是把完成首课后的主页文案契约用于零进度主页，原始失败保留。
- matched-observed.json逐状态登记来源：主页/弹层采用home观察，其余状态采用course观察；两者同构建，不把两个过程伪装成单次执行。matched-result.json冻结frontend-english-v3：128pass、0fail、105not_run，整体fail。不是减少或放宽断言。
- pixel-diagnostic.json：原版/候选第二课15题前后共30对，30对different。只按实测窗口内容矩形去标题栏、2x降采样，无额外遮罩或通过容差。原版部分截图在过渡期、角色有动画、原生文字抗锯齿不同，诊断不等于视觉通过。归档候选PNG加course-前缀，哈希对应实际文件。

看到的差异仍包括角色静态图/动画姿态、填空与词库间距、气泡箭头、下划线、检查栏与跳过按钮、源反馈文案、完整结算链及音频输出。新增组件不能替代这些结果的验收。

## 复跑

从仓库根使用全新输出目录，原生UI观察串行执行：

```bash
python3 projects/duolingo-web/compile-english-second.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/my-second-home projects/duolingo-web/fixture-reference-en-zh-v2.json --seed-progress projects/duolingo-web/evidence/english-home-v2/progress-after-first.json --reference-color-scheme light --observe-home-popover
swift projects/duolingo-web/observe-frontend.swift artifacts/my-second-course projects/duolingo-web/fixture-reference-en-zh-v2.json --reference-color-scheme light --walk-course --english-first-wrong
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v3.json --observed artifacts/my-second-course/observed.json --out artifacts/my-second-course/result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/my-second-course --second-lesson --out artifacts/my-second-course/pixels.json
```

全程fresh主页与after-first契约的两项状态差异会重现；单独主页回放提供匹配状态。按状态组合时必须保留两份源回执及来源映射。当前Guidebook观察仍是历史西语实现，不能作为英语Guidebook通过。

## 复盘与下一步

此前错误的根因是把接口静态题表和已有业务通过当作完整前端规格，没有持续验证实际页面变化。第二课给出可证伪反例：同一初始题表在第12题实际转入挑战翻译。类型核对可以拦截此例，仍拦不住同类型题面变化；探索应继续读取现场、核对题面/词库/提示/角色/音频，把分歧和未访问分支反馈到下一轮。不能用再加一个类型分支宣称RSI已完成。

源第二课完成页已继续到连胜页、建档提示和第三课入口，证据在../english-second-v1。后续继续第三课和其它导航/恢复分支，同时修复上述实际前端差异；消融使用冻结起点和资源，比较真实遗漏发现及复刻质量，当前尚无新探索机制收益结论。不新增审批或产品范围限制。
