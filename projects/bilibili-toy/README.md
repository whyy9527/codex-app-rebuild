# Bilibili Toy 本地复刻案例

原版入口：<https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html>。
目标与完成条件由 `rebuild.json` 连接原生 Goal；方法见仓库复刻工作流。

当前可运行基线使用原站公开发布的静态应用代码、数据、字体与素材，
配合本仓库编写的本地启动、只读接口与参数转发适配。这不是独立重写的应用源码。
发布包和原始证据保存在被 Git 忽略的 `private/` 中，不随仓库再分发。
来源及摘要由准备命令写入 `private/resources.json`。

从仓库根运行：

```sh
python3 -m projects.bilibili-toy.tools.prepare
python3 -m projects.bilibili-toy.tools.serve --port 4617
```

打开 <http://127.0.0.1:4617/>。准备命令需要 curl 和原版公开资源可访问；
本地服务只监听 loopback。准备成功后应用数据与素材从本地读取。
右侧 Toy 平台侧栏和顶部作者／关注／话题区域已按用户截图要求删除，
主内容占满释放出的宽度。原版静态发布包保留；派生模块只调整分享基址
并取消挂载顶部作者组件。公开只读响应快照供原应用可选 SDK 读取，
来源及摘要位于 `private/site/host/provenance.json`。
账号写入未接入，外链仍打开原站；服务工作线程及远端遥测不注入。
战报及二维码基址适配为当前域名；原版模块保持原字节，派生的
`assets/local-index.js` 和变更摘要记入资源清单。外壳 iframe 使用原版实测
沙箱权限，原生确认框未开放；因此“重新预测”与原版一样不清空草稿。

共同 E2E 使用 `scenarios.json` 与 `frontend-contract.json`。原生 UI 回放
须由当前 Codex 在 `cua_repl` 中给 `tools/e2e_native.mjs` 的
`installNavigationE2E` 传入实际 Edge App、`node:fs/promises` 和
`private/e2e-bridge` 路径，并逐条 await 服务请求。运行前选中目标
原版或本地标签页；来源守卫不匹配会停止，不争抢其他标签页。

```sh
python3 -m projects.bilibili-toy.tools.e2e source --out projects/bilibili-toy/private/reference-new
python3 -m projects.bilibili-toy.tools.e2e candidate --out projects/bilibili-toy/private/candidate-new
python3 -m workflows.rebuild.project run --workspace . --project projects/bilibili-toy/rebuild.json --command compare --observed projects/bilibili-toy/private/candidate-new/observed.json --out projects/bilibili-toy/private/comparison-new.json
```

RSI 使用 `rsi/config.json` 与 `tools/native.mjs`，桥接方法相同；每次 collect
须实际服务新的发现与独立评价请求。历史池是不可覆写的探针证据，
不是浏览器远程状态备份。页面刷新保留浏览器存储与真实时钟。

回放阶段与侧栏旅程使用 `journeys.json` 和 `rebuild.json` 指向的本地冻结契约，运行
`python3 -m projects.bilibili-toy.tools.e2e source --suite journeys --out <新证据目录>` 或相同的 candidate
命令，并在 CUA 装载 `tools/journey_native.mjs` 的 `installJourneyE2E`。
该驱动按相同动作采集赛前、事件跳转、四个阶段及侧栏状态。

历史结果与局限见 `evidence/`。导航、方法接线或单元测试通过不能
替代完整视觉、播放、声音、预测保存与移动端验收。

手机响应式观察使用 `mobile.json` 和 `tools/mobile_native.mjs`。在 CUA 中
给 `installMobileUI` 传入实际 Safari App、文件 API、完整入口 URL、
新证据目录及实测窗口 UUID；两端使用同一准备与操作。原版参考为
375×667、99% 截图缩放、2x 像素比和 Safari 默认 UA，滚动归零并将
播放器暂停在赛前、1x、关闭闲置换台。空草稿通过独立测试 origin
准备，保留已有草稿。原版 Android UA 会触发 B站 App 限制，单独记录。

```sh
python3 -m projects.bilibili-toy.tools.freeze_mobile --reference <原版-observed.json> --candidate <候选-observed.json> --out projects/bilibili-toy/private/mobile-contract-new
python3 -m workflows.rebuild.project run --workspace . --project projects/bilibili-toy/rebuild.json --command mobile_compare --observed <候选事实.json> --out projects/bilibili-toy/private/mobile-comparison-new.json
node projects/bilibili-toy/tools/mobile_native.test.mjs
```

完整截图保留，比较只取实测的完整手机视口；不遮挡作者区域、侧栏、
倒计时或交互状态来取得图片通过。最新手机结果见
`evidence/mobile-2026-10-15.json`；内容检查通过不代表整页视觉通过。

