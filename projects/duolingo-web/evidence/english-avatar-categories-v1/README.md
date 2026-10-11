# 横向探索、前端模具与原版头像渲染

本页是d7a26ce阶段历史；其“分类未接入”等结论后来由[组合批次](../english-avatar-composition-v1/README.md)推进，原始失败不改写。

本批没有围绕倒计时或已通过的肤色保存流程继续优化。上一批的“其余八分类未访问／未接入”决定先横向访问九个实际分类；第一次失败又改变了探索方法：视口内19个radio不能代表脸部全部70个radio。采集器新增真实DOM分组、完整选项、中心命中、视口相交和滚动区域，保持“页面存在”与“实际操作过”分开。

## 实际发现

干净保存状态从原版刷新后取得，九个分类共17组、282个选项。各分类总数为15、6、70、88、29、20、21、9、24。完整分组见[source](source/)和[探索反馈](exploration-feedback.json)；282是选项数，不是已测试次数或独立业务发现数。

先前只点击每类顶部选项，遗漏了完整下层分组。事前保存[策略修订](lower-groups/policy-before-deployment.json)，随后实际滚动、选择并切走再访表情、发型、面部细节、耳环、鼻环、胡须、头饰七组；七组实际命中、选中、草稿保留均观测到。所有九分类顶部选择也保留。它们没有保存，没有验证所有选项、任意组合或重启恢复。策略由当前Codex会话依据真实失败修订，不是独立策略worker或完整Dream-RSI；没有新匹配预算消融或因果收益结论。

另发现编辑器高度有历史依赖：本次顺序访问时肤色主Canvas352点、身体432点，后续扩展至684点，再回肤色仍684点、完成按钮移到视口外。不能仅按当前分类用固定高度定义页面；这条补充探针保存在[返回肤色观测](extra/return-skin.json)，尚未独立冻结/实施。不同顺序需继续探索。

## 模具与真实候选失败

v59原样保留v58的4303项，追加1587，共5890；冻结九个分类状态和七个下层状态。16个新状态包含整图、实际文字、可见动作几何、角色、启用/选中态；完整分组库存另保留，逐选项交互与音频继续pending。源投影1555pass、32新增pending，另4303旧项未运行，只是参考自洽，不证明候选。

实施前实际Swift进入已保存编辑器后尝试身体分类，报`No observed control: avatar-category-1`。修改后同样失败：其余八分类仍是没有交互的图片。最终分类轨迹仅采到肤色1状态，61pass/16fail/5795not_run/18unavailable；整图fail。初次别名误指向尚不存在的通用choice ID，实际肤色控件没有映射，16pass/1fail/78unavailable；保留[旧场景](baseline-scenario-before-alias-fix.json)及负回执。修正为真实avatar-skin ID没有改变冻结要求，只揭示更多已存在差异，不能把分数变化当产品收益。

## 原版资源接入

通过干净重载时实际响应取得不含账户标识的[原版渲染配置](renderer-config.json)，从真实UI选中项映射17个输入，未猜测随机初始状态。原版公开Rive文件、SMAvatar/SMButtons、cover/center与builder zoom3来自实际加载资源和组件代码，[来源与哈希](renderer-provenance.json)保留。18个选中/未选中公开图标已取得，尚未接为原生分类交互。

Swift预览改用原版Rive运行时SMAvatar；15肤色从实际按钮值15→1控制SkinTone，保留其它实际初始输入及原动画默认值，禁动画时设0。旧截图帧不再驱动预览。真正的其它分类选择、SMButtons缩略图、组合保存和档案展示仍待实施；不要称已完成完整头像系统。

最终二进制21个真实原生状态、保存/重启/放弃流程76项通过。实际运行时19条数字输入回读覆盖15肤色、其它17项源初始输入与zoom；16项[渲染接入检查](native-renderer/renderer-validation.json)通过，资产SHA一致。AXUnknown没有暴露SwiftUI accessibilityValue，采用自有进程日志实际读取Rive数字，保留这个限制。日志未逐帧对齐截图；不证明动画时序、声学或像素等价。

该21状态在v59仍331pass/92fail/5374not_run/93unavailable，六张整图全fail。不要将它与仅1状态分类轨迹累计。[分类失败](native-categories-final/validation.json)、[保存流程前端](native-renderer/validation.json)、[流程验证](native-renderer/flow-validation.json)、[对照](comparison.html)。归档截图路径重定位后重新比较，原观察/验证另保留，不算新的原生执行。

构建、30核心、61Python、14Node通过，三个采集器语法及冻结字节复现通过。没有放宽前端断言或增加产品限制，Goal继续active。下一步按原版完成九分类/滚动/组合/保存和头像展示，同时继续主页导航、课程整图和真实声音差异；原始Dream-RSI/Cordis及旧负消融继续见[研究来源](../../../../docs/RESEARCH.md)。

## 复跑

从仓库根，新输出目录/文件必须不存在：

```sh
node projects/duolingo-web/explore-avatar-categories.mjs --cli <playwright-cli> --session <owned-source-session> --out artifacts/categories-new --inventory-only
python3 projects/duolingo-web/freeze-avatar-categories.py --out-dir artifacts/categories-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift projects/duolingo-web/observe-frontend.swift artifacts/categories-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/avatar-categories-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v59.json --observed artifacts/categories-native-new/observed.json --out artifacts/categories-native-new/validation.json
python3 projects/duolingo-web/verify-avatar-renderer.py --native artifacts/avatar-save-native-new --out artifacts/avatar-save-native-new/renderer-validation.json
```

最后一个命令需先用avatar-save-scenarios-v1.json运行完整15色原生轨迹；分类命令当前因缺控件退出1，前端比较也退出1。去掉inventory-only会实际选择各分类顶部未选项；lower-groups脚本需先保存当前已观测组名的policy-before-deployment.json。采集不代替服务端状态重置，未保存更改离开时可能触发退出提示。
