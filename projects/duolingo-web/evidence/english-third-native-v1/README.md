# 英语第三课原生接入与仍存差异

当前默认en-zh-v3为三课各15题，第三课采用实际12正常+3现场挑战，未复制初始API的旧尾部。首节点总课数仍为4，后续节点继续探索。源观察、前端契约v4和原论文保持；本批不代表1:1或RSI收益。

## 编译与业务

词库编译以多重集核对API与真实UI顺序，每块词都有独立ID；两个“不要”不再被字典合并。选择/撤回按ID，判题按实际词序和数量，交换两块相同文本不改变句子；少选一块会判错。源完整替代答案判题器、源重复词块撤回/交换身份轨迹未单独执行，不能宣称这些已与原版完全等价。

第三课3处鼓励文字、实际挑战题面/词库接入。66项公共源资源（45语音、21SVG/PNG）记录哈希；v1/v2夹具和资源清单字节保持，v3重编译确定。9项Swift核心检查通过，包含重复词块独立性、撤回、数量、词序、解锁及存储边界。

首次全程原生回放还暴露一项进度错误：完成全部已编译课会把整个course记完成。原版已知首节点4课且后面还有未编译节点，因此修正为只有没有未编译路径时才记course完成；旧错误credit会在完成记账时清除，单课成绩保留。initial-progress.json保留反例，resume-progress.json和final-progress.json证明3课完成、红心4、completedCourses为空。不是把三课变成范围上限。

## 实际原生与前端

final-observed.json来自修正后同一构建的单次完整回放：首课误选sugar→重练→第二课全对→第三课全对，walk_error=null。第9题实际AX读到第一块选中后禁用、第二块仍可用，撤回第一块不影响第二块，全部撤回后检查不可用。六个独立读数均true，截图及verification.json保存。它们是候选实测，源撤回仍未单独验证。

观察器在首课完成回主页时保存匹配的home状态，进入第二课前保存对应弹层；初始零进度主页保留为home-initial。当前结果无需组合不同运行或构建：frontend-english-v4共372项，221pass、151not_run，整体fail。initial-result.json保留先前以fresh主页比较after-first参考的两条失败；未放宽断言，后续按实际阶段采样。

final-pixels.json有第三课15题前后30对，30对different。截图按实测内容矩形去标题栏/2x降采样，无容差或遮罩。初次比较未处理采集器相对路径，尚未比较就失败；diagnostic-first-failure.json保留，修正为归档原图路径后才生成结果。只有final-*候选截图对应最终像素回执。

已知视觉差异包含完整角色/动画、气泡、下划线、词块和内容间距、底栏/跳过、反馈及结算。接口给第9题的是title为Junior - Cropped的SVG，实际原版显示完整角色，不能把接口素材关联当作页面素材相同。public-graphics-inspection.json记录当前自有原版加载的公开Lottie路径，lottie-metadata.json保存元数据/哈希；是否对应题目角色仍需映射，不凭资源出现就替换角色。语音文件传输、核心通过和像素差异统计均不是声学/视觉验收。

## 复跑

从仓库根，原生UI操作串行，输出目录必须全新：

```bash
python3 projects/duolingo-web/compile-english-third.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/my-third-full projects/duolingo-web/fixture-reference-en-zh-v3.json --reference-color-scheme light --walk-course --english-first-wrong --exercise-duplicate-words
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v4.json --observed artifacts/my-third-full/observed.json --out artifacts/my-third-full/result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/my-third-full --third-lesson --out artifacts/my-third-full/pixels.json
```

`--start-lesson-index 2 --seed-progress projects/duolingo-web/evidence/english-second-native-v1/course-progress.json`可原位验证第三课与旧credit修复，不能拿此局部回放代替三课完整回放。原版仍在第三课完成页，继续结算/第四课、角色动画与其它未访问分支；候选完整结算链、声音输出和真实匹配资源消融继续补齐。Goal active。


进一步核对发现，原采集白名单还丢弃了character.url、idle/correct/incorrectAnimation和name等字段，graphics-source-gap.json保留具体字段和原证据摘要。当前已按character上下文开放这些字段及课题example/exampleTokens，语法检查通过；下一真实sessions尚未采集这些值，不能宣称完整角色映射完成。已找到的三份Lottie内部名字均指向Duo，因此不把它们误配为Junior。


### 当前审阅对照

`python3 projects/duolingo-web/render-third-comparison.py --out artifacts/my-third-preview/index.html`从归档原图生成主页、首题、重复词块题、现场挑战四组对照。使用本地静态服务器查看；CSS只按实测窗口标题栏高度裁切，未改变原图。该入口替代旧v3演示页作当前审阅，不能把目测当作前端通过。
