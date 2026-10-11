# 通用练习展示补漏：原版红心、底栏和普通听写

2026-10-11。固定参考是已实际采集的中文→英语原版完整练习，未用新实现替换原图。本批没有新源导航；通过检查既有DOM、两次结算快照及PNG发现遗漏。完整Goal保持active，仍需1:1前端、真实探索及消融，原始论文与负结果保留在[研究文档](../../../../docs/RESEARCH.md)。

## 先冻结，再实现

原版红心奖励页实际有五个IMG、四实一空，还保留“回顾本单元／重新练习／继续”。`after-settlement.json`与11秒后的`heart-reward-continue.json`均确认这些控件，不能当短暂残影忽略。`freeze-general-practice-presentation.py`原样保留v28全部1835项，v29新增五个图形矩形及三个控件的角色/enabled/位置/文案共16项，合计1851。源投影104pass/0fail/1747not_run，只是源证据自校验。旧候选归档按v29重评83pass/50fail/1707not_run/11unavailable，新缺失媒体矩形不能算通过。

通用课程夹具v2编译实际五个资源引用，旧v1保留，主课程v11不变。50个公开原版资源有摘要；仅新增两种心形SVG/PNG，原资产未重渲染。编译器首次把静态图标送到角色图片域的helper而断言失败，改为已有home/icon资源类别，不扩大域规则。新增可选heartResources不改变旧课程语义。红心页画面与原版底部控件补齐；回顾目前仍是静态文本，角色断言会失败，不能冒充已实现点击行为。重新练习仍只重放固定实例，自适应选择未知。

## 错误共享布局与反例修复

首次把普通listen复用listenTap蓝色播放布局。实际完整回放退出0，但听写整图RGB均值由[4.120,4.160,5.237]变为[6.030,3.970,4.057]，平均误差反而上升。保留native-01及负结果，回看实际q11 PNG发现原版是Bea旁的白色分段播放、对话尖角及多行文本框，而非独立蓝色按钮。

最终分开两种布局：普通听写复用原版Bea Rive及已记录播放图形，补白色分段框/尖角、正常/慢速播放、多行输入和空值提示；listenTap保留其独立蓝色布局。native-02通过真实键入Coffee or tea?继续完成整条47状态轨迹，再终止/重启。主六课不变，错答后3心、奖励后4心的回执见final-business.json。最终普通听写整图RGB均值[1.567,1.697,2.741]，**仍fail**；未据此宣称角色动画或字体完全一致。

红心页均值由[3.372,4.262,3.639]降到约[0.715,0.753,0.629]，**仍fail**。文字组合通过不证明整页通过，五颗心实际y203而源202.75，按钮位置也有小数差。没有放宽0容差或屏蔽字体/动画。全部诊断见image-delta.json。

## 验收与剩余差异

最终共同v29：89pass/55fail/1707not_run/0unavailable；新增16项为7pass/9fail。原88项练习要求为47pass/41fail，40张整图全fail。新失败包含五颗心0.25点误差、三个底栏几何和回顾角色；候选回顾是AXStaticText而原版是button，保留明确失败。原生执行通过与前端失败分别报告。

最终构建通过，24业务核心检查和完整56 Python检查通过。输入/渲染最后修订后又执行完整47状态原生回放。原始与归档PNG逐字节核验，仅重绑定相对路径后重新执行共同验收。编译重复输出字节一致，旧要求也完整结构比较一致。

继续探索：听写/听词组的“现在不做听力题”可见入口仍未在候选补齐；对应实际动作分支、回顾/重新练习真实语义、字体、精确小数布局、角色/图标帧和进度条颜色/权重均有差异或未知。正常口语、其余导航、音频相等及真实自主探索效果也继续。此批没有声学新增结论或RSI收益结论。

## 复跑

仓库根执行，原生输出须使用新目录：

```sh
python3 projects/duolingo-web/freeze-general-practice-presentation.py
python3 projects/duolingo-web/compile-general-practice.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
swift projects/duolingo-web/observe-frontend.swift artifacts/practice-presentation-new \
  projects/duolingo-web/fixture-reference-en-zh-v11.json \
  --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json \
  --reference-color-scheme light --observe-quests --exercise-general-practice
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v29.json \
  --observed artifacts/practice-presentation-new/observed.json --out artifacts/practice-presentation-new/result.json
```

前端比较预期非零退出，不能改断言使之通过。资源下载/隔离渲染使用已有fetch-english-resources.py、v2资源清单，读取其资源摘要；无需触发原版账户、发布或麦克风。
