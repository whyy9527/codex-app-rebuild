# VALORANT 决赛预测器

复刻指定 Bilibili Toy 的预测站体验，内容改为 2026 上海全球冠军赛，
只预测 10 月 17 日败者组决赛与 18 日总决赛。

从本目录运行：

```sh
npm run build
python3 -m http.server 5173 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:5173/`。这是本地预览，未部署到外部站点。

更新官方数据并重新构建：

```sh
npm run sync-data
npm run build
```

官方对阵仍为 TBD 时，应用保留待定标识，通过 16 日的晋级情景分析两场
可能对阵。它不会把用户选择的情景写成官方赛果。八个原版模型频道保留；
只接入经核实的实际输出，其余显示待预测。凭证只通过现有 CLI 或环境变量
使用，不进入应用或数据文件。当前运行证据及剩余差异见 [STATUS.md](STATUS.md)。

项目方法与命令入口为 [rebuild.json](rebuild.json)，素材和来源见
[ASSET_NOTICES.md](ASSET_NOTICES.md)。浏览器验收的细节由
[contracts/scenarios.json](contracts/scenarios.json) 连接。
