# 第七课：正常听力、输入偏好、跳过重练及真实结算

2026-10-11。源已完成第七课并返回主页：第二节点Lesson4of4、生命3、宝石510。初始公开session与前半程在english-secondary-actions-v1；本批从第4题整句正确反馈续接，没有reload重新生成或将初始API顺序当完整轨迹。完整Goal继续active。

## 本次实际发现

- 第5题正常四组听音配对全部接受，保留每次实际播放URL到公开pair的映射。
- 第6题“不要咖啡，谢谢。”直接以键盘打开、输入空，No coffee, thank you.接受。第7题“加冰吗？”直接是整句模式、显示减少难度，With ice?接受。结合旧q1切键盘而q4最初仍填空，确认两种偏好独立跨题保留；q8/q14再次显示对应模式。此前每题重置模式的实现错误。
- 第7/8题之间实际生命2→3，触发原因未知；没有把它实现为正确题奖励，也不把固定生命2当完整同状态基线。
- 第9题No填空接受；第10题暂缓口语后显示麦克风关闭/15分钟恢复，随后插入Thank you.中译；之后才出现原API的coffee and tea。第12题goodbye填空接受，原第13口语变成Goodbye.中译，第14题整句接受。普通口语识别和计时恢复未验证。
- 初始q0跳过不扣心；末尾实际进入复习介绍，同一道tea and coffee重现为错题重练。纠正后结算“完美！/你练习全对，无错完成本单元”、15经验/100%。这是本轨迹事实，不据此推导所有跳过时的连对、评分或重练公式。
- 结算接“先贤成就等级已提升！”第2级/你赚取了100经验，再接建档提示；点稍后再说返回主页。没有创建账号或将成就100经验误算成本课经验。

所有答案反馈先保存再继续；最终一次继续的回执先显示旧题/禁用继续，后续只观察到真实结算，没有重复点击。settlement-visual明确从实际PNG人工读取动画数字；不把AX父节点所有0–9当显示分数。

## Lin身份核实及接入

这次当前题面coffee and tea与原API q11一致，API角色LIN，实际PNG确认为橙色外套角色；capture-source-canvas导出12个不同帧、实际scale1.15/位移及300966字节Rive。公开CDN解压字节和actual buffer均为c47e42bcec34efea33de36432d6c53aeb0a4d87a0367cf177afe8dfa7ada7d54，绑定源身份en-image-cf56f9ea0c179f90206b。实际bundle同哈希。

旧误名lin文件实际Bea的失败不改写。新绑定依据当前提示、API角色、实际PNG、renderer及字节核验；不是重新相信文件名。插入Thank you的角色另有实际renderer证据，未擅自套到Lin。相位、口型、音频和原生整页仍未证明一致。

## 偏好实现与实际验证

Lesson分别保存词库键盘和填空整句的偏好，切题清空两种答案缓冲，按新题实际支持的模式恢复对应偏好；不支持切换的题不清除偏好。范围是已观察的同一课内，跨课/重启尚未知。compile-input-preference-probe从源q6/q7及接受回执生成v3四题探针，保留旧v1/v2和58项前端规格。

原生观察器先读取新题提示、真实AXTextArea及检查状态；已自动恢复整句的题直接输入，不盲点切换。实际preferences-native01走28状态、walk_error=null，确认q4初始fill、q6/q7初始full且缓冲空，四题全部接受。19项核心检查、Swift构建和47项框架/控制回归通过；框架通过不代替产品验收。源58项54pass/4not_run；原生45pass/9fail/4not_run，整体fail。新增9项偏好/接受要求通过，旧8项切换分数几何及1项Falstaff几何仍失败，没有改容差。

四题探针压缩了原版中间匹配/口语/插入题，生命/总题数/连对也不同。不能用它证明第七课已原生重建或整页同状态视觉通过；默认课程尚未填齐输入模式元数据，跨课偏好及普通口语仍待探索。

## 整课模具与剩余工作

freeze-seventh-frontend按真实UI回执冻结39源状态/419项，包含跳过、正常听力、口语暂缓、替换题、重练、额外成就、建档、主页；初始API只作为内容补充。第七课原版收集事实回放为341pass/78not_run，78项像素/实际声音仍未验证。这是已采集事实回放，不是另一次原版活体整课复跑。

产品v13保留旧v12全部1061项，再加419项，共1480；不把组件45项累计成产品通过。完整原生第七课尚未编译：listenIsolation选项被旧sanitizer遗漏，跳过与新结算/插入未接入。新要求的未覆盖会直接保留，不通过删题或替代声音处理。exploration-frontier列实际反例、状态、未知和下一步。

完整六课从空进度实际273状态、walk_error=null、生命2、六课完成而completedCourses为空；v13为662pass/42fail/776not_run，其中新419项全部未覆盖，旧失败仍42项。回执在six-course-regression，未累计组件结果。Dream-RSI/Cordis论文及负面结果仍在docs/RESEARCH.md；本批实际探索揭露了新遗漏，没有执行新的匹配预算RSI消融，也不宣称无人监督探索或一般收益。

## 复跑

仓库根，已有macOS辅助功能权限，新输出目录；前端因失败/未覆盖非零。

```sh
python3 projects/duolingo-web/compile-input-preference-probe.py
python3 projects/duolingo-web/freeze-seventh-frontend.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-input-preferences
artifacts/observe-input-preferences artifacts/input-preferences-review projects/duolingo-web/fixture-reference-en-zh-secondary-v3.json --walk-course --exercise-input-modes --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-secondary-v3.json --observed artifacts/input-preferences-review/observed.json --out artifacts/input-preferences-review/frontend-result.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-seventh-v1.json --observed projects/duolingo-web/evidence/english-seventh-v1/source-full-observed.json --out artifacts/seventh-source-review.json
```
