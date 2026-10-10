# 整句输入与实际角色布局修正

2026-10-11，继承english-secondary-actions-v1的真实原版观察。本批完整Goal保持active，默认课程键盘模式集成、正常第七课、跳过结算、视觉/声音1:1与真实RSI消融仍未完成。

## 依据与修正

原版整句编辑区是[300,336,600,170]，19px/400、24px行高、浅灰背景与2px边；上方为175高角色行，标题后没有旧28点间距。源底栏宽920，切换动作居中，检查按钮150宽。此前Swift只画单行TextField并漏角色行，因此虽然可提交，输入区仍有75/131点纵向差异。

LearningView现在显示角色行与气泡，整句使用真正多行编辑器，底栏居中、按钮按原版尺寸/颜色/底边绘制。完成翻译标题间距、源2题起连对显示也已修正；旧源快照明确1题不显示、2/3/4题显示。其他历史题型/反馈/退出UI差异未被排除出目标。

ReferenceAnswerEditor直接拥有NSTextView与SwiftUI绑定，禁用本机智能引号、破折号、文字替换和拼写自动纠正，保留输入原样；没有通过评分器把弯引号归一化成直引号。它使用源19px/400字体和实际多行编辑区。默认五课/显式六课尚未配置整句模式；本批局部fixture是源第1/4题动作探针，不等价于原版整个第七课。

## 素材身份的失误与撤回

当前原版第4题Falstaff反馈的actual canvas、12帧、renderer buffer与公开Rive CDN解压字节一致，actual scale1.1及偏移/状态机已绑定到其原有素材身份en-image-58f00fb33fb90339eef1。正确/错误触发与原生SDK复用现有架构，口型、相位、时长和声学同步仍未知。

首轮错误地用旧探针文件名english-sixth-lin-renderer推断Lin身份；该旧批README和character-binding.json其实已明确它实际是Bea。我漏读该证据，native01–05误配画面保留。最终删除Lin→Bea绑定及重复二进制，没有改写旧事实。asset-verification同时保留字节匹配和identity_binding=REJECTED，说明哈希相等不证明角色身份；最终仅新增Falstaff Rive。Lin仍用历史接口图像，完整原版角色未知，不能算1:1。fixture保留Lin源身份，不将错误素材固定成产品要求。

## 实际失败推动修正

- native01/02：AXPress在实际完成切换后返回失败，停止并保存现场。明确按钮AX标签也未解决；没有在同一轨迹重试可能已经执行的动作。
- native03：向PID投递鼠标事件没有触发切换；后续缺失输入被真实验证捕获，未当空值通过。
- native04：屏幕坐标点击完成四个输入中间态，AX提交也实际正确，但AXPress回执仍失败。
- native05：模式、提交、继续均以自有窗口实际坐标单次点击推进，发现I'd被系统编辑器变成I’d，原生判错且进入重练；没有伪造整课完成。
- native06：自有NSTextView关闭替换后，两题全程24状态，walk_error=null，原输入保留、两题接受、未扣心。其指针事件、AX、实际PNG和进度保留。native07补齐切换按钮isButton可访问性角色后同样24状态、无执行错误、两题接受；输入几何及49项结果不变，两轮均保留。

原有48项契约断言没有修改：原生36pass/8fail/4not_run；6项输入区几何从fail变pass，均精确[300,336,600,170]。8项切换几何仍因0.0078125/0.2265625/0.453125点差异fail，零容差保留。v2新增Falstaff反馈实际渲染几何1项：原生[295.1,152.25,129.8,192.5]，源x=295.08612060546875，仍fail。因此v2共49项，原版45pass/4not_run，原生36pass/9fail/4not_run，整体fail；不是放宽阈值后的成功。

6对同视口整页图片全部different。探针与原版的生命、先前题序、总题数和连对不同，Rive相位未对齐；pixels.json只作差异诊断，不作完整同状态产品验收。首个像素命令因manifest缺limitations失败，修正该元数据后才产生结果，失败留在pixel-command-failure.json。实际音频未新增验证。

Swift构建通过；18项核心检查通过。本批未修改框架Python或评分规则。完整六课从空进度实际执行273状态、walk_error=null、生命2、六课完成且completedCourses为空；v12仍662pass/42fail/357not_run，旧失败未增加。独立回执在six-course-regression，不将探针结果累计进整课验收。

## 复跑

仓库根、macOS辅助功能权限；每次新输出目录；前端因失败/未知返回非零。像素诊断可返回零但仍different/not_proven，不能把命令退出码当像素通过。

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-input-layout
artifacts/observe-input-layout artifacts/input-layout-review projects/duolingo-web/fixture-reference-en-zh-secondary-v2.json --walk-course --exercise-input-modes --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-secondary-v2.json --observed artifacts/input-layout-review/observed.json --out artifacts/input-layout-review/frontend-result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/input-layout-review --pairs projects/duolingo-web/evidence/english-input-layout-v1/pixel-pairs.json --out artifacts/input-layout-review/pixels.json
```

源当前仍停在第七课第4题整句正确反馈。下一步沿既有源轨迹补齐正常第七课和跳过重练/结算；核实Lin实际renderer，集成默认模式并修反馈/主页等真实视觉与声音差异。研究与历史负面实验仍由docs/RESEARCH.md维护；这轮是实际差异修正，不是RSI策略收益或无人监督探索证明。
