# 主页共享滚动、列表盒模型和新探索入口

继续实际原版探索，而不是只跑旧题目：新标签保留原未完成课程，实际发现延迟指南教练再次出现；下层第一电台出现“公寓参观／完成以上全部等级才可以解锁哦！／未解锁”；点击“跳到第 2 部分”进入独立`/lesson/unit/12/test`，显示“挑战通关测试，跳级到第 2 部分！／下次再说／立即开始”，实际下次再说返回。电台弹层及该完整测试尚未接Swift，不计通过。源新标签最初1192×705仅保留探索证据，排除前端冻结；后续实际设为1200×732。

实际CSS显示原版右栏是上下两层sticky：先随页面移动，随后吸住底部，返回栏吸顶。原生以前两个独立ScrollView不等价。现在主内容／右栏共享滚动，右栏按实际内容高度与视口计算偏移；原生NSClipView实际位移扣除窗口contentInsets。初版SwiftUI Preference高度为0，坐标亦含-32窗口inset，导致右栏整页滚走或固定32点误差，失败保留。日志和实际UI验证是修复依据，没有伪造AX几何或放宽断言。

源任务卡早期165点、稳定175点；早期指南顶部与稳定顶部分别留存，不能互换参考。稳定右栏727点；页脚UL为64点、margin16px 10px 4px、两行LI20点且margin-bottom12点。Swift原先仅排两行文字，漏掉列表盒模型约18点，已按原版接入。CSS字重核查及本机CoreText回退均为PingFangSC-Semibold，本批没有凭感觉全局改字体。

主页导航及右栏两个导航入口改为真实AXLink，保留原动作。原版“查看排行榜”带0.8字间距、79×18，顶部现精确匹配；“显示全部”仍有0.203125点宽度差。共享页脚／滚动作用于主页及复用页面，不是给某张图加固定偏移。

v67完整保留v66的12822项，追加462共13284，包含早期／稳定指南、底部、电台弹层和独立跳级入口5源状态。原生新4红心夹具独立于旧5红心夹具。最终最新二进制[两状态视觉旅程](native-final/observed.json)无驱动失败，[严格结果](native-final/frontend-v67.json)153pass／17fail／13114not_run，两整图仍fail。底部两导航Y差由11.140625缩至1.140625点；前一4状态版本底部mean RGB差[7.06736,5.12231,7.20673]，本版同一源底部为[2.43239,2.36194,2.63967]。顶部约[3.12909,2.98362,3.51128]。这些指标只代表所比较状态；未知音效、路径和其它页面不能据此算完成。

[native-before-footer](native-before-footer/)保留前一4状态／5语音播放／滚动返回版本及22个失败；[native-shared-scroll-failed](native-shared-scroll-failed/)和[native-offset-failed](native-offset-failed/)保留最初错误。编译失败也保留；不把旧二进制运行当新构建成功。同最新二进制[旧主页3状态回归](native-home-regression-final/observed.json)无驱动失败，v64为195pass／19fail／10568not_run／183unavailable，独立计数，不将结果相加。32业务核心／61Python／19Node通过；冻结可复现。声学跨应用一致性仍未知，未宣称1:1或RSI收益。

[历史](history.json)69状态／35记录边；[frontier](frontier.json)2237未解决状态动作。新增状态、角色和库存不等于已探索完整。[下一步反馈](exploration-feedback.json)优先独立单元跳级、下层电台／部分快速导航、原版第一阶段英语指南及焦点词语。RSI论文保持在[研究文档](../../../../docs/RESEARCH.md)，真实同预算发现效果及消融仍待实施，完整Goal active。

## 复跑

在仓库根执行，输出目录须未存在。原生观察需已授权的辅助功能／录屏；不重置真实原版进度。

```sh
python3 projects/duolingo-web/freeze-home-scroll.py --out-dir artifacts/home-scroll-freeze-new
python3 -m projects.duolingo-web.compile-home-scroll-frontier --out-dir artifacts/home-scroll-frontier-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/home-scroll-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-scroll-v1/prepared-progress.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/home-scroll-visual-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v67.json --observed artifacts/home-scroll-native-new/observed.json --out artifacts/home-scroll-native-new/frontend-v67.json
node --test projects/duolingo-web/*.test.mjs
python3 -m unittest discover -v
```

[实际对照](comparison.html)供审阅，不能替代严格比较。带五次播放的4状态场景见`home-scroll-scenarios-v1.json`，运行另需`--audio-recorder`传入以`swiftc -parse-as-library`编译的自有应用录音器；最新两状态场景未重新录音，不把早期录音当最新声学验收。
