# 第二节点输入题：实际原生组件验证

2026-10-11。原版已实际接受听音填词Tea和反向翻译填词tea；听音输入的非空启用、清空禁用、提交后锁定均有源证据。新增text_entry状态、固定句子前后缀、正常/慢速公开语音与原版当前反馈文案。两个输入状态以独立probe夹具验证，不冒充完整原版课时；默认四课57题未被替换，第二节点仍未正式解锁接入。

本批12项核心通过。final-observed/window/progress/result及六张PNG来自同一次实际原生运行，walk_error=null。组件契约18项：12pass、0fail、6not_run，整体fail。6个未覆盖为两题各自视觉、声音及完整源判分。六对同题内容、同视口像素全部different；probe的全课进度和初始红心与原版轨迹不一致，故不是完整同状态验收；图片/字体/布局与正常/慢速图标尚未1:1。两份新公开音频与实际Swift bundle哈希一致，不据此声称听感一致。

第一次使用AXSetValue只改了屏幕字段，没有通知SwiftUI输入绑定，检查按钮仍禁用并超时。failed-observed保留这一失败。改为给自有独立候选PID发送真实键盘事件，执行输入、清空、重输并核对真实AX状态后，keyboard/final两次实际运行走通；不是把驱动写入值当通过。最终另接入实际反馈标题。

当前本地自由输入判分只对精确值Tea/tea有原版正向证据。大小写、空白、标点、拼写容错及错误后的重练没有验证，精确匹配仍是待替换的临时实现，不能宣称完整原版判分。没有测试或虚构麦克风识别。实际原版“现在不做口语题”分支显示“麦克风已关闭”“将在15分钟后恢复”，已追加到产品v7，候选未实现。v7共578项，完整产品本批未重跑；此前v6的341/8/205仍是e6a2349那次四课运行结果，不与组件结果合并冒充同一产品运行。

原版题目未观察到的模板英文鼓励语已从源题型底栏移除。源码观察先于实现；组件契约文件在初版实现后生成，因此本批不是预注册模型/RSI消融。真实探索策略效果仍待同起点同资源对照。

从仓库根复跑，输出目录须不存在：

```sh
python3 projects/duolingo-web/compile-english-input-probe.py
python3 projects/duolingo-web/freeze-english-node2.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
artifacts/observe-frontend artifacts/input-recheck projects/duolingo-web/fixture-english-input-probe.json --walk-course --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-input-probe.json --observed artifacts/input-recheck/observed.json --out artifacts/input-recheck/result.json
```

资源来自reference-assets-english-input-probe.json，已随Git交付。产品目标保持完整；下一步继续第二节点的错误判分、后续题目与口语实际识别路径，以及听音配对原生能力和角色动画。
