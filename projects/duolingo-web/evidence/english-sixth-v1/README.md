# 第六课实际续探：两种暂缓、替换尾部与独立结算

本批从上一批原版已接受sugar后的反馈原位继续，完成en/zh第六课并返回主页。前半程证据分别保留在[角色探索](../english-character-render-v1/README.md)、[听力暂缓](../english-listening-decline-v1/README.md)、[反馈动作](../english-feedback-actions-v1/README.md)，未重建或覆盖历史。没有把接口原列表当实际题目顺序。

## 实际过程

糖之后实际出现tea with sugar翻译、Good morning, coffee with ___, please.填空和再来一些咖啡的拼句；均获原版正向反馈。随后coffee with sugar口语点击“现在不做口语题”，实际提示“麦克风已关闭 / 将在15分钟后恢复”；继续后插入同句翻译，生命仍2。之后Sugar or ___?填空、Hello!翻译、hello翻译；最后一个替换原API listenMatch。挑战提示之后的三道实际自由输入分别是：

- 早上好，我想要咖啡，谢谢。
- 你好，我想再来点咖啡，谢谢。
- 早上好，我想再来一些茶，谢谢。

三题均由逐题原版正向反馈确认，不能复用API末三题答案。实际结算显示“完美！ / 你练习全对，无错完成本单元”，截图15经验、100%；没有错误重练。继续直接到建档提示，点击稍后再说返回主页：第二节点Lesson 3 of 4、生命2、宝石510。没有第五课任务/宝石页。结算数字动画在AX同时暴露0–9，completion-visual.json明确标注分数来自实际PNG人工读取，不是AX或公式验证。

## 模具及结果

`advance-visible-reference.mjs`每次先fresh snapshot，只有一个已观察且启用的“继续”才使用实际ref点击，保存前后快照；不会解题或按API索引推进。`answer-text-reference-live.mjs`用实际已观察的唯一输入label填写，保存输入前/填写后/反馈及答案回执，继续为独立操作。既有输出/intent阻止未知重复提交。其首版已实际接受本批四次输入；随后新增可见题面/提示采集，供下批保留typed题缺失的AX提示，未将尚未执行的新字段伪造成历史证据。q7使用直接CLI输入，保留before/feedback和独立动作记录。

相对截图路径由浏览器工作目录解析，拼句截图以submitted-before/feedback文件名归档；直接输入截图位于主artifacts，本案均复制实际PNG，不用合成图片补录。

`freeze-english-sixth.py`从实际快照/正向反馈冻结25状态、306需求。typed题在AX缺题面，使用紧邻的实际CLI DOM快照恢复提示，不读取API猜测。原版256pass/50not_run，整体fail；50项为逐状态视觉/声音缺口。产品v11保留v10的752项并增至1058项。用上一批真实默认五课AX观测对v11比较为434pass/11fail/613not_run，文件名prior-five-v11-result.json明确这是历史观测，未冒充当前重新跑六课或实现完成。

当前默认Swift仍五课72题。本批尚未编译第六课；下一步据本轨迹接入默认分支时需区分听力/口语暂缓和正常路径，不能把所有用户都强制带入固定暂缓序列。尚缺正常分支完整现场、计时/恢复、声音输出、同状态视觉与实际探索消融。

历史追加实际转移后42个动作resolved、117个pending。集合仅包含已记录动作，不是全App覆盖率；没有自主RSI或消融收益结论，原论文和负面实验继续保留。完整Goal active。

## 复跑与接续

仓库根运行，验收因未覆盖项返回失败；输出使用新名字，命令分别执行。

```sh
python3 projects/duolingo-web/freeze-english-sixth.py
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-sixth.json --observed projects/duolingo-web/evidence/english-sixth-v1/source-observed.json --out artifacts/sixth-source-review.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v11.json --observed projects/duolingo-web/evidence/english-feedback-actions-v1/five-observed.json --out artifacts/sixth-prior-five-review.json
python3 -m capabilities.rebuild.discovery --history projects/duolingo-web/evidence/english-sixth-v1/exploration-history.json --out artifacts/sixth-frontier-review.json
```

当前原版停在六课后主页。下次先读取实际页面，不重复提交已完成挑战或假装新会话可直接重置到历史账号状态。源启动/状态复现仍需继续完善。
