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
平台侧栏复用公开发布 UI，作者信息和相关内容接入公开只读响应快照；
快照来源及派生包摘要位于 `private/site/host/provenance.json`。默认构建
复用已有快照，显式更新使用 `python3 -m projects.bilibili-toy.tools.prepare_host --refresh`。
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

用户后续指定的发布目标是 `https://s16.xinxiayiyan.com/`；完成条件修订见
`rebuild.json`，发布在完整验收之后执行。现有官网首页保留。
