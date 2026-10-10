# 第二节点首课：原版完整轨迹已取得，候选整课待接入

2026-10-11。原版第二节点首课已实际走完并回主页：15个评分题、1个实际展示后暂缓的口语阶段，随后重练1道热茶输入题。trajectory.json串联每步原始回执；最初entry.json与显式reload后的session.json是两个实例，完整轨迹属于后者，不能混成同一题序。

## 新发现及负面证据

- “现在不做口语题”显示麦克风关闭、15分钟后恢复；后续出现Coffee, please.、tea、Tea, please!等插入的替代翻译题，原API第7题随后仍出现。固定API序号不能代表实际UI题序。replay-03/05在作答前保留失步；没有照旧答案盲答。未触发麦克风录音/识别，15分钟真实恢复规则未验证。
- 输入Tea与tea、Coffee翻译、完整句Coffee or tea?及填词coffee均有接受反馈。hot tea输入cold被拒，红心4→3，显示完整正确句；课末重练HOT接受。空白、标点、拼写容错和94%计分公式未知。
- 听音配对实际错配再扣红心3→2，允许原地重试并锁定成功配对。listen-match8/11保留逐按钮当前播放URL、译文、操作、反馈和几何。源课末只重练热茶，没有再次重复已修正的配对。第一道配对的逐按钮JSON因过渡异常丢失，反馈PNG保留；first-pairing-bindings从实际DOM属性和公共API派生绑定，不伪称已保留完整听感证据。
- 旧回放器把不支持的听音配对选项模型报告为choice_set_changed。这是能力缺口；已新增同题型uncovered分类，实际review-entry验证了修复。原版真正的题序变化仍会被身份校验拦截。历史失败不删除。
- 过渡中旧/新challenge可同时可见；tail.json保留再次严格定位失败。独立重新读取唯一稳定状态后继续，未重复已接受的题目。探索器新增稳定可见状态等待。
- 完成稳定PNG为13经验、94%，4项听力挑战。AX包含滚动数字全集，通用文本矩形裁切尝试也包含相邻数字，complete-visible-text记录负面结果，不能当数值真相。随后实际显示每日任务30/30、5宝石奖励、建档提示，选择稍后再说回主页。通知浮层拦截下一节点点击，node2-after-five-blocked保留；下次再说后才取得无遮挡主页与第二节点第2/4弹窗，宝石510、红心2。

全身角色由118×175 Canvas绘制，与接口的半身SVG/PDF不同。实际区域帧可能混入叠层，不是可直接复用的透明素材。公共WASM的具体渲染器与动画绑定仍未知；辅助CDN为smart_tip_en_zs，不冒认动画文件。matching-render只保存当前DOM扬声器/波形静态帧，动画仍待复刻。

## 当前候选与继续路径

[输入组件](../english-input-native-v1/README.md)和[听音配对/错误重练组件](../english-pairing-native-v1/README.md)已实际原生验证，14项核心通过。默认仍四课57题；完整第五课、口语暂缓与动态替代分支、每日任务结算及510宝石主页尚未接入。不能把组件通过记为整课复刻完成。

exploration-history是人工按真实回执整理的状态与操作，经已有discovery生成36个已观察动作、15个待探索动作；通知遮挡的失败仍保留。它不代表自动发现、穷尽覆盖或Dream-RSI收益。回放历史推动了本次策略修正：先核对当前题身份、区分插入题/未支持题、等待稳定可见状态并记录每步失败。真实同起点同预算探索机制消融仍待开展，原始论文及旧零收益结果不改。

从仓库根复算未访问分支，输出须不存在：

```sh
python3 -m capabilities.rebuild.discovery --workspace . --history projects/duolingo-web/evidence/english-next-node-v1/exploration-history.json --out artifacts/node2-frontier-recheck.json
```

当前源浏览器停在无遮罩的第二节点第2/4弹窗，尚未启动下一课。下一步将这条完整轨迹编入默认第五课，并继续第二节点其余三课、口语识别及分支探索，保持完整1:1目标。


后续实现更新：完整第五轨迹已编译为英语v6并接入默认Swift；源捕获记录保持原样，当前验证与仍未完成的分支见[第五课原生证据](../english-fifth-native-v1/README.md)。
