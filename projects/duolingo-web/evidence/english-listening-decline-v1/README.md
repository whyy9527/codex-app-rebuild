# 执行遗漏的听力暂缓分支

2026-10-11。原版第六课真实续探、独立 Swift 路径实现与默认五课回归；完整1:1与RSI消融仍未完成。

## 新发现

从上一批 Hello./Lucy 未答状态续接，“你好”实际接受，“好棒！”且连对2题；随后出现听音配对。待探索清单已有“现在不做听力题”，本次真正执行：

1. 配对未作答，点击“现在不做听力题”。8个配对按钮禁用，显示黄色“听力题已跳过 / 将在 15 分钟后恢复”，继续可用，红心仍为2。
2. 继续后先插入“coffee with milk”的拼句题，词库为牛奶/我/咖啡/加。“咖啡 加 牛奶”实际接受，“你太棒了！”，连对3题。
3. 再继续才进入原API第3题“咖啡加牛奶 / coffee with ___”。输入milk实际接受，“好棒！”，连对4题。
4. 再继续出现sugar→中文拼句，词库咖啡/糖；不是原API第4条listenMatch。当前停在这道题，尚未作答。

API会话列表不能当作最终页面题序。暂缓没有被当成答对或扣心，但它会改变后续内容。15分钟仅是实际文案；恢复时刻、跨课/重启持续性与完整后续替换规则未观察。

`english-sixth-lin-renderer.*`是按“下一条API应为LIN”初始预期命名的探针。**实际导出的buffer是Bea**，与上一批独立验证的Bea哈希完全一致；`character-binding.json`记录这一反例。没有把LIN映射到Bea或修改旧素材身份。原始文件名保留供追溯。

`exploration-history.json`保存7状态、6条真实转移；通用discovery消费者重新导出20个待访问动作。历史反馈使本次从正常答案循环转向未访问分支，发现插入题与后续替换；这是代理依据证据调整探索，不是自主RSI策略生成或效果消融。原论文及负面实验仍在[研究来源](../../../../docs/RESEARCH.md)。

## 实现与验收

`Question.listeningDecline`保存已观察的动作/提示，Lesson支持未评分暂缓、锁定配对输入并保持红心/错误/重练队列；继续进入夹具冻结的实际插入题，再进入原填空题。没有猜测通用替换算法或编造计时器。当前只有**独立已观察路径夹具**配置该分支；默认五课尚未获得各自暂缓后的完整源轨迹，不能说默认产品已经支持完整听力暂缓。

原生run01失败：核心已支持，但LearningModel.advance仍只允许普通反馈/题间/口语状态，“继续”后停在暂缓页。保留`native-run01-*`。修正集成门槛后，final实际采到14个状态，walk_error=null，明确`stopped_at_question=en-zh-decline-fill`；停在填空接受反馈，未点击完成，不记完整课时完成。

初始19项只覆盖主要路径，原版与原生均13pass/6not_run。复查源反馈页发现“太简单 / 太难 / 报错”也应有可执行存在断言，加入后当前22项为：**原版16pass/0fail/6not_run，Swift13pass/3fail/6not_run，整体fail**。三项缺失动作没有用普通文本或无效按钮冒充完成。旧19项契约单独保留，不修改历史结果的口径。

源首次提取还出现三个采集错误：把配对序号误读成红心、AX省略两段可见提示。现在只读标题前的player header，并使用当时独立采集的visible DOM/hint事实。`source-run01-result.json`保留失败；`source-run01-observed.json`是从冻结原始事实重新执行旧提取所得，已验证与原失败观察digest完全相同，不是新增现场采样。

6对实际PNG全部different。原生按实际content rect裁标题栏并从2x降采样；原版不改像素、不遮罩。**原版此前已答两题，局部原生探针从配对开始，整课进度背景不同**，因此这是同题面/反馈的差异诊断，不能称完整同状态像素验收。API配对音频左侧顺序在本探针未实际播放绑定；插入题实际语音、动画时序、计时恢复和次要动作行为仍未验证。

16项核心通过。当前源码默认五课连续回归214状态、walk_error=null、stopped_at_question=null，2红心、五课完成记录、completedCourses为空；共享v10仍为 **434pass/11fail/307not_run，整体fail**。局部路径与五课结果不相加。

## 复跑

仓库根，使用不存在的输出目录：

```sh
python3 projects/duolingo-web/compile-listening-decline.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-listening-decline.json --observed projects/duolingo-web/evidence/english-listening-decline-v1/source-observed.json --out artifacts/decline-source-recheck.json
artifacts/observe-frontend artifacts/decline-recheck projects/duolingo-web/fixture-listening-decline.json --walk-course --exercise-listening-decline --stop-after-question-id en-zh-decline-fill --seed-progress projects/duolingo-web/evidence/english-listening-decline-v1/initial-progress.json --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-listening-decline.json --observed artifacts/decline-recheck/observed.json --out artifacts/decline-recheck/result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/decline-recheck --pairs projects/duolingo-web/evidence/english-listening-decline-v1/pixel-pairs.json --out artifacts/decline-recheck/pixels.json
artifacts/observe-frontend artifacts/decline-five-recheck projects/duolingo-web/fixture-reference-en-zh-v6.json --walk-course --english-first-wrong --english-fifth-mixed-errors --exercise-duplicate-words --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v10.json --observed artifacts/decline-five-recheck/observed.json --out artifacts/decline-five-recheck/result.json
```

前端命令预期非零；原生stop参数显式记录局部结束，不伪装整课完成。像素分析需Pillow。`capture-visible-state.mjs`采集当时可见DOM/AX、几何、样式和PNG，不导航、不导出隐藏会话；与CLI真实动作分开执行。一次旧ref失效后重新snapshot恢复，未重复提交答案。

## 接续

源仍在第六课sugar题，未答。继续该真实暂缓分支、采齐后续替换与结算，并探索次要反馈动作、录音与恢复；据完整证据将路径接入默认课程。继续补全主页、角色/结算渲染器及实际声学/前端要求，再固定预算比较探索机制。Goal保持active；本局部夹具没有缩小完整复刻目标。
