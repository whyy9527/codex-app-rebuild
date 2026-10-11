# 从保存头像扩展到主页阶段与实际返回路径

2026-10-11，继续中文母语→英语的任务自有原版会话。前批留下“编辑器保存不等于其它页面消费”的遗漏，本批实际回访个人页，又由主页 `/sections` 入口扩展到阶段列表与独立跳级测试。[动作前策略](policy-before-actions.json)、[主页扩展](policy-home-extension-before-actions.json)、[负反馈后的弹窗复查](policy-language-close-before-actions.json)均保留；这是历史反馈指导的实际探索，尚非已证明收益的 RSI 自动循环或消融。[原始论文与已有负结果](../../../../docs/RESEARCH.md)继续适用。

原版实际发现与证据：

- 保存的完整头像在个人页使用480×224 Canvas、原配置背景色及素材默认Zoom1；编辑器仍Zoom3。个人页铅笔进入干净编辑器，完成禁用；返回进入独立404，404实际主页链接返回学习页。
- 国家图标打开480×204语言弹窗，包含英语／中文、204经验和实际课程链接；实际X关闭，课程链接返回学习页。初次把Escape当关闭是错误判断，重复原版Escape后等待30秒仍可见。[原推断](transitions-before-escape-recheck.json)、[失败输出](escape-wait-failure.txt)、[复查](escape-recheck.json)与[更正动作记录](transitions.json)都保留。
- 主页阶段列表包含八阶段和每日巩固，不只首屏当前单元。原版跳至第2阶段进入独立通关测试引导，继续显示“我爱”三选一；本次未提交答案，退出首题直接返回阶段列表。第1阶段继续返回学习页。阶段3～8与每日巩固只有DOM库存，未执行。[源13状态](source/)、[卡片布局](section-card-layout.json)。

采集器现在分开保存视口动作、完整渲染控件库存、遮挡／滚动与实际执行。原生采集器保留没有开发者ID的实际AX控件，不凭缺ID断言不存在。[历史](history.json)含13状态、10条执行边；[frontier](frontier.json)保留329项待探索记录，包含重复状态、遮挡底层及屏幕外控件，不能当329条独立业务或可达行为。它由实际历史生成，未用候选通过分数消除未知分支。

独立源重跑又发现动态首题：原先“我爱”，第二次“鸟”，第三次“可爱”，均在同一路由；没有提交答案。固定等待“我爱”的首驱动失败，保留[失败和现场](source-replay-first-failure/)，更正为等待实际choice界面并读取当前题目后，[第二次6状态／5导航源复跑](source-replay/transitions.json)完成返回主页。源驱动不是新需求发现算法，但真实失败指导了模具修正。[三实例反例](dynamic-first-receipt.json)要求下一步按实例准备共同夹具；不能把v62旧首题当全部跳级内容，新增两实例目前尚未编入候选前端契约。

## 实现与严格验收

Swift个人页消费保存的完整17项状态、SMAvatar和源背景配置，接实际铅笔、语言弹窗、X关闭和课程返回。404从错误的带侧栏分支改为独立页，消费原版SVG、公开DIN字体及真实主页返回。五个原版图形及两字体来源／解码摘要见[资源](resources-complete.json)、[字体最终回执](error-fonts-final.json)。没有用替代素材或缩小产品范围解围。

v61原样保留v60的7394项并追加726；实际Escape复查后v62再保留v61并追加320，总8440。共有13状态、同视口1200×732的整图、文字、动作几何／角色／状态与弹窗／主页实际存在性，音频仍pending。源自洽1033pass/7407not_run不是候选通过。冻结结果与独立复现字节相同。

| 实际轨迹 | 版本 | pass | fail | not_run | unavailable |
| --- | --- | ---: | ---: | ---: | ---: |
| 原二进制基线，2状态 | v61 | 60 | 10 | 7930 | 120 |
| 首次实现，6状态，错误弹窗／返回 | v61 | 195 | 62 | 7616 | 247 |
| 最终，9状态 | v62 | 356 | 61 | 7631 | 392 |
| 同最终二进制旧组合回归，15状态 | v62 | 1222 | 267 | 6951 | 0 |

[最终真实观测](native-final/observed.json)、[逐项比较](native-final/validation.json)、[部分返回检查](native-final/route-validation.json)：保存个人页旅程实际走通，50项源派生状态／运行时检查通过；**主页阶段旅程仍失败 `No observed control: open-sections`，九张整图全部fail**。392 unavailable主要为未映射控件，不是成功；30核心、61Python、14Node通过不能代替前端。不同轨迹的分数不能累加。头像回归27项保存／运行时检查通过，17组282选项库存通过；仍有267前端失败，不证明任意组合或声学一致。

[失败历史](failure-history.json)另保留驱动重复字典key崩溃、Escape下层AX仍可调用的误导、字体gzip未解码、注册修补无效、Swift6构建失败后误用了旧二进制，以及首次回归未读取主页和错误调用状态前缀。最终成功构建后实际日志确认两个DIN字体；失败没有被改写成完成。归档只重定位截图路径，保留此前观测、结果和图片摘要，再跑比较；不是新执行。

**下一步先补主页阶段入口、完整阶段导航和下层单元，继续独立跳级题与真实声音；不再反复局部修头像或倒计时。** [探索反馈及开放分支](exploration-feedback.json)保留邀请／登录、其它组合、整图／声音及同预算真实探索消融。完整Goal仍active，1:1尚未完成。

## 复跑

仓库根执行；新的输出目录／文件必须不存在。源13状态来自已保存头像的实际会话，源端没有服务器重置能力；原生显式种子来自前批真实保存，不能把拷贝文件说成原版重置。主页阶段已有独立源驱动，实际6状态／5导航动作复跑完成；个人页／语言弹窗整旅程的独立源驱动仍待补。

```sh
node projects/duolingo-web/observe-home-sections.mjs --cli <playwright-cli> --session <owned-source-session> --out artifacts/sections-source-new
python3 projects/duolingo-web/freeze-profile-return.py --out-dir artifacts/profile-freeze-new
python3 projects/duolingo-web/freeze-profile-return.py --with-closure --out-dir artifacts/profile-closure-freeze-new
python3 -m projects.duolingo-web.compile-profile-return-frontier --out-dir artifacts/profile-frontier-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/profile-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --seed-preferences projects/duolingo-web/evidence/english-avatar-composition-v1/native-final/progress.json.preferences.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/profile-return-closure-scenarios-v1.json
python3 projects/duolingo-web/verify-profile-return.py --native artifacts/profile-native-new --out artifacts/profile-native-new/routes.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v62.json --observed artifacts/profile-native-new/observed.json --out artifacts/profile-native-new/frontend.json
```

原生旅程当前预计以阶段入口缺失非零退出；比较也预计非零。不要把退出码或仅旅程完成当1:1。源CLI即使退出0也可能输出 `### Error`，必须解析实际Result后才继续；现有源采集辅助脚本已执行这个检查。
