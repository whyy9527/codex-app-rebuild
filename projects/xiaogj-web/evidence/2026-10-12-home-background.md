# 首页背景弹层与新共同模具

本轮 preflight connected，主 RSI 池及评价未变。原版新分支的实际再部署仍待前台窗口安排；本轮消费已有历史截图，修复已知产品差异并扩充共同模具。

## 来源与实现

当前 Codex 查看原版 `private/reference/2026-10-12-home/background-options.png`。可见展开态为三列六项缩略图，弹层与首页右侧按钮边缘对齐，标题和说明同行；荷塘清韵有蓝色选中边框。候选原先为两列文字块，图片作为整个按钮背景，位置也未与右边缘对齐。

候选改为独立预览区域、三列布局、约 470 点宽、标题说明同行，并显示当前选中项边框。山水预览使用既有忽略路径的实际资源，纯色／渐变预览根据截图近似实现；仍需严格图像比较，不能把近似资源当成完成。没有修改背景选择或持久化规则，也没有在原版选择或保存背景。

`home-background-contract.json` 包含截图来源的标题、说明及六组可见名称／描述、实际采样尺寸、严格整图和两项 pending。原版缺 AX，不能由截图推断其角色、键盘或关闭行为。`home-background-scenarios.json` 保存同状态展开与关闭步骤及来源限制，`rebuild.json` 增加 compare_home_background 入口。

## 观察器发现与实际回放

实际候选 AX 将带 aria-pressed 的选项呈现为 toggle button。原观察器只读取 button 等节点，漏掉完整选项名称；修正正则以读取实际 toggle button，不拆分或填充期待文字。未改 RSI 的固定发现／评价输入或评分协议。

构建后 CUA 实际刷新首页、回到顶部、点击换背景并采集 AX／截图。首次捕获在 `private/home-background-candidate-20261012`，实际查看发现上下间距仍大于参考；调整标题底距与名称／描述行距后再次构建并实际刷新复跑，最终捕获在同名 `-fixed` 目录。当前 Codex 查看最终配对截图，保存哈希绑定的状态复核；再次点击换背景关闭，AX 确认标题消失。未选择或保存背景。

共同结果 9 pass、1 fail、2 not_run：标题、说明、六组选项文字及采样尺寸通过；严格整图失败，RGB 平均绝对差约 (3.100,2.817,2.761)。两项 pending 保留原版 AX 与交互、持久化未知。原版历史图片不是本轮重新执行的连续旅程，候选关闭通过也不冒充原版关闭通过。

## 验证与入口

Node 24.18.0、pnpm 11.15.1 构建、类型检查及三个首页状态测试通过；最终仅调整 CSS 间距后重新构建，产物 `index-DyWhWCfO.css`、`index-B9d_9HRK.js`。观察器最终修改后完整 unittest 91 项通过，git diff --check 通过；没有修改或提交其他案例工作。

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-background-candidate-20261012-fixed --out projects/xiaogj-web/private/home-background-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_background --observed projects/xiaogj-web/private/home-background-new.json --out projects/xiaogj-web/private/home-background-result-new.json
```

整图失败退出保留。全范围 Goal 继续 active，未知业务和原版实际新分支 RSI 再部署仍未完成。