播放器键盘旅程在 `journeys.json` 的 `keyboard` 中，复用同一 Safari
驱动的 `focusPlayer`、`key` 和 `selectModel`；后者传入
`{prepare:false}` 时保留真实切换后的自动播放行为。按共享步骤执行后，
原始 AX、截图及按键时间戳进入各端新 private 目录。倍速按钮没有 AX
选中值，需从原始截图观察标签，并保存对应图片摘要，不能用预期值回填。

```sh
node projects/bilibili-toy/tools/keyboard_evidence.mjs freeze <原版-observed.json> projects/bilibili-toy/private/keyboard-contract-new
node projects/bilibili-toy/tools/keyboard_evidence.mjs observe <候选-observed.json> projects/bilibili-toy/private/keyboard-facts-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/bilibili-toy/rebuild.json --command keyboard_compare --observed <候选事实.json> --out projects/bilibili-toy/private/keyboard-comparison-new.json
```

冻结器从前后 AX 重新提取事实；采样期间变化的原版字段保持 pending，
不成为静态参考。结果和观察器修订见 `evidence/keyboard-2026-10-16.json`。

八个 AI 频道的桌面视图由 `journeys.json#channels` 定义，CUA 中给
`tools/channel_native.mjs` 的 `installChannelUI` 传入实际 Safari、文件
API、完整入口、独立输出目录和窗口 UUID。`prepare` 后按模型调用
`selectModel`，再逐视图 `navigate`、`collect`；同一套动作操作原版和候选。
普通桌面模式及手机模式分别记录，不复用两者的截图几何。

选手表的 AX 行会随实际滚动逐段出现。驱动保留各段原文和截图，冻结器
重新提取完整原生表格的行数；`showing … of … items` 不能直接作为行数。
通用容器仍被截断时停止，不把末尾片段当成完整页面。

```sh
node projects/bilibili-toy/tools/channel_evidence.mjs freeze <原版-observed.json> projects/bilibili-toy/private/channel-contract-new
node projects/bilibili-toy/tools/channel_evidence.mjs observe <候选-observed.json> projects/bilibili-toy/private/channel-facts-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/bilibili-toy/rebuild.json --command channel_compare --observed <候选事实.json> --out projects/bilibili-toy/private/channel-comparison-new.json
node projects/bilibili-toy/tools/channel_native.test.mjs
```

范围和结果见 `evidence/channels-2026-10-16.json`。内容比较覆盖主视图，
比赛详情、战报展开和整页视觉仍需各自的实际证据。

冻结回放契约：

```sh
python3 -m projects.bilibili-toy.tools.freeze_journey --reference projects/bilibili-toy/private/reference-journey/observed.json --out projects/bilibili-toy/private/contract-new.json
```

完整原版回放文字只进入本地 private 契约。原生截图尺寸变化后，先实测
浏览器内容边界，再给 e2e 命令传入 `--content-top`（导出截图像素坐标）；
旧参考尺寸不匹配时保留 unavailable，不缩放或遮罩以取得通过。

入围赛预测使用 `prediction.json` 和 `tools/prediction_native.mjs` 的
`installPredictionE2E`。本轮使用 Safari 原生 App，因 Edge 的嵌套内容点击与
焦点采集不稳定。驱动要求空草稿，遇到已有草稿会停止；它不自动清空预测。
实际原版“重新预测”未出现确认且没有重置，因此本轮用新建的临时私密窗口
准备空状态，再在同一窗口回放本地端。运行命令：

```sh
python3 -m projects.bilibili-toy.tools.e2e source --suite prediction --case playin --content-top 112 --out projects/bilibili-toy/private/prediction-reference-new
python3 -m projects.bilibili-toy.tools.e2e candidate --suite prediction --case playin --content-top 112 --out projects/bilibili-toy/private/prediction-candidate-new
node projects/bilibili-toy/tools/freeze_prediction.mjs projects/bilibili-toy/private/prediction-reference-new/observed.json projects/bilibili-toy/private/prediction-contract-new.json
node projects/bilibili-toy/tools/prediction_native.test.mjs
```

`112` 是本轮 Safari 导出截图中的实测内容起点，复跑前须重新测量。
冻结器从实际 AX 重新提取事实；同名的两场比赛保留独立控件编号。
入围赛的历史比较见 `evidence/prediction-2026-10-15.json`；覆盖入围赛及
刷新后的草稿保留。完整随机赛程内容、资料授权、声音和移动端需分别验收。

预测用例分别准备状态：`playin` 要求空草稿；`share` 要求没有选中胜者或
锁定结果，并使用实际原版 UI 复制的战帖编码；`locked` 要求已有完整、锁定
的测试预测。后者核验各端自己的锁定时间及选择在刷新、重置尝试和复制后
保留，不用随机生成的不同对阵宣称整张预测内容一致。选择一个 `--case`
后由同一 `installPredictionE2E` 服务，两端使用同一用例。

