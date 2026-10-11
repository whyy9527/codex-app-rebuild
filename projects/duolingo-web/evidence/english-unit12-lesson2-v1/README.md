# 单元12第二课：完整题轨迹与主页交互补漏

由前批历史中“下一课重复上一课／发音遮罩／电台未实现”的遗漏继续实际探索。原版中文→英语访客状态保持；没有重置原版进度。实际完成第二课12道判分题、1次口语暂缓、2个鼓励页、13张回顾卡，15XP／100%；档案提示后回到Lesson3of6，刷新仍保留进度。原版第三课弹层已观察，第三课内容尚未执行。刷新后的学习提醒真实拦截节点点击，先记录失败，再用原版“下次再说”关闭；不能强制穿透遮罩冒充成功。

Swift接入独立第二课及60资源清单、带预填词的拼句题、完整回顾句子、独立原版Junior+Duo结算画帧。主页按已完成实例更新2/6→3/6，保留4生命。加入“公寓参观”锁定弹层及发音引导遮罩。真实鼠标点击高亮进入发音页时保留遮罩，外部点击关闭，保存后重启不再出现。准备文件显式设置pending，仅为可执行交互前置；原版延迟出现时机未复现，不能说生命周期1:1。

## 前端验收

[v71](../../frontend-english-v71.json)完整保留v70的15255项，追加30源状态，共16500项。逐题答前／反馈保留控件角色、enabled、几何、CSS、文字范围、裁剪祖先和命中事实；共同契约检查整图、控件几何／角色／enabled，CSS及点击命中不能由AX库存推断等价。新发现的刷新提醒和第三课弹层继续进入历史与frontier，尚待新增共同验收项。

最终实际40状态、0驱动失败；[UI结果验证](native-final/validation.json)9项通过。[严格前端结果](native-final/frontend-v71-portable.json)：543pass、282fail、14752not_run、923unavailable；本轮对应35张整图全部fail。第二课新增项426pass／268fail／30not_run／521unavailable。未知、未重跑旧状态和未映射控件均不算通过。遮罩源背景节点y=-176.3515625，原生y=317.1484375，493.5点滚动差异意味着前置状态未对齐，不能将其整图差异全部归因产品绘制。电台源节点还有44.5点差异，未编造自动滚动规则来消分。

[失败记录](native-failed-attempts.json)保留编译错误、旧构建误用和原生遮罩缺少enabled事实。修正构建后真实导航成功，补AX事实后跑完整链路。第二课原版声音资源已接入；本轮未新增真实应用输出录音，不能套用上一课的声学证据或声称第二课音效已1:1。原版动画仍是观察帧，运动和相位未等价。

## 探索与RSI

[历史](history.json)126状态、67有回执边、[frontier](frontier.json)3233待探索动作。历史遗漏推动选择第二课，发现orderTapComplete、不同题目和刷新提醒；没有推断未执行后继。下一步继续第三课、指南词语点击／悬停、错题和正常口语、声音实测，以及实际布局／字体差异。RSI必须通过选择新分支发现遗漏；本轮不是RSI因果收益证据。[Dream-RSI和Cordis](../../../../docs/RESEARCH.md)原论文与机制记录保留，真实匹配预算模型实验04尚未执行；02和03不可判定结果不改写。

## 复跑

仓库根运行，使用新输出路径：

```sh
python3 projects/duolingo-web/compile-unit12-lesson2.py --out-dir artifacts/lesson2-compile-new
python3 projects/duolingo-web/freeze-unit12-lesson2.py --out-dir artifacts/lesson2-freeze-new
python3 -m projects.duolingo-web.compile-unit12-lesson2-frontier --out-dir artifacts/lesson2-frontier-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/lesson2-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit12-lesson2-v1/prepared-progress.json --seed-preferences projects/duolingo-web/evidence/english-unit12-lesson2-v1/prepared-preferences.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/unit12-lesson2-native-scenarios-v1.json
python3 projects/duolingo-web/verify-unit12-lesson2-observation.py --native artifacts/lesson2-native-new --out artifacts/lesson2-native-new/validation.json
python3 projects/duolingo-web/bind-frontend-aliases.py --observed artifacts/lesson2-native-new/observed.json --aliases projects/duolingo-web/evidence/english-unit12-lesson2-v1/aliases.json --out artifacts/lesson2-native-new/observed-bound.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v71.json --observed artifacts/lesson2-native-new/observed-bound.json --out artifacts/lesson2-native-new/frontend.json
```

35核心检查、61Python检查、21Node检查通过；编译器／契约逐字复现见[回执](reproducibility.json)。核心检查不验证UI或音频。归档本机路径、PNG位置及文本末尾转换见[审计](archive-audit.json)，原始和归档摘要分开。Goal保持active，完整1:1和真实RSI效果实验尚未完成。
