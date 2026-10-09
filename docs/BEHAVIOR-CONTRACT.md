# 共享业务规格与适配协议

`capabilities/rebuild/contracts.py` 拥有场景断言；平台适配器只执行动作并返回观察。浏览器与原生客户端使用同一份场景、前置状态及断言，分别驱动界面。协议机制与产品证据分开；Duolingo 案例已用真实浏览器和 macOS 辅助功能驱动实际 SwiftUI 客户端，首批四条共享场景通过，见案例记录。

## 输入

从显式 workspace 读取两个相对路径 JSON 文件；不默认读取项目或账号。`schema_version` 当前为 1。

规格包含：

- `revision`、`parent_digest`：第一批 parent 为 null，增量批次引用真实冻结父批次的规范化 JSON SHA-256。
- `source`：kind 为 `original_online` 或 `local_reference`，填写 version、date、scope、reset_limitations。不能把本地替身声明为线上原版。
- `fixture`：共同夹具的相对文件路径。夹具包含实际 `data` 和非空的 `initial_state`；后者是重置必须返回的可观察状态断言。
- `behaviors`：唯一 id、description、discovery。observed 必须附本地 evidence 文件路径；decision 必须给 rationale；unknown 不允许附已断言步骤。
- 已知行为包含 `precondition` 对象和非空 `steps`。每步有非空 `action`、`expect` 对象。适配器收到动作，统一引擎检查 expect。

行为片段示例仅说明格式，不是 Duolingo 的已观察规则：

```json
{
  "id": "complete_lesson",
  "description": "完成后保留进度",
  "discovery": "decision",
  "rationale": "待业务观察后确认或调整的教育基座决策",
  "precondition": {"lesson": "intro", "completed": false},
  "steps": [
    {"action": {"type": "finish_lesson"}, "expect": {"completed": true}},
    {"action": {"type": "restart"}, "expect": {"completed": true}}
  ]
}
```

目标配置的 `targets` 必须同时声明 reference 和 candidate。每侧声明 kind、layer、command 和非空 acceptance_paths。reference.kind 必须与 source.kind 一致；candidate.kind 必须为 candidate。layer 可为 browser_ui、native_ui、core 或 test_double，不能把后两者作为 UI E2E 证据。

`command` 是可信本地 argv，不经 shell 展开。`acceptance_paths` 声明驱动器、断言依赖和配置；规格、夹具及证据自动加入保护。不要把可编辑的 candidate 产品实现放入验收保护，否则修改实现也会破坏冻结批次。所有声明必须实际存在；目录检查新增、删除与修改。

## 适配器协议

每次命令从 stdin 读取 JSON，请求 operation 为 start、reset、scenario 或 stop；共同 fixture 随请求传入。适配器负责可重复启动、真实数据准备、环境重置和登记资源清理。命令返回后若保留服务进程，必须由 stop 显式清理；当前执行器不提供守护进程资源管理。

scenario 请求包含 scenario_id、precondition 和 actions，**没有 expect**。驱动器需实际建立前置状态，在响应的 precondition_state 中返回动作前的观察，由统一引擎核对；再按顺序执行每个动作，不能以收到的动作数代替已执行步数。

stdout/stderr 可记录诊断，但必须恰有一条完整结果行：

```text
APP_REBUILD_RESULT {"operation":"scenario","scenario_id":"complete_lesson","precondition_state":{"lesson":"intro","completed":false},"observations":[{"step":0,"state":{"completed":true}},{"step":1,"state":{"completed":true}}]}
```

reset 返回 `state`，由统一引擎比较 initial_state。start、stop 返回匹配的 operation。无法执行时可返回匹配 operation、status 为 unavailable/fail/invalid 及非空 reason 的协议结果；适配器不能自行声明 pass。进程错误应非零退出；空执行、错误身份、缺步、多步、截断或非法协议不能通过。对象按字段子集比较，列表顺序及长度严格一致，基本类型严格一致，true 不等于 1。

这是可信适配器协议，不是防伪认证。适配器可以撒谎，所以实际 UI 结论仍需可追溯交互证据；测试替身必须标为 test_double。

## 命令与冻结

从本工具仓库根运行，workspace 为被验收项目。下面路径是调用者填写的示例：

```bash
python3 -m workflows.rebuild.cli check --workspace <项目> --spec spec.json --targets targets.json
python3 -m workflows.rebuild.cli verify --workspace <项目> --spec spec.json --targets targets.json --target reference --out artifacts/reference.json
python3 -m workflows.rebuild.cli freeze --workspace <项目> --spec spec.json --targets targets.json --receipt artifacts/reference.json --out artifacts/batch-v1.json
python3 -m workflows.rebuild.cli verify --workspace <项目> --spec spec.json --targets targets.json --target candidate --frozen artifacts/batch-v1.json --out artifacts/candidate-01.json
python3 -m workflows.rebuild.cli coverage --workspace <项目> --spec spec.json --targets targets.json --receipt artifacts/candidate-01.json
```

每个已知行为前重置，全部场景后再次重置并检查初始状态，最后 stop。参考端全部已知行为通过且输入、实现未变，才能冻结。candidate 验收必须引用冻结批次，保护期间发现任何验收输入变化均拒绝。未知行为仍在报告中，不计作通过；只有 unknown 的清单不能完成。

`--timeout` 控制每次适配命令，`--max-seconds` 控制整个业务批次，Pipeline 还传入持久 deadline。总预算耗尽后不再启动新动作；stop 保留最多5秒的独立清理额度。外层 Harness 的总预算继续生效。进程组超时清理由执行器负责；适配器自己启动的独立服务需要 stop 管理。项目运行数据和回执应写在 artifacts，避免混入源码完整性清单。

`--out` 不覆盖旧文件；每次尝试使用独立路径，保留失败证据。输出还可省略并交给 Harness 捕获；正式实验须持久保存原始回执。退出码 0 为已执行的通过，1 为实际验收未通过，2 为输入/协议使用错误。

增量规格需先重新确认参考端；freeze 时提供 `--parent artifacts/batch-v1.json`，并令 spec.parent_digest 等于父批次摘要。旧的已知场景不得移除或改弱，新增发现形成新批次。原有批次文件不可覆盖；产品规则确需改变时应单独解释，并设计明确的新基线，不能借增量发现偷偷修改旧断言。

## 覆盖与证据

报告分离 discovery 和执行 status：unknown、observed、decision 表示知识来源；not_run、pass、fail、invalid、unavailable、timeout 表示执行状态。保存规格/配置/输入/源码摘要、动作观察、差异、生命周期、命令输出和耗时。源码或规格变化后，旧回执仍是历史证据，但不能作为当前通过状态。

本通用层不提供自动业务发现；案例层已有浏览器与原生 UI 驱动，范围见 `projects/duolingo-web/README.md`。阶段控制与显式任务接续已接入，原生单任务模型 Stop 续跑已验证；完整多阶段模型重建仍待验证。当前测试在临时目录运行真实子进程和明确的状态机替身，证明协议与断言机制，不证明 Duolingo 覆盖或模型收益。
