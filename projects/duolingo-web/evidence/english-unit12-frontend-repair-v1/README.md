# 普通课程前端修复、真实声音与第三课跳过探索

上一轮40状态无驱动失败不代表1:1。本批按原版前端失败回执修复：普通assist题误走旧布局，选项偏下约65点且AX为button；改用原版radio布局，保留预填／角色语义。实际两道assist答前和反馈的三项选项几何／角色，以及答前跳过控件，共[30项验证](native-final/repair-validation.json)通过。源动作中实际存在的跳过标签由编译器接入，不给未观察题目默认添加。选择题原版完整交互分支仍须继续探索。

原生生命图标原引用不存在的heart资源。原版第三课实际IMG明确为32×32及公共URL，已接已有同URL原资源en-home-088202fb75fb12b0eec8，修正header高度及ordinary assist布局。不是用问号或自绘心形替代。其他题型和字体／文字度量没有据此宣布等价。

## 实际结果

最终同一二进制实际40个UI状态、0驱动失败；[业务UI检查](native-final/validation.json)9项通过。对未改变的[v71](../../frontend-english-v71.json)，[最终严格结果](native-final/frontend-v71-portable.json)613pass／236fail／14752not_run／899unavailable，相对上一轮543／282／14752／923，新增70通过、减少46失败和24不可验证；35张整图仍全部fail。中间两次完整回放分别272和260fail，保留[二进制和结果摘要](intermediate-runs.json)，不隐藏迭代。

[v72](../../frontend-english-v72.json)完整保留v71，新增实际刷新主页、提醒遮挡、第三课入口、第三课首题及跳过反馈，共17092项。[v72结果](native-final/frontend-v72-portable.json)716pass／243fail／15042not_run／1091unavailable；37张已比较整图全部fail。提醒尚未实现，第三课内容尚未接入，保留not_run，不能因旧路径通过删除新需求。

两次真实UI操作分别点击第二课图片选择living room、提交第二课assist；只录自有应用PID、不录麦克风。[实际输出测量](native-final/audio-measurements-portable.json)对两个不同原语音资源的相关系数约0.99999995／0.99999240，拟合增益约0.99999789／0.99995112。第二个窗口测的是实际播放的答案语音，不把它称为已验证的正确提示音。源事件缺失的提示音没有添加替代资源；完成音效及原版总体声学输出依然未知。录音及动作时间戳保存，不用非零音量代替资源验证。

## 新探索改变下一步

原版实际进入第三课，首题Is the kitchen clean?；实际点击空答案“跳过”后显示“正确答案：厨房干净吗？”，选项禁用，生命保持4。已有核心skip同样不扣生命，本批不改写它；没有声称所有阶段跳过都遵循该规则。原版停在第三课首题跳过反馈，后续尚未执行；访客进度没有重置。

[历史](history.json)128状态、69条有回执边，[frontier](frontier.json)3257待探索动作。由历史遗漏选择新分支；下一步继续第三课及回顾、实现提醒及验证其遮挡、文字几何／CSS和整图、原版动画及声音对齐、真正匹配预算的模型04。RSI因果实验未完成，本批前端修复不是机制消融。[Dream-RSI与Cordis原论文](../../../../docs/RESEARCH.md)及既有02／03不可判定结果保留。

## 复跑

从仓库根使用新输出目录；先构建再运行原生观察器。原版历史回执不是可任意重置的在线账号。

```sh
python3 projects/duolingo-web/compile-unit12-lesson2.py --out-dir artifacts/repair-compile-new
python3 projects/duolingo-web/freeze-unit12-home3.py --out-dir artifacts/home3-freeze-new
python3 -m projects.duolingo-web.compile-unit12-repair-frontier --out-dir artifacts/repair-frontier-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/repair-owned-recorder-new
swift projects/duolingo-web/observe-frontend.swift artifacts/repair-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit12-lesson2-v1/prepared-progress.json --seed-preferences projects/duolingo-web/evidence/english-unit12-lesson2-v1/prepared-preferences.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/unit12-lesson2-native-audio-scenarios-v1.json --audio-recorder artifacts/repair-owned-recorder-new
python3 projects/duolingo-web/measure-lesson2-owned-audio.py --native artifacts/repair-native-new --out artifacts/repair-native-new/audio-measurements.json
python3 projects/duolingo-web/bind-frontend-aliases.py --observed artifacts/repair-native-new/observed.json --aliases projects/duolingo-web/evidence/english-unit12-frontend-repair-v1/aliases.json --out artifacts/repair-native-new/observed-bound.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v72.json --observed artifacts/repair-native-new/observed-bound.json --out artifacts/repair-native-new/frontend-v72.json
```

35核心／61Python／21Node检查通过，源编译与冻结逐字复现；日志、[归档审计](archive-audit.json)、[复现检查](reproducibility.json)保存。原生截图与声音字节未改动，归档仅变更位置、本机路径、JSON格式和终端EOF，摘要区分原始与归档。当前仍非1:1，完整Goal active。
