# Duolingo 网页参考案例

这是私有 Codex App Rebuild 的第一个真实业务案例。网页只作为行为参考，Swift 教育基座使用原创名称、课程与素材。当前已完成首批观察，原版适配处于可行性验证；Swift 客户端和跨端冻结验收尚未交付。

## 现有产物

- [实际观察与范围](evidence/2026-10-10-observations.md)：正常答题、错误反馈、配对、错题重练、退出与刷新。
- [观察计划](OBSERVATION-PLAN.md)：仍未覆盖的拼句和其他边界。
- `spec.draft.json`：单一业务动作与预期草案；未冻结，不能视为已确认参考验收。
- `fixture.json`：公共初始状态与动作语义；不能注入 Duolingo 后端。
- `original-adapter.mjs`：真实 Playwright UI 驱动，stdin 接收操作/动作，stdout 输出 `APP_REBUILD_RESULT`。不接收预期值，不自报通过。
- `probe-reference.py`：执行草案的单场景原版可行性检查，复用共享断言函数，保存启动、重置、场景、再次重置和停止的记录。输出种类为 `reference_feasibility`，不是主验收引擎接受的冻结回执。
- [四条原版可行性结果](evidence/REFERENCE-PREFLIGHT.md)：均通过，未作为冻结回执。
- [本机 Swift 环境](ENVIRONMENT.md)：编译能力与原生 UI 验收限制。

## 安装与运行

需要 Python 3.11+、Node.js 20+、可访问 Duolingo 的网络。以下命令从仓库根执行：

```sh
npm ci --prefix projects/duolingo-web
cd projects/duolingo-web
npx playwright install chromium
cd ../..
python3 projects/duolingo-web/probe-reference.py --scenario choice-wrong --out projects/duolingo-web/evidence/local-choice-wrong-01.json
```

`--scenario` 可选 `choice-empty`、`choice-correct`、`choice-wrong`、`exit-cancel`。输出路径必须是仓库内新文件，不覆盖旧失败。单次适配命令上限 180 秒，最多五个生命周期/场景命令；引导最多 20 步，每步等待可操作状态最多 30 秒。需要观察窗口时设置 `REBUILD_HEADED=1`。

每条命令拥有并关闭自己的临时浏览器。`start/reset` 实际导航到课程入口；`scenario` 从新的访客上下文经公共引导建立题目初态。它不会恢复既有账号，不保存 cookies/storageState，不重置远程服务，也不保证服务端随机选项顺序。这个重置策略只适合首批独立场景；课中刷新、连续课程和完成后持久化的场景需要同一命令内维护上下文并另行验证。

适配器依据当前可操作选项所属题目容器定位，不读取全页最后一个标题。继续后等待旧引导组选项消失，避免动画残留。未知题型或词义映射停止并保存当前 AX 证据，不猜答案。首次缺少 Playwright 浏览器的失败保留在 `reference-probe-01.jsonl`；恢复安装后的初态探针在 `reference-probe-02.jsonl`。

## 推进门槛

先完成原版可重复执行验证与原生动作适配设计，建立完整 reference/candidate 配置，使用主验收入口重新运行并冻结。可行性记录不能直接交给冻结步骤。已观察但尚未转为场景的行为仍属待验收；拼句保持 unknown。后续独立遗漏发现必须寻找初始观察以外的缺口，不能把本轮已看到的错题重练事后当作补充探索收益。

首批四个场景只覆盖选择、反馈和退出取消。完整 Goal 还要求退出确认、未完成进度丢弃、配对、错题重练、结算、恢复、课程进度、拼句、Swift 原生 UI 和真实业务消融；这些没有被缩减或宣称完成。
