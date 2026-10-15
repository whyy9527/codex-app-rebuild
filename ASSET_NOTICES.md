# Sources and rights

The front end is independently written for this repository. The user's reference
is [S16 AI 预测大赛](https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html),
content version `43482999941120-v26695`. Its code, datasets, fonts and character
art are not redistributed by this project.

Tournament facts are normalized from the public Riot Games VALORANT Esports
site. `data/event.json` retains the official source URLs and response digest.
The stage/date source is [Champions Shanghai: Everything You Need To Know](https://valorantesports.com/en-US/news/champions-shanghai-everything-you-need-to-know).

Team logo URLs are taken from the official schedule's team records. Decorative
agent image URLs are taken from the [official agent directory](https://playvalorant.com/en-us/agents/).
Those marks and images remain the property of Riot Games and the respective
teams. The source files contain URL references, not redistributed media files;
the repository's MIT license does not grant rights to those external assets.
No partnership with Riot, the teams, the reference author or model providers is
implied. The decorative agent/channel pairing is a design choice.

`data/gpt-6.1-sol-forecast.json` and `data/deepseek-forecast.json` contain actual,
independent model responses after schema validation. Model identity is verified
from the Codex CLI startup header or provider response plus official model
catalog, not a model-authored identity claim. The earlier
`evidence/current-session-analysis.json` is explicitly a current-session analysis and is not
served as GPT-6.1 sol's independent output.

The app bundles the unmodified OPPO Sans 4.0 font from the official ColorOS download
with its complete license notice in `assets/fonts/OPPO-Sans-LICENSE.txt`. The included
license permits bundling unmodified fonts with software and requires this attribution
and retained notice. Font bytes match `data/font-source.json`; they are not licensed
under this repository’s MIT license. No subset or format conversion is shipped.

## MiSans、Anton 与 JetBrains Mono

本应用使用 MiSans 字体，版权归 Xiaomi Inc.。未修改的 MiSans Regular WOFF2 来自
[小米官方下载](https://hyperos.mi.com/font/en/download/)，仅随本应用使用与分发，
不是独立字体镜像；完整许可见 `assets/fonts/MiSans-LICENSE.pdf`。

Anton 与 JetBrains Mono 来自 Google Fonts 官方仓库，遵循 SIL Open Font License 1.1，
完整版权和许可分别保存在 `assets/fonts/anton-OFL.txt`、`assets/fonts/jetbrainsmono-OFL.txt`。
全部字体来源和 SHA-256 见 `data/font-source.json`；原始文件未改编或子集化。
