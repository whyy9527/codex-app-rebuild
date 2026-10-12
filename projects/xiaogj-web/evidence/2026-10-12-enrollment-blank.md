# 新学员报名空表单：既有证据接入候选与共同前端模具

原生 Goal 继续全范围复刻。本轮使用历史中已实际导航到的新学员报名证据，不进行受前台窗口争用影响的原版 collect，也不声称新增了完整 RSI 世界。既有主 RSI 协议、冻结池、选中策略和成功再部署回执未改。

## 来源与边界

实际来源为 `private/reference/enrollment.ax.txt` 及配对 `enrollment.png`。当前 Codex 查看原图并核对表单 AX；截图为 2940×1666，包含未选择性别、空姓名／手机号／账号／身份证号、两项日期、收费项目空表以及右侧横向裁切。AX 中另有隐藏弹层内容，观察器只读取当前位置至报名入口之间的实际页面区段，不把隐藏内容推断为已访问分支。

租户账号后缀和两个日期从该 AX 提取到忽略的 `private/reference/enrollment-defaults.json`，时间字段采用保存文件的时间戳。它们是冻结观察默认值，日期跨日规则和账号生成方式仍未知；没有使用原版登录凭证作为候选数据。

## 实现与模具

候选新增报名空表单、共享前台业务侧栏、选择入口、十三列表头、空表提示及报名按钮。共享 Zod／ts-rest 契约连接 NestJS EnrollmentModule 与 React Query；没有观察数据时 API 返回 503，不填充模拟租户。

未观察的人员／课程等选择与报名提交只显示未完成提示，不生成订单、收费或报名成功结果。可编辑输入、默认状态和页面结构仍须实际候选验收。表单宽度与列宽按截图估计，不能当作已通过的几何测量。

`enrollment-frontend-contract.json` 包含共同文本、角色、输入值、未选中状态、实际截图尺寸和严格整图要求，并保留四组 pending。观察器只采集实际文本、控件值及图像，统一去除标签末尾冒号和图标码；图像前置状态复核绑定实际截图哈希。

历史原版模具结果 `private/enrollment-source-frontend-v2-result-20261012.json`：55 pass、4 not_run、0 fail。整图自比较仅验证这份固定参考及采样链，不证明任何候选视觉一致。

原生 CUA 本轮只读检查未返回可确认的任务标准窗口／候选标签，因此没有继续操作其他页面，没有实际候选 UI 采样。使用空 observations 明确记录候选未运行，`private/enrollment-candidate-not-run-result-20261012.json`：59 not_run；比较实际退出 1。不能把 HTTP 成功或构建成功代替此结果。

## 验证与复跑

Node 24.18.0、pnpm 11.15.1 下构建与类型检查通过；首页状态测试三项通过，仓库 unittest 91 项通过，`git diff --check` 通过。首次构建发现客户端非 200 分支响应类型为 unknown，已按显式 503 分支处理并重新构建通过。首页测试曾误在仓库根执行而找不到 package.json，改为案例目录执行后通过。

重启前核对实际项目 Node 进程和工作目录，仅重启所属 API。实际 `GET /api/enrollment/defaults` 的完整响应与本地观察快照精确相等，此项只证明数据链已运行。

原版事实采集复跑：

```sh
python3 -m projects.xiaogj-web.tools.enrollment_frontend_observations --ax projects/xiaogj-web/private/reference/enrollment.ax.txt --image projects/xiaogj-web/private/reference/enrollment.png --review projects/xiaogj-web/private/reference/enrollment-review-20261012.json --out projects/xiaogj-web/private/enrollment-source-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/xiaogj-web/rebuild.json --command compare_enrollment_frontend --observed projects/xiaogj-web/private/enrollment-source-new.json --out projects/xiaogj-web/private/enrollment-source-result-new.json
```

候选获得真实同状态捕获后用同一观察器及同一比较入口，另提供相应哈希的真实截图复核。仍需在浏览器可持续控制后完成原版分支探针、完整池策略比较、选中策略实际再部署，以及报名页两端共同业务和前端 E2E。未改变用户目标，原生 Goal 保持 active。
