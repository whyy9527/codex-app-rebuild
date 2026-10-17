# VALORANT 决赛预测器

复刻指定 Bilibili Toy 的预测站体验，内容改为 2026 上海全球冠军赛，
只预测 10 月 17 日败者组决赛与 18 日总决赛。

从本目录运行：

```sh
npm run build
python3 -m http.server 5173 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:5173/`。用户已确认独立发布目标 `https://valorant.xinxiayiyan.com/`；当前发布回执见 [STATUS.md](STATUS.md)。

更新官方数据并重新构建：

```sh
npm run sync-data
npm run build
```

官方对阵仍为 TBD 时，应用保留待定标识，通过 16 日的晋级情景分析两场
可能对阵。它不会把用户选择的情景写成官方赛果。只保留 GPT、DeepSeek、豆包、MiMo 四个已完成预测的模型；
人像采用用户授权生成的四位透明底娘化 AI 立绘，保留原角色辨识特征；来源、历史素材与生成提示词见素材记录。凭证只通过现有 CLI 或环境变量
使用，不进入应用或数据文件。当前运行证据及剩余差异见 [STATUS.md](STATUS.md)。

项目方法与命令入口为 [rebuild.json](rebuild.json)，素材和来源见
[ASSET_NOTICES.md](ASSET_NOTICES.md)。浏览器验收的细节由
[contracts/scenarios.json](contracts/scenarios.json) 连接。

发布流程与独立站点恢复说明见 [deploy/README.md](deploy/README.md)。

首页战术沙盘的共同输入、真实生成与校验边界见 [TACTICAL.md](TACTICAL.md)。用户已批准本轮四模型真实沙盘与黑白金改动发布，具体回执与状态见 [STATUS.md](STATUS.md)。


## 赛前证据包与实际模型链路

`data/evidence-v2.json` 保存来源、首次观察时间、事实ID、19场四强相关系列赛和46图统计。
旧输出保持原文件，时点更正见 `data/forecast-inputs.json`。比赛开赛时间不等于知识截止时间；
源页未提供历史发布时点时不能补造。包内prediction_status是冻结时的状态，实际新运行以
`data/forecast-v2/models.json` 为准；输入冻结后不修改来迎合结果。

采集/编译（需要 `pip install -r scripts/requirements-evidence.txt` 与 `pdftotext`）：

```sh
python3 scripts/evidence_pack.py --collect --cache private/evidence-cache-new
python3 scripts/run_evidence_models.py --out private/evidence-run-new
```

第二条仅准备共同输入、提示词、schema与预算，不调用模型。用户2026-10-16最终确认先不加
人格或辩论：每家一次逐因素有证据判断→预测BP/选边→逐图概率→程序计算系列赛与共同种子
抽样→模型明确虚构的模拟复盘。参考对标公开流程，未复制未公开权重公式。

`forecast_contract.py` 拥有七因素、三条件对阵和证据引用契约；`mapSeriesDistribution`
只计算五图给定概率的BO5分布，仍假设地图独立。`compute_v2.mjs` 计算条件夺冠概率和一次
模拟。概率预测与单次剧情分开；原始响应、请求、模型目录和身份回执保留在私有运行目录。

真实生成使用 `--run --approval-file <approval.json>`，授权须绑定该包SHA、batch=evidence-v2、
四家精确频道、每家最多4次和额外API总额¥10。计划每家2次，失败补调用也计数；
不换模型、不充值、不订阅，GPT只用现有ChatGPT额度。旧2/2账本不可复用。
结果写 `data/forecast-v2/`，校验后进入运行清单；旧预测不覆盖。

当前走位仍是既有单独Ascent固定假设场景，不冒充本轮任意BP地图的实际阵容或FPS战斗。
