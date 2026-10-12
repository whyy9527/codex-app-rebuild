# 快捷操作新增草稿共同验收

本轮 preflight connected；已完成的主 RSI 链不变，没有启动原版新 collect 或将本轮候选回放冒充胜出策略再部署。

## 来源与契约

原版 `private/reference/2026-10-12-home/quick-added-full.ax.txt` 为完整实际捕获：七项默认功能后追加邀约查询，搜索为空，目录中邀约查询为 disabled。该文件证明当时的八项草稿状态，没有配对截图或完整动作回执，不推断先搜索再添加是否自动清空、取消恢复或保存规则。

新增 `home-shortcut-added-contract.json` 冻结标题、八项精确顺序、空搜索、目录选项角色及禁用状态，并保留视觉和其他输入两项 pending。观察器加入 quick-added 状态和实际目录按钮的角色／可用属性，未填期待值。source 转换及共同比较为 5 pass、2 not_run，不称本轮原版新旅程通过。

## 候选实际操作

使用上一轮已构建且无产品改动的候选，CUA 实际刷新、回到顶部、进入首页编辑、打开快捷配置，保存初始事实，点击空搜索目录中的邀约查询并保存八项 AX／截图。首次使用旧编号被原生工具拒绝，未完成动作；随后重新读取实际节点并执行成功。当前 Codex 查看候选八项截图；原版无配对图片，视觉保持未运行。

实际捕获在 `private/home-shortcut-added-candidate-20261012`。使用同一观察器及契约，候选也是 5 pass、2 not_run。目录选项变禁用和八项顺序通过共同比较；未修改产品以追求计数。

随后实际取消快捷配置，重新打开并捕获 quick-reopened，再取消配置与首页编辑。候选三次实际选择数为 7→8→7，前七项顺序保留，取消后完整恢复；原始 AX 文件哈希及逐项选择在 `candidate-draft-return.json`。该回执明确标记 candidate-only，原版取消行为为 unknown，未写入共同通过结果。返回首页 AX 确认自定义首页入口恢复、保存按钮消失。未保存偏好。

## 验证

完整 unittest 91 项通过，git diff --check 通过。仅修改观察器、项目入口、共同契约与证据，没有产品代码改动，因此沿用上一轮构建产物 `index-DyWhWCfO.css`、`index-B9d_9HRK.js`，没有声称本轮重建。完整动作及来源边界由 `home-shortcut-added-scenarios.json` 记录。

```sh
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-shortcut-added-candidate-20261012 --out projects/xiaogj-web/private/home-shortcut-added-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_shortcut_added --observed projects/xiaogj-web/private/home-shortcut-added-new.json --out projects/xiaogj-web/private/home-shortcut-added-result-new.json
```

pending 继续失败退出。全范围 Goal 仍 active；原版未知分支、实际新 RSI 再部署及完整产品验收未完成。
