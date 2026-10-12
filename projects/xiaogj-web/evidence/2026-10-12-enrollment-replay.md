# 报名空表单实际候选回放与观察器补漏

上一轮新增空表单后尚未实际驱动候选，本轮优先验证该主页面。原版采集安排尚未答复；没有重启原版 collect，没有创建第二个续跑器或宣称新的 RSI 部署成功。

## 实际入口与运行代码

检查发现原生应用按 bundle ID 绑定存在歧义：本机有 Edge 主应用和两个更新器版本。使用主安装目录中的明确应用路径重新绑定，再通过原生 Window 菜单选择已有候选窗口。未操作其他页面的内容。此方式只恢复当次候选操作，不证明原版采集可持续独占窗口。

实际从候选学员信息管理侧栏点击新学员报名时，浏览器仍显示旧占位页；刷新经过 URL 守卫确认的候选页面后，才看到当前报名表单。说明构建成功和开发服务存活均不能证明已有浏览器页面消费了新代码。本轮没有将旧页面算作新实现。

实际 AX、截图和首次结果保存在 `private/enrollment-candidate-20261012`。本轮截图均为 2940×1666。逐张查看实际截图和配对 AX，哈希绑定的复核记录保存在相应 `review.json`；继续同一内容裁切、色彩归一化与严格整图比较。

## 失败、根因与修正

首次比较 46 pass、9 fail、4 not_run。其中八项文本失败对应候选按钮只有 AX 控件节点，没有单独 text 子节点，而原版链接含 text 子节点。截图确认这些文字实际可见。观察器现在同时读取 button／link 自身的实际名称，保留原版和候选相同的规则；没有复制期望、没有改契约或把缺失节点回填为成功。用同一张首次截图重新采集得到 54 pass、1 fail、4 not_run；修订观察器在历史原版得到 55 pass、4 not_run。

另从实际截图确认通用输入规则的高 CSS specificity 覆盖了日期宽度和账号宽度：日期仍为普通字段宽度，账号后缀落在输入框外。将输入排除条件改为 `:where`，使专用宽度生效；同时修正表单底部间距、表格前两列宽度、未选中控件外观和报名按钮位置。

Node 24.18.0／pnpm 11.15.1 构建和类型检查通过后，再刷新经过守卫确认的候选页面并实际复采，结果在 `private/enrollment-candidate-20261012-layout`：54 pass、1 fail、4 not_run。严格图像项仍 fail。两次实际采样的 RGB 平均绝对差约为 (6.054, 5.596, 5.385) 与 (3.864, 3.636, 3.951)；只说明这两次采样的差异变化，不能取代一致性要求。

当前候选构建产物为 `index-PdyL06_k.css` 与 `index-BoKlzsKQ.js`。UI 通过已运行 Vite 开发服务刷新读取当前实现；构建验证、实际 UI 动作和比较结果分别保留，不将构建产物存在作为界面通过证据。

## 未完成与复跑

契约文件未修改，仍保留选择分支、提交、横向滚动、跨日日期和账号规则未知。实际只验收空表单界面，没有提交原版业务数据，没有验证候选报名成功或持久化。全范围 Goal 继续 active。

```sh
python3 -m projects.xiaogj-web.tools.enrollment_frontend_observations --ax projects/xiaogj-web/private/enrollment-candidate-20261012-layout/blank.ax.txt --image projects/xiaogj-web/private/enrollment-candidate-20261012-layout/blank.png --review projects/xiaogj-web/private/enrollment-candidate-20261012-layout/review.json --out projects/xiaogj-web/private/enrollment-candidate-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_enrollment_frontend --observed projects/xiaogj-web/private/enrollment-candidate-new.json --out projects/xiaogj-web/private/enrollment-candidate-result-new.json
```

最终工具验证：完整仓库 unittest 91 项通过，构建和类型检查通过，方法 preflight connected，`git diff --check` 通过。connected 仍只证明方法接线；本轮实际未运行原版 RSI 再部署。
