# 项目入口与 Goal 模板

`python3 -m workflows.rebuild.project` 连接目标、模具和现有命令，不创建运行状态。由当前 Codex 使用 [Workflow](WORKFLOW.md) 选择行动；只有用户明确要求启动 Goal 时才将 `goal` 输出传给原生 `create_goal`。

## 一份项目配置

所有路径相对显式 workspace。最小配置可在原版探索前创建，不要求先有契约或驱动：

```json
{
  "schema_version": 1,
  "name": "目标 App",
  "source": "原版入口、可访问环境及已知重置限制",
  "target": "目标语言与平台",
  "objective": "用户要求的复刻结果",
  "completion": [
    "原版已发现需求进入共同业务和前端模具",
    "主要用户旅程与已发现体验差异按原版实现并验证",
    "可启动、可复跑，剩余未知明确交付"
  ],
  "inputs": {},
  "commands": {}
}
```

`completion` 保存案例完成条件，具体期望值由契约拥有。新增输入填在 `inputs`，填写的文件必须实际存在；未知输入暂不声明，不制造空通过文件。标准索引名：

| 输入名 | 用途 |
| --- | --- |
| `fixture` | 实现／回放使用的共同数据 |
| `frontend_contract` | 当前共同前端要求 |
| `exploration_history` | 既有状态、动作和转移记录，供 frontier 读取 |
| `rsi_config` | Dream-RSI 的固定发现／评价协议、初始快照与策略 |
| `rsi_pool` | 可选当前选用的历史池，status 校验世界、快照和策略的哈希；不是 Goal 状态 |
| `historical_frontend_result` | 可选已保存结果，永远按历史显示 |
| `case_status` | 案例范围、已验证能力与未完成项 |

其他输入可指向业务规格、适配配置及证据。项目清单仅连接这些文件，不复制断言或运行任务状态。[Duolingo 配置](../../projects/duolingo-web/rebuild.json)是完整已有案例。

## 调用方式

```sh
python3 -m workflows.rebuild.project goal --workspace . --project projects/duolingo-web/rebuild.json
python3 -m workflows.rebuild.project status --workspace . --project projects/duolingo-web/rebuild.json
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command build
```

`goal` 只输出 `{"objective": "..."}`，可作为原生工具参数；不输出默认 token_budget、不写 Goal 文件、不创建任务或安装 Hook。已有 Goal 时由当前 Codex 按宿主能力读取和接续。`status` 返回已记录的模具规模、前沿与历史结果，不是验收命令，零退出码仅说明索引读取成功。

## 连接现有命令

`commands` 是命令名到 argv 数组的映射。CLI 不经过 shell，不隐式启动浏览器或模型；实际执行需显式 `run --command`。命令所需构建、驱动与验证由该命令拥有。

```json
{
  "commands": {
    "build": ["your-build-tool", "build"],
    "rsi_collect": ["python3", "-m", "workflows.rebuild.dream", "collect", "--workspace", ".", "--config", "case/rsi.json", "--out", "{out}"],
    "rsi_replay": ["python3", "-m", "workflows.rebuild.dream", "replay", "--workspace", ".", "--config", "case/rsi.json", "--pool", "{observed}", "--out", "{out}"],
    "replay": ["your-ui-driver", "--out", "{out}"],
    "compare": ["your-comparator", "--observed", "{observed}", "--out", "{out}"]
  }
}
```

`{out}` 由 `--out` 替换，必须是工作区内尚不存在的路径；CLI 不创建它，由目标命令写入。`{observed}` 由 `--observed` 替换，必须是已有文件。其他参数按字面传递。构建／验收失败退出码原样返回，不将产生报告误记为通过。

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command replay --out artifacts/replay-new --dry-run
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command compare --observed artifacts/replay-new/observed.json --out artifacts/compare-new
```

`--dry-run` 只显示 argv，不执行。清单是可信本地命令配置；用户当前授权决定是否启动实际观察或修改，配置存在本身不授权恢复已结束的试验。

RSI 的候选源码、继续使用的池及反馈由 [RSI 接口](RSI.md)定义。上例 `rsi_replay --observed` 指向真实 pool；修订时按该接口传入 `--candidate`，或把本次候选 argv 写入同一项目命令。接续 collect 时同样显式传入选中池。不要始终从 initial_policy 重开而丢掉已选策略。
