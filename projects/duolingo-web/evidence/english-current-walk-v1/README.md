# 当前题连续探索、引导页与成绩单漏采

2026-10-11。接续[听音填空负结果](../english-isolation-presentation-v1/README.md)，修正当前题驱动在引导页断开的机制，并实际访问结算的回顾、关闭和重练。完整Goal仍active，1:1标准不变；原始RSI论文和既有负消融保留于[研究来源](../../../../docs/RESEARCH.md)。本批没有模型调用或新消融，不声称RSI收益。

## 真实续跑

`replay-reference-session.mjs --current-only --current-steps N`现在每步从当前可见renderer读取公共字段，不预读初始/未来题单。新参数是一次调用的操作预算，不是产品范围限制。默认仍单步；已有初始记录模式保留。实际空choices翻译按现场唯一启用的输入框填写公共solution，不造词库；身份检查仍在作答前。当前模式媒体记录改为本次调用/上一反馈之后的增量，避免历史记录反复膨胀；播放调用不证明声音输出一致。

上一实例剩余“茶加糖”“咖啡加糖”“你好，早上好，咖啡加糖，谢谢。”实际接受3题，加前批13题共16。到结算保存`uncovered_current_state`和PNG，退出1；没有自动点击未知结算继续。真实`重新练习`生成另一套题，不能假设题目不变：当前驱动先接受6题，在口语`Good morning, I'd like water and tea.`停止未覆盖。人工实际暂缓、观察麦克风关闭并继续后，驱动接受10题，自动跨过一次已观察挑战引导页，再到结算留待探索回执。`source/retry-after-speech.json`含真实interlude动作与逐题结果。

这补上了已知引导页的自动接续，但口语仍人工交接，未知页面仍需探索；不能称所有阶段已经无监督。最初口语暂缓CLI引用因采集刷新而失效，未执行动作；重新获取snapshot后才成功，失败记入摘要。两套实例均未出现listenIsolation，本批没有获得新波形或该题暂缓规则。

## 模具漏采与新规格

实际结算回顾有17张卡，包含16道评分题和暂缓口语。旧选择器只抓`button`和`role=dialog`，漏了`DIV role=button`；现在采集所有实际`[role]`，同一口语展开页面从17条元素事实增至35条，其中17张卡。`checkVisibility`包含布局上可见但视口外的卡，PNG只证明1200×732视口；不把全部卡称为当前屏幕均可见。

实际点击口语卡`Hot, please.`后，它显示绿色勾，且“你的答案”和“正确答案”都为`Hot, please.`。这仅是原版展示，不证明曾录音或评分。关闭后重开时指针附近的听力卡还出现答案，hover/focus/click触发差异继续列入frontier，不能直接认定只响应点击。

`freeze-current-walk.py`由原版JSON/PNG产生v33，完整保留v32的1912项，新增111项，共2023：两个回顾状态的17卡几何/角色/enabled、标题/提示、口语答案和整图。字体、滚动、其它卡展开与声音尚需更多可执行事实，未因这111项而宣称前端完整。源投影新增111全pass；全集210pass/0fail/1799not_run/14unavailable，历史缺事实不补为通过。

没有修改Swift或新跑原生。本批只重评上一实际`native-final`回执，94pass/56fail/1870not_run/3unavailable；新增111全not_run。候选回顾仍静态文本，需实现真实历史再验证，不能由原版自检冒充候选通过。原有整图/波形/暂缓/声音差异继续保留。

## 下一实施批次

先观察回顾触发和滚动，把实际当前实例历史（含暂缓口语）带到Swift，接回顾/关闭/重练并按同状态验证；继续其它实例寻找听音填空及暂缓、正常口语和其它未访分支。探索优先级依据实际失败与未访问frontier调整，而非反复跑已通过题。完整状态与负结果见[摘要](exploration-summary.json)。

## 复跑

```sh
node --test projects/duolingo-web/*.test.mjs
python3 -m unittest discover -v
python3 projects/duolingo-web/freeze-current-walk.py --out-dir artifacts/current-walk-freeze-new
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v33.json --observed projects/duolingo-web/evidence/english-current-walk-v1/reference.json --out artifacts/current-walk-source-new.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v33.json --observed projects/duolingo-web/evidence/english-isolation-presentation-v1/native-final/observed.json --out artifacts/current-walk-native-reassessment-new.json
```

12 Node/56 Python通过，最终Node重跑及两个JS语法检查通过；冻结器重编译逐字节相同。回执整体退出1是保留失败/未覆盖，不是通过。真实线上续跑需显式CLI/session及新输出名：`--current-only --current-steps 24 --stop-before-type listenIsolation`，每次先检查当前页面；只操作当前真实状态，不能把历史回执当当前会话重放起点。
