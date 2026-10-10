# 第二次发音练习探索与配对前端修复

本批原本准备探索正常口语。实际第二次练习入口为+10经验，内容变成sip/zip/sap/zap，10道选择后直接配对，未出现首次的got口语；四组配对接受后更正六道错题，结算“你莫不是特工？／本单元中，你完成了11项听力挑战”，有回顾本单元/继续。匿名建档稍后再说返回发音页。没有把首次课程顺序强加给第二次。错误预判口语的本地文件speech-before已按实际内容归档为matching-before，原始本地文件保留。

## 新事实与未覆盖

真实刷新前后ɑ0.05、ɛ0.041666668、s0.1、z0.1保持。前两项来自首次练习，后两项在第二次由0变为0.1；入口仍+10。初次回主页快照还读到s/z0，稳定后的独立捕获才更新；不能把过渡态当作未保存。增长规则仍未知，不据两个样本写通用公式。

第二次没有口语的原因未知。当前浏览器麦克风权限为prompt，mediaDevices与SpeechRecognition存在；这只能证明API可用，不能解释排题。未调用麦克风，也未修改权限。匿名更多实际点击/hover均未观察到设置菜单，后续继续寻找真实入口；不以此永久划除正常口语。

六道错题复习均纠正；最后继续后旧禁用选择控件在动画中残留，旧驱动误点而超时。保存review01失败后，独立读取确认原版已结算，没有重答。驱动现等真实可操作radio或实际非选择题/结算，增加明确终态采集。初次终态探针0动作、terminal=true，只验证当时已有终态；随后第三次真实重练验证见下文，不把空跑称作整课成功。

[discovery-frontier.json](discovery-frontier.json)保存第二套内容、口语缺席、结算回顾、进度恢复及设置入口的已观察/未知和下一探针。第二套尚未编入原生课程，进度保存也尚未实现；探索得到原版证据不等于候选已完成或RSI有收益。

## 前端修复及验证

两次原版配对都为左330/右615、宽255高58、纵向247/315/383/451。旧候选是150宽跳过样式，且右列顺序错误。v21保留1650项后新增40项：八个矩形、角色、初始/完成enabled及标签顺序。先用旧原生观察验证基线，新增28pass/12fail；修复后新增40pass，八项矩形零容差通过。

原生控件共享显式NSButton角色/命中矩形和独立绘制面，按Question.rightOrder排右列；音频/匹配仍走现有LearningModel/Lesson。实际重新走52状态，四错重练、配对及返回完成，主进度仍六课/生命3。构建和22核心检查通过；未改Python核心，不重复运行框架检查。JS语法及实际终态检查通过。

完整本次1690项为170pass、23fail、1497not_run；六对同状态图全部different，未放宽标准。配对before三通道平均差从[3.915,2.487,3.859]降到[3.143,1.269,2.415]，反馈从[3.928,2.613,5.067]降到[2.654,1.339,3.794]。右列源词例中心均为756.5，删除额外间距使原生词例向左7点，重新走52状态；初次对齐证据保存在native-initial-alignment。其余四对也比较，q0图完全保持旧像素差；不能称整图或声音一致。第一次基线比较误用上一批仅保存四图的子集而缺matching PNG；改用同一原始完整capture（相同binary digest），没有重跑或补造原始图。

## 复跑

    swift build --package-path projects/education-swift
    swift run --package-path projects/education-swift LearningCoreChecks
    swift projects/duolingo-web/observe-frontend.swift artifacts/practice-match-new projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice
    python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v22.json --observed artifacts/practice-match-new/observed.json --out artifacts/practice-match-new/frontend.json
    python3 projects/duolingo-web/compare-english-captures.py --native artifacts/practice-match-new --pairs projects/duolingo-web/evidence/english-pronunciation-matching-v1/pairs.json --out artifacts/practice-match-new/visual.json

前端预期非零失败；图像零退出只表示诊断完成。新探索脚本从当前真实页面续跑，不重建已经完成的远程尝试；使用fresh输出目录和实际当前题序。原版当前在第三次结算的成绩单内，首张tell/tall卡已展开，完整Goal active。下一步由上述frontier继续第二套编译、恢复/正常口语、结算回顾和已有视觉/声音差异；匹配预算的真实复刻质量消融仍待完成。

## 第三次实际验证与口语分支

第三次为tell/tall/pot/pet，确实出现tell口语，推翻永久关闭的解释。新默认驱动保存10个复合键的反馈答案；口语暂缓、配对后，把这份answer_memory接入续跑，五道错题均以prior_feedback选正确答案，无额外错误。最后真实到结算，没有旧禁用按钮误点；由于终态检查时点未确认slide，首次将结果保留为unhandled。后续现场有session-complete-slide，0动作探针确认terminal=true；又补充实际“回顾本单元”按钮作为终态信号，未重新跑一条完整切换，不能夸大这项修复的验证范围。

正常口语前置已捕获：原播放按钮29×22、录音600×70且enabled，均不同于候选。按[CDP官方PermissionDescriptor/设置接口](https://github.com/ChromeDevTools/devtools-protocol/blob/master/json/browser_protocol.json)只对当前来源临时设microphone denied，确认denied才点击录音；原版显示“未授权使用麦克风”及帮助链接，finally恢复prompt并实际读回。没有录麦克风/环境声音。模态框仍阻断speaker输入，第一次点击超时保留；从实际截图定位关闭圆圈后关闭，再播放tell捕获原beaen媒体URL，并暂缓口语。现场反馈为“说得真不错！”，不能说是识别成功，也不能假定所有暂缓文案固定。

新访问回顾本单元，成绩单包括17张卡（12个原始步骤含口语/配对，另5个重练），首张展开“你的答案： tell 正确答案： tall”。这提供独立的答案复核入口，候选尚没有成绩单。source-third保留动作、截图、反馈记忆及失败；不把这些新观察作为后续实验未见留出。

随后v22保留v21，冻结下一实现批的12项口语/权限及成绩单要求，共1702项。用本批相同52状态观察做基线：171pass/24fail/1501not_run/6unavailable。配对40项仍全pass；6项口语控件不可用和成绩单未访问明确暴露实现缺口，不能用v21通过子集掩盖。正常录音/识别、后续内容和持久化仍未完成。下次前端复验用frontend-english-v22.json；v21与其回执保留。

实际反馈记忆和原版探索改变了行为与下一任务，这不是匹配预算的机制收益证明。完整Goal仍active；下一步接通口语权限/录音基础、由统一观察生成后续练习并保存进度，以及按固定起点/预算完成真实前端质量消融，不能以继续堆课程替代质量实验。

CLI输出现显式区分terminal/unhandled_state/budget/error并保存stop_reason。现有结算/成绩单上0动作探针验证terminal分类；它只说明本单元问题已经完成，不说明成绩单探索、原生复刻或完整Goal完成。源当前仍停留成绩单首卡，没有自动退出或重启。
