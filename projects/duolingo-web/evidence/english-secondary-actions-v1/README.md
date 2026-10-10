# 第七课次要动作：源探索、输入模式与保留的前端失败

2026-10-11，中文→英语，真实访客原版，第六课后第二节点第3/4单元。当前原版停在第七课重新生成实例的第4题：整句翻译已接受，尚未点继续。完整Goal仍active。本批是两题动作探针，不替代默认五课或显式六课验收。

## 反例改变探索方法

此前主要沿正确答案推进，虽然API有题表，跳过、键盘、难度切换和正常听力分支仍未进入模具。本次选择这些未执行动作，得到原实现无法通过的独立需求。

- 起始听音配对的现场在secondary-q0-before；capture-reference-session重新加载后，首题变为tea and coffee。secondary-reset-q0是新实例；不能将reload当成原题重置，也不能声称执行了旧初始配对。
- 第0题点跳过，显示“正确答案：茶和咖啡”，生命保持2。是否入重练、怎样结算尚未观察；没有以普通答错扣心实现。
- 第1题“谢谢。”切键盘→输入Thank you.→切词库，词库仍空且检查禁用；再切键盘，原输入保留且检查可用，提交获“太棒了！”。
- 第2题四组正常听音配对实际完成。新answer-listening-pairs-live工具读取每次实际播放URL，再匹配公开API的translation；不按API数组顺序猜左按钮。四组接受、生命2；播放资源绑定不代表声学等价。
- 第3题实际为listenIsolation，选择音频2获“好棒！/意思是：不要冰，谢谢。”。sanitizer遗漏options/blankRange字段，保留缺口；没有重新加载补数据后冒充同一题。
- 第4题填空“I'd like water __ coffee, please.”；加大难度变整句翻译。输入I'd like water and coffee, please.，切回填空仍空，切回整句保留输入，提交获“非常好！”。
- 连对1时未显示，2/3/4时实际显示。原生>=5的阈值是新增已知差异，尚未修复。
- 源DOM采样enabled=true与同次AX检查disabled冲突。本契约用实际AX快照确认禁用状态，保留原DOM值；不是两份都算通过。

原始公开session、逐步AX/DOM、截图和答案回执保留。source-observed是依据这些快照整理的事实，不是重新执行整课的源驱动。尚未执行动作及反例→方法调整见exploration-frontier.json；这不证明自主RSI或匹配预算收益。

## 冻结与实现

实现前冻结frontend-english-secondary-v1的48项：输入/检查状态、切换文案、实际接受、控件几何及4项像素/声音待验证。源44pass/4not_run。两题fixture来自实际第1/4题，顺序压缩，原版先前成绩/生命与探针不同，不能作整课进度或整页像素等价证据。原版的跳过、listenIsolation与后续题目没有被探针排除出完整目标。

Question增加可选keyboardAnswer/keyboardPrompt；Lesson分别保存词库/填空与整句输入，切换只切模式，反馈锁定输入，切题重置。两条源接受的整句进入探针；默认课程尚未配置，不把局部实现说成默认所有题可切换。大小写、标点、同义答案和跨题模式偏好仍未完整验证。

原生观察器使用实际AX和键盘操作，保存empty/filled/returned/reopened/feedback；不由核心测试代替真实窗口。18项核心通过，Swift构建通过；native-run01实际24状态、walk_error=null；观察器随后避免将缺失输入控件当作空值，native-run02同样24状态、walk_error=null、结果不变，两轮均保留。48项共享契约：30pass/14fail/4not_run。14项全为输入区与切换按钮几何差异；没有调大容差或改源坐标。角色/气泡、输入编辑区域、页脚布局、实际像素与声音仍待修复。

## 复跑

仓库根，已有macOS辅助功能权限；用新输出目录。比较因fail/not_run返回非零。

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-secondary-frontend
artifacts/observe-secondary-frontend artifacts/secondary-review projects/duolingo-web/fixture-reference-en-zh-secondary-v1.json --walk-course --exercise-input-modes --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-secondary-v1.json --observed artifacts/secondary-review/observed.json --out artifacts/secondary-review/frontend-result.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-secondary-v1.json --observed projects/duolingo-web/evidence/english-secondary-actions-v1/source-observed.json --out artifacts/secondary-source-result.json
```

完整六课从空进度回归实际273状态、walk_error=null，生命2、六课完成、completedCourses为空；v12仍662pass/42fail/357not_run，失败数未变，回执在six-course-regression。不会把新探针30项通过累计到旧产品1061项。Dream-RSI/Cordis原论文和历史消融仍由docs/RESEARCH.md索引，真实探索策略的同起点同预算消融未完成。
