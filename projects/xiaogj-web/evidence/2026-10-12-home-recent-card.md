# 近期开班卡片：实际内容与添加草稿回放

上一轮完成首页图标消费修复及配置回放，本轮继续全范围 Goal。尝试独立 IAB 入口以解决原版前台争用，工具明确返回 Browser is not available: iab。没有重启 Edge collect，没有把缺少浏览器空闲安排当作用户授权或完成；现有 RSI 协议和完整再部署回执保持原样。

## 原版来源与实现

`private/reference/2026-10-12-home/recent-card.ax.txt` 实际包含最近30天开班卡片、摘要、四列表头和一行班级数据。`recent-card-draft.ax.txt` 是添加后的弹窗差分，实际只剩新手指南及一个添加按钮。原版没有这张卡片的配对截图，不能从 AX 推断视觉通过。

新增 `home_recent snapshot` 将真实卡片事实提取到忽略的 `private/reference/recent-classes.json`。观测时间字段使用保存文件的时间戳；保留冻结数据，不推断跨日刷新规则。共享 Zod／ts-rest 契约连接 NestJS HomeController 的 recent-classes API 与 React Query。候选新增卡片的实际表格和已观察的查看全部班级入口；缺少快照时返回 503，不生成模拟班级。

查看全部班级的后续行为尚未观察，当前点击只提示未完成，不能算业务实现完成。原有新手指南仍未完成；没有用原创内容代替原版。

## 实际候选旅程与比较

Node 24.18.0、pnpm 11.15.1 构建及类型检查通过后，核对所属 API 的实际进程与工作目录，只重启项目 API。实际 GET 响应与本地观察快照完整相等，但此项不代替 UI 验收。

在已知候选 URL 守卫下刷新首页，进入编辑、打开添加卡片、点击近期开班对应添加按钮。实际弹窗只剩新手指南；关闭后采集卡片 AX，再滚动两页并采集实际截图。当前 Codex 实际查看截图确认表格已显示。最后取消首页编辑，完整 AX 确认自定义首页入口恢复，近期开班卡片不再出现，没有保存偏好。

所有候选事实在 `private/home-recent-candidate-20261012`。添加后的弹窗原始文件为 `added-modal.ax.txt`，为共同观察器另存同字节的 `recent-card-draft.ax.txt`，没有改写内容。取消返回只验证了候选实际行为；原版该完整连续旅程尚未重跑。

共同内容比较器从实际两端 AX 读取摘要、表头和全部单元格，精确比较三项：3 pass。另在私有副本故意修改一个实际单元格，得到 2 pass、1 fail，实际退出 1；原始捕获和原版来源均保持完整，证明比较器确实能检测数据差异。

共同前端契约包含卡片标题、摘要和表头，以及添加后仅剩的新手指南名称／描述／选项集合。原版固定事实与候选分别得到 10 pass、3 not_run。未运行项显式保留原版缺失截图、导航／隐藏及其他输入、保存／持久化／权限／日期规则；这些结果不证明布局、字体、图标或业务持久化一致。

## 验证及复跑

构建、类型检查、首页状态测试三项通过。构建产物为 `index-Ae1pyvtE.css` 与 `index-Bwunml2V.js`，实际 UI 经 Vite 刷新消费当前实现。完整仓库 unittest 91 项、方法 preflight、`git diff --check` 通过；preflight connected 仅证明已有方法接线，不能证明新一轮原版部署成功。

实际连续旅程见 `home-recent-scenarios.json`。内容比较：

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_recent_classes --observed projects/xiaogj-web/private/home-recent-candidate-20261012/recent-card.ax.txt --out projects/xiaogj-web/private/home-recent-content-new.json
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-recent-candidate-20261012 --out projects/xiaogj-web/private/home-recent-frontend-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_recent_frontend --observed projects/xiaogj-web/private/home-recent-frontend-new.json --out projects/xiaogj-web/private/home-recent-frontend-result-new.json
```

原版探索阻塞仍在；仍须获得可持续控制的目标后实际 RSI collect／完整池 replay／选中策略再部署，再扩充两端共同业务和前端验收。Goal 保持 active，未缩小全范围目标。
