# 头像编辑、保存与原版返回反例

沿上一批frontier，先继续实际原版探索再实现。初始创建页选第二肤色后点完成，原版改成“修改虚拟头像”并打开退出确认；继续编辑后刷新，第二肤色仍在，完成恢复禁用。干净返回进入`/profile/undefined`再跳404。编辑改成第一肤色后返回也确认，放弃后仍跳404。通过真实排行榜页脚再访已创建档案，不再出现首次头像引导。保存/返回轨迹见[逐动作记录](transitions.json)，不是自行设计常见保存流程。

原版15个肤色逐一真实点击，实际Canvas各采3帧，共45帧，颜色从实际控件子节点读取。每组3帧哈希均不同，否定“预览静态”的猜测。Swift当前使用每肤色一个原版绘制帧驱动预览，属于尚待替换的部分实现；没有复现原版动画或其它8分类。不得以这些图片或本轮成绩宣称完整头像系统或1:1。原始drawing buffer与页面截图分开保存，没有把页面截图裁成角色素材。

补充边界：干净的已保存编辑器点击当前已选第二色，原版完成也从禁用变为启用，见extra/same-selected-action.json。这条新增源用例还未作为独立的已保存同色原生场景运行，不包含在76项流程通过中。

## 实现与验收

Swift接真实开始、档案头像入口、15单选、触碰后完成启用、保存后确认/继续、重新启动回读及放弃编辑。avatarSkin是可选偏好字段，真实旧偏好可继续读取；原版保存状态作为录制快照夹具回放。新保存头像在档案/排行榜上的展示、其它分类和原版完整动态渲染、浏览器离开警告仍缺；邀请及累计经验继续在frontier。

v58保留v57的3855项，追加448，共4303。源投影442pass和6pending，仅证明参考一致。最终原生21状态无驱动失败：首创建、15选择、保存/重启/回读、改色返回/放弃。v58为331pass/92fail/3787not_run/93unavailable，6张已比较整图全部fail。未映射分类/控件仍unavailable，未运行其它页面仍not_run。

独立[流程回执](native-final/flow-validation.json)76项通过，期望来自实际原版保存/刷新/放弃状态及15个真实选择。真实偏好保存1，重启后选择1且完成禁用，改成0再放弃也没有把0写入保存。它不证明图像、声音、动画或其它分类。相同最终二进制档案4状态回归93pass/10fail/4106not_run/94unavailable，三图仍fail。

首轮AXPress第二色失败、直接Radio容器的54点几何与零alignmentRectInsets未修好的负结果保留。显式NSButton子节点容器后21状态走通；按钮合成层减少文本阴影和图像差异，但92项严格失败未消失。原版reload先报告beforeunload、后续accept又称无对话框；不推断自动关闭机制。

构建04、30核心业务检查、10公开SVG/PNG哈希、45Canvas帧哈希、15预览字节身份及冻结复现通过。[逐轨迹汇总](verification-summary.json)、[实际对照](comparison.html)、[下一步](exploration-feedback.json)。没有声学等价或新RSI因果收益结论；匹配预算真实探索消融仍需执行。归档后重算validation.json路径/摘要，旧回执validation-before-path-rebase保留。

## 复跑

从仓库根运行，新目录/回执文件须不存在：

```sh
python3 projects/duolingo-web/freeze-avatar-save.py --out-dir artifacts/avatar-save-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/avatar-save-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/avatar-save-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v58.json --observed artifacts/avatar-save-native-new/observed.json --out artifacts/avatar-save-native-new/validation.json
python3 projects/duolingo-web/verify-avatar-flow.py --observed artifacts/avatar-save-native-new/observed.json --preferences artifacts/avatar-save-native-new/progress.json.preferences.json --out artifacts/avatar-save-native-new/flow-validation.json
```

前端比较仍退出1，须读逐项失败。源新鲜采集使用capture-visible-state.mjs和capture-avatar-skins.mjs，需先确认真实当前页为肤色编辑器且15个radio；采集仅修改未保存选择，原版刷新/离开可能触发退出警告。旧创建0与当前保存1属于不同录制状态，不能拿不同状态截图混比。
