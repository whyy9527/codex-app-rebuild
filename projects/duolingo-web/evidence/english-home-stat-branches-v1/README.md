# 主页下游：课程目录、红心练习与补心持久化

接续 [顶部菜单探索](../english-home-stats-v1/README.md)，实际进入原版的添加课程、红心练习、补心、Super建档和返回链。旧505宝石/4红心夹具保留，新155/5单独留证，不替换旧参考。

## 发现及采集修正

- 添加课程进入 `/courses` 目录，包含33个母语选项及课程卡，不能用已有个人档案语言弹层代替。
- 旧采集器漏掉原版menuitem；补入后实际重新采集英语和添加课程。原生select还因opacity0被误过滤，但实际中心命中为true。现在透明控件的绘制可见性和操作库存分别记录。实际选择English进入 `/courses/en`，选择中文返回 `/courses/zh`；界面语言仍为中文。33个选项及Enter/Space逐状态分别保留，不能一次选择就消掉整个控件。
- 做练习获取红心进入独立 `/practice`，首题听音配对。实际离开未作答练习直接回主页。已有练习实例不能冒充该新实例。
- 补心350实际让4→5红心，400ms回执仍显示505宝石，稍后截图/刷新显示155；刷新后红心5保留。满心时补心与练习禁用。没有相同400ms的原生捕获，瞬态要求为pending，不捏造匹配或失败。
- 访客Super进入年龄建档页；关闭先回登录，再关闭回主页。第一次关年龄页后对底层主页的按键/悬停被登录遮罩挡住，保留失败。后续实际关闭登录后键盘打开课程菜单成功。

[原始状态与动作](source)、[历史](history.json)、[前沿](frontier.json)、[反馈](exploration-feedback.json)、[归档摘要](archive-audit.json)。错误等待英语标题的动作已实际完成语言切换，但等待超时，因为标题仍为中文；后续真实捕获和返回操作证明结果，不把超时整段算执行通过。早期courses-canonical-state文件实际仍是登录页，其实测内容用于登录状态，未按文件名推断课程目录。

## Swift 与严格验收

接入原版红心弹层、五颗原素材、补心交易保存、满心禁用、已有独立练习入口、Super建档→登录→主页。核心进度增加spentGems，旧存档默认0，实际350扣费随重启保存。付款瞬态/不足宝石的原版路径、正常练习新实例及收益仍待探索；本轮不声明这些已经等价。

最终同一二进制实际10状态，0驱动失败；重启后AX文字包含5和155、存档hearts5/spentGems350，两个满心按钮禁用，Super关闭到登录、课程Return仍展开。[验证](validation.json)、[旅程](journey.json)、[实际原生](native-complete)、[绑定观察](observed-bound.json)。初次6状态、随后8状态及最终10状态均留证，不合并成独立样本。

v76保留18935旧要求，新增1192，共20127。本轮481pass/65fail/18954not_run/627unavailable；7张匹配整图全fail。课程目录/新听音实例/连胜日历与全音效未完成。前沿165状态/87边/4699待探索记录，不是产品完成率。[严格结果](frontend-v76.json)。67 Python、21 Node、36 Swift核心及构建通过；36包含真实交易扣费、拒绝及存档回读检查，核心通过不代表视觉通过。

## 复跑

从仓库根，使用新的输出路径：

```sh
PYTHONPATH=. python3 projects/duolingo-web/freeze-home-stat-branches.py --out-dir artifacts/stat-branches-repro
python3 projects/duolingo-web/bind-home-stat-branches.py --native projects/duolingo-web/evidence/english-home-stat-branches-v1/native-complete/observed.json --aliases artifacts/stat-branches-repro/aliases.json --out artifacts/stat-branches-observed.json
python3 -m capabilities.rebuild.frontend --contract artifacts/stat-branches-repro/contract.json --observed artifacts/stat-branches-observed.json --out artifacts/stat-branches-result.json
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/stat-branches-native projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-stats-v1/native-final/progress.json --seed-preferences projects/duolingo-web/evidence/english-home-stats-v1/native-final/progress.json.preferences.json --exercise-home-journey projects/duolingo-web/evidence/english-home-stat-branches-v1/journey.json
```

共同前端命令预期退出1，保留失败。五份冻结输出可逐字重建；绑定只读取实际AX和同二进制旅程，不能供应pass标记。原版日期、网络及访客状态变化须另采，不替换冻结证据。原资源SVG及3倍PNG摘要见resources.json，空心素材保存的是原版动画的一帧，动画一致性没有因此成立。

本轮为真实产品反馈驱动探索，没有新的模型策略调用或匹配预算消融。原RSI论文与04负面结果保留，下一次模型策略应消费这些前端遗漏与输入方式并另行验证收益。完整Goal active。
