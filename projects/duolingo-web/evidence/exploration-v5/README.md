# 实际会话数据与遗漏状态（2026-10-10）

产品仍未达到1:1。此批改进探索和模具，不把三节课当作目标范围上限。

此前按已知题型逐词推断答案，把大量执行花在重复解题；接口数据、题间状态及结算后的分支没有进入模具。现在从原版实际POST sessions响应取得公开课程字段，同时走真实UI确认顺序、动作和正向反馈。接口是补充证据，不替代前端观察。

- `third-lesson.json`：第三课13题，包含图片选择、意义选择、配对、双向翻译；API答案与实际打乱的词库/配对顺序分开保留。逐题操作和反馈、26张前后截图、22次媒体play调用。仅保留公开内容字段，未保存账号/会话标识或追踪值。
- 两种题间鼓励页原先完全遗漏；`completion-states.json`又记录评分进度、连续学习提醒、Legendary邀请和注册提示。它们已进入新的前端契约，Swift未实现时必须保持未覆盖。
- `home-after-third.json`：点击LATER后，原版第一节点完成，下一节点为Lesson 1 of 4，右侧变为Bronze League。最初截图在路径仍加载时取得，不能拿空白路径证明完整主页视觉；AX状态与后续加载截图分别保留。
- `speech-resources.json`：31个原版公开语音文件的URL、字节数和SHA-256。按题目/选项上下文关联，不把同一个词的不同声音压成一条系统TTS。媒体调用和播放器推进不等于实际输出音色/时序验收；原版反馈音效仍未对齐。
- `compiler-boundaries.json`：缺反馈、词库不符和原版拒绝答案会停止编译；不是探索效果或产品质量测试。
- `history.json`、`frontier.json`：保留旧历史，加入真实题间及结算状态与未访问动作。图仍有跨会话断点；未访问优先队列不是RSI策略自改进。

采集中的定位错误、动画重叠、题间页失步和Continue后仍停留原反馈均保留在第三课记录。最后两题从实际索引11续跑，期间一次人工再次点击仍可见的Continue；不能把这批称为全程无人干预成功。最终原版确实显示Lesson Complete，再继续观察结算分支。

## 复跑

从仓库根，在自己拥有的Playwright CLI标签停于未完成的原版lesson：

```sh
node projects/duolingo-web/capture-reference-session.mjs --cli <playwright_cli.sh> --session <owned-session> --out artifacts/source-session-new.json
node projects/duolingo-web/replay-reference-session.mjs --cli <playwright_cli.sh> --session <owned-session> --out artifacts/source-ui-new.json --screenshot-prefix source-new
python3 projects/duolingo-web/compile-session-course.py
python3 projects/duolingo-web/verify-product.py --out artifacts/product-new
```

capture会重新加载并产生新课程实例；replay消费同一标签内捕获的公开数据。实际失步会保留输出并失败，核对现场后才能显式`--start-index`续跑，不把未知状态默默跳过。固定v5编译入口使用本批已确认记录，默认Swift为三课37题。旧v4夹具和旧断言保留。

下一步是补题间/结算/完成节点的真实状态与视觉，验证原版语音输出，进入第二节点继续寻找新题型与交互；把这些实际失败用于探索策略选择，再进行同起点、同资源的机制消融。RSI论文仍见[研究来源](../../../../docs/RESEARCH.md)，尚无本批RSI效果或消融收益结论。

## 当前验收回执

`product-result.json`：代码、资源、夹具/契约/证据摘要在执行期间保持不变；冻结业务12/12通过，三课37题实际原生AX走完、237项文案通过。课程契约另8项未覆盖，主页/设置文案19项通过另2项未覆盖，偏好9项通过另1项未覆盖；原版偏好对照仍7通过、2失败、1未覆盖。统一结果fail。`native-observed.json`保存83个实际原生状态，没有walk error；文案通过不证明视觉或声音一致。

Swift构建、核心5项、Python47项、三种编译边界及真实播放器推进/静音分离检查通过。语音文件31项SHA与下载字节固定；这些检查不代表原版输出身份、完整无人值守续跑或RSI效果。历史扩为50状态、49转移、30待探索动作，仍有跨会话断点。

随后尝试下一节点时，实际Guidebook教学遮罩截获点击；顺着高亮链接进入原版Guidebook，见`guidebook-tour.json`及新截图。这是冻结v5回执完成后新发现的下一批需求，尚未实现、尚未加入该冻结批次。浏览器当前停在`/guidebook/es/1`；下一轮先采齐Guidebook，再回主页继续第二节点，不能强制穿透遮罩伪造正常路径。
