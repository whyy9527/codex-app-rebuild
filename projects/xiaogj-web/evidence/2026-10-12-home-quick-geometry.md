# 快捷配置弹窗几何修正及实际复验

本轮 preflight connected。原版新分支 RSI 再部署仍待前台控制条件，已完成主链不变；本轮针对已有原版证据的候选视觉失败修产品，没有重新定义目标或改比较标准。

## 观察与修改

原版来源 `private/reference/2026-10-12-home/quick-config.png`。当前 Codex 查看两端截图，测量蓝色连通区域：原版标题栏约 x295.5、y140.5、宽879、高41点；上一版候选约 x295.5、y144.5、宽878.5、高38点。该色域测量是截图中的蓝色内部区域，不冒充 DOM 完整几何。

快捷弹窗专用标题改为 16px／22px，底栏 padding 从 16 调为 10 点，按钮设最小宽60点、间距24点，提示文字灰色。弹窗在当前视口按 8vh 顶距定位；内容区仍高516点，顶部留白减少4点。搜索标题原先继承 h4 的上下外边距，把32点输入行撑高；专用规则去掉该外边距，目录分组标题按已观察尺寸调整为13px／20px。修改限定于快捷弹窗，未将此布局套到指标或其他弹窗；其他视口仍须原版同状态验证。

## 实际回放与结果

Node 24.18.0、pnpm 11.15.1 构建、类型检查和三个首页状态测试通过，产物 `index-CVLNqvRd.css`、`index-Be-UqClx.js`。实际 CUA 刷新候选、回到首页顶部、进入编辑及快捷配置，保存截图／AX；粘贴邀约搜索并取消，再进入指标配置、恢复背景顶部并保存；取消后打开添加卡片，关闭并取消首页编辑。最后 AX 确认自定义首页入口恢复且保存按钮消失。捕获在 `private/home-quick-geometry-20261012`，没有保存偏好。

当前 Codex 实际查看两张配对候选截图，保存哈希绑定复核。沿用未修改的共同契约：26 pass、2 fail、4 not_run。快捷配置 RGB 平均绝对差由 (9.159,8.647,7.513) 降至 (2.455,2.335,2.279)，指标配置约 (3.052,2.809,2.769)。两项严格整图仍失败，字体、控件、素材和动态指针差异保留；数值下降不能证明 1:1 完成。

本轮仅修改案例 CSS，未改仓库工具，未重复完整 Python 测试。git diff --check 通过。

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-quick-geometry-20261012 --out projects/xiaogj-web/private/home-quick-geometry-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_configuration --observed projects/xiaogj-web/private/home-quick-geometry-new.json --out projects/xiaogj-web/private/home-quick-geometry-result-new.json
```

严格比较失败退出保留，全范围 Goal 仍 active。