完整匿名竞猜使用 `prediction.json#tournament`，在 CUA 给
`installTournamentUI` 传入实际 Safari、文件 API、完整入口、新输出目录与
窗口 UUID。按协议调用 `begin/click/fill/capture/reload`，保留每次选择前后
AX。两端各自生成随机对阵，选择策略只读取实际显示概率；不复制存储或种子。
好友导入使用原版 UI 实际复制的战报编码，两端导入相同编码。

```sh
node projects/bilibili-toy/tools/tournament_evidence.mjs freeze <原版目录> projects/bilibili-toy/private/tournament-contract-new
node projects/bilibili-toy/tools/tournament_evidence.mjs observe <候选目录> projects/bilibili-toy/private/tournament-facts-new.json
python3 -m workflows.rebuild.project run --workspace . --project projects/bilibili-toy/rebuild.json --command tournament_compare --observed <候选事实.json> --out projects/bilibili-toy/private/tournament-comparison-new.json
node projects/bilibili-toy/tools/prediction_native.test.mjs
```

本轮验证 46 次逐场选择、七轮记录、锁定与编辑草稿的关系、分享和好友
默契度。各端锁定时间只和自身记录比较；随机赛程验证晋级与配对规则。
原始整页截图差异仍保留，详情见 `evidence/tournament-2026-10-16.json`。

用户后续指定的发布目标是 `https://s16.xinxiayiyan.com/`；完成条件修订见
`rebuild.json`，用户后续要求先发布当前预览版；完整复刻验收继续。现有官网首页保留。

预览版发布使用独立的 `bilibili-toy-s16` systemd 服务（128 MiB、25% CPU），
仅绑定代理 Docker 网络的宿主网关，外部流量经现有 Nginx TLS 入口。默认本地
启动仍只监听 loopback。无需构建容器或修改现有官网部署仓库。

```sh
python3 -m projects.bilibili-toy.tools.certificate --install
python3 -m projects.bilibili-toy.tools.deploy --publish
```

先提交和推送审核后的部署输入。发布包在本地 ignored `private/deploy/`，
逐文件 SHA-256 与包摘要核验；短期私有 OSS 对象用于传输。服务器暂存必须
为磁盘上的 `/var/tmp/bilibili-toy-s16-*`。线上 `/release.json` 提供版本及
验收状态。公共 HTTPS、资源和 UI 验证通过后才删除传输对象与压缩包，保留
旧 release、代理配置及回退目录。回退命令为服务器上的
`sh /opt/bilibili-toy/current/deploy/rollback.sh <本次暂存目录>`。首次发布
回退会停用本站入口；后续回退恢复上一版本，不修改现有官网。

公网 HTTP 当前被阿里云 ICP 接入层拦截，HTTP-01 不能用于签发证书。
本站改用 Certbot DNS-01；TXT 验证及清理由本机 Aliyun CLI 完成，
DNS 凭证不上传服务器。证书与私钥只进入本机 ignored private 目录、
短期私有传输对象及服务器 TLS 目录，不进入 Git 或应用发布包。
`tools.certificate --install` 在接近到期时续签并安装；安装后需要
`docker exec nginx-app nginx -t` 与平滑 reload。当前没有安装本机定时任务，
维护者需在证书到期前执行该命令。访问本站使用完整 HTTPS 地址。

声音行为协议在 `audio.json`。先在 CUA 中将 `tools/audio_native.mjs` 的
`installAudioUI` 绑定到本任务独占的 Safari，再用 `prepare` 准备各用例。
只录本任务 Safari PID 的应用输出；录音前确认其他 Safari 窗口没有播放。
CLI 复用仓库已有 ScreenCaptureKit collector，不传 Swift AX 动作、不录
麦克风或屏幕。启动后必须等本次 `ready.json`，再由 CUA 调用
`run({url, dir, seconds:3})` 实际播放和暂停；本轮使用 30 秒采集窗口
以容纳工具往返，12 秒早期尝试因动作未落在窗口内而无效。

```sh
python3 -m projects.bilibili-toy.tools.capture_audio --pid <本任务实际 Safari PID> --seconds 30 --out <新的 private 录音目录>
python3 -m projects.bilibili-toy.tools.freeze_audio --captures <private 两端录音目录映射 JSON> --out <新的 private 契约目录>
python3 -m workflows.rebuild.project run --workspace . --project projects/bilibili-toy/rebuild.json --command audio_compare --observed projects/bilibili-toy/private/audio-contract-v1/candidate.json --out <新的 private 比较结果.json>
```

采集必须顺序进行：上一个 collector 终态后才能切换到下一端页面。
每次使用新目录，录音、UI 动作时间和采样帧共同构成证据。分析依赖
本机可选 NumPy/SciPy。共同断言只覆盖已观察 BP 场景的输出、静音及
恢复；首个音效波形和原版重复测量单独报告，不作为全音效一致判定。
历史录音早于用户删除两个 UI 区域，详见 `evidence/audio-2026-10-15.json`。
