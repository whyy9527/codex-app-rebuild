# 从分类库存推进到组合、滚动和重载

2026-10-11，继续实际中文母语→英语访客原版。上一批九分类／下层组探索留下“Swift只支持肤色、组合未保存”的缺口，本批先采实际布局及组合操作，再接入九分类和完整状态保存。282个选项是发现的库存，不是282次交互通过。[原版配置与来源](../english-avatar-categories-v1/renderer-provenance.json)、[当前源操作](transitions.json)、[探索反馈](exploration-feedback.json)。

## 原版发现与代码化模具

实际选择Body3、MainHair59、Nose Piercing1、BackgroundColor2，点完成／继续编辑，刷新后访问九分类，读取17组选中值。初次刷新只采到加载壳，保留`reloaded.json/png`，它不作已加载验收；另一次明确等待“肤色”和15个radio后采`reloaded-ready.json/png`。脚本现在也等待这个真实就绪条件。

`layouts.json`保留实际源布局，`relative-layouts.json`只减去实际滚动区原点，供Swift布局消费，未修改源选项值。左侧主Canvas在访问高分类后保留684点；右侧选项区域仍可按分类缩小，不能把两者混同。选鼻环实际内滚1152点，之后需外滚到视口外的完成按钮；两个滚动层分别进入原生旅程。

v60原样保留v59的5890项，追加1504，共7394。冻结15状态的文字、可见动作几何／角色／启用／选中、整图，15音频项仍pending。源自洽1489pass、5905not_run；不是产品通过。源采集先于候选实现，编译器在本批代码修改期间建立，不冒充事前预注册消融。

## 实际实现与失败

Swift现在消费原版九分类配置、17组282个选项、选中／未选中图标及SMButtons缩略图，用SMAvatar组合预览。保存完整17项状态，并兼容旧avatarSkin。初次九分类实际原生9状态，17组库存／选中检查通过，但v59仍643pass/237fail/5010not_run，九张整图均失败；这份[首次证据](categories-first/)不是最终二进制。

组合轨迹02、03、04均在外层滚动时崩溃，只采到前四状态。[失败历史](failure-history.json)与[04原始观测](native-failed-04/)保留。日志是NSWindow约束更新循环，非AX单纯超时。04仅关闭radio内部HostingView尺寸反馈仍失败；05同时让头像固定尺寸按钮的HostingView不再发布尺寸约束，同一实际滚动轨迹才跑通。未证明单个控件的唯一归因。通用控件提供显式opt-in，其他页面保持默认。

[最终15状态](native-final/observed.json)没有驱动失败，两次实际wheel均测到位置变化且进程存活；17组选中／库存检查通过，完整保存字节、实际Rive输入回读和旅程检查27pass。旧15色／保存／重启／放弃21状态回归76pass。它们不证明任意组合、像素、动画或音频一致。

最终v60：**1222pass/267fail/5905not_run/0unavailable**。失败为252几何项与15整图；249几何差异在0.5点内，其余3项为完成及确认动作4点偏差，未放宽零容差。旧保存回归在v60仍331pass/92fail/6878not_run/93unavailable，六张整图fail。不能累计不同轨迹的分数或把旧项not_run解释成回归通过。归档只重定位截图路径并重跑比较，保留重定位前观测／结果与截图哈希，不算新执行。

30核心、61Python、14Node通过；当前构建、采集器语法及冻结复现通过。未完成的主页整体差异、头像跨页展示、邀请／登录分支、原版实际声音采集、动态动画同步、真实探索策略消融继续开放。原始Dream-RSI/Cordis及无收益实验保留在[研究来源](../../../../docs/RESEARCH.md)。本批是历史反馈指导的实际补漏，不是已证明RSI因果收益。

## 复跑

仓库根执行，输出目录／文件需不存在；源脚本从已保存且进入头像编辑器的任务自有原版会话开始，会实际保存组合，不是只读。

```sh
node projects/duolingo-web/observe-avatar-composition.mjs --cli <playwright-cli> --session <owned-source-session> --out artifacts/composition-source-new
python3 projects/duolingo-web/freeze-avatar-composition.py --out-dir artifacts/composition-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/composition-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/avatar-composition-scenarios-v1.json
python3 projects/duolingo-web/verify-avatar-composition.py --native artifacts/composition-native-new --out artifacts/composition-native-new/composition-validation.json
python3 projects/duolingo-web/verify-avatar-inventory.py --observed artifacts/composition-native-new/observed.json --source-pattern 'projects/duolingo-web/evidence/english-avatar-composition-v1/restored-{i}.json' --state-prefix avatar-composition-restored- --out artifacts/composition-native-new/inventory-validation.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v60.json --observed artifacts/composition-native-new/observed.json --out artifacts/composition-native-new/validation.json
```

最后的前端比较预期仍退出1。源脚本输出是新观察，不能自动覆写冻结证据；新增发现编译下一版。独立音频输出检查不能由本批头像点击轨迹代替。
