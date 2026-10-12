# 首页配置共同模具、实际回放和 SVG 消费修复

上一轮报名回放已完成具体进展。本轮依据已有首页配置证据，补验尚未复验的快捷配置、名称搜索、指标配置和添加卡片入口。没有启动原版 collect 或第二套续跑器；现有 RSI 冻结池和已完整再部署的主详情协议未改。

## 来源与共同要求

原版参考为 `private/reference/2026-10-12-home` 中 quick-config、quick-search-pasted-full、overview-config 和 add-card 的实际 AX，以及前两种配置弹窗的配对截图。当前 Codex 实际查看原版和候选截图；两端配置截图均为 2940×1666。添加卡片原版只有 AX 差分，观察器只读取其中增加／变化的节点，不补造完整旧树或截图。

`home-configuration-contract.json` 冻结七项已选功能的顺序、空搜索输入、粘贴邀约后的输入值及唯一结果、四个指标的角色／可用／勾选状态、已选数量、添加首页卡片标题、截图尺寸及严格整图比较。四项 pending 保留目录截取、拖动与其他输入、添加行为、保存及持久化等未知；不以当前菜单或视口定义需求全集。

源侧结果 `private/home-configuration-source-diff-result-20261012.json`：28 pass、4 not_run。原版整图自比较只验证固定参考及采样链，不证明候选一致。连续旅程复跑步骤见 `home-configuration-scenarios.json`；历史分状态来源不冒充原版新执行的连续旅程。

## 候选实际失败与修正

经已知候选 URL 守卫，从首页进入编辑模式，打开快捷配置并实际粘贴邀约，取消后进入指标配置和添加卡片，再取消首页编辑。没有保存原版或候选偏好。首次完整事实在 `private/home-configuration-candidate-20261012`，共同结果 24 pass、4 fail、4 not_run。

实际截图暴露首页和快捷配置图标整体空白。资源请求确实 200，文件确有 183 个 symbol，但 DOM 抽取出的 SVG 根未带 SVG 命名空间，不能作为有效外部符号资源消费。新增 `prepare_home_symbols` 保留原始文件，将规范化结果写到新的忽略路径；直接验证全部节点属性与文本相同、183 个符号保留且节点进入 SVG 命名空间。相同输出可幂等复跑，已有不同输出不覆盖。没有上传或提交原版媒体。

候选改为消费规范化的外部 SVG。构建后刷新实际页面，逐张查看截图确认图标恢复。另修正添加弹窗标题、已选数量的单个文本节点、配置弹窗头部尺寸和数据概览的专用宽度／行高；新增专用类不将指标尺寸套到其他弹窗。

## 实际复验与剩余差异

Node 24.18.0、pnpm 11.15.1 构建及类型检查通过后，同样从首页执行上述旅程，实际捕获到 `private/home-configuration-candidate-20261012-fixed`，最后取消编辑并确认自定义首页入口恢复。当前 Codex 查看两个配对截图后写入哈希绑定的复核，使用同一契约比较：26 pass、2 fail、4 not_run。两项 fail 均为严格整图，默认值和已覆盖状态断言通过。

图像 RGB 平均绝对差：快捷配置约 (23.783,22.195,19.622) 到 (20.283,19.219,17.587)；指标配置约 (38.241,32.953,31.880) 到 (18.985,17.917,17.188)。背景首页编辑布局、弹窗间距、字体、控件与动态指针仍有差异，不能以这些数值下降声明 1:1 完成。

构建产物为 `index-Bdlie37I.css` 和 `index-Bn-7mnpd.js`；实际 UI 经运行中的 Vite 刷新读取当前实现。完整仓库 unittest 91 项、首页状态测试三项通过，方法 preflight connected，`git diff --check` 通过。构建曾误在仓库根运行而找不到 package.json，已在案例目录重新执行通过；Python 始终从仓库根执行。

## 复跑入口

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command prepare_home_symbols
python3 -m projects.xiaogj-web.tools.home_observations --captures projects/xiaogj-web/private/home-configuration-candidate-20261012-fixed --out projects/xiaogj-web/private/home-configuration-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_home_configuration --observed projects/xiaogj-web/private/home-configuration-new.json --out projects/xiaogj-web/private/home-configuration-result-new.json
```

全范围 Goal 继续 active。原版窗口安排仍待确认，本轮没有完成原版新分支的实际 RSI 再部署，也没有验证保存、鉴权或业务持久化。
