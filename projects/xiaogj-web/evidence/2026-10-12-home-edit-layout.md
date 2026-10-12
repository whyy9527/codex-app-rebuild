# 首页编辑布局与配置共同复验

本轮先运行项目 preflight，结果 connected；接线结果不证明完整产品验收。主 RSI 历史池与评价不变。依据已有原版配对截图修正已知前端失败，没有把候选回放冒充原版新 collect／再部署。

## 来源与实现

当前 Codex 实际查看 `private/reference/2026-10-12-home/quick-config.png`、`overview-config.png` 及上一版候选截图。原版首页编辑工具条居中悬浮，宽约 860 点、高 80 点、底距 24 点，恢复默认与取消／保存在右侧；候选原来铺满底部。原版卡片显示虚线边框，拖动栏高约 48 点，编辑时自定义首页入口消失。

实现加入仅在草稿期间使用的 home-editing 类，修正卡片边框、拖动栏、隐藏／配置按钮、工具条位置与按钮顺序，并按已观察状态隐藏自定义首页入口。指标弹窗调整标题字号、复选框及行内间距、底部按钮宽度与间距。没有改动保存、权限或持久化规则；这些原版分支仍待观察。

## 实际验证

Node 24.18.0、pnpm 11.15.1 构建、类型检查和三个首页状态测试通过，产物 `index-BXHOqjES.css`、`index-CIkqG5wL.js`。本轮仅改案例 React/CSS，没有修改仓库工具，未重复运行完整 Python 测试。

构建后通过 CUA 在实际候选刷新，回到首页顶部，进入编辑、打开快捷配置、粘贴邀约搜索、取消，再打开指标配置、取消、打开添加卡片、关闭，最后取消编辑。捕获在 `private/home-edit-layout-20261012`；返回 AX 确认自定义首页入口恢复且保存按钮消失。指标配置按钮初次因不在可见区域未生效，随后实际滚动到入口并点击；弹窗打开后实际向上滚动背景恢复顶部。没有伪造捕获或保存首页偏好。

当前 Codex 查看实际两种配对截图后写入哈希绑定的复核。共同契约未改，结果 26 pass、2 fail、4 not_run，两项失败为严格整图。快捷配置 RGB 平均绝对差由上一版约 (20.283,19.219,17.587) 降至 (18.536,17.813,16.242)，指标配置由 (18.985,17.917,17.188) 降至 (16.296,15.867,15.328)。工具条与卡片编辑几何更接近参考，仍保留弹窗、字体、颜色、素材和动态指针差异；数值下降不等于视觉验收通过。

## 复跑

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-edit-layout-20261012 --out projects/xiaogj-web/private/home-edit-layout-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_configuration --observed projects/xiaogj-web/private/home-edit-layout-new.json --out projects/xiaogj-web/private/home-edit-layout-result-new.json
```

严格比较继续失败退出。全范围 Goal 仍未完成；未知业务、原版新分支 RSI 再部署及全范围业务／前端 E2E 继续待验收。
