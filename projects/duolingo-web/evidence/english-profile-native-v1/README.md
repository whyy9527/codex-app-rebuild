# 独立访客档案：Swift接入与前端验收

沿上一批已冻结v56实现排行榜页脚进入独立访客档案，接原版8个素材、头像引导关闭、加入月份、统计/成就展示及真实成就404结果。页脚实际链接保留徽章图片节点，侧栏个人档案仍沿原版进入注册提示。

`guest-profile-snapshot.json`明确保存原版当次访客204总经验、2连胜等快照；这不是累计经验引擎。当前头像开始/头像编辑/国家选择/邀请入口仍是缺失交互，其中开始与邀请仅有视觉呈现，不能当已实现按钮。第三成就图未采到，未替换成原创图。原版保存/下方内容/分享结果继续留在frontier。

## 验证与负结果

首轮实际页脚点击落进旧原创renderer：ReferenceHome有子页，LearningView白名单没注册。保留native-route-failed真实截图，按route-fork-entry-audit审计后补两个顶层目的地。v57原样保留v56的3846项，追加9项源快照证明的档案/引导/错误页可见性；不改旧断言。旧轮缺少新事实时仍记unavailable。

最终同一二进制执行4状态：档案引导→关闭→成就404→返回排行榜，驱动无失败。v57为93pass/10fail/3658not_run/94unavailable；新增667项中93pass/10fail/470not_run/94unavailable。三整图全部fail，显示全部和Later几何、404链接/布局仍fail。Later外围identifier移除没有修好AX尺寸，不能当已确认根因。未映射/缺失控件仍unavailable，没有自动算通过。

同二进制排行榜选择/悬停/清除2状态回归87pass/15fail/3753not_run，恢复前批计数和实际页脚徽章节点，严格徽章尺寸仍fail。早期一次hover目标缺失、Button吞掉徽章节点及children:contain无效均保留；后一次独立native链接层复跑通过，不推断未知hover失败根因。

构建07、30核心检查、8资源哈希及冻结字节复现通过。[逐轨迹汇总](verification-summary.json)、[实际截图对照](comparison.html)、[后续缺口](exploration-feedback.json)。没有声学等价、完整1:1或RSI因果收益结论。验证路径归档后重新评估，validation-before-path-rebase保留前回执；不是新的原生执行。

## 复跑

从仓库根运行，新输出目录/文件须不存在：

```sh
python3 projects/duolingo-web/freeze-guest-profile-navigation.py --out-dir artifacts/guest-profile-navigation-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/guest-profile-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/guest-profile-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v57.json --observed artifacts/guest-profile-native-new/observed.json --out artifacts/guest-profile-native-new/validation.json
```

另用leaderboard-visual-scenarios-v1.json跑原有状态回归，再sample-frontend-colors.py取实际颜色并比较同v57。前端仍有失败，退出1为预期回执结果；不能据驱动退出0宣称前端通过。
