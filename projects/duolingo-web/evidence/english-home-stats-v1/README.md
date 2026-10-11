# 主页顶部：输入方式与前端采集遗漏

原版中文→英语访客：阶段2/unit12，10分、1天连胜、505宝石、4红心，CSS视口1200×732。实际操作发现四个悬停弹层、英语选择关闭、宝石小店导航与连胜多月日历。课程仅聚焦不展开，Enter展开；红心根按钮点击后关闭。[源证据](source)、[历史](history.json)、[反馈](exploration-feedback.json)。添加课程、补心/Super/练习及日历后续尚待探索实现。

## 采集反例

page.screenshot前后原版悬停弹层消失，旧PNG不能作同状态参考。CDP截图保留弹层，但PNG2400×1464与DOM DPR1不符。独立Page.getLayoutMetrics给出物理视觉视口2400×1464、CSS视觉视口1200×732，测得backing_scale2。只接受前后状态一致的calibrated采集；首批错误尺度、失败及超时保留诊断。不凭PNG猜尺度、不裁剪或平移掩盖差异。[采集审计](sampling-audit.json)、[归档摘要](archive-audit.json)。

## 实际实现与验证

Swift顶部入口由静态图文改为AXButton；课程/宝石原版弹层、英语选择关闭及宝石小店导航接入。真实聚焦+Return在修复前不展开，修复共享按键处理后展开，两个版本均留回执。这是产品反馈修复，不是同预算RSI收益。

最终鼠标8状态与键盘2状态使用同一二进制，0驱动失败。[验证](validation.json)、[鼠标旅程](journey.json)、[键盘旅程](keyboard-journey.json)、[实际观察](observed-bound.json)。共同v75保留17652旧要求，新增1283共18935；本轮451pass/57fail/17863not_run/564unavailable，7张实际匹配整图均fail，日历未接原生。计数仅属于本批，不是产品完成率。连胜、红心弹层与添加课程仍未实现。[严格结果](frontend-v75.json)。

历史156状态/80边，4310待探索记录。四入口分别记录hover/click/Enter，悬停不清除其他方式，旧记录不回填。67 Python、21 Node、35 Swift核心及构建通过；旧v74冻结输出、逐项状态和图像指标不变，v75五份冻结输出可逐字重建。[回归](regression.json)。

## 复跑

从仓库根使用新输出目录：

```sh
PYTHONPATH=. python3 projects/duolingo-web/freeze-home-stats.py --out-dir artifacts/home-stats-repro
python3 -m unittest discover -v
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
```

capture-visible-state.mjs的--preserve-hover使用实测CDP图像/几何并记录前后状态。observe-frontend.swift的focus_key通过实际AX聚焦和CGEvent，不设置业务状态。bind-home-stats.py只绑定实测别名和AX文字派生的弹层存在，合并要求同一二进制。准备夹具、旅程和回执均在本目录。原版日期、访客进度和网络变化不能替换冻结参考。

本轮没有新模型调用，消融04的0/0负面结果保留。下一轮策略应消费输入方式和前端失败，而非仅计新增文字。完整Goal active。
