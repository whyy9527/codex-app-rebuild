# Duolingo 网页参考案例

> 2026-10-10 更正：下文是历史局部验收记录，不能证明 1:1 复刻完成。用户指出探索不足、前端需求未进入 E2E、自行增加替代内容限制。现已撤回产品完成结论；当前原生 Goal 要求修正探索与模具。原始测试与失败证据保留。


这是私有 Codex App Rebuild 的第一个真实业务案例。当前目标是网页到 Swift 的 1:1 复刻；此前原创课程与素材只是历史实现，不能作为复刻标准。已交付12条跨端冻结验收与可运行 SwiftUI 两课时教育基座；真实多阶段模型续跑已有[一次完整可行性证据](../model-pipeline/README.md)；[四组业务消融](../business-ablation/REPORT.md)已完成，均公开12/12与留出2/2、另1未知；N=1未观察到通过率收益。

当前复现入口是文末的冻结 v2 命令。以下草案和首批运行记录保留探索历史；它们的范围与限制不代表当前 v2 尚未实现这些功能。回执证明记录时的源码与输入，后续代码变化需要重新验收。

## 早期探索产物

- [实际观察与范围](evidence/2026-10-10-observations.md)：正常答题、错误反馈、配对、错题重练、退出与刷新。
- [观察计划](OBSERVATION-PLAN.md)：首批探索计划与当时未知的拼句/边界；当前确认范围见文末 v2。
- `spec.draft.json`：单一业务动作与预期草案；未冻结，不能视为已确认参考验收。
- `fixture.json`：公共初始状态与动作语义；不能注入 Duolingo 后端。
- `original-adapter.mjs`：真实 Playwright UI 驱动，stdin 接收操作/动作，stdout 输出 `APP_REBUILD_RESULT`。不接收预期值，不自报通过。
- `probe-reference.py`：执行草案的单场景原版可行性检查，复用共享断言函数，保存启动、重置、场景、再次重置和停止的记录。输出种类为 `reference_feasibility`，不是主验收引擎接受的冻结回执。
- [四条原版可行性结果](evidence/REFERENCE-PREFLIGHT.md)：均通过，未作为冻结回执。
- [本机 Swift 环境](ENVIRONMENT.md)：编译能力与原生 UI 验收限制。

## 安装与重放早期探索

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

## 早期推进门槛与范围

先完成原版可重复执行验证与原生动作适配设计，建立完整 reference/candidate 配置，使用主验收入口重新运行并冻结。可行性记录不能直接交给冻结步骤。已观察但尚未转为场景的行为仍属待验收；拼句保持 unknown。后续独立遗漏发现必须寻找初始观察以外的缺口，不能把本轮已看到的错题重练事后当作补充探索收益。

首批四个场景只覆盖选择、反馈和退出取消。当时后续要求的退出确认、进度丢弃、配对、错题重练、结算、恢复和拼句，现已进入文末 v2 的跨端验收。真实业务消融与[整体审计](../../docs/DELIVERY-AUDIT.md)已完成；首批通过仅是历史阶段证据。

## 正式首批跨端验收

`spec-v1.1.json`、`fixture-v1.json` 与 `targets-v1.1.json` 是这一批的输入。原版使用线上西班牙语入门词汇，候选使用原创英语问候课；选择 correct/wrong 对应各自题面的明确映射，共享同一套场景和业务预期。历史测试允许题面、选项顺序和课程内容不同，因此不能声称比较了相同题库；这不授权当前 1:1 交付保留这些差异。

先从仓库根构建当前产品，再运行实际原生验收：

```sh
swift build --package-path projects/education-swift --product LingoSeed
python3 -m workflows.rebuild.cli verify --workspace . --spec projects/duolingo-web/spec-v1.1.json --targets projects/duolingo-web/targets-v1.1.json --target candidate --frozen projects/duolingo-web/evidence/batch-v1.1.json --timeout 60 --max-seconds 600 --out artifacts/duolingo/candidate-new-01.json
```

v1.1 原生驱动只启动已构建的二进制，调用者必须先构建当前源码；该阶段未纳入构建的限制，已由 v2 构建包装器补齐。驱动通过自己启动的子进程 PID 查找 AXWindows，点击实际控件并返回可见属性，不访问其他应用。需要当前进程拥有辅助功能权限。

