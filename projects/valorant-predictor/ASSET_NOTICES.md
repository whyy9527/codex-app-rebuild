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
