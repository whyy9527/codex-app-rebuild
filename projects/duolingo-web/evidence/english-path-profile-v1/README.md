# 下一Practice的建档提示、CSS背景遗漏与年龄分支

2026-10-11。接续[宝箱探索](../english-chest-v1/README.md)。上一轮为有效进展，本轮接其真实未实现的Start→建档提示→稍后返回。完整Goal仍active；原始Dream-RSI/Cordis及负面实验仍保留在[RESEARCH](../../../../docs/RESEARCH.md)。无新RSI效果或声学验证。

## 新探索与模具补漏

源恢复/learn、宝箱已开、525宝石。第一次连续打开Practice/Start，链接在等待稳定期间被移出DOM；实际超时，没有完成Start。刷新快照后选择实际内层Practice按钮，重新打开Start，正常到已观察建档提示。事件和错误摘要在`action-journal.json`保留；不能把等待超时当成功或未检查便重发。

模态DOM有一个SPAN而非IMG，CSS background-image为原版`efff73c7255e0a6eff22f1ddc22b087b.svg`。原先只抓img/svg/canvas，遗漏了Duo自拍图。采集器新增**实际视口内的CSS背景媒体**及rect/backgroundSize/position/repeat；没有读隐藏会话数据。实测144×250、背景auto250px、位置50%50%。v42保留v41全部2373项，追加背景几何1项，共2374；在UI实施前冻结，源自检561pass/0fail/1799not_run/14unavailable。

源正常关闭X后，提示消失、底层第1/2单元弹层保留。最初误用getByTestId，它默认找data-testid，而此源DOM是data-test；超时后根据实际DOM使用精确属性选择，实际关闭成功。未force或删除遮罩。稍后返回行为沿用此前实际证据。

再打开Start并实际点创建档案，出现**年龄页**：你的年龄是……、空年龄输入、禁用下一步；不是直接展示姓名邮箱表单。新`source/age-form`保存真实前端，未填写年龄、提交账号或登录。v43保留2374旧项，新增标题、输入/Next几何角色enabled及整图8项，共2382；候选这8项全not_run，年龄合法性和Next之后流程仍未知。源最新569pass/0fail/1799not_run/14unavailable。当前原版结束在空年龄页。

## Swift与真实失败

ReferenceHome的下一Practice Start改为可执行链接语义，打开新的ReferencePathProfile覆盖层；保留底层路径弹层，Later只关闭覆盖层，525和开箱记录不变。原版Duo/关闭SVG按实际尺寸在独立context渲染，PNG分别432×750、48×48，源和渲染SHA均核验。按源450×569.5模态、144×250背景与文本/按钮位置实现。**创建档案当前仍不可用**，因年龄页尚未实施；这是明确的实现缺口和enabled断言失败，不是新产品规则或额外审批。下一批必须接已观察年龄页，不能把此处当完整建档流程。

实际8原生状态完成开箱、真正重启、下一节点、Start、建档提示、Later返回，无驱动失败；关闭布尔与525通过。共同v43为43pass/21fail/2318not_run，年龄8项全未运行。原生背景[528,111.5,144,250]与源[528,111.25,144,250]差0.25点；创建按钮y536与535.75、Later x552.5/y602.5/宽95与源552.59375/602.25/94.8046875不同，仍严格fail。全部整图、原有主页/宝箱差异保留，不能称1:1。

首次比较把真实AXLink与源link判失败：跨平台角色映射只含button/radio/checkbox，遗漏link。补AXLink→link，并新增测试证明AXButton仍失败、缺角色仍unavailable；没有把button宽泛视为link或放宽几何。保存映射前原生比较报告（43之前为42pass/22fail，v42），最终按最新v43重评；规格增量与比较器修正分别记录，不能把分数变化当RSI效果。

相同最终二进制默认第八课41状态回归无驱动失败，共同v43为133pass/17fail/2232not_run；原13卡/结算失败保持。构建、29核心、57Python、14Node通过，两个冻结脚本逐字节复现。没有新模型消融，不把资源身份或程序回放当声音一致。

## 复跑

```sh
python3 projects/duolingo-web/freeze-path-profile-art.py --out-dir artifacts/path-profile-freeze-new
python3 projects/duolingo-web/freeze-path-age-form.py --out-dir artifacts/path-age-freeze-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
node --test projects/duolingo-web/*.test.mjs
swift projects/duolingo-web/observe-frontend.swift artifacts/path-profile-native-new projects/duolingo-web/fixture-reference-en-zh-v13.json --seed-progress projects/duolingo-web/evidence/english-chest-v1/progress-seed.json --reference-color-scheme light --exercise-path-chest --exercise-path-profile
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v43.json --observed artifacts/path-profile-native-new/observed.json --out artifacts/path-profile-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v43.json --observed artifacts/path-profile-native-new/observed-colors.json --out artifacts/path-profile-native-new/validation.json
```

使用新输出目录；原生任务顺序运行。默认第八课回归换为该课seed和`--observe-quests --exercise-eighth-review`。源年龄页当前不能盲重放Practice入口，先观察当前状态。[frontier](frontier.json)、[逐构建验证](verification-summary.json)和SHA清单保留，Goal不收窄或完成。
