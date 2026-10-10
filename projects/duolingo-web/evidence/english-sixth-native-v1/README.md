# 第六课原生轨迹与前端模具修正

从[实际第六课](../english-sixth-v1/README.md)编译15道评分题、一次不计分听力暂缓和一次口语暂缓，实测进入挑战、结算、建档并返回主页。`fixture-reference-en-zh-v7.json`扩充为六课，明确只包含第六课已观察的双暂缓路径；默认启动仍v6五课。正常听力/录音后的后续没有源证据，不能用此夹具强制替换正常分支或声称默认已完成六课。

## 编译及真实改动

首两题来自实际Bea/Lucy及已接受反馈，听力暂缓/插入咖啡加牛奶/填空复用实际前半程证据，后半程逐题从真实答案回执编译。三道挑战取当前DOM提示和已接受输入，不取API尾部。Junior/Oscar填空角色身份由实际PNG确认并写入元数据；输入组件仍缺完整角色/气泡，其它未映射角色和自适应语音仍缺。口语语音为对应公开API资源绑定，不是声学等价证据。

UI修正包括输入框源标签与170点区域、口语暂缓反馈三动作、连对计数，以及第二节点课次/进度环。连对仅评分正确才增加，暂缓不增加；核心实际轨迹检查确认15题对应15次。主页任务改为源进度快照配置，第五/六课实际30经验、30/30，默认五课也获得修正。

17项核心检查通过，SDK构建通过。run01实际走完整条轨迹，60状态、生命2、六课已完成、completedCourses仍空；原306项为174pass/82fail/50not_run。修正后run02同样60状态、无walk_error，原冻结契约193pass/63fail/50not_run。旧失败未覆盖。

## 修正源采样，而不是迎合错误字符串

原版AX/YAML的`text: "2"`被旧采样器当成含引号的文字；结算动画的父节点还包含所有被裁切的0–9，并拼接标题/统计文案。这些节点字符串不能指定实际显示的文字。`revise-english-sixth-copy.py`保留v11/原306项及失败结果，创建新修订：解码序列化引号；结算独立文案来自实际完成PNG及明确标为人工读取的completion-visual.json。`copy-sampling-revision.json`逐项记录34处采样修订，不将它们归为Swift产品修复。

修订后独立第六课309项：原版259pass/50not_run；原生228pass/31fail/50not_run，均整体fail。31项仍含跳过、键盘、加大难度及后续主页/导航/通知/页脚；页脚AX分组差异也尚未解决。没有用采样修订放宽50项视觉/声音未验证要求。产品v12保留v10的752项并加入新309项，共1061项。

25对实际源/原生同视口截图全部different。原生按实际窗口标题栏/2x比例归一化；完整问题分母、角色、布局、结算英雄区、音频等仍未对齐，不用遮罩或通过阈值。`native-final-pixels.json`是失败诊断，不是1:1通过。

默认五课当前实际回归220状态、无walk_error；对v12为434pass/11fail/616not_run，11项失败未增加。新第六课当时未执行，所以309项未覆盖，不把组件结果加到该次五课回执中。

完整六课随后从空进度在同一构建单次连续执行：273状态、walk_error=null，最后生命2、六课completedLessons、completedCourses为空。v12为662pass/42fail/357not_run，整体fail；full-*保存独立实际回执，不是把两次组件观测拼接成全程。

## 资源与失败保留

公开资源清单114项，实际bundle的138份SVG/PNG/音频哈希均匹配。只新增一个对应口语的源MP3，其它资源复用已核验文件；哈希或播放调用不代表实际音色/时序一致。通用资源工具重渲染既有PNG时七份字节改变，其中六份像素也改变；保留比较和尝试哈希，恢复既有提交版本，不顺带改动默认素材。

首轮bundle路径采样用错目录名，记录unavailable，不编造首轮资源快照；最终实际bundle逐文件校验通过。SDK构建的资源复制已在恢复后重新执行。账号信息及原始stdout不入库，实际截图及AX失败和结果保留。

## 复跑

从仓库根，macOS辅助功能权限和Swift/Rive依赖已就绪；每次使用新输出目录。验收因失败/未覆盖返回非零，各命令分别执行。

```sh
python3 projects/duolingo-web/compile-english-sixth.py
python3 projects/duolingo-web/revise-english-sixth-copy.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
artifacts/observe-frontend artifacts/sixth-review projects/duolingo-web/fixture-reference-en-zh-v7.json --walk-course --start-lesson-index 5 --exercise-listening-decline --seed-progress projects/duolingo-web/evidence/english-feedback-actions-v1/five-progress.json --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-sixth-v2.json --observed artifacts/sixth-review/observed.json --out artifacts/sixth-review/frontend-result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/sixth-review --pairs projects/duolingo-web/evidence/english-sixth-native-v1/pixel-pairs.json --out artifacts/sixth-review/pixels.json
artifacts/observe-frontend artifacts/six-course-review projects/duolingo-web/fixture-reference-en-zh-v7.json --walk-course --english-first-wrong --english-fifth-mixed-errors --exercise-duplicate-words --exercise-listening-decline --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v12.json --observed artifacts/six-course-review/observed.json --out artifacts/six-course-review/frontend-result.json
```

原版仍在六课后主页。下一步区分正常/暂缓的实际分支并接入默认，补齐现有跳过/键盘/难度/主页行为，修25对视觉与实际声音差异，开展同起点同预算的真实探索消融。原始Dream-RSI/Cordis及负面实验继续保留；本批没有宣称自主RSI或探索收益。完整Goal active。
