# 真实源 App 探索策略消融

[预注册协议](PROTOCOL.md)固定模型、预算、评价与先后顺序。`evidence/training01` 保存四个真实原版分支及完全一致的根快照；采集过程为准备阶段人工驱动，不能写成模型探索收益。`registration.json` 绑定文件及世界哈希。

`replay.py` 用同一个可见标签决策接口执行历史分支回放，拒绝根状态变化、歧义后继及未记录结果。初始模型只见根和动作标签；反馈只包含已回放轨迹，不能偷看未来。事实atoms不是完整业务需求或视觉验收。

```sh
python3 projects/exploration-ablation/run.py --codex "$CODEX_CLI_PATH" \
  --registration projects/exploration-ablation/registration02.json \
  --world projects/exploration-ablation/evidence/training01 \
  --out artifacts/exploration-ablation-model02
```

运行入口先核对冻结摘要。正式调用前必须提交推送本协议和基线。每次真实Codex CLI进程限180秒、read-only，原生横幅验证gpt-6.1-sol/medium；失败不换样本。控制组先封存，再提供反馈改进实验组。`selection-seal.json` 之后才可访问在线留出动作。该阶段尚未证明1:1复刻质量改善，后续产品实现对照仍待完成。

首次批次因服务拒绝模型未产出策略，实际CLI横幅版本与命令版本不符；[失败回执](evidence/failure01/diagnostic.json)保留。02修订只显式绑定bundled CLI及哈希，先提交推送再调用，不能把失败隐藏为重试。

02三次实际进程均成功，横幅模型/effort/CLI版本与注册一致；六个回放候选代理分数为70、34、4、70、70、40，控制组封存后回放为70。两组均选择了训练高分策略，尚不能宣称收益；[选择封存](evidence/model02/selection-seal.json)后才执行在线留出。
