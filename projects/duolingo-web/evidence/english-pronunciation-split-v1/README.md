# 发音练习分段控件与模具补漏

原版 q5 是白色165宽的分段播放控件，候选却显示两个蓝色80宽按钮。旧契约只检查选项与反馈文字，遗漏真实播放控件的形状、尺寸和反馈状态。实际原版答题后禁用两个按钮，揭示deck/dock；同音题分别揭示get/get、deck/deck。这些来自原版归档，不从答案或URL猜词。

v20在1638项之后追加12项源需求，旧项逐项完全保留。新增8pass、4fail；四项零容差几何均差0.25点，没有放宽。完整同次结果130pass、23fail、1497not_run；基线按同一v20为126pass、27fail、1497not_run。完整结果只覆盖本次52个原生状态，不能用其他构建的结果填剩余1497项。

## 实现与保留失败

`Question.practiceAudioLabels`承载实际反馈揭示词，编译器只读归档禁用speaker标签。独立NSButton拥有点击、禁用和AX角色，hosting面绘制原speaker图、下划线与白色分段外框。驱动实际点击每次sameDifferent的两段，再答题、复习、结算、稍后建档及退出；仍六课/生命3，未修改主课程进度。

第一次原生表示没有进入AX树，8项unavailable、2项反馈词fail；`failure-missing-ax`保留。加容器后暴露AXUnknown，`failure-unknown-role`保留；明确button角色后通过。没有把画出来等同于可操作，也未用测试自填pass。分段按钮图像/声音时序仍有差异。

原退出资源名不存在，显示问号；从原观察记录的CDN URL取实际SVG，独立浏览器上下文渲染18×18@3x后关闭，替换练习图标。首取gzip字节误按UTF-8解码失败，修复及资源摘要见close-resource.json。

构建、22核心业务检查和52框架检查通过。四对同状态图片全部different。共同sRGB、按实测窗口裁标题栏及2x下采样，不遮罩/移动图像。q5-before三通道平均绝对差从[4.618,2.768,2.776]降到[1.547,1.115,1.792]，q5-feedback从[8.207,5.271,4.678]降到[4.534,3.597,3.890]；这是局部修复诊断，不能称作1:1通过、RSI收益或消融结果。

## 复跑

    swift build --package-path projects/education-swift
    swift run --package-path projects/education-swift LearningCoreChecks
    swift projects/duolingo-web/observe-frontend.swift artifacts/practice-split-new projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice
    python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v20.json --observed artifacts/practice-split-new/observed.json --out artifacts/practice-split-new/frontend.json
    python3 projects/duolingo-web/compare-english-captures.py --native artifacts/practice-split-new --pairs projects/duolingo-web/evidence/english-pronunciation-split-v1/pairs.json --out artifacts/practice-split-new/visual.json

前端预期非零失败；图像工具零退出只是诊断执行完毕。原版原始证据在[前一批](../english-pronunciation-practice-v1/README.md)。字体、反馈图形/颜色、原生进度条、正常口语、结算统计/条件文案、音标恢复和声学一致性仍未完成；完整Goal active。持续实际探索未访问分支，真实复刻质量的匹配预算消融仍待完成，不用增加断言数量代替它。
