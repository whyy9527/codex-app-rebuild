# 首页趋势图的实际形状差异修正

上一轮周期内容复验后，本轮继续依据已有趋势截图修正明显差异，没有恢复受前台争用影响的原版 collect。现有完整 RSI 池和主详情再部署回执保持不变。

## 来源与发现

当前 Codex 实际查看原版 `private/reference/2026-10-12-home/chart-schedule-full.png`、`chart-attendance.png` 及对应 AX 差分，再实际驱动候选切换出勤率、滚动并查看截图。候选原曲线使用末端水平切线的 S 形三次路径，原版最后一段继续陡升；绘图区原高度 210 点，原版两种图表实测约 224 点。原版面积呈灰蓝，候选两组彩色面积叠加偏棕。

两端截图滚动位置不同，不能以当前捕获做严格整图一致判定。原版图表 AX 仅为更新差分，没有补造全树或 Canvas 曲线数据。

## 测量与实现

对固定原版出勤截图的实际橙色曲线采样，保存原始采样点、端点和模型到忽略的 `private/home-chart-candidate-20261012/source-curve-measurement.json`。在零点切线水平的约束下拟合归一化三次曲线，控制参数约 (0.487365, 0.833272, 0.549108)。源图采样对该模型的 RMS 约 0.244 个原始像素，旧 S 形模型约 116.122。此数值只是固定参考曲线的建模误差，不是候选图像通过证据，也不证明原版使用该算法。

候选使用该固定观察段的近似控制点，修正网格间距、基线位置、柱高、日期与基线间距，以及出勤模式面积填色。仍保留原有固定数据图实现；其他数据形状、跨日刷新和一般插值算法尚未原版验证，不能声称已实现通用原版图表引擎。

## 实际回放和限制

Node 24.18.0／pnpm 11.15.1 构建、类型检查和三项首页状态测试通过后，刷新实际候选，再切换排课点名和出勤率并保存 AX／截图到 `private/home-chart-candidate-20261012-fixed`。实际点击屏幕外控件会自动滚动控件到视口，后续另滚动半页采集 `attendance-visible.png`；当前 Codex 实际查看该图，确认曲线末端形状已变化且绘图区完整可见。

新增共同摘要契约与观察器事实转换：原版差分的完整链接名称、候选合并文本节点均从实际 AX 读取。原版固定事实与候选各为 2 pass、2 not_run；两项未运行明确对应同状态严格图像比较。来源截图和当前截图的滚动／整体布局仍未一致，没有修改既有严格图像阈值，没有移动对齐图像或将拟合分数当成视觉通过。

最终构建产物为 `index-C2Xe_9UO.css` 和 `index-CK3G2HxD.js`，实际 UI 通过 Vite 刷新消费当前实现。完整仓库 unittest 91 项、方法 preflight connected 和 `git diff --check` 通过。

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-chart-candidate-20261012-fixed --out projects/xiaogj-web/private/home-trends-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_trends --observed projects/xiaogj-web/private/home-trends-new.json --out projects/xiaogj-web/private/home-trends-result-new.json
```

完整首页布局、图表交互／输入方式、声音、持久化及其他业务旅程继续待验。原版新探索阻塞仍在，全范围原生 Goal 保持 active。
