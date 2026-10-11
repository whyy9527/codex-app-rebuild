# 排行榜前端遗漏：原版观察与保留失败

本批从原版状态面板的截图差异继续探索，确认原来漏掉的两种绿色状态底、实际悬停 brightness(0.9)、面板与页脚的不对称徽章、段落左右12px内边距。Source CDP与原生CoreText探针均解析为PingFang SC；没有据此全局换字体。实际原版先选首个状态、悬停，再清除，保留三份原始状态截图；账号数字路径已脱敏。

v55原样保留v54的3084项，追加104项，共3188。模具包含同状态整图、12个可见控件的角色/可用性/几何、选中与页脚状态、两徽章几何及精确sRGB取样；可见12个控件不代表实际执行了12个选择结果。源自检102pass，仅证明投影一致。

最终原生两状态87pass、15fail、3086not_run。两张整图仍失败，选中徽章AX边界42/26点对源40/24点仍失败，11项精确颜色失败。RGB平均差异从选中[2.52,2.25,2.81]降至[1.81,1.76,1.92]、清除[2.31,2.11,2.58]降至[1.86,1.77,1.91]，不等于1:1。段落内边距恢复后，相比上一版本差异略增，换行与行距仍待对齐。

同一最终二进制执行5个保存/重启状态及10个主页分支，驱动均无失败；分别35pass/10fail/3143not_run和119pass/23fail/3046not_run。这些独立轨迹不能累计为全产品覆盖。构建和30项核心业务检查通过。

[实际截图对照](comparison.html)、[逐轨迹汇总](verification-summary.json)、[历史反馈及待探索分支](exploration-feedback.json)。下一步优先进入已发现的个人档案链接及其它未访问主页分支，再完善交互与声音。原版实际音频等价、自适应选题和匹配预算的RSI效果消融均未证明。

## 保留负结果

native-interrupted保留旧二进制首轮进程丢失；原因未知。native-intrinsic-failed保留NSImageView原始尺寸溢出，其检查通过数增加但图像质量变差。native-sized和native-final保留修正尺寸及内边距后的结果。未降低图像/几何/颜色阈值，也未把辅助功能边界改写成预期值。validation-before-path-rebase是归档路径变更前回执；validation.json对归档观察重新计算，不是新原生执行。

## 复跑

从仓库根运行，输出目录必须不存在：

```sh
python3 projects/duolingo-web/freeze-leaderboard-visual.py --out-dir artifacts/leaderboard-visual-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/leaderboard-visual-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/leaderboard-visual-scenarios-v1.json
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v55.json --observed artifacts/leaderboard-visual-native-new/observed.json --out artifacts/leaderboard-visual-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v55.json --observed artifacts/leaderboard-visual-native-new/observed-colors.json --out artifacts/leaderboard-visual-native-new/validation.json
```

最后一步有失败断言时退出1，须读逐项回执。驱动使用实际指针悬停后AX press，不声称物理鼠标点击等价。font probe是CoreText构造器探针，不等于直接读取全部SwiftUI字形。
