# App 重建工作流

当前可执行范围包括共享业务规格、参考确认、冻结、candidate 验收及持久阶段推进。当前 Codex 负责观察和编辑，阶段控制器提供 next_action 并检验阶段证据；原生单任务模型 Stop 续跑已验证；Duolingo 案例首批浏览器／原生 UI 共享验收已通过，更多业务与完整多阶段模型重建仍待验证。不要把手工依次执行本清单算作完整自动循环。

1. 显式选择 workspace、原版范围及平台。记录原版日期/版本、可访问状态和重置限制。
2. 探索正常、错误、边界、退出和恢复路径。保存实际证据，填写逐行为清单；未知不得写为通过，自定规则标 decision。
3. 编写共同数据夹具、单一场景与统一断言；为 reference/candidate 配置独立动作适配器。协议由 [业务规格文档](../../docs/BEHAVIOR-CONTRACT.md)维护。
4. `check` 校验输入；`verify --target reference` 实际确认已知行为；只有通过且输入未变才能 `freeze`。
5. 用冻结 batch 驱动 candidate 验收。把规格、配置、夹具、证据及适配器加入 Harness.acceptance_paths；声明实际命令、verify_seconds 和总预算。每次根据实测失败提出假设、修改产品实现、重新验收，保留所有失败。
6. `coverage` 重建当前行为状态，检查是否使用当前规格及源码的回执。未执行、未知与不可用分开。
7. 独立补充探索初始清单以外的路径。新发现建立下一版、确认 reference、引用冻结父批次；保持旧已知场景，candidate 再跑完整增量规格。
8. 业务通过后分别进行实际原生界面、视觉及模型效果评估。实验需要事前固定协议，不能用机制测试替代。

用户要求先完善工具并进行机制消融，再开始 Duolingo 观察。线上原版与固定本地参考必须明确区分；测试替身只用于机制验收。

## 持久阶段入口

从工具仓库根运行：

```bash
python3 -m workflows.rebuild.pipeline start --workspace <项目> --spec spec.json --targets targets.json --max-steps 50 --max-seconds 3600
python3 -m workflows.rebuild.pipeline status --workspace <项目> --run <运行ID>
python3 -m workflows.rebuild.pipeline step --workspace <项目> --run <运行ID>
```

start 可在规格文件创建前运行；explore 退出要求规格中有 observed 行为及真实证据路径，specify 校验共享输入。reference、freeze、implement 各阶段由 step 实际执行或校验，不接收手填通过标志。失败留在原阶段，回执写入 artifacts/rebuild，状态写入忽略的 .codex/rebuild。已启动服务仍由适配器 stop 管理。

初版实现通过后必须进入 discover。补充探索检查 normal、error、boundary、exit、recovery、state_link，审查文件格式为：

```json
{
  "parent_batch_digest": "<当前冻结批次的规范化JSON摘要>",
  "checks": {
    "normal": "evidence/normal.md", "error": "evidence/error.md",
    "boundary": "evidence/boundary.md", "exit": "evidence/exit.md",
    "recovery": "evidence/recovery.md", "state_link": "evidence/state-link.md"
  }
}
```

这份审查是证据索引，不是自动质量判定。需要实际交互证据来支撑内容；测试替身不能证明原产品探索。规格必须有至少一个此前未覆盖的新 observed 行为及真实父批次引用，再执行 `step --audit artifacts/discovery.json`。新版本重新确认参考端并冻结，旧断言不得改弱；新版通过后 review 要求有界清单无 unknown、每项通过，且规格、源码及审查证据仍一致。

Pipeline 的 complete 仅指这份有界业务清单已走完流程；独立原生UI、视觉和模型效果仍按运行 Goal 验收，不能据此完成整个 Goal。

若由 Harness 驱动整个阶段过程，可将 `pipeline status --require-complete` 作为冻结 verifier。Codex 读取 next_action，调用 step 实测，再修复失败。该模式不要在探索前冻结可变的规格文件；每个实现批次由自己的 frozen_batch 保护。保护稳定的工作流入口和已有验收依赖，并保留工具仓库版本。模型是否实际依据 Stop 继续，必须另有宿主日志证明。

跨会话时先明确暂停 Harness 任务，用户选择该任务后调用 exploration_adopt 到新会话，再显式恢复。运行ID和 verifier 保持不变，阶段、历史、预算不重置；不得自动认领其他会话任务。
