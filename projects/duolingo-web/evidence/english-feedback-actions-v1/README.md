# 原版反馈动作：实际探索与原生验证

本批从第六课的实际 sugar 题继续，选择“糖”后原版接受，显示“非常好！”和连续五题正确。未推进到下一题。原版为 en/zh、1200×732；原生单题探针只有一次答题，没有原版此前五题的进度、Oscar渲染及音频，不能把整页图片对照称为同一完整产品状态。

## 实际发现

原版“太简单”可选中，“太难”会替换前者，再点同一项可取消。报错弹窗包含六种原因，未选择时提交禁用；“其他问题”和“音频听起来不正确”可同时选中。Escape关闭后恢复反馈，再次打开全部未选、提交禁用；最后再次Escape关闭。证据为各 english-feedback-*.json/png、sugar-answer.json。未提交虚假报告；提交结果、评价的服务器效果和其他题型的报错原因仍未知。

`exploration-history.json`在此前听力暂缓历史上追加本批实际转移。frontier为16个resolved动作、60个pending；只是已观察动作集合，不是全App覆盖率。反馈遗漏驱动本次探索修订，不是自主RSI或收益实验。Dream-RSI、Cordis与原实验继续由[研究来源](../../../../docs/RESEARCH.md)维护。

## 实现与验收

Swift增加反馈动作、互斥可取消评价、六项多选报错及关闭重置。报错原因由Question元数据承载；当前仅fixture-feedback-actions.json冻结此题，默认课程其他题没有已观察原因，完整产品接入尚未完成。提交服务未实现。源图标来自公开CDN，resources.json保存SVG与渲染PNG哈希；icon-decompression.json保留首次误存gzip字节的失败。

先冻结frontend-feedback-actions.json，再独立读取原版DOM与实际原生AX。31项中，两端均25pass、0fail、6not_run，整体fail。未验证包括同状态视觉、音频、其他题型、提交服务、评价持久效果、原生Escape/点击遮罩关闭。原生实测关闭使用关闭按钮，不冒充测过键盘及遮罩。

native-run01/02保留report-submit定位失败；第二轮失败PNG证明弹窗已显示。SwiftUI父级accessibilityIdentifier传播到子控件，导致其ID覆盖，使用明确contain容器后修复。run03实际跑通，再修正蓝色描边复选框及启用提交按钮样式，native-final来自run04，16个状态、无walk_error、明确局部停止。没有删除断言。

九对整页图全部different，且完整题前状态不一致。四对弹窗卡片在两端实测同为[478.5,202.5,243,327]时仍全部different；卡片诊断排除卡片外区域、保留文字/复选框/抗锯齿差异，不设通过容差。run03及最终像素结果均保留。几何相同不能证明1:1。

听力暂缓22项回归为16pass、0fail、6not_run，原来缺少的三个动作入口已补齐；核心16检查通过。默认五课实际214状态、五课完成、生命2，共752项为434pass、11fail、307not_run，整体fail。five-*来自最后仅调整报错弹窗样式之前的构建，该回放未打开报错；最终弹窗改动由run04验证。两类回执不能混为完整产品通过。

## 复跑

从仓库根执行；输出目录与JSON使用新的名字。需要macOS辅助功能权限、已有Swift/Rive依赖和源资源。

```sh
python3 projects/duolingo-web/freeze-feedback-actions.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-feedback-actions.json --observed projects/duolingo-web/evidence/english-feedback-actions-v1/source-observed.json --out artifacts/feedback-source-review.json
artifacts/observe-frontend artifacts/feedback-native-review projects/duolingo-web/fixture-feedback-actions.json --walk-course --exercise-feedback-actions --stop-after-question-id en-zh-feedback-sugar --seed-progress projects/duolingo-web/evidence/english-feedback-actions-v1/initial-progress.json --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-feedback-actions.json --observed artifacts/feedback-native-review/observed.json --out artifacts/feedback-native-review-result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/feedback-native-review --pairs projects/duolingo-web/evidence/english-feedback-actions-v1/pixel-pairs.json --out artifacts/feedback-native-review-pixels.json
python3 projects/duolingo-web/compare-report-card.py --native artifacts/feedback-native-review --out artifacts/feedback-native-review-card.json
```

前端验收因not_run返回失败，各命令分别执行。下一步从原版当前已接受的sugar反馈继续第六课，采集暂缓后的完整替换、结算及未知分支，编入默认路径；同时修已测视觉/声音差异，完成真实探索机制消融。完整Goal保持active。
