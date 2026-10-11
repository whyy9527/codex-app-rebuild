# 原版主页 Duo 动画 · 仍非1:1

上一批修高光/声音后仍有整图失败，主页Duo也仍是旧静态帧。本批依据这个历史缺口回到真实`/learn`，观察可见SVG及页面实际加载资源，冻结后实施原生动画。这是一次依据失败调整探索路线的实际记录，不是已证明的RSI策略收益。

## 原版发现与冻结

客态中文→英语，八课完成、宝箱已开、525宝石。唯一可见1080×1080 Lottie SVG边界为`[506,224.85546875,238,288.7578125]`；页面实际加载公开`pathCharacters/01a1427cc5613179ea3d7568a5f7445b.json`。资源名`duo_u1_0_twirl_019_lottie`，60fps、0–280帧、1080×1080，两个嵌入矢量composition，无外部位图。下载字节为gzip，先记录传输摘要，再解压原字节，未改路径或关键帧。

`source-motion.json`记录6张实际PNG/SVG及时间，约1.925秒；在固定Duo矩形中5对相邻PNG均变化。另7个SVG样本跨6.044秒，超过名义4.667秒，仍在变化。公共`window.lottie`不存在，未读取私有应用状态替代；准确循环、暂停和触发规则仍未知。`resource.json`及原资源SHA连接实际URL与Swift包内文件。

实施前v47保留v46全部2479项，新增6个实际整图断言及1个几何断言，共2486。源自比较670pass/17unavailable/1799not_run，仅证明冻结/比较内部一致，不是Swift通过。旧断言没有放宽或移除。

## Swift与真实验证

接入固定版本Lottie 4.6.1，用原JSON在原生SwiftUI视图中播放，替换静态`duo-observed-frame`；按原版已开箱状态调整容器位置/尺寸，缺资源明确显示载入失败。其他已观察状态沿用原有布局，未证明其动效一致。SDK、固定版本、实际构建及复跑信息在`runtime.json`，不是重新画一个近似角色。

旧构建实际6帧在Duo矩形5对均不变；新构建5对均变化，原生窗口能看到原动画。几何由旧`[501.5,265.5,243,243]`变为`[506,225,238,288.5]`，仍与原版相差0.14453125点纵向位置及0.2578125点高度；严格断言继续fail。六张整图也都fail，运动本身不等于动画还原。

两个动效轨迹按完整v47各0pass/7fail/2479not_run；不要把“5对变化”计入1:1通过数。连续帧没有控制共同相位，且当前源倒计时是2小时，Swift冻结v13仍是4小时；现有整图不能证明同时间同相位的一致性。下一步应补共同时间/相位夹具，不能通过屏蔽时钟、加像素容差或替换参考图掩盖这一缺口。

旧动效驱动曾把八课完成主页标成历史首课完成`home`，因此多报无关文案失败。`native-before/observed-raw.json`保留原始标签，`observed.json`明确只将初始状态改成`home-motion-initial`，六个动效帧未改。新驱动直接使用该状态名；其他带进度夹具的启动标为seeded-home，不冒充首课home。此标签修正不计产品改善；既有首课断言仍等待其真实场景执行。

相同最终二进制八课41状态回归无驱动失败；明确修正状态绑定后为114pass/13fail/2359not_run，原始133/17/2336回执保留，不将转为未执行的检查算改善。开箱/重启最终6状态19pass/12fail/2455not_run，底色、倒计时和整图差异仍在。带正确状态标签的中间回归曾重启后只采到LingoSeed、随后无法找到下一Practice，保留chest-state-failed的5状态失败；粗course-entry不足以确认所需主页就绪，驱动改等实际path-chest后再采集，最终6状态通过流程。具体瞬态原因尚未确定，不据此改产品规则。29核心通过。初次依赖下载与构建约302.78秒，不能作为业务效果或RSI增益；未新增机制消融。详细结果见`verification-summary.json`。

## 复跑

从仓库根使用新输出目录，顺序运行原生任务：

```sh
python3 projects/duolingo-web/freeze-home-motion.py --out-dir artifacts/home-motion-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/home-motion-native-new projects/duolingo-web/fixture-reference-en-zh-v13.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-motion
python3 projects/duolingo-web/analyze-home-motion.py --reference projects/duolingo-web/evidence/english-home-motion-v1/reference.json --candidate artifacts/home-motion-native-new/observed.json --out artifacts/home-motion-analysis-new.json
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v47.json --observed artifacts/home-motion-native-new/observed.json --out artifacts/home-motion-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v47.json --observed artifacts/home-motion-native-new/observed-colors.json --out artifacts/home-motion-native-new/validation.json
```

图像分析需Pillow；前端比较因实际失败返回1。动效诊断只读取实际截图，不根据播放器“正在播放”标志生成通过。原版当时状态、未探分支见[frontier](frontier.json)。原始Dream-RSI/Cordis、真实消融及无收益结果仍在[研究文档](../../../../docs/RESEARCH.md)。完整Goal保持active。
