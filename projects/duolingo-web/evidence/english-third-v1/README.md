# 英语第三课：用真实失败修正探索驱动

本轮从上一检查点的第3/4课开始弹层原位继续，原版实际完成第三课15题：12正常题、3现场挑战。当前停在单元完成页；Swift仍为前两课，第三课尚未编译，不能宣称已实现。

## 两个实际遗漏

1. 第9题“No milk and no sugar, please.”的词库有两块“不要”，需要各选择一次。replay-01在第一块选择前因同名按钮strict-mode失败，actions为空。改成逐次选择可见且可用的词块后，从索引9原位续跑；replay-02保存两次不要分别对应occurrence0/1及原版正向反馈。不能把重复文本合并为一个词块。当前Swift编译器的文本字典也会合并重复项，是下一批必须修复的业务模具缺口。
2. 第12题初始API为translate，题面“water and coffee”，但实际同样是translate，变成挑战题“糖和牛奶”，词库and/no/milk/sugar。上一版仅核对DOM题型会放过此变化；本次完整词库/题面核对在任何答案操作前报告same_type_content_changed，actions为空。没有把另一类型变化冒充本次同类型证据。

reference-challenge-identity.mjs将当前UI与API期待分别保存，比较题型、完整词库多重集和可取得的提示。原版hint-token的textContent为空，但aria-label及父容器innerText有实际文字；新驱动读父容器，可用时做规范化相等。没有专门提示容器时退回当前题目文本中的存在检查，并明确记录较弱证据；尚不承诺所有题型的精确身份、音频/角色一致性。选项顺序可洗牌，词块数量不能被集合去重。

## 实际续跑与回执耐久性

现场挑战分别为“糖和牛奶”→sugar and milk、“茶和咖啡”→tea and coffee、“不要冰，不要水，谢谢。”→No ice and no water please，原版均接受。第12题作答/截图/继续已执行，但在同一callback立即读下一题时遇到两个过渡challenge节点，结果JSON丢失。adaptive-12-recovery.json只引用保存的原版正向反馈PNG及随后确认的第13题，不伪造AX反馈。

因此增加answer-reference-live.mjs：从实际可见词库执行模型提供的词序，保存前后文本、提示、词库、图像、动作与正误回执，然后才由独立操作进入下一题。第13/14题都先取得回执，再单独继续，实际到达单元完成页。新入口不是固定题表回放，也没有自动发明后台挑战规则；答案由Codex根据当前题面选择。

## 探索账本与共享前端契约

history.json有34个实际状态、35个转移，保留重复词块失败和同题型分歧两个unavailable尝试以及实际成功续跑。discovery输出frontier.json：33个动作已记录结果，18个已观察但未执行动作仍待探索（如跳过、键盘输入、完成后回顾）。此账本仅描述本课，不能代表整个App的覆盖率；前两课、主页和其它导航证据保持在原目录。

frontend-english-third-v1冻结139项源需求：题目标题、实际词库、提示/标识及待验证视觉/音频/交互/重复词块。frontend-english-v4保留v3全部233项，再加入本课139项，共372项；拿当前v2候选的实际观察比较为128pass、244not_run，整体fail。候选没有访问第三课，不能将源观察算候选通过。

这是历史失败→驱动调整→真实续跑→新需求→契约的实证。没有策略生成、历史树离策略评估或匹配预算消融，不能宣称Dream-RSI收益。预注册的新实验应使用已提交基线和相同揭示顺序，不能将此回归检查当作真实模型消融。模型token/费用与精确人工时间未采集，记unknown。

## 复跑与接续

从仓库根：

```bash
node projects/duolingo-web/check-reference-identity.mjs
python3 -m capabilities.rebuild.discovery --workspace . --history projects/duolingo-web/evidence/english-third-v1/history.json --out artifacts/my-third-frontier.json
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v4.json --observed projects/duolingo-web/evidence/english-second-native-v1/matched-observed.json --out artifacts/my-third-frontend.json
```

检查消费真实冻结轨迹，不能重放已完成原版会话来冒充新的在线执行。自有duolingo-english标签当前在第三课完成页，先读取现场，再走结算/第4课及其它前沿。第三课候选接入必须支持重复词块身份与判题，补齐实际挑战尾部、鼓励/结算、角色、布局及声音，不复制未出现的API末尾。完整Goal继续active。
