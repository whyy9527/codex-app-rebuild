# 听音配对与输入重练：真实业务规则修正

2026-10-11。原版第二节点首课已实际完成，并经每日任务、5宝石奖励、建档提示和通知提示回到主页。完整原版轨迹见[trajectory.json](../english-next-node-v1/trajectory.json)。默认Swift仍为四课57题；第五课完整分支尚未正式编译接入，以下两项是能力实测，不能冒充产品完成。

## 原版事实与实现

原版listenMatch在左侧四个数字/扬声器按钮播放英文，右侧译文独立排序。选错会扣红心，源现场3→2；当前题可重试，配对成功两侧锁定。混合错误轨迹到课末只重练填错的热茶题，已在原地修正的配对不再次重练。旧文字配对题的未观察罚则保持历史边界，不用它覆盖新题型。

Swift已修正左侧原音、右侧排序、错配扣心并立即保存、错误状态、重试与锁定。扬声器/波形来自当前原版DOM静态帧，使用观察到的状态颜色作为模板着色；不是完整原版动画。4个公开音频文件、2张静态帧与实际Swift bundle哈希一致，未证明系统输出/听感相同。

原版输入cold被判错并扣心，正确句显示hot tea；课末重练输入HOT被接受。Swift补齐完整正确句、大小写比较、清空输入后重练和提交锁定。大小写规则由这次HOT接受推导；空白、标点、拼写容错仍未知，不宣称完整源判分。

## 实测结果

14项核心通过。听音配对实际原生运行从3红心执行一次错配、重试、完成、回主页，最终存储2红心，completedCourses为空。run01及run02各8项几何失败保留；修正描边命中范围、行间距及列距后，final为14pass、0fail、4not_run，整体fail。8个按钮在1200×732内容视口的实测几何与原版相同，但三对原版/原生PNG全部different。

另外独立原生热茶验证从4红心输入cold，显示完整正确句，进入重练并接受HOT；hot-observed/result/progress及PNG来自同一次运行，walk_error=null。该组件7pass、0fail、3not_run，整体fail。图片、声音、错配动画及完整判分尚未验证。组件课时进度与原版完整课时不同，部分红心上下文也不同，不称完整同状态1:1。

产品契约v9保留旧版并增至606项；本轮未重跑完整产品，不把两个组件结果与旧四课回执相加冒充同一次验收。此前v6的341/8/205仍属于e6a2349那次运行。原始RSI论文与历史实验保留；本轮不是预注册探索消融，没有策略收益结论。

## 复跑

从仓库根，输出目录须不存在：

```sh
python3 projects/duolingo-web/compile-english-pairing-probe.py
python3 projects/duolingo-web/freeze-english-hot-review.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
# seed.json为 {"completedCourses":[],"completedLessons":{},"hearts":3}
artifacts/observe-frontend artifacts/pairing-recheck projects/duolingo-web/fixture-english-pairing-probe.json --walk-course --exercise-wrong-audio-pair --seed-progress projects/duolingo-web/evidence/english-pairing-native-v1/initial-progress.json --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-pairing-probe.json --observed artifacts/pairing-recheck/observed.json --out artifacts/pairing-recheck/result.json
# hot-seed.json为相同空进度但hearts=4
artifacts/observe-frontend artifacts/hot-recheck projects/duolingo-web/fixture-english-hot-review-probe.json --walk-course --exercise-typed-review --seed-progress projects/duolingo-web/evidence/english-pairing-native-v1/hot-initial-progress.json --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-hot-review-probe.json --observed artifacts/hot-recheck/observed.json --out artifacts/hot-recheck/result.json
```

前端命令均预期失败。资源已随Git交付。下一步把完整第五课、口语暂缓分支及实际结算/主页接入默认实现，再继续其余三课、录音识别、视觉声学和真实探索策略消融。
