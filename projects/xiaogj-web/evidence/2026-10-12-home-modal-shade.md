# 弹窗背景偏亮的共同原因与实际复验

本轮项目 preflight 为 connected，已完成主 RSI 链不变。原版新分支再部署仍受前台窗口控制条件限制；本轮修复已有配对参考中的产品差异，不宣称完成新的原版探索。

## 证据与修改

当前 Codex 查看原版 `private/reference/2026-10-12-home/customize.png` 与 `quick-config.png`，对两个历史实际捕获中相同背景位置的 15×15 像素块求 RGB 中位数。五处原始像素比值约 0.496–0.505，白色卡片背景 255→127，支持黑色遮罩约 50% 的判断。这是对实际捕获的测量，不把整图差异归因于一个参数，也未改变 ICC 归一化或验收阈值。

候选 `.modal::backdrop` 原为 `#0006`（40%），现改为明确的 `rgb(0 0 0 / 50%)`。四位颜色 `#0008` 实际为 8/15，不能精确表达 50%；中间构建曾捕获这个临时值，已重新构建并检查最终产物为 `#00000080`，该中间产物不作为最终 UI 证据。

## 构建和真实操作

Node 24.18.0、pnpm 11.15.1 构建、类型检查、三个首页状态测试通过。最终再次构建的产物为 `index-Cyr7KIT0.css`、`index-C70gQXH3.js`，实际候选刷新后回放配置旅程。

CUA 实际进入首页编辑，保存无弹窗基线，打开快捷配置并保存 AX／截图，粘贴邀约搜索，取消；滚动到数据概览配置入口，打开后向上滚动背景恢复首页顶部，保存指标弹窗 AX／截图；取消后打开添加卡片，再关闭并取消首页编辑。返回事实确认自定义首页入口恢复、保存按钮消失。捕获与哈希绑定复核在 `private/home-modal-shade-20261012`。没有保存原版或候选偏好。

当前 Codex 实际查看两张最终候选截图。候选同位置背景像素比值约 0.496–0.502，与原版测量一致。两端存在素材、字形、控件、弹窗几何与指针差异，不能据此称整图通过。

## 共同 E2E

沿用未修改的 `home-configuration-contract.json`，结果 26 pass、2 fail、4 not_run。快捷配置 RGB 平均绝对差由上一轮约 (18.536,17.813,16.242) 降至 (9.159,8.647,7.513)，指标配置由 (16.296,15.867,15.328) 降至 (3.052,2.809,2.769)。两项严格整图比较继续失败退出；没有遮罩、容差或放宽断言。

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-modal-shade-20261012 --out projects/xiaogj-web/private/home-modal-shade-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_configuration --observed projects/xiaogj-web/private/home-modal-shade-new.json --out projects/xiaogj-web/private/home-modal-shade-result-new.json
```

本轮只修改案例 CSS，未改仓库工具，未重复完整 Python 测试。Goal 仍 active，完整业务、前端、鉴权、权限、持久化及未知分支验收未完成。