正式记录见 [原生迭代](evidence/NATIVE-V1-ITERATION.md)：v1 原生因快照超限而整体失败，v1.1 保留四项断言、重新确认原版与父批次后，两端均 4/4 通过；word-tiles 在这两批仍为 unknown。完整协议、冻结及参考/候选回执均在 evidence 中，覆盖报告为 `coverage-v1.1.json`。Swift 构建和启动见 [客户端说明](../education-swift/README.md)。

## 补充探索增量 v1.2

首批通过后，实际探索发现初始场景未覆盖“提交前从错误选项改选正确选项”。真实证据、原版和原生 UI 的五项通过回执、父批次关系及覆盖报告见 [增量准备记录](evidence/V2-PREPARATION.md)。`spec-v1.2.json` / `targets-v1.2.json` / `evidence/batch-v1.2.json` 是该阶段的冻结批次；word-tiles 在该批仍为 unknown。客户端已有改选能力，这次没有产品代码修改，不能声称修复收益。

## 完整学习批次 v2

最新冻结输入为 `spec-v2.json`、`fixture-v2.json`、`targets-v2.json` 和 `evidence/batch-v2.json`，父批次为 v1.2。参考端 `reference-v2-02.json` 与原生端 `candidate-v2-01.json` 均12/12通过，完整性检查通过；覆盖报告为 `coverage-v2-01.json`。历史草案与失败没有覆盖。

12条包括空答案、正确/错误选择、退出取消、改选、配对完成、正确/错误拼句、拼句撤回、错题重练、完成返回及刷新、第二课退出丢弃并重开。候选题库为原创两课时。线上原版不能注入该题库，比较的是共享动作语义与业务断言，不是相同内容或后端状态。

```sh
python3 -m workflows.rebuild.cli verify --workspace . --spec projects/duolingo-web/spec-v2.json --targets projects/duolingo-web/targets-v2.json --target candidate --frozen projects/duolingo-web/evidence/batch-v2.json --timeout 360 --max-seconds 1800 --out artifacts/duolingo/candidate-v2-new-01.json
```

参考确认可使用相同 spec / targets、`--target reference`，输出新文件。原版运行需要网络和 Playwright Chromium。v2 参考场景在同一临时浏览器上下文内完成连续学习/刷新；命令间仍是新访客，不恢复账号或重置服务器。未知词义/题型停止并保留证据。

v2 的 candidate 命令 `build-native.py` 先构建当前源码并记录源码/二进制摘要，再由 v3 Swift AX 驱动操作自有子进程窗口。与早期直接运行二进制的 v1.1 命令不同，它包含构建，不会把旧二进制算作当前源码通过。须有辅助功能权限。参考与候选适配器只接收动作、不接收预期，统一引擎应用断言。

[学习批次记录](evidence/V2-PREPARATION.md)保留驱动失败、冻结和实现顺序。旧候选不能读取新题库，baseline 12项 unavailable；首次 Swift 构建缺少 import，随后构建通过。两者都不是产品业务 fail→pass。新实现首次完整原生12项通过，不能据此声称反馈循环或模型的收益。

六个实际界面及方法见 [界面检查](evidence/V2-DELIVERY.md)。检查涉及课程路径、选择、配对、解锁、拼句及反馈；截图不证明学习效果或模型能力。候选端 `{}` / null 进度误接受已单独复现并修复，冻结的五项存储启动检查通过；共享 v2 12项与 v1.2 5项回归通过（candidate-v2-02.json / candidate-v1.2-02.json）。见 [存储修复](evidence/PROGRESS-REPAIR.md)，未修改共享 Duolingo 断言。

本轮最终复验：主产品原生12/12、核心5项及Python43项通过，当前回执和全部八项边界见[交付审计](../../docs/DELIVERY-AUDIT.md)。

## 当前统一产品验收

```sh
python3 projects/duolingo-web/verify-product.py --out artifacts/product-new
python3 -m capabilities.rebuild.discovery --history projects/duolingo-web/evidence/exploration-v4/history.json --out artifacts/frontier-new.json
```

产品入口执行冻结业务 E2E，再启动隔离 Swift 子进程采集主页/More 的 AX 文本，执行 `frontend-v4.json` 断言。任一失败或尚未验证，统一结果即失败。当前真实基线：业务12/12通过，原版10项文案在候选均失败，另3项未验证，整体失败；原版同一组10项均通过。AX 文本只验证可访问文案，不能证明视觉可见或 1:1；视觉、音色及悬停检查仍待实现，不用文案检查冒充它们。

[探索与差异记录](evidence/exploration-v4/README.md)保存真实来源、待探索分支和本轮失败。
