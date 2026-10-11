# 口语权限分支与探索反例

本批实现已观察的口语入口、拒绝弹窗、关闭与暂缓；正常口语尚未完成。源依据是首次 got 口语与第三次 tell 权限拒绝，沿用原证据，v23保留v22的全部1702项并追加3项状态要求。没有用候选推测原版评分。

## 探索与实现

第四套真实原版是 seal/zeal、sit/zit，十选择→配对→六错更正→结算→稍后建档→返回。第五套 pot/pet、dock/deck 也在十选择后进入配对，没有口语。这推翻了“元音练习必有口语”的假设；口语出现条件仍未知，不实现猜测的冷却期。两次轨迹和第四套实际配对/返回归档于 source-fourth/source-fifth；第五套仍停留配对，不能算完成。第四/第五套未编译进候选，继续列为缺口，不作为范围限制。

Swift接入显式按钮触发的AVAudioEngine/Speech基础、取消与过期回调隔离，嵌入麦克风和语音识别用途说明。Apple要求[语音识别授权](https://developer.apple.com/documentation/speech/asking-permission-to-use-speech-recognition)与[麦克风用途说明](https://developer.apple.com/documentation/bundleresources/information-property-list/nsmicrophoneusagedescription)。这只是接线：onFinal尚未接评分/推进，录音状态呈现、正常成功/失败反馈和完整识别均未验证，不能宣称可完成口语题。没有将文本相等伪装成原版口语评分器。

原版麦克风/关闭SVG按真实公开URL及哈希归档，转换PNG时保留gzip解码失败。录音与播放控件的原版矩形、角色、启用状态已验证；暂缓按钮宽度仍为160.5而原版160.6015625，零容差失败保留。角色和首套口语原音仍缺失。

## 实际验证

构建、23项核心检查通过；原生55状态、完成后终止/重启进入sip/zip，并保持主六课/生命3。v23共1705项：182 pass、24 fail、1499 not_run、0 unavailable，仍整体fail；新增三项状态全部通过。录音/播放控件各三项及拒绝标题/帮助文本通过不代表整个口语功能通过。

七对同状态同视口图像全部different，包含首次got口语前态。拒绝弹窗源是第三次tell而候选是首次got，因此不将两者整图冒充同状态比较。原生拒绝由--verify-speech-denied在权限请求和输入捕获前注入；它验证应用拒绝分支，不证明实际macOS权限流程或识别。验证没有录制麦克风/环境。

失败回执在failures.json。v1-04确实显示弹窗，但外层AX identifier覆盖标题/关闭标识；保留原探针，移除覆盖后重跑。No child home的两次失败保留，根因未完全确认；检查器由precondition改为throw确保退出清理。两个普通启动探针成功，未把可选诊断参数的失败归因当作定论。最终进程句柄已回收，observed/restart产物齐全，现场无残留LingoSeed；不补造丢失的退出码。

## 复跑

仓库根执行；用新的输出目录，需macOS AX/截图权限：

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/speech-permission-fresh projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice --exercise-speech-denied --verify-pronunciation-restart
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v23.json --observed artifacts/speech-permission-fresh/observed.json --out artifacts/speech-permission-fresh/frontend.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/speech-permission-fresh --pairs projects/duolingo-web/evidence/english-speech-permission-v1/pairs.json --out artifacts/speech-permission-fresh/visual.json
```

前端命令因真实差异退出1；图像命令零退出只代表比较执行。下一步以实际可达口语分支观察录音/反馈，使用明确的预录音输入验证正常流程，修复图像差异和音标进度规则；不能用继续增加课数代替探索策略效果检验。完整Goal active，既有真实消融负面结果继续保留。
