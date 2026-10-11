# 默认第八单元、13卡回顾与实际结算

2026-10-11。接续[等级入口探索](../english-home-frontier-v1/README.md)。完整Goal仍active，未增加产品限制，也没有新RSI效果结论；原始Dream-RSI/Cordis及负实验仍见[RESEARCH](../../../../docs/RESEARCH.md)。

实际原版在13卡回顾后依次进入英语分数进度、经验宝、传奇挑战邀请、建档页；选择“不，谢谢”和“稍后再说”后返回学习路径。此时两个Lesson节点均已完成，出现“打开宝箱”。这补足了第二节点第4/4单元的语义：把它编进默认主课第八单元，而不是另加一个孤立演示实例。前七课定义原样保留；v12实际共有115道评分题（前七课103题，纠正旧README的102计数），新增12题及一条未评分的口语暂缓。

`compile-level-review.py`只收录实际反馈或实际口语记录，保留13条历史顺序；未提交的探索边界不是一次尝试。共享编译器按4份实际接受回执支持完整句翻译。默认主课回顾现在调用真实历史，暂缓Thank you.仍为nil评分。第二节点完成显示修正，8课完成不会设置整课程完成。新26项公开原版资源逐项核验SHA；这证明资源身份，不证明实际应用音频输出一致。

## 模具与前端失败

v38保留v37全部2298项并追加实际四页的23项，共2321。`freeze-eighth-settlement.py`从实际JSON/PNG重建，编译器及冻结输出逐字节复现。源自检508pass/0fail/1799not_run/14unavailable；源没有执行的要求不算通过。

默认第八课修改前/后各41原生状态，均真实从学习路径进入，完成12评分题、暂缓、13卡回顾、长答案、滚动往返、结算、返回和真实进程重启；无驱动失败，重启显示8/8且保存八课ID，completedCourses仍空。两轮前端均133pass/17fail/2171not_run，不能合并不同轨迹通过数。长浮层整图RGB平均差由约[3.74,2.87,4.53]降为[2.11,1.77,2.35]，仍fail。源274.0703125×136边界与原生274×142仍不同，原生AX包含箭头区域，不能把文字节点误当整个浮层。

浮层布局从固定78/-74改为标题与正文测量：源长卡标题/检查图标最大25高、15间隔、40高正文、8间隔得到相对103点；短卡和上方浮层保留同一计算路径。此处是依据观察修布局，不是已证明所有字体/视口的一般算法。长答案AX改为实际组，保留原PNG与失败；没有放宽容差。

结算当前仍复用通用renderer，分数图形/经验宝/传奇插画未还原，四页按钮位置/尺寸全部失败；传奇Start仍缺真实行为。完成后候选宝箱仍锁定图，原版已可打开；此差异进入frontier，不能把课程通过当主页1:1。新第八课逐题前端尚未全部冻结；通用练习默认回顾仍无元数据。正常口语、自适应选择、听音填空暂缓、声音和其他页面继续探索。

同一最终二进制回归17卡44状态、18卡49状态（含Escape），均无驱动失败；分别147pass/7fail/2167not_run及212pass/10fail/2099not_run。保留旧红底及全部整图失败。构建、28核心、56Python、14Node通过。没有本批声学验证或模型消融；布局修正不当RSI收益。

## 复跑

```sh
python3 projects/duolingo-web/compile-level-review.py
python3 projects/duolingo-web/freeze-eighth-settlement.py --out-dir artifacts/eighth-freeze-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
node --test projects/duolingo-web/*.test.mjs
swift projects/duolingo-web/observe-frontend.swift artifacts/eighth-native-new projects/duolingo-web/fixture-reference-en-zh-v12.json --seed-progress projects/duolingo-web/evidence/english-eighth-integration-v1/progress-seed.json --reference-color-scheme light --observe-quests --exercise-eighth-review
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v38.json --observed artifacts/eighth-native-new/observed.json --out artifacts/eighth-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v38.json --observed artifacts/eighth-native-new/observed-colors.json --out artifacts/eighth-native-new/validation.json
```

旧17/18卡回归分别将最后一个Swift开关换为`--exercise-current-review`/`--exercise-error-review`，seed使用`english-pronunciation-v2/progress-source.json`。各用新的输出目录，原生任务顺序运行。当前原版已结束于`/learn`、宝箱待打开，不能盲重放旧题。seed是映射到共同课程的已观察进度夹具，不是原版账号数据。逐二进制、失败与未知见[verification-summary](verification-summary.json)，原始图片摘要见`sha256-manifest.json`。
