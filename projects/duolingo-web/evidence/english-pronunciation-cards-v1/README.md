# 前端模具接入真实图像比较，修正发音卡片

原先共同契约将整图要求记为 pending，实际像素差异只在案例外部脚本报告。局部业务通过因此无法约束前端交付。这批把已有截图比较能力接到通用契约，不新增产品限制，也不改变 1:1 目标。

## 观察与修正

2026-10-11 当前原版 characters 页首次捕获处在 scrollY=620，保留 source/source.json 和 PNG；随后实际滚回顶部，保存 source/source-top.json 和 PNG。card-details.json 保存39张卡的真实DOM/CSS。音标19px/500/19px行高，单词15px/500/15px，进度条上间隔5px，按钮高68px。Swift音标从17改19、内容顶部12、明确文字行高和68点点击区域；之前AX高64，之后高68。宽度和分数坐标仍有差异，不能算整体几何通过。

当前原版有非零音标进度和变化中的倒计时。整页验收继续使用已有冻结零进度参考，不把不同状态图片混成同状态通过。æ cat未增长卡的整数包围区域[442,291,598,360]，旧参考与当前原版逐像素相同，证明本卡样式仍适用；不证明整页版本/进度相同。候选同区域平均RGB差异约2.904降至1.846，整页约[3.626,3.231,3.788]降至[3.480,3.085,3.642]，仍全部不同。区域指标只是诊断，不能替代整图。

## 通用模具

capabilities/rebuild/images.py拥有ICC→sRGB转换与实际PNG比较；capture_color.py保留兼容导出，避免两处复制算法。驱动提供文件及实测窗口、内容区域、backing scale，不提供验收pass。比较器独立读取PNG、验证尺寸、裁切实测标题栏、下采样至冻结CSS视口，无掩码、偏移搜索或放宽容差。Pillow仅在image_pixels时需要，缺依赖/缺图/缺元数据为unavailable。

v25将v24的一个pending整图义务具体化为image_pixels，再追加7幅已冻结同题状态图片；所有旧的可执行要求原样保留。receipt.json记录逐项演进审计。不能说1718项逐字未变，因为其中一项pending已具体化。

原生before仅2状态、after实际61状态，不能直接比较全量通过数来声称改善。after共192pass/35fail/1498not_run/0unavailable；相比v24，新增8个实际图像失败（1项由pending执行，7项追加），不是8个产品回归。8幅真实整图全部失败；其它pending、正常口语评分/推进、增长规则、后续课程与自主探索收益仍未解决。

## 验证与可复跑证据

Python完整55测试通过，含驱动pass不能掩盖一个RGB通道差1、真实裁切、缺依赖及错误尺寸。最初直接比较器的macOS /var别名根路径校验失败，统一resolve根路径后完整重跑通过。Swift构建及23核心检查通过，61状态原生执行结束码0；退出取消、放弃不写入及真实重启选下一套均实际执行。没有环境录音。核心通过不代表视觉/声音一致，也不证明RSI收益；既有论文和负面消融保持不变。

native-before/after保留原始observed.json；before的observed-with-capture.json只把既有真实文件和窗口元数据绑定到原观察。observed-portable.json仅将capture.path重定位到入库PNG，receipt.json逐文件校验字节SHA，既不修改PNG也不修改AX事实。归档回放无需原机应用；安装Pillow后在仓库根运行，预期退出1且192/35/1498/0：

```sh
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v25.json --observed projects/duolingo-web/evidence/english-pronunciation-cards-v1/native-after/observed-portable.json --out artifacts/cards-replay.json
```

重新实际驱动使用新输出目录及当前源码，macOS需已有AX/截图权限：

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/output/playwright/cards-fresh projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice --exercise-speech-denied --verify-pronunciation-restart --exercise-practice-quit
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v25.json --observed artifacts/output/playwright/cards-fresh/observed.json --out artifacts/output/playwright/cards-fresh/frontend.json
```

[实际图片对照](comparison.html)。完整Goal保持active，下一步继续从真实前端失败与尚未访问分支工作，不能用这张卡的修正收缩目标。
