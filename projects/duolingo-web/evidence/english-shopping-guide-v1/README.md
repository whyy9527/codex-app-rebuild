# 英语购物指南与下一购物实例：探索发现模具遗漏

实际源为中文母语→英语、第2阶段购物指南 `/guidebook/en/11`，505宝石／1连胜／10分夹具独立于旧530／2状态。观察保留在[source](source/)，没有改用自创内容或固定页面子集作为完成标准。

指南五个原版播放入口均实际点击，取得对应公开语音；实际滚动、返回，以及hat的hover／click／Enter也保留。hat未出现可见释义，不能据此发明交互或认定所有词不可点击。采集器原来漏掉逐字且aria-hidden的整句英文和roleless tabindex词语，本批补独立rendered_text_groups及focus_candidate库存：5整句／28词语；库存不是已执行覆盖。真实浏览器字体检查发现CSS500英文实际用Duolingo400，中文字幕为PingFangMedium，翻译为PingFangRegular，分别接入Swift，没有全局改写字重。

Swift接原购物指南的文本、几何、静态原角色、词下划线、返回、五段原语音及实际speaker Lottie。录制自有Swift应用第一语音按钮7秒，与该原文件对齐相关系数0.99957（[诊断](speech-diagnostic.json)）；这是实际应用输出与源文件比较，原版浏览器声学输出仍不可用，未证明两应用完整音效一致。没有录麦克风。

严格v66保留v65全部12029项，追加793，共12822项。[最终原生轨迹](native-final/observed.json)4状态／5播放／滚动返回，无驱动失败；[严格结果](native-final/frontend-v66.json)142pass／28fail／12400not_run／252unavailable，3整图仍fail。旧字体版124pass／46fail保留在[native-before-font](native-before-font/)。修字体后顶部图mean RGB差从[6.78449,4.58274,6.09768]变为[6.85255,4.69078,6.22408]，反而稍差；底部图下降。不能用文本通过数增长宣称视觉改善。首次录音器缺失失败保留在[native-missing-recorder](native-missing-recorder/)。同二进制旧主页夹具独立5状态结果322pass／103fail，见[native-home-regression](native-home-regression/)，不与本轨迹相加。

继续从指南返回点第2/5购物课，实际发现新词形orderTapComplete。第一次旧模具错误要求尚未填出的完整句可见；修为独立的可见句架、示例、空格数和词库多重集比较。第二次错误点击全页同名按钮且没有切换空格，原版判错并扣心，原始失败保留。修为实际选择每个空格、只从word-bank取词后，后续原版`Yes, I want a shirt.`题接受。第二实例另发现DOM逐词换行让`This __ is on sale.`的旧context检查误失败；只规整排版空白，保留词义及词库检查，真实续跑接受。见`grocery-next-current-01`至`06`；第二实例尚未接Swift，不宣称自适应选课完成。口语跳过后的“麦克风已关闭／15分钟后恢复”反馈必须实际继续，旧自动驱动超时也保留。

[历史](history.json)63状态／34记录边，[frontier](frontier.json)2014未解决状态动作。hover／click无弹层保留unavailable；五次播放记录为真实动作流水，没有虚构五个目的状态。新增分支导致队列增长，不代表探索退步或全部需求已知。RSI原论文保留于[研究文档](../../../../docs/RESEARCH.md)；本批是实际反馈驱动的补漏，尚无同起点同预算的RSI效果消融。

优先继续：主页及指南右栏滚动同步、原导航link角色和整图；词语焦点／释义未知行为；第一阶段英语指南仍落旧渲染内容；当前第二购物实例的前端冻结及Swift接入；下层路径、故事／电台及未访问入口。重置／独立原版启动的完整等价性、跨实现音效、真实消融仍待验证，完整Goal active。

## 复跑

仓库根执行；输出目录须未存在。源采集使用正在访问原版的自有session；不要为复跑重置真实进度。

```sh
python3 projects/duolingo-web/compile-shopping-guide.py --out-dir artifacts/shopping-compile-new
python3 projects/duolingo-web/freeze-shopping-guide.py --out-dir artifacts/shopping-freeze-new
python3 -m projects.duolingo-web.compile-shopping-guide-frontier --out-dir artifacts/shopping-frontier-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/shopping-owned-audio
swift projects/duolingo-web/observe-frontend.swift artifacts/shopping-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-shopping-guide-v1/prepared-progress.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/shopping-guide-scenarios-v1.json --audio-recorder artifacts/shopping-owned-audio
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v66.json --observed artifacts/shopping-native-new/observed.json --out artifacts/shopping-native-new/frontend-v66.json
node --test projects/duolingo-web/*.test.mjs
python3 -m unittest discover -v
```

32核心／61Python／19Node通过。编译数据、冻结契约及前沿可复现；全部资源来源及hash见[resources.json](resources.json)，实际speaker动画gzip解码证据见[speaker-animation-resource.json](speaker-animation-resource.json)。动画相位未证明一致，未放宽已有断言。
