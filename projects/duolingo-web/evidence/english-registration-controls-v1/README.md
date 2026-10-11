# 注册输入控件与独立登录分支

2026-10-11。接续[注册路径](../english-registration-v1/README.md)，根据整图失败及未实现控件选择新探索，而非只重复课程。完整Goal仍active，Dream-RSI/Cordis及既有负面/不可归因消融保留在[RESEARCH](../../../../docs/RESEARCH.md)。本批没有新RSI效果或声学实验。

## 实际原版发现

主页创建档案→年龄页→登录，出现独立登录表单：邮箱或用户名、密码、忘记密码、Google/Facebook/**Apple**。它不同于注册方式页；尚未实施/提交登录或进入OAuth/忘记密码。源`login-empty`归档，不因其它注册流程通过而计入完成。

实际填合成年龄28并点击清除，值为空、Next禁用；再次填28→Next→电子邮件。仅输入合成测试串abc，显示密码后type=text且值abc，再隐藏后type=password且值abc；没有真实凭证或帐号提交。`interaction-probes.json`直接来自实际动作结果，冻结脚本检查它，不能从截图推测交互。当前源停在邮箱表单、abc隐藏。

CSS/CDP实际字体探针：标题26/700/PingFangSC-Semibold与DuolingoSans-Bold，年龄输入20/500、内边距8px14px，空placeholder中文PingFangSC-Medium；按钮15/700。原始h1探针因匹配底层和覆盖层两标题失败，修为当前覆盖层，保留这一负面记录。CoreText探针仅为同字体描述符的shaping，不冒充渲染后SwiftUI字形检验。

v45实施前冻结，保留v44全部2433项，新增43共2476：清除按钮、清空结果、密码框/显示按钮角色/几何/enabled、真实显示隐藏反馈、四个整图及新登录页。源自校验/候选比较分别报告；不能把旧未执行项累加为通过。3个实际inline SVG按原色解析CSS变量，保留path字节，独立context渲染72×72透明PNG及SHA；没有替代图标。

## 原生修复及失败

年龄清除按钮重建真实空输入，显示/隐藏按钮切换NSTextField/NSSecureTextField并保留内容。按原版输入字体与padding调整cell、标题色60、说明色119、按钮0.8字距；按钮阴影移到背景图层，避免给文字重复投影。焦点蓝边、法律链接、错误图标/排版等仍不同。相对上一批，邮箱空表单整图RGB差约1.10/0.95/0.89→0.88/0.78/0.73，年龄页约1.85/1.37/1.22→1.87/1.52/1.30，略增的负结果保留，不能把局部字体修正宣称全图改善。

`native-cell-failed`：自定义cell默认不可编辑，AXStaticText/实际输入失败；修复isEditable/isSelectable，未把静态文字映射成textbox。`capture-failed`：初始窗口截图失败、旧precondition使解释器trap且遗留自有子进程，确认进程后终止；未生成观察回执，标为unavailable。截图失败现在抛明确错误，不伪造PNG。

`native-before-shadow`20状态完成；接下来的两次在年龄输入停为2，先前“只要不回写编辑器就解决”的解释不足。保留`native-sync-failed`、`native-inactive-failed`。实际回顾回归另在33状态报“No active owned review scroll target”，见`eighth-focus-failed`。输入驱动现在激活并确认目标自有进程，再聚焦真实输入；滚轮同样确认目标。没有把观察超时当成功，也没有放宽实际键盘结果或滚动几何。编辑视图初始化时取模型值、由实际编辑发布状态，显式clear/reveal通过identity重建，避免延迟模型回写。

最终两次独立20状态各116pass/31fail/2329not_run；新增20pass4fail19not_run。相同二进制八课41状态133pass/17fail/2326not_run，无驱动失败。逐构建回归结果见`verification-summary.json`，每次按同一完整契约独立比较。未探索登录页仍not_run，四个新增整图仍fail；不能把真实控件交互通过当1:1。29核心/58Python/14Node和构建通过；这些检查不能替代前端或声音。

## 复跑

```sh
python3 projects/duolingo-web/freeze-registration-controls.py --out-dir artifacts/registration-controls-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
node --test projects/duolingo-web/*.test.mjs
swift projects/duolingo-web/observe-frontend.swift artifacts/registration-controls-native-new projects/duolingo-web/fixture-reference-en-zh-v13.json --seed-progress projects/duolingo-web/evidence/english-chest-v1/progress-seed.json --reference-color-scheme light --exercise-path-chest --exercise-path-profile --exercise-registration --exercise-registration-controls
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v45.json --observed artifacts/registration-controls-native-new/observed.json --out artifacts/registration-controls-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v45.json --observed artifacts/registration-controls-native-new/observed-colors.json --out artifacts/registration-controls-native-new/validation.json
```

新目录、原生任务顺序执行。八课回归换第八课seed及`--observe-quests --exercise-eighth-review`。前端比较当前因真实差异返回1；[frontier](frontier.json)继续跟踪登录/主页/声音及其它未访分支。完整Goal不收窄或完成。
