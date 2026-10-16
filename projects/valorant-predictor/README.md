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
人像采用用户指定 S16 页面中对应模型的半身立绘与头像。凭证只通过现有 CLI 或环境变量
使用，不进入应用或数据文件。当前运行证据及剩余差异见 [STATUS.md](STATUS.md)。

项目方法与命令入口为 [rebuild.json](rebuild.json)，素材和来源见
[ASSET_NOTICES.md](ASSET_NOTICES.md)。浏览器验收的细节由
[contracts/scenarios.json](contracts/scenarios.json) 连接。

发布流程与独立站点恢复说明见 [deploy/README.md](deploy/README.md)。

首页战术沙盘的共同输入、真实生成与校验边界见 [TACTICAL.md](TACTICAL.md)。用户已批准本轮四模型真实沙盘与黑白金改动发布，具体回执与状态见 [STATUS.md](STATUS.md)。
