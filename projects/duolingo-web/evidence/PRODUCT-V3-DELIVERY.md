# 产品修正 v3 交付审计 · 2026-10-10

当前运行 Goal 的六项标准逐项核验，契约仍由用户对话、原生 Goal 和 PRODUCT-ACCEPTANCE-v3.md 拥有。本文记录证据，不重新定义完成范围。旧完成判断的[撤回与反思](../../../docs/REBUILD-RETROSPECTIVE-2026-10-10.md)继续保留。

| Goal 标准 | 当前实际证据 | 结论与边界 |
| --- | --- | --- |
| 1 原版观察 | [观察与入口对应表](PRODUCT-V3-REVIEW.md)、[原版截图来源](product-v3-reference/sources.json)、既有 duo-04/05/06/08/14/21 记录 | 实际访问匿名主页、选择、配对、退出、导航、指南；拼句使用同日既有实际截图。选项与正确反馈的media-playing已观察。用户私人截图未提交。More展开内容及账号后端仍未知，没有冒充已观察。 |
| 2 真正学习主页 | [UI35项](product-v3-final/ui.json)、home-wide/home-narrow/unlocked-home/completed-home 截图、LearningView与LearningModel | 自然启动1200×760；白底三栏、导航、横幅、弯曲节点、右栏。实际课程、完成/锁定/重练、解锁、统计与跨进程恢复；数字来自进度。截图入口逐个对应，线上账户/购买/竞争明确未连接。 |
| 3 视觉对应 | [可切换的并排对照](product-v3-comparison.html)、product-v3-final的22张实际窗口截图 | 已逐张查看全部22张；主页、图卡、两列配对、拼句角色/发音提示/答案横线/词块、顶栏与底部反馈区对应。绿色#58cc00、正确#d7ffb8、粉红错误、青蓝选中、圆润字重、2px边框、厚按钮和节点阴影。保留素材、题量、字体实现和间距差别，不声称像素一致。1200宽窗与820窄窗实测；窄窗侧栏图标、课程滚动，底部Check可见。 |
| 4 实际声音 | [七段应用输出回执](product-v3-final/audio.json)、LearningAudio、AudioChecks与采集器 | 实际UI触发发音、正确、错误、配对自动完成、结算与拼句提示，有非零系统音频信号；静音期间完成配对，peak/RMS为0。静音立即停止/阻断、恢复可播、重启偏好保留；单播放器/单语音引擎替换前声。四种原创WAV可解码且彼此不同，播放器时间推进。回放样例本地artifacts/product-v3/audio-04/correct-replay.wav；数字输出已证实，物理音量/主观音色未代验。 |
| 5 完整纵向体验 | UI35项及[冻结原生12项](product-v3-candidate-07.json) | 实际主页→选择正误→配对→错题→完成→解锁第二课→拼句正误/撤回/错题→完成→主页，重启恢复；退出取消/确认与导航课程入口均实测。课程/状态/存储在Foundation核心，交互在Model，显示在View；展示不读取答案字段决定插画或提示。 |
| 6 验证及交付 | Swift构建、核心5项、UI35项、音频7段、[原生12项](product-v3-candidate-07.json)、README/AGENTS/ARCHITECTURE/ROADMAP/历史审计 | 冻结v2规格/夹具/12项断言未变。私有Git提交、推送、远端一致和最后客户端启动在本次宿主操作记录核验。没有公开、部署或发布。Dream-RSI/Cordis及旧失败/零收益保留。 |

## 不隐藏失败

本轮 ui-08 发现拼句Check因展示条件误改而缺失，[原始失败回执](product-v3-final/prior-ui-failure.json)保留；修复生产条件后同一检查继续要求Check存在，ui-09全35项通过。没有改题库或放宽断言。

冻结复验06记录11通过、1不可用：运行中改了对照HTML说明，源码摘要发生变化，reset完整性保护拒绝旧回执。保留[06原始结果](product-v3-candidate-06.json)；停止修改输入后完整重跑07，不把不可用算通过。

## 启动与复验

从仓库根运行，macOS 14+、Swift6。音频采集检查另需支持当前ScreenCaptureKit API的宿主SDK、已授予屏幕录制/辅助功能权限；不需要麦克风：

```sh
swift build --package-path projects/education-swift --product LingoSeed
projects/education-swift/.build/debug/LingoSeed --fixture projects/duolingo-web/fixture-v2.json --progress artifacts/my-lingoseed/progress.json
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/product-ui-checks.swift artifacts/ui-new
python3 projects/duolingo-web/product-audio-checks.py artifacts/audio-new
python3 -m workflows.rebuild.cli verify --workspace . --spec projects/duolingo-web/spec-v2.json --targets projects/duolingo-web/targets-v2.json --target candidate --frozen projects/duolingo-web/evidence/batch-v2.json --timeout 360 --max-seconds 1800 --out artifacts/native-new.json
```

检查依次运行，期间不编辑纳入摘要的源码/HTML或验收输入。输出目录换新，已有用户进度不重置。普通启动的静音偏好保存在进度文件旁 `.audio.json`。主页侧栏及练习右上角都可切换声音。

## 保留的产品边界

本次是以Duolingo网页为参考的Swift教育基座产品修正：原创两课、三题型、原创角色/声音与本地进度。账户同步、在线支付/排行、完整课程内容、语音识别、教育效果、iOS构建均没有声称交付；界面明确服务未连接。零生命不阻断、错误配对不扣生命、主动退出丢弃未完成尝试为已记录产品决策。不能把本次验收结论改写成整个Duolingo等价、全部未知规则覆盖或RSI有收益。
