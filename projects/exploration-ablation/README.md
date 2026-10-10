# 真实源 App 探索策略消融

[预注册协议](PROTOCOL.md)固定模型、预算、评价与先后顺序。`evidence/training01` 保存四个真实原版分支及完全一致的根快照；采集过程为准备阶段人工驱动，不能写成模型探索收益。`registration.json` 绑定文件及世界哈希。

`replay.py` 用同一个可见标签决策接口执行历史分支回放，拒绝根状态变化、歧义后继及未记录结果。初始模型只见根和动作标签；反馈只包含已回放轨迹，不能偷看未来。事实atoms不是完整业务需求或视觉验收。

```sh
python3 projects/exploration-ablation/run.py \
  --world projects/exploration-ablation/evidence/training01 \
  --out artifacts/exploration-ablation-model01
```

运行入口先核对冻结摘要。正式调用前必须提交推送本协议和基线。每次真实Codex CLI进程限180秒、read-only，原生横幅验证gpt-6.1-sol/medium；失败不换样本。控制组先封存，再提供反馈改进实验组。`selection-seal.json` 之后才可访问在线留出动作。该阶段尚未证明1:1复刻质量改善，后续产品实现对照仍待完成。
