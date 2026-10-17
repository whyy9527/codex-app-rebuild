# Sources and rights

The front end is independently written for this repository. The user's reference
is [S16 AI 预测大赛](https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html),
interaction reference originally recorded at `43482999941120-v26695`.
On 2026-10-16 the user explicitly requested its four model-persona portraits.
Historical half-body and head images for GPT, DeepSeek, Doubao and MiMo are
retained from version `43482999941120-v26947`; model mapping, URLs and
SHA-256 digests are retained in `data/assets.json`. The source author is
我叫张大喵. Its application code, LoL characters, match data and predictions
are not shipped. Attribution does not imply a provider endorsement; image rights
remain with the respective rights holders and are outside the repository MIT license.

Tournament facts are normalized from the public Riot Games VALORANT Esports
site. `data/event.json` retains the official source URLs and response digest.
The stage/date source is [Champions Shanghai: Everything You Need To Know](https://valorantesports.com/en-US/news/champions-shanghai-everything-you-need-to-know).

Team logo URLs are taken from the official schedule's team records and remain
the property of Riot Games and the respective teams. The previous decorative
VALORANT agent images have been removed from the runtime asset manifest.
No partnership with Riot, the teams, the reference author or model providers is implied.

The four files listed in `data/model-forecasts.json` contain actual,
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

## Explicitly fictional match content

The four files listed in `data/model-fiction.json` contain actual model-authored
fiction bound to the same deterministic series results. BP, round scores, stories,
MVPs and 0–10 ratings are labelled fiction and do not represent real performances.
The player-name index prioritizes official Vitality, G2 and 100 Thieves roster pages;
LOUD is explicitly supplemented by the VLR esports database. Names are an index,
not a claim about confirmed match-day starters. Map names come from Riot's game
catalog; the seven-map creative pool is not certified as the tournament's pool.
Source URLs and limits are in `data/fiction-context.json`. No invented quotes or
endorsements are attributed to players.

## Tactical sandbox demonstration

The Ascent/Haven minimaps and ten agent display icons are unmodified Riot Games
game assets obtained via the public, unofficial [Valorant-API](https://valorant-api.com/)
catalog on 2026-10-16. Source URLs, UUIDs and SHA-256 digests are retained in
`data/tactical-assets.json`. These assets are not covered by the repository MIT license.
This free, nonofficial community visualization was created under Riot Games'
[Legal Jibber Jabber](https://www.riotgames.com/en/legal) policy using assets owned
by Riot Games. Riot Games does not endorse or sponsor this project.

The ten-agent lineup and map graph are fixed inputs. Each published tactical plan
contains independently generated model choices of nodes and times. The viewer
expands those choices along the frozen graph; these are hypothetical movement
plans, separate from event BP predictions, not confirmed team selections, match
telemetry, simulated combat or a validated FPS simulator.

## 2026-10-16 font loading optimization

Body copy and Chinese headings use the device's system sans-serif stack. OPPO
Sans and MiSans are retained as unmodified historical assets with their complete
notices, but are no longer declared or requested by runtime CSS. No font subset
or conversion is made. Anton and JetBrains Mono remain on-demand Latin/numeric
fonts retaining `font-display: swap`, so system text remains available while
these small optional display resources load.

## User-selected GPT character · 2026-10-16

The unmodified `assets/models/gpt-dragon.webp` is the hero image and first
“GPT 娘 · 角色立绘” item on the user-specified
[GPT character page](https://genderswapai.com/zh-CN/ai-gijinka/gpt).
Creator: **ZipZipPipe**; the page links the
[original post](https://www.bilibili.com/opus/1233069202138464289).
The white-haired dragon character is used as a model selector illustration,
not as an official OpenAI identity. It is displayed with proportional CSS sizing.
No third-party scripts, generator, registration or paid image calls are used.
The file, page, creator, original-post URL and SHA-256 are recorded in
`data/assets.json`; image rights remain with their respective holders. The
previous S16 GPT assets are retained as historical sources.

## 分批因果回放素材

当前首页的七张真实小地图与特工头像取自 [Valorant-API](https://valorant-api.com/)，底层游戏资产权利归 Riot Games 等相应权利人。地图来源UUID、资源URL、图像SHA-256、真实callout区域和坐标保留在 data/causal/map-context.json；实际选用特工头像来源及摘要保留在 data/causal/agents.json。区域坐标源于目录变换，模型路线是区域序列假设，不是官方轨迹、测绘导航网格或已验证FPS可行路径。

## 2026-10-17 图片 BP 与官方赛事视觉

七张地图场景图来自既有 Valorant-API 同 UUID 的游戏资源 splash，地图名与当前小地图逐一核对。来源 URL、原图摘要、比例缩放和 WebP 派生摘要见 `data/causal/map-art.json`；战术播放继续使用原有真实小地图，不把宣传图当作位置坐标。

上海赛事龙形主视觉和金色标题装饰直接取自用户指定的腾讯/Riot 官方活动页 https://val.qq.com/act/a20260828shanghai/index.html ，来源及处理摘要见 `data/causal/event-art.json`。仅作独立预测站的赛事视觉引用，不接入登录、领取奖励或官方互动接口，也不表示官方背书。原图权利归腾讯、Riot Games 等相应权利人；页面仍保留非官方说明。

## 2026-10-17 GPT 真透明派生图

当时GPT立绘与头像使用 `assets/models/gpt-dragon-transparent.png`，保留用户指定的ZipZipPipe白发龙娘。原网页WebP为RGB白底，作者原帖前三张PNG亦未发现有效透明通道；原始 `gpt-dragon.webp` 原样保留。新PNG由内置imagegen以 `transparent_background=true` 仅去背景，未用Python改图；实际RGBA透明区、边缘与黑/白/金背景合成已检查。处理前后摘要与原作者来源仍见 data/assets.json；这不是新的模型或人物官方形象。

## 2026-10-17 个人账号页头图标

`assets/social/` 的 Bilibili、小红书和音符标识来自 [Simple Icons](https://github.com/simple-icons/simple-icons)，原始 SVG 按 CC0-1.0 分发，许可全文及逐文件来源和 SHA-256 保存在同目录。抖音入口使用共用音符标识（来源名 TikTok），链接仍为用户本人提供的抖音主页分享链接。图标仅标识链接所去的平台，不表示账号认证、平台背书或合作；商标权仍归相应权利人。

## 2026-10-17 四位角色表情与透明立绘更新

用户要求将本轮封面里的更鲜明表情用于官网，四张当前立绘与头像均来自内置 imagegen，以原网站角色和用户认可的四人封面为参考，设置 `transparent_background=true`。GPT 保留白发龙娘，DeepSeek 保留蓝发女仆，MiMo 保留橙白兔耳与玩偶，豆包保留黑衣短发 3D 形象。新表情和动作是静态 AI 生成视觉，不代表模型人格、发言或官方形象。

当前素材位于 `assets/models/refreshed-20261017/`，完整生成提示词见该目录 `prompts.json`。官网使用无损 WebP；与生成 PNG 的解码 RGBA 字节逐一比对一致。四图均为 1086×1448，有真实透明区域、透明四角和接近不透明的服装主体；已在深色和白色底色检查显示效果。原始来源和历史版本仍由 `data/assets.json` 的历史字段保留，既有作者和权利声明继续适用；更新不表示取得新的第三方授权。
