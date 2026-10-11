# 发音练习退出：反馈反例→规格→Swift→原生验证

本批本来探索正常口语，但真实第六套仍在十选择后进入配对，没有口语。主课程第八课入口现在连续两次弹匿名建档提示；“稍后创建帐户”后再次点击仍弹提示。没有登录、创建账号或修改隐藏状态。设置实际只有音效、动画、鼓励和听力四开关，未发现口语开关。正常口语继续列为缺口，不能把这批退出功能算成口语完成。

## 探索发现及反例

第六套配对中退出出现确认框；旧Swift直接丢弃。取消后原版实际回到完全相同ARIA题目/控件状态，确认退出回characters；下一次未答或选中未提交直接退出。初版“只要答过题就确认”被原版反例推翻：一个错误后退出直接返回，等待确认超时。进一步实测两错仍直接返回，两错后一对会确认，第一题直接答对也会确认，先对再错仍确认。这支持已获得正确进度触发确认，排除了尝试次数、三题阈值和当前连对次数。

实际receipt、DOM、媒体、截图位于source；settings-click-timeout-home是菜单消失后的主页，真正设置在settings-hover.json；graded-first-quit-returned是等待确认超时后的真实characters页，不能算确认出现。候选依据已答前缀与错题队列推导已获正确进度，不另复制一份进度状态。未观察长串全错、部分匹配、口语识别成功等退出边界，不推断它们已经通过。第六套、这些中途探测都未完成整套，不计新增完成课程。

## 模具与视觉

旧capture-visible-state只保存按钮内图片，确认框独立Duo原图因此漏掉。现在额外采集所有可见img/svg/canvas的矩形、公共资源URL或inline/blob类型和固有尺寸；不读隐藏应用数据。实际新采集找到了120×120哭泣Duo，原SVG公开URL、SHA和240×240透明PNG渲染方式在asset.json。checkVisibility是DOM可见性，不等于遮挡或像素等价；画布内容/时序仍需单独验证。

保留输出stem碰撞EEXIST：原动作raw已有时截图被写出、随后保存raw失败。新预检在任何浏览器调用前检查三个产物；故意不可用CLI及既有输出的实际探测确认先拒绝，原JSON/PNG哈希不变。它防止证据被覆盖，不限制产品行为。

v24保留全部1705旧要求，并增加13项源要求。新确认框使用原版文案、原素材、控件和几何；首次60状态大幅偏移源于固定frame中的自然内容居中，改成topLeading。第二次61状态剩向下0.25点。第三次按面板高度386.5和displayScale补偿分数居中，实测变成向上0.25点，弹窗RGB差异变大，撤回补偿；当前仍保留三项几何失败。没有修改共享控件/验收容差，各次失败完整保存。

compare-dialog.py只比较完整弹窗的整数包围区域[408,172,792,560]，先ICC统一sRGB、按实测标题栏裁切及2x下采样。源和候选都先对后错，但具体题目/练习实例不同，所以只报告弹窗区域诊断，不称整页同状态一致；没有掩码、平移搜索或通过阈值。另重跑原有七对完整同状态截图，不能用区域诊断替代它们。

## 复跑

仓库根使用新输出目录，原生需AX和截图权限。拒绝注入在权限请求/捕获前执行，不录制环境声音：

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/output/playwright/practice-exit-fresh projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice --exercise-speech-denied --verify-pronunciation-restart --exercise-practice-quit
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v24.json --observed artifacts/output/playwright/practice-exit-fresh/observed.json --out artifacts/output/playwright/practice-exit-fresh/frontend.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/output/playwright/practice-exit-fresh --pairs projects/duolingo-web/evidence/english-speech-permission-v1/pairs.json --out artifacts/output/playwright/practice-exit-fresh/visual.json
python3 projects/duolingo-web/evidence/english-practice-exit-v1/compare-dialog.py --native artifacts/output/playwright/practice-exit-fresh --out artifacts/output/playwright/practice-exit-fresh/dialog-visual.json
```

比较命令因现有真实差异仍整体fail；图像脚本零退出仅表示计算完成。完整Goal active。此批是人工反馈驱动的真实补漏，未证明RSI或自主探索收益；既有模型消融负面结果保留。后续继续正常口语预录音输入的源探测、图形/声音、结算和音标进度，不用反复补题替代探索效果验证。

原版次数/正误对照脚本保留为probe-exit-count.mjs，调用格式为`node projects/duolingo-web/evidence/english-practice-exit-v1/probe-exit-count.mjs COUNT FRESH_OUTPUT_STEM OPTION_INDEX --cli CLI_PATH`。需已有duolingo-english会话停留characters；源码只选择可见radio、读取反馈并退出，不读评分答案或隐藏状态。COUNT=2/OPTION_INDEX=0得到两错直接退出；COUNT=3/0得到两错一对确认；COUNT=1/1得到首题正确确认。原版随机内容可能变化，必须读取新反馈，不把索引当作永远正确的答案。每次确认出现后应按实际退出按钮返回，再跑下一探测。

## 最终实测

当前构建及23核心检查通过；原生61状态、进程退出0，取消前后完整AX一致；两错直接退出、先对再错确认、放弃后重进首题、完成后终止重启到sip/zip均实际执行，未完成尝试不写进度，主六课/生命3不变。v24共1718项：{'not_run': 1499, 'pass': 192, 'fail': 27}；新增13项中10通过、3几何失败，整体仍fail。七对整图全部different；弹窗区域仍different，RGB均差[2.6405713058419242, 2.347340796821306, 2.3163257087628866]，只作局部诊断。verification.json及native保存当前二进制哈希和回执。
