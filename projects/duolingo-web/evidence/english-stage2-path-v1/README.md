# 第二阶段路径、购物单元与延迟指南遮罩

这批实际进入原版购物课，保留10道已接受题、1次口语跳过、两次鼓励、11张回顾卡、填空答案展开、建档提示及返回主页。原版延迟出现指南遮罩，阻止实际路径点击；失败与随后允许的指南入口均保留。原版指南第一句真实按钮触发了原始语音文件，不能据此声称系统实际出声。

本次独立持久化浏览器准备得到10分／505宝石／1连胜／10任务，与上一批530宝石／2连胜／50任务分开。购物前排行榜未解锁，购物后青铜等级，节点由Lesson1/5变为2/5。`prepared-progress.json`是同状态候选夹具，不是原版服务器重置。浏览器本机profile与storage checkpoint不提交，关闭再开原版的等价性尚未验证。

## 实现与验收

Swift接15个已渲染路径节点、两个禁用宝箱、原版Bea生火动画、课程／锁定故事弹层及真实购物实例。原版Lottie SVG帧用img绘制出现重复黑头；改为实际inline SVG DOM后正确，失败图保留。原生六帧角色区域均发生变化，只证明实际运动，不证明与原版相位一致。

从主页进入购物课、接受10题、跳过口语、两次鼓励、展开回顾、结算、返回及真实重启，共32个原生状态无驱动失败。初轮错误地复用青铜等级起点，随后按购物前／后来源修正并持久化；两轮均保留。32核心／61Python／17Node检查通过。

v65完整保留v64的10965项，追加1064共12029项、31个新源状态。最终比较189pass／165fail／11290not_run／385unavailable；已比较29张整图全fail。几何、角色、文案、音频及未知分支不放宽断言。未解锁外的路径按钮仍有未实现行为；第二购物实例、指南遮罩、英语购物指南、完整字体／像素／音效及广泛导航尚未完成。购物入口目前重放已观察实例，不能视为自适应课程选择。

## 探索反馈

[历史](history.json)保留54状态、31条记录边（含不可用），[frontier](frontier.json)有1668条未解决状态动作；重复控制不合并成虚假的覆盖率。延迟遮罩导致的失败仍pending，不能把控制库存当执行覆盖。[下一步选择](exploration-feedback.json)优先延迟UI、购物指南、下一购物实例及下层路径。RSI原论文保留在[研究文档](../../../../docs/RESEARCH.md)；这批有实际反馈驱动补漏，但没有同起点同预算消融，不能宣称RSI因果收益。

原版独立浏览器82506的实际对齐采集为零输出；此前CLI回报82491是Node daemon，不是浏览器。无触发的静音片段不能证明原版静音，当前音频声学一致性仍unavailable。未录麦克风或其它应用。

## 复跑

在仓库根执行，观察命令需当前自有浏览器session，原生观察需辅助功能／录屏权限。`--out-dir`使用不存在目录。

```sh
python3 projects/duolingo-web/compile-stage2-grocery.py --out-dir artifacts/grocery-compile-new
python3 projects/duolingo-web/compile-stage2-path.py --out-dir artifacts/path-compile-new
python3 projects/duolingo-web/freeze-stage2-grocery.py --out-dir artifacts/grocery-freeze-new
python3 -m projects.duolingo-web.compile-stage2-grocery-frontier --out-dir artifacts/grocery-frontier-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/grocery-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-stage2-path-v1/prepared-progress.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/stage2-grocery-scenarios-v1.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v65.json --observed artifacts/grocery-native-new/observed.json --out artifacts/grocery-native-new/frontend-v65.json
```

原版准备与结算helper保留实际失败边界，不把退出0但无`Result`算成功；准备配置只属于该次测试夹具。观察预算按每次helper显式设置，跨helper的整批动作尚未集中计量，不能用于同预算消融。完整Goal继续active。
