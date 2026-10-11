# 年龄输入、注册方式与空邮箱表单的实际分支

2026-10-11，接续[建档提示](../english-path-profile-v1/README.md)。完整 Goal 仍 active；Dream-RSI、Cordis 和此前不可归因/无额外收益的实验见[研究来源](../../../../docs/RESEARCH.md)。本批没有新消融或声学一致性结论。

## 原版探索与模具

从真实空年龄页填合成年龄 28，下一步启用；清空后禁用，再填 28 实际点击，进入注册方式页。实际点击电子邮件，出现姓名（选填）、邮箱、密码与初始就启用的创建帐户。空表单真实提交显示“邮箱地址无效”“密码太短了”，标题/姓名/邮箱上移24点、按钮/法律说明下移24点。随后实际返回两次，年龄仍28，关闭回 /learn。没有填写姓名、邮箱、密码或创建帐号；Google/Facebook、正常登录、非空提交和年龄边界未探索，继续留在 [frontier](frontier.json)。

`source/` 保存五个原版 JSON/PNG，`action-journal.json` 与 `input-probe.json` 对应实际操作。年龄 input 的实际 type 是 text，无 min/max/pattern；不能假定数字范围。填入后年龄输入宽347而空值宽371，Next y372.5而初始376.5，不能只复用空页截图。源5个公开SVG按实际渲染尺寸导入，资源SHA和3倍PNG尺寸核验。

实施前冻结 v44，原样保留 v43 的2382项，新增51项，共2433：填入/清空的实际反馈、注册方式、空表单及错误态的文案、角色、几何、enabled和整图。`freeze-registration.py` 重编译字节一致。源自检是规格一致性，不能当候选验证；历史不可验证项仍保留。

## Swift 实测与失败

Create 已接入年龄→方式→邮箱→空提交错误→返回→关闭，沿用原版素材；不是完整注册服务。Google/Facebook在原版启用，候选仍禁用，明确计作未实施的失败，而非产品限制。登录、法律链接、年龄清除按钮、密码显示按钮及非空注册尚未实现；图形、字体、焦点和文本内边距差异继续修复。

首轮原生驱动把填入后的等待标识写死成 answer-input，进入年龄页后失败；修为传入的真实标识，保留 `native-failed`。第二轮16状态完成，但输入框实际AX高度23而源44，填值宽度/Next位置也错。修改真实布局后，SwiftUI更新与NSTextField编辑器竞争，把28截成2；保留 `native-editor-failed`。修为编辑器拥有在途输入，实际键盘重跑成功，未用AX值赋值绕过绑定。

最终16状态无驱动失败，共同v44 **96pass/27fail/2310not_run/0unavailable**；新增51项45pass/6fail，填入清空反馈及新增控件几何通过，4张新增整图和2个OAuth enabled失败。原生路径数不是需求全集，其他未执行要求不能累计旧回执充当通过。修正前87pass/36fail和两个失败边界都保留。最终同一二进制八课41状态回归无驱动失败，133pass/17fail/2283not_run；逐构建结果见 `verification-summary.json`；不能以流程完成宣称1:1。

构建、29业务核心、58Python、14Node检查通过；核心验证不替代前端。未修改前八课题单/评分，无音频采样或RSI效果宣称。

## 复跑

```sh
python3 projects/duolingo-web/freeze-registration.py --out-dir artifacts/registration-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
node --test projects/duolingo-web/*.test.mjs
swift projects/duolingo-web/observe-frontend.swift artifacts/registration-native-new projects/duolingo-web/fixture-reference-en-zh-v13.json --seed-progress projects/duolingo-web/evidence/english-chest-v1/progress-seed.json --reference-color-scheme light --exercise-path-chest --exercise-path-profile --exercise-registration
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v44.json --observed artifacts/registration-native-new/observed.json --out artifacts/registration-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v44.json --observed artifacts/registration-native-new/observed-colors.json --out artifacts/registration-native-new/validation.json
```

使用新目录、原生任务顺序运行。八课回归用 `english-eighth-integration-v1/progress-seed.json` 及 `--observe-quests --exercise-eighth-review`，不带 chest/profile/registration 开关。前端命令当前预期因真实差异返回1。完整Goal不收窄或完成。
