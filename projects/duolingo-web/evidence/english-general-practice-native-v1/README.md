# 独立练习的Swift实现、实际回放和未通过的前端验收

2026-10-11。需求来自[上一批实际原版轨迹](../english-general-practice-v1/README.md)，共同契约保持v28全部1835项，未删除或放宽要求。这个批次接入独立练习，不代表Duolingo 1:1完成；完整Goal继续active。原始RSI研究及负面消融保留在[研究文档](../../../../docs/RESEARCH.md)。

## 实现与实际验证

`compile-general-practice.py`从真实评分回执编译16道题，包含口语暂缓后的插题、三道实际挑战替换、错误复习和三页结算。单独Course通过任务页“去学个单元”加载；主课程夹具v11及六课解锁保持原样。原版参考答案字段不直接生成键盘控件，只有实际可见切换入口才编译该能力。主课程扣心默认仍为1；这个实际通用练习实例的错误扣心为0。源实际5XP/94%只绑定观测到的1次错误，其他错误数不猜评分公式。

原生驱动执行真实按钮、键入和终止/重启，保存47状态。`native-06/observed.json`为最终回放；`native-business.json`核验：故意错答后仍3心、奖励页继续前3心/之后4心、主六课集合不变、独立完成记录、真实重启以及输入框实际矩形。核心24项业务检查通过，完整56 Python与4 Node检查通过，最终Swift构建通过。原发音流程52状态回归执行退出0，单独共同验收179pass/32fail/1624not_run/0unavailable；不能与本批计数累加。

48个原版语音/效果/SVG资源有摘要，另保存原版实际播放按钮的两个inline SVG帧与渲染摘要。配对成功四个不同原音及最终反馈可并发；通用练习不补合成点击。`native-05/owned-output.json`记录只来自自有子进程、麦克风关闭的14秒输出和8次真实配对操作，peak约0.827、rms约0.036。WAV保存在忽略的本地运行目录，摘要见同目录owned-output-digest.json。它证明该构建在真实动作期间有声音输出，**不证明与原版声学相等**，也未覆盖全部静音/反馈场景。最终06仅修改输入间距；声音证据仍明确属于05的binary SHA。

## 共同契约结果

| 回放 | pass | fail | not_run | unavailable |
| --- | ---: | ---: | ---: | ---: |
| native-01，在第5题中止 | 51 | 15 | 1769 | 0 |
| native-04，完整轨迹 | 80 | 48 | 1707 | 0 |
| native-05，原音输出及播放控件 | 80 | 48 | 1707 | 0 |
| native-06，修正输入间距 | 81 | 47 | 1707 | 0 |

新增88项通用练习要求最终46pass/42fail。40张整图全部fail，另有配对右按钮几何和红心页合并文案失败。仍缺角色/动画、奖励图形、多个题型及反馈布局等一致性。键盘文本框由189.5→378.5→355修正，最后矩形为原版[300,355,600,170]，正常/慢速按钮也按源矩形实现。不能用几何一项通过替代整图；源配对动画帧的宽度与候选静态按钮不同，时序还需继续探索，现有失败保留。早期主页要求和当前六课前提不一致仍在全量报告中，未自行删掉。

## 保留的失败与反思

- 首轮编译根据API有参考答案，误给中文翻译题加键盘入口。core-01/02和native-01失败。按实际源控件修复，core-03和后续24检查通过，旧夹具摘要与副本仍在native-01。
- native-02/03在第7题AXPress返回成功但切换未生效而停止。03新增失败边界截图，仍显示键盘态；04独立重跑改实际屏幕点击后走完。不是把失败操作重试后写成首次通过。
- 首次资源脚本缩进错误未执行下载，修复后下载/校验48项。旧脚本重渲染两个已有PNG，先保留本地生成副本，再按HEAD恢复原字节，最终manifest核验一致。现在仅渲染缺失PNG，避免无关资产漂移。
- 播放控件复用初次构建因类型private失败，改为共享同一控件后构建通过。第一次间距修正漏计父VStack的23.5间隔，实测仍fail，再修并真实回放。构建失败、错误的核心产品名调用及正确验证日志均保留在checks。

代码化模具必须包含原版可见能力和实际输入状态，不能把接口字段或流程通过当成前端需求全集。本轮人工补漏和修复有证据，仍不是自主探索效果或RSI收益证明。

## 新的源探索与frontier

`source-probe/discoveries.json`记录新的实际实例：重新进入/重载会变题；一题assist答错后直接退出，红心4不变。另一次配对选择“现在不做听力题”，实际标题为“听力题已跳过”，然后进入“牛奶”assist；答对后退出出现确认，确认返回learn。立即点击后的快照尚未显示弹窗，独立稳定捕获才看到确认，未重复点击。错误角色定位button/link的探针失败也保留。

这条听力暂缓的候选标题仍错，新增实例未接入通用选择器；正常口语、奖励上限/自然恢复、结算重新练习/回顾、确认取消/放弃的原生回放、全部图像和声学相等继续探索与实现。不会用固定实例取代完整目标，也不会引入无关的产品或审批限制。

## 复跑

从仓库根执行，输出使用新目录：

```sh
python3 projects/duolingo-web/compile-general-practice.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
node --test projects/duolingo-web/reference-challenge-identity.test.mjs
mkdir -p artifacts/general-practice-recorder
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/general-practice-recorder/capture-owned-audio
swift projects/duolingo-web/observe-frontend.swift artifacts/general-practice-new \
  projects/duolingo-web/fixture-reference-en-zh-v11.json \
  --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json \
  --reference-color-scheme light --observe-quests --exercise-general-practice \
  --general-practice-audio-recorder artifacts/general-practice-recorder/capture-owned-audio
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v28.json \
  --observed artifacts/general-practice-new/observed.json --out artifacts/general-practice-new/frontend-v28.json
```

比较命令预期返回fail；零退出仅用于实际回放/检查执行，不代替前端通过。归档PNG与原始运行逐字节相同，仅重绑定仓库相对路径并重新评价；编译重复输出逐字节一致，见fixture-reproducibility.json。48资源及两个实际SVG帧另有摘要，缺失动画或未观察规则不计通过。
