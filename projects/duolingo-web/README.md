# Duolingo 网页参考案例

这是私有 Codex App Rebuild 的第一个真实业务案例。网页只作为行为参考，Swift 教育基座使用原创名称、课程与素材。已交付首批四条跨端冻结验收与可运行 SwiftUI 选择课；完整学习流程和真实业务消融仍待完成。

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

首批四个场景已在网页和真实原生 UI 两侧通过，只覆盖选择、反馈和退出取消。完整 Goal 还要求退出确认、未完成进度丢弃、配对、错题重练、结算、恢复、课程进度、拼句、Swift 原生 UI 和真实业务消融；这些没有被缩减或宣称完成。

## 正式首批跨端验收

`spec-v1.1.json`、`fixture-v1.json` 与 `targets-v1.1.json` 是这一批的输入。原版使用线上西班牙语入门词汇，候选使用原创英语问候课；选择 correct/wrong 对应各自题面的明确映射，共享同一套场景和业务预期。线上题库无法注入，允许题面、选项顺序和课程内容不同，不能声称比较了相同题库。

先从仓库根构建当前产品，再运行实际原生验收：

```sh
swift build --package-path projects/education-swift --product LingoSeed
python3 -m workflows.rebuild.cli verify --workspace . --spec projects/duolingo-web/spec-v1.1.json --targets projects/duolingo-web/targets-v1.1.json --target candidate --frozen projects/duolingo-web/evidence/batch-v1.1.json --timeout 60 --max-seconds 600 --out artifacts/duolingo/candidate-new-01.json
```

当前原生驱动只启动已构建的二进制，调用者必须先构建当前源码；下一批完整修复循环还需把构建纳入验收命令，防止使用旧二进制。驱动通过自己启动的子进程 PID 查找 AXWindows，点击实际控件并返回可见属性，不访问其他应用。需要当前进程拥有辅助功能权限。

正式记录见 [原生迭代](evidence/NATIVE-V1-ITERATION.md)：v1 原生因快照超限而整体失败，v1.1 保留四项断言、重新确认原版与父批次后，两端均 4/4 通过；word-tiles 在这两批仍为 unknown。完整协议、冻结及参考/候选回执均在 evidence 中，覆盖报告为 `coverage-v1.1.json`。Swift 构建和启动见 [客户端说明](../education-swift/README.md)。
