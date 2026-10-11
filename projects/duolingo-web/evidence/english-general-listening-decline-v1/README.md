# 听力暂缓改变实际题单

2026-10-11，原版中文→英语 `/practice`，1200×732。实际完成16道评分题，两次暂缓未评分；结算显示全对。完整Goal仍active。这批是探索和模具修正，**没有新的Swift实现或原生通过结论**。

## 实际路径与反例

`session.json`保留初始公开题单。`replay-to-tap.json`实际评分前六题，停在第六索引的listenTap，观察7行不等于答了7题。新增`--stop-before-type`允许在指定已观察类型交还探索，避免自动把待探分支答掉；后续驱动输出显式区分answered、stopped和outcome。旧回执产生于增加answered字段之前，未事后补造运行字段。

实际听词组水和咖啡：点击“现在不做听力题”后显示**“听力题已跳过／将在 15 分钟后恢复”**，词库禁用；继续后插入同句中文翻译，答对后才出现口语。口语句子为“Good morning, hot coffee or with ice?”；暂缓后出现的却是**water and tea**翻译，而非这句口语的翻译。之后依次是tea and coffee、咖啡加牛奶、No coffee, thank you.、不要牛奶也不要糖谢谢、谢谢再见、挑战题热茶／冰水／不要冰不要水。每次实际提交均接受，见十份独立answer回执及前后PNG，另有六题前缀回执。

这推翻“暂缓只跳过当前位置”及“初始API题单就是执行轨迹”。Swift当前`declineListening`仅接收listenMatch，固定advance直接走下一题；不能只扩大按钮类型就宣称修复。下一实施批次须用已冻结轨迹补插入、变题、评分与继续状态，并验证普通未暂缓路径未改变。选择其它替换内容的算法、完整重置与实例控制仍未知，不能把本实例当通用选题规则。

结算继续直接到建档提示；稍后再说回/learn，红心5。进入练习前只读取了主页AX，没有独立保存PNG，因此本批不能单独证明奖励上限或重置。原版的15分钟文案有证据，实际计时恢复未测。建档旧ref首次失败，刷新snapshot确认未动作后成功，保留失败摘要；没有创建账户。

## 前端模具与验证

采集器新增可见文字Range几何及computed CSS，并保留可见inline SVG。比如coffee-milk反馈实际“棒棒哒！”为24px/700/30px、rgb(88,167,0)。这不等于解析了实际fallback字体；DOM裁切、动画数字也可能仍出现，不把全部数字当可见成绩。PNG保持原字节，归档manifest记录摘要。

`freeze-general-listening-decline.py`原样保留v29的1851要求，v30新增28状态、34前端要求，共1885；包含实际暂缓提示、插入题、后续替换题、反馈、挑战转场及结算整图。源自校验34pass/0fail/1851not_run，只证明这批参考自身一致。旧native-02归档重评89pass/55fail/1741not_run/0unavailable，新34项全部未运行；没有新原生截图，不合并源自校验与候选结果。

这次选择分支来自既有“缺暂缓入口”失败反馈，发现了状态机遗漏；仍是人为选择并实际探索，不宣称自动RSI策略、发现速度或消融收益。原论文、既有负面实验继续由[RESEARCH](../../../../docs/RESEARCH.md)拥有。剩余前端、音效、主页、正常口语及整App探索继续，目标未缩减。

## 复跑

```sh
python3 projects/duolingo-web/freeze-general-listening-decline.py --out-dir artifacts/decline-new
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v30.json --observed projects/duolingo-web/evidence/english-general-listening-decline-v1/reference.json --out artifacts/decline-source-new.json
node --test projects/duolingo-web/reference-challenge-identity.test.mjs
```

比较命令整体返回fail是预期：1851旧状态没有在本源投影中访问。真实浏览器回放会生成新实例，不保证恢复本题单；使用新输出目录，并先确认页面当前状态。归档PNG和回执可离线复核，无需账户。

本批56 Python和4 Node检查通过，两个JS语法检查通过，旧要求结构相等、重复编译字节一致及归档摘要核对通过。Swift未修改，未运行新的原生验收。
