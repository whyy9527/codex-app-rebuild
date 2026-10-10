# Guidebook、角色、题间状态与新题型（2026-10-10）

本批仍不是1:1交付。用户随后建议复刻英语学科，下一阶段以中文母语学习英语为默认参考；本批西语观察保留为历史及通用呈现/状态实现的证据，不继续将西语内容扩张作为当前主目标。

## 实际观察与实现

- `guidebook.json`：实际Unit 1 Guidebook的五组关键短语、连接词y/o说明、表格、两组例句和七次发音调用。七按钮对应六个不同的公开语音文件；`guidebook-resources.json`固定来源与SHA。没有用通用学习介绍替代原版内容。
- `ReferenceGuidebook`取代旧通用弹窗，保留侧导航/右栏，支持返回主页和逐句原版语音。词语释义提示、完整气泡/滚动/动效和音频输出仍未完成。
- `character-resources.json`：第三课七个实际角色SVG与透明PNG的来源及摘要。新版夹具将角色资源关联到原题，意义选择和拼句已使用；旧课未采齐的角色依然存在替代图形缺口。
- `fixture-reference-v6.json`从冻结v5增加原版实际两处题间状态；`compile-course-v6.py`从观察记录编译。鼓励页期间阻断隐藏题目输入，Continue后返回同一道下一题。核心检查确认这一条全对轨迹；错误、重试等轨迹的触发条件尚未确认，不能声称完整规则已还原。动画和原版提示音仍未验证。

## 几何检查与保留的失败

首轮`first-product-*`保留两项几何失败。标题最初拿原版满宽h2块与原生AX文字边界比较，是采样对象不一致；`guide-speaker.json`补采DOM Range文字边界，v6.1契约明确更正此对象，旧契约和失败不删除。原版标题文字边界约179.65×29.5，原生180×29，位置一致。不能据此宣称整个Guidebook视觉一致。

发音图标最初为系统符号，尺寸/位置不符；现在用原版实际SVG帧并保留源文件。最终原生按钮为[306,377,29,22]，原版[306,378.03125,29,22]，y差1.03125超过冻结的1点容差，仍判失败；没有放宽阈值。

`product-result.json`为中断期间已经完成的真实验收，继续检查其文件及摘要后保存：冻结业务12/12通过；课程文案及两处题间文案共239通过、9未覆盖；Guidebook 25通过、1几何失败、3未覆盖；主页/设置文案19通过、2未覆盖，偏好9通过、1未覆盖，原版偏好仍7通过、2失败、1未覆盖。实际原生三课37题、题间状态和课后Guidebook均走通，无walk error；统一结果fail。代码、资源和引用输入在执行期间保持不变。

Swift构建和6项核心业务检查通过。声音调用、可解码文件、播放器推进与声卡实际输出分别对待，当前没有新增原版/候选输出音色及时序的声学通过结论。

## 探索没有停在第一节点

顺着Guidebook引导返回后，原版第二节点Lesson 1 of 4可实际进入。`next-node-session.json`保存15题公开字段；同一标签上复用捕获及回放工具，11题得到正向反馈、两次题间页被记录，随后在真实“Complete the chat”页停止并报告`Uncovered type: dialogue`。原始现场、截图和失败见`next-node-ui.json`。会话另包含`listenTap`；其实际UI尚未走到，不能把接口类型直接当完成的前端发现或实现。

新类型已经进入前端契约的未覆盖项，不能通过把目标限制为前三课隐藏。当前回放还没有完整处理新题型，也没有证明RSI策略自改进或真实探索消融收益。原始论文与历史无收益记录继续由[研究来源](../../../../docs/RESEARCH.md)维护。下一阶段先采真实英语课程，把共性能力迁移过去，课程特定假设重新确认。

## 复跑

从仓库根：

```sh
python3 projects/duolingo-web/compile-course-v6.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 projects/duolingo-web/verify-product.py --out artifacts/product-v6-new
```

此入口当前仍验收历史西语夹具，不是英语复刻完成证据。候选默认课程尚待真实英语数据替换；没有将旧原创英语夹具冒充原版英语课程。
