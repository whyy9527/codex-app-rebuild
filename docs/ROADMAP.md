# Roadmap

状态截至2026-10-11：1:1 复刻未完成。v3 的局部检查保留，但不能支持产品完成声明。当前原生 Goal 已重新创建并 active；优先修复探索机制和覆盖前端需求的模具，再依真实差异修 Swift。

当前英语v6默认五课72题，加一次未评分口语暂缓；第五课插入题、混合错误/重练、四页结算与返回主页已进入实现。15项核心通过；本批实际原生路径、共享前端v10的752项结果和失败由[第五课证据](../projects/duolingo-web/evidence/english-fifth-native-v1/README.md)维护。录音识别、第二节点后续三课、角色/动画、视觉声学等价、次要交互与真实探索策略消融未完成。旧四课与组件结果保留，不累计成一次通过率。

最新角色批次：已确认Bea/Lucy独立Rive渲染buffer并接入默认五课，修复标题及角色纵向布局。当前五课214状态，434pass/11fail/307not_run；角色组件3pass/1fail/5not_run，仍有横向几何、实际像素/动画/声音差异。源第六课只完成第0题，停在第1题未答。完整失败、接续和复跑由[角色渲染批次](../projects/duolingo-web/evidence/english-character-render-v1/README.md)维护；RSI探索策略及匹配预算消融仍待完成。

最新听力暂缓批次：实际执行遗漏分支，发现插入翻译及后续替换；局部原生路径可运行，完整默认分支未接入。22项源16pass/6not_run，原生13pass/3fail/6not_run；16项核心通过，默认五课v10仍整体fail。[轨迹、失败与接续](../projects/duolingo-web/evidence/english-listening-decline-v1/README.md)。

次要动作增量：实际探索键盘/词库、填空/整句、跳过和正常听音配对，新增listenIsolation缺口；两题原生切换已执行，48项仍14几何失败/4未验证，18项核心通过。默认课程集成、跳过重练/结算、后续第七课及真实RSI策略消融未完成。[证据与接续](../projects/duolingo-web/evidence/english-secondary-actions-v1/README.md)。

整句布局增量：多行输入/角色行/底栏和连对阈值已修；6项输入区域精确几何通过，49项仍36pass/9fail/4not_run。实际Falstaff源Rive已核验接入；误用旧Lin文件名的Bea绑定已撤回。完整Lin、默认输入模式、源后续轨迹及RSI消融继续。[失败与复跑](../projects/duolingo-web/evidence/english-input-layout-v1/README.md)。

第七课续探已实际闭环到主页；跳过与重练/100%结算、独立偏好、插入/替换、额外成就已冻结。真实Lin已接入，19项核心和28状态四题偏好路径通过；58项前端仍9fail/4not_run。v13增加419项第七课要求，完整六课仍662pass/42fail，新增整课需求未覆盖。下一步接入整课跳过/听力/替换/重练与结算，再修视觉声音并开展RSI策略消融。[证据](../projects/duolingo-web/evidence/english-seventh-v1/README.md)。

| 阶段 | 已交付 | 验收与范围 |
| --- | --- | --- |
| 0 定位与改名 | 私有codex-app-rebuild；README、AGENTS、哲学、架构与研究来源 | Dream-RSI/Cordis及历史无收益保留；没有开源或部署。 |
| 1 规格与运行工具 | 共享语义场景、参考确认/版本冻结、阶段持久化、行为进度、有限迭代及显式接续 | 43项机制/控制检查通过；真实宿主单任务和多阶段Stop续跑、同任务新会话接续及完成停止已有证据。已知观察模板不证明新颖自动发现。 |
| 2 固定业务实验 | 前置36项机制实验；独立预注册的四组真实业务对照 | 两会话/组、相同基线和上限；四组封存后均公开12/12、留出2/2，另1未知；N=1无通过率收益，费用unknown，失败与权限诊断保留。 |
| 3 Duolingo观察 | 首两课的正常、错误、退出/恢复、配对、拼句、错题与完成证据 | 原版12/12；补查发现提交前改选缺口并建立增量批次。线上临时访客和语义范围，不是整个产品或离线原版。 |
| 4 Swift教育基座 | 原创两课时、三题型、学习状态机、错题队列、解锁、SwiftUI与持久进度 | 历史v2原生12/12、核心5项；六张旧截图只证明旧界面可读。v3产品修正已开始，旧截图不代表当前UI。真实存储错误先冻结、复现、修复及回归；macOS可运行，iOS未验证。 |
| 5 历史工程审计 | 运行入口、实验原始记录、未知/产品决策、源码与输入摘要、文档和私有Git交付 | [本轮审计](DELIVERY-AUDIT.md)；最终提交/远端一致性由运行记录确认。 |

## 证据入口

- [机制报告](../projects/rebuild-mechanisms/REPORT.md)：固定36项及真实单任务宿主，不代替业务效果。
- [模型流程](../projects/model-pipeline/README.md)：失败run01、修复去重后的run02与真实跨会话阶段证据。
- [业务消融](../projects/business-ablation/REPORT.md)：四组、原始失败、零收益、用量和限制。
- [参考案例](../projects/duolingo-web/README.md)：实际原版观察、冻结和跨端场景。
- [教育基座](../projects/education-swift/README.md)：构建、独立运行、重置与题库扩展。

## 后续研究方向

后续范围应重新确定，不能把下列方向当已实现能力：更复杂App及多次重复的新预注册；新的盲留出与探索遗漏评价；实际iOS构建、更多窗口尺寸和中断恢复；用真实发现历史研究并验证探索策略改进。已公开的本轮留出不能继续冒充盲测试，页面层数不决定尝试次数。

原版未知规则、在线服务变化、教育效果、统计收益和完整Dream-RSI/Cordis复现均不在本轮完成声明内。

## 历史 v3 产品修正（局部证据）

三栏主页、图片选择卡、两列配对、拼句角色/发音提示/答案横线、固定底部反馈、退出弹窗和导航卡片已完成参考对照。自然启动1200×760、820窄窗、完成/锁定/重练/重启恢复已检查；原创音效与系统英文发音实际输出录音通过，静音输出为零。源码、回归、截图和音频分别记录证据；[本轮交付](../projects/duolingo-web/evidence/PRODUCT-V3-DELIVERY.md)保留两次失败及修复。此前将 RSI 和探索策略改进一并排除的安排撤回；机制应直接服务发现遗漏与复刻质量。

## 当前修正顺序

1. 撤回 1:1 完成结论，保留既有回执；移除自行添加的替代内容与产品范围限制。
2. 从真实页面列出状态及未访问动作，继续探索并保存历史；先补 More 悬停菜单→Settings 等已漏分支。
3. 让模具执行前端需求断言，统一比较状态、视口与采样比例；业务测试和前端结果共同决定交付。
4. 依失败逐项修复 Swift 的内容、素材、布局、导航、反馈和声音。
5. 在真实探索历史上验证策略调整，并用同起点同资源消融比较需求发现及复刻差异。

上述步骤尚未全部完成，不再用检查数量替代完成判断。

### 当前已验证的第一步

统一产品入口现已将冻结12条业务 E2E 与前端契约合并判定：业务通过，前端10项文案失败、3项未验证，整体失败。原版同10项文案通过。真实 More→Settings→Privacy→Help 历史可推导22个待探索动作；这是分支记录能力，还不是 RSI 策略自改进。原版字体、几何与素材路径已有采集。详见[本轮证据](../projects/duolingo-web/evidence/exploration-v4/README.md)。


### 当前 v4 实现与失败回执

已从原版实际观察编译西语两节课24题，默认Swift使用原版公开字体/图形/题图；修正第一节点含三节课的关系。当前统一回执：冻结业务12/12、题目文案144/144通过；主页/More 12项通过，Settings 7项失败，视觉/原版音频2项未验证，整体失败。Swift构建、核心5项、Python46项通过。首轮10项文案失败和后续悬停/提示失败均保留，不覆盖历史证据。

实际窗口装饰和Retina采样已有可复跑归一化与差异输出，仍不能算1:1视觉验收。探索历史扩为11状态、11真实转移、23待访问动作，含未知短语→原版确认的反馈链。第三节、Settings实际行为、其它导航、原版声音、动画及后续路径继续补齐；RSI策略自改进与探索效果消融尚未执行。当前Goal保持active。


### v4.1继续进展

已实现原版Preferences布局、四个开关及外观选择，并加入共享控件几何/重启恢复契约。原生9项通过、1项课程效果未验证；相同契约在原版匹配初态的最新观察7通过、2持久化失败、1未验证，统一产品结果保持失败。原生文案19项、课程文案144项、冻结业务12项通过；视觉/原版声音未完成，Python47项与核心5项通过。具体反例和诊断由[案例证据](../projects/duolingo-web/evidence/exploration-v4/README.md)维护。

真实跨课探索已消费green→verde的参考确认，完成前两课后在第三课停于新blue题并保存26个现场与知识快照。历史17状态、18转移、24待探索动作；这是实际续探与知识更新，尚不是RSI策略自改进或消融收益。继续定位偏好保存反例、观察课程数据结构、采齐第三课、补原版语音及剩余前端分支，并开展探索策略实验；Goal保持active。


### v5：用真实会话数据补模具并继续发现遗漏

原版第三课13题已交叉确认，默认Swift三课37题；31个公开源语音按题目/选项上下文接入，实际播放器推进及音效开关/全局静音分离通过。捕获公开sessions字段与真实UI回放形成独立工具，接口提供答案不代表前端已验收。回放失步及一次人工续点保留。

新发现两种题间页、四个结算状态和完成后节点/联盟变化，全部进入新前端契约。当前冻结业务12/12、三课文案237项通过，课程契约8项未覆盖；其它视觉/声音与原版偏好反例仍使统一产品结果fail。Swift构建、核心5项和Python47项通过。历史50状态、49转移、30待探索动作；这不是完整探索覆盖或RSI策略自改进。

下一批补齐上述实际状态与视觉/声音输出，并进入下一节点寻找新需求，保留真实失败用于预注册的探索机制对照。[本批证据](../projects/duolingo-web/evidence/exploration-v5/README.md)维护回执与续跑位置。Goal保持active；RSI研究与消融尚未完成，未限制目标为三课。


### v6继续进展与英语课程转向

Guidebook改为实际页面内容与七次逐句语音（六个源文件），第三课接入七个原版角色，课程状态加入两处实际题间页。冻结业务12/12、核心6项通过；课程文案/题间文案239项通过另9未覆盖，Guidebook25通过、1几何失败、3未覆盖；整体fail。首轮标题采样对象不一致及系统图标失败保留，原版图标修正后仍有1.03125点y差，未放宽容差。

实际进入原版第二节点并捕获15题；复用回放完成11题后停在真实dialogue页面，接口另有listenTap。新题型进入未覆盖项，未伪造支持。用户随后建议英语学科，当前主目标转向中文母语学习英语，西语作为历史证据与通用能力来源。英语原版正在观察，默认候选仍为西语历史夹具，不能拿旧原创英语内容算已转换。

接下来确认真实英语课程的首课、主页、题型、素材和音频，建立对应夹具与前端契约，再迁移通用实现；同时继续处理鼓励页错误路径、结算、声音输出与探索机制对照。RSI论文和历史实验保留，完整Goal仍active。[v6证据](../projects/duolingo-web/evidence/exploration-v6/README.md)。


英语参考已实际进入中文界面首课，sessions确认en/zh，共15题，含listenTap/dialogue。首次误选sugar后观察到扣心和红心教学遮罩，两个“继续”使通用定位失败；明确关闭遮罩后保留错误反馈。见[英语参考记录](../projects/duolingo-web/evidence/english-v1/README.md)。当前只是参考探索，不是英语候选已完成，下一轮以该真实现场接续。


### 英语首课真实续跑与状态契约

本轮从错误反馈原位续跑，遇到listenTap/dialogue时保留未支持失败，扩充驱动后按真实索引接续，实际完成首课全部15题以及错题重练。记录两次鼓励、完整完成链、匿名7天连胜目标、稍后建档及英语主页。英语主页包含发音入口，首节点Lesson 2 of 4，不能套用西语三课路径。生成29状态/74项的英语参考与前端契约（15文字、59待覆盖），候选全部not_run。下一步将这些证据编译为Swift课程与页面状态，接入同状态验收；声音输出、视觉等价、导航/恢复探索及真实消融仍未完成。见[英语证据及复跑入口](../projects/duolingo-web/evidence/english-v1/README.md)。


### 英语原生首课执行

Swift默认已切真实en/zh首课15题，保留每题sourceType、逐选项图像、21条源语音、13个源SVG/PNG及对话头像。7项核心检查通过，实际原生全对/首题答错→重练两条轨迹完成；源/候选标题15通过、59未覆盖。按实际内容矩形对齐的28对截图均有差异，未放宽验收。下一步迁移英语主页/四课首节点与后续课程、真实红心教学/鼓励/完成链，修正文案/几何/字体/图形及音频输出；English完整共享业务规格、探索机制消融仍待完成。见[原生执行证据](../projects/duolingo-web/evidence/english-native-v1/README.md)。


### 英语主页、弹层及动态尾部发现

主页迁移中文导航/右栏、旗帜/发音源资源、五节点及四课环，加入真正的开始弹层。v2主页文案/导航几何23通过；v2.1含弹层26通过、1失败、75未执行，第2课开始仍失败，未用首课重放替代。新主页首课原生错误/重练回归执行完成，核心7检查通过。保留gzip资源、颜色环境、AX标签/点击区域首轮失败，未放宽断言；主页像素仍有差异。[主页证据](../projects/duolingo-web/evidence/english-home-v2/README.md)。

原版第2课已实际完成：发现orderTapComplete，扩充驱动原位续跑后，又发现API末3题与实际三个挑战翻译不同。已保留静态驱动失败、真实动作/正向反馈和完成页；下一轮从当前完成页继续，按真实轨迹编译第2课，不能仅复制API列表。[第二课证据](../projects/duolingo-web/evidence/english-second-v1/README.md)。首页剩余行为、完整结算、声学、视觉与RSI真实消融仍未完成。


### 英语第二课实际接入与原版继续探索

默认v2已接入两课各15题，第二课为12正常+3实际挑战，保留原API未访尾部为未知分支。填空固定句段/范例/撤回、三处鼓励、挑战提示及源资源接入；8项核心通过，原生首课误答/重练后进入第二课全对完成，主页开始修复。前端v3匹配状态128pass、105not_run整体fail；fresh主页与after-first契约的2条状态不匹配失败原样保留，第二课30对截图全different。无新增视觉或声学通过结论。[本批回执与复盘](../projects/duolingo-web/evidence/english-second-native-v1/README.md)。

原版第二课完成后实际走过连胜提醒、建档提示、回主页，排行榜剩1课，首节点进入第3/4课。当前从此现场继续探索第三课；完整结算链、角色动画/布局、音频输出和其它导航/恢复继续补齐，真实RSI探索对照尚未完成。Goal保持active，不把两课或类型核对当作探索完成。


### 英语第三课探索：同类型变化与重复词块

原版第三课实际15题已完成，Swift尚未接入。第9题两个“不要”暴露驱动和编译器的文本去重假设；驱动按可用词块原位修正，编译器/候选仍待补。第12题仍为translate但题面/词库已替换，本轮新增独立UI身份核对在操作前实际捕获same_type_content_changed。保存反馈后再进入下一题的新入口已在后两道挑战验证，保留首次过渡导致回执丢失的反例。

第三课历史34状态/35转移，33动作已记录结果、18已观察动作待执行；共享前端v4保留已有233项并新增139项，当前候选128pass、244not_run整体fail。下一轮从原版第三课完成页继续，接入重复词块及实际第三课，继续修结算/视觉/声学并开展匹配资源的探索机制对照；不能将本轮身份回归检查称作RSI消融。[本轮证据](../projects/duolingo-web/evidence/english-third-v1/README.md)。


### 英语第三课原生接入与进度反例修复

默认en-zh-v3为三课45道实际题目，保留双“不要”独立身份、三处鼓励及动态挑战尾部。9项核心通过；最终同一构建单次原生回放完整三课，重复词块6个AX读数通过。修复学完已编译子集即错误标记整条未编译路径完成的问题，保留首次credit反例和重跑。

前端v4当前221pass、151not_run整体fail；首次fresh/after-first主页状态不匹配的两条失败保留，观察器现从同次回放的实际阶段取匹配主页/弹层。第三课30对截图均different；API角色SVG为Cropped，与原版完整角色不符，已记录公开Lottie资源待映射，不以API素材齐全宣称页面相同。v1/v2字节保持，v3确定性及66资源哈希核验。

继续原版第三课完成页→结算/第四课、角色动画/布局、声学和其它探索前沿，真实探索机制消融仍未执行；完整Goal active。[本批回执](../projects/duolingo-web/evidence/english-third-native-v1/README.md)。


素材缺口的进一步根因：旧采集白名单丢弃角色url、idle/correct/incorrectAnimation及name；当前扩展为仅角色上下文保留，范例字段同时保留，下一实际session验证值与页面关联。现有三份公开Lottie命名为Duo，不能当Junior完整角色替代。


### 英语第四课：探索模具修复与新结算链

实际完成原版第四课12题，并发现挑战入口、复习说明、难题说明、英语分数、双倍经验奖励及传奇邀请。听力转录不可见造成的身份误判已用当前显式播放回执修正，文字题核对未放宽。保留失败、原版截图和角色idle/correct/incorrect动画来源。v5共519项：当前三课候选221pass、4fail、294not_run，整体fail；4个明确失败是三课后主页青铜/宝石差异。Swift第四课、视觉/声学等价和RSI探索机制消融尚待完成。见[第四课证据](../projects/duolingo-web/evidence/english-fourth-v1/README.md)。Goal保持active。


### 英语第四课原生接入

默认v4为57题，挑战入口/两处说明进入状态机；实际四课从空进度完成，核心10项通过。三课后主页505/青铜卡片修正，70个公开英语语音随Git交付。前端v5为303pass/8fail/208not_run，第四课24对截图全部不同；下一批直接修第四课完整结算与完成路径，再处理源动画、几何和实际声音。RSI消融未开展，完整Goal保持active。[实际证据](../projects/duolingo-web/evidence/english-fourth-native-v1/README.md)。

第二节点输入增量：实际观察听音、反向填词接受与口语暂不练分支；原生输入组件12pass/6not_run，12项核心通过，六对像素仍不同。产品v7保留v6并增至578项，整体验收尚未重跑；默认四课未替换，完整第二节点和RSI策略消融仍待完成。[证据](../projects/duolingo-web/evidence/english-input-native-v1/README.md)。

本批原版第五课实际完成：暂缓口语后插入替代翻译、两次扣心、只重练typed error、13经验/94%、任务30/30、5宝石、主页510及第二节点第2/4。候选配对14/0/4、热茶重练7/0/3，14项核心通过；完整第五课尚未编入默认。source history导出36 resolved/15 pending，不是RSI收益证据。[当前实测](../projects/duolingo-web/evidence/english-pairing-native-v1/README.md)。


### 反馈次要动作的探索与交互接入

实际访问评价切换/取消、报错多选、Escape关闭和重开重置。共享31项原版/原生均25pass、6not_run；九对整页及四对同几何弹窗仍different。听力暂缓回归16pass/6not_run，默认五课仍434pass/11fail/307not_run。保留两次原生AX失败及contain容器修复，不将交互通过称作视觉通过或RSI收益。历史前沿16resolved/60pending；从实际糖题已接受反馈继续第六课。完整默认分支、视觉/声学与真实探索消融仍未完成。[本批证据](../projects/duolingo-web/evidence/english-feedback-actions-v1/README.md)。


### 第六课实际完成与契约增量

实际续探完成第六课：听力及口语暂缓产生替换，三道挑战不同于API尾部；结算15经验/100%，直接建档后回主页，第二节点3/4、生命2、宝石510。冻结25状态/306新需求，源256pass/50not_run；v11共1058项，用上一批五课实际AX对照434pass/11fail/613not_run。默认仍五课，尚未编译第六课，不能用历史五课观测宣称新整课通过。探索历史42resolved/117pending，完整Goal active。[源轨迹、回执和接续](../projects/duolingo-web/evidence/english-sixth-v1/README.md)。


### 第六课原生全程与源采样反例修正

显式v7编入已观察双暂缓轨迹，默认仍v6五课，正常分支未采齐。17项核心通过；默认共享输入标签/区域、口语暂缓动作、正确连对计数、第二节点进度和30经验任务已修。独立六课从空进度连续273状态，无walk_error、最终生命2。源序列化数字和动画父文本误采样在新v12修订，v11及失败保留；1061项当前662pass/42fail/357not_run。第六课25对像素仍全部不同，声学与真实探索策略消融未完成。完整Goal active。[源码、失败、资源及复跑](../projects/duolingo-web/evidence/english-sixth-native-v1/README.md)。


### 跳过不扣心与原题重练的原生分支

源证据先冻结，独立skip不复用答错评分；实际原生空答案跳过→反馈→重练引导→原题→完成走通。20项核心、47项框架通过。初次按钮152×48与源150×50不符，保留失败并用零容差断言修正；59项现43pass/6fail/10not_run，五对图片仍全部different。压缩单题无法验证整课生命刷新、15连对及结算，完整第七课未接入默认；真实RSI消融仍待执行。完整Goal active。[证据和复跑](../projects/duolingo-web/evidence/english-skip-native-v1/README.md)。


### 七课默认集成、前端控件契约与反例保留

默认 v8 已接入七课102道计分题，真实从空进度回放430状态，无 walk_error。21项核心、48项框架检查通过。前端 v14 保留1480项旧需求并新增9项角色、enabled及Skip几何要求；最终985pass/69fail/435not_run，九项新增要求全部通过。第七课314/27/78；38对截图仍全部不同，声学等价未证明。保留构建失败误跑旧二进制的作废回执，严格构建入口及运行哈希防止复发。

下一步从第八课实际挑战入口继续探索，同时修复已经发现的布局、字体、动画和音频差异；采齐 radio1、正常口语、偏好恢复及生命刷新原因。不能以扩大课程数量掩盖已有前端失败。真实匹配预算 RSI 探索消融仍未执行，完整 Goal active。[本次实际回执](../projects/duolingo-web/evidence/english-seventh-native-v1/README.md)。


### 听力控件的选中与几何补漏

v15保留1489项并增8项真实原版断言。独立原生radio2实际点击及接受，四项checked与四项零容差几何通过；保留alignmentRectInsets无效尝试。49框架、21业务检查通过。局部契约50pass/4fail/1443not_run，两对截图仍不同，尚缺听力暂缓、反馈补词/绿色及动态角色；不把前一构建七课结果移用到新构建。CoreText同配置回退PingFangSC-Semibold，源入口字号24而候选28，后续逐状态修复。[证据及复跑](../projects/duolingo-web/evidence/english-radio-layout-v1/README.md)。完整Goal active，真实RSI消融未执行。


### 原版反馈补词、sRGB像素契约与第八课退出分支

默认v9七课102题保留旧v8，新增实际反馈补词及正确静态波形。构建、21核心、50框架通过；从真实归档六课进度走完完整第七课81状态，无walk_error。v17保留全部旧要求并新增5项反馈及9项第八课退出/重进入口，共1511项；本次353pass/33fail/1125not_run。补词和两项背景色通过，两项边框仍零容差失败；两对整页仍不同。发现macOS ICC与浏览器未标记sRGB字节直接比较的模具错误，统一ICC→sRGB后仍保留旧失败和未修差异。真实访问第八课下次再说、返回主页并重进入口；尚未作答/集成。完整Goal active，RSI消融仍未执行。[回执及复跑](../projects/duolingo-web/evidence/english-radio-feedback-v1/README.md)。


### 探索消融正式预注册

已实际采集四个源主页分支，四次根快照一致；建立经验回放、模型策略接口和摘要注册。正式模型与在线留出前先提交推送协议；原始事实新颖度只是选择代理，实际复刻质量仍需独立实现对照。旧历史状态歧义及单路径偏差已识别，不用手写缺陷注入代替模型探索。[协议及输入](../projects/exploration-ablation/README.md)。

探索消融01已真实调用，但服务拒绝gpt-6.1-sol、实际启动横幅0.139.0与命令版本不符，零策略/零在线动作，记unavailable并保留失败。02预注册只显式绑定bundled CLI版本和哈希，原模型、数据、评价和预算不变，未提前宣称修复成功。

消融02显式bundled CLI调用已成功：三次真实进程的启动版本、模型和effort一致。模型提出策略并按已揭示回放反馈修订，实验组及控制组封存后训练分数均70；原始失败01保留。已封存两组策略，在线留出尚未执行；不能将离线分数称为泛化或复刻质量收益。

### 真实探索消融02在线审计

三次真实模型调用、封存后四次源动作已完成；两组离线均70，实验组选中初始策略未变。两组在线均选择发音→排行榜，但首次发音只采到空壳，第二次才加载正文，原始25对265计数不可归因于策略，正式比较unavailable。保留失败及脱敏证据，不在02补跑。新观察确认发音入口背后的正文、音标按钮与进度需求；Swift导航存在不等于发音页完成。下一批先修页面就绪及冷/热状态测量，重新预注册，02已见页面不冒充新留出；随后扩共同契约、实现并测真实质量。完整Goal仍active，[实测报告](../projects/exploration-ablation/REPORT.md)。

### 发音页实测补漏与采样03

03修复正文就绪，52框架检查通过；先推送再执行四次实际源动作。发音两次均240事实，但最终主页倒计时12→11小时导致预注册根一致性检查中止，完整比较unavailable，不补跑凑分数。另行探索原版发音页39音标按钮，快速播放采集存在归因歧义，保留原始窗口URL并待重测。v18保留1511旧项，加78项至1589；实际Swift点击发音仍显示路径，新页44fail/30unavailable/4not_run。源几何、正文及音标/分组已冻结，下一步直接实现Swift页面，重测音频后接真实播放并比较；练习链/进度恢复继续探索。完整Goalactive，[证据与复跑](../projects/duolingo-web/evidence/english-pronunciation-v1/README.md)。

### Swift发音页及真实原版音频

已实现39音标/词例/分组/进度条，修复顶层路由遗漏及LazyVGrid离屏AX缺字，保留两次失败。逐项播放完成边界重测39个源按钮，排除v1快速采样串音归因，绑定39个原版MP3。v10保留七课102题，只补真实六课主页连胜/倒计时元数据；匹配生命3。构建、21核心、52框架通过；新页59pass/15fail/4not_run，整图different，未放宽几何。实际owned音标点击录音非零，但声音等价未证实。原版练习入口已进入dock/deck听辨首题，候选开始仍是旧通用页；下一步从真实练习续跑并实现，继续修视觉/输出。完整Goalactive，[证据与复跑](../projects/duolingo-web/evidence/english-pronunciation-v2/README.md)。

### 发音练习实际续跑与Swift入口

原版走完听辨、sameDifferent、口语暂缓、配对、错题复习、结算/稍后建档并返回；保留过渡重影、单speaker假设、URL答案键串题导致24次额外错误及结算过渡超时。按题型/选项/音频绑定修正探索，不称作RSI收益。Swift入口已接独立Lesson，52个原生状态、主六课/生命3不变；新增49前端要求44pass/5not_run，横排radio零容差几何及旧纵排回归通过。完整v19共1638项，本次122pass/19fail/1497not_run，三对整图different。构建、22核心、52框架通过。原版练习后音标进度增长，候选仍缺持久化；正常口语、结算统计/条件文案及声音/视觉等价未完成。完整Goalactive，[证据与复跑](../projects/duolingo-web/evidence/english-pronunciation-practice-v1/README.md)。


### 分段播放的前端模具补漏

旧练习只检查选项，漏掉白色165宽分段speaker及反馈揭示词。v20保留1638项并追加12项，原生实际播放、答题/复习和返回52状态；新增8pass/4fail，四项几何仍差0.25点不放宽。整次130pass/23fail/1497not_run，四对整图different。保留AX缺失及AXUnknown失败，修复原退出资源缺失问号；构建、22核心、52框架通过。已知视觉/声学、口语、结算、音标持久化及未访问分支继续推进，真实质量消融仍未完成。完整Goal active。[证据及复跑](../projects/duolingo-web/evidence/english-pronunciation-split-v1/README.md)。


### 第二次发音练习与原生配对修复

实际第二次为sip/zip/sap/zap，10选择→配对→六错更正，没有首次口语；结算11听力挑战，返回及真实刷新保持ɑ/ɛ及新s/z进度。口语缺席原因未知，第二套选择/持久化未集成；frontier保存下一步，不强套首次轨迹。驱动最后切换误读禁用旧控件超时但源已完成，保留失败；就绪修改仅实测当前终态，完整切换待验。配对宽高/顺序已按原版修复，v21新增40项全pass，八矩形零容差通过；同次52原生状态，完整170pass/23fail/1497not_run，六对图片不同。构建/22核心通过，正常口语及声学/视觉/真实质量消融仍未完成。完整Goal active。[源证据、frontier及复跑](../projects/duolingo-web/evidence/english-pronunciation-matching-v1/README.md)。


第三次探索实际出现tell口语，临时denied→实际录音按钮→未授权模态→恢复prompt已验证，无环境录音；关闭真实弹窗后播放原tell媒体、暂缓口语及配对。默认源驱动已保存反馈记忆，五道错题均按prior_feedback更正；最后到结算无禁用旧按钮误点，终态首次记unknown后现场确认，按钮终态fallback尚未完整回跑。成绩单17卡及首张tell/tall答案揭示已观察。v22冻结后续口语/权限/成绩单12项，共1702；同次原生观察171pass/24fail/1501not_run/6unavailable，不能掩盖录音控件缺失。源当前第三次成绩单首卡展开。下一步实现口语基础、统一编译后续练习和持久化，并以已有实际缺陷/契约基线预注册真实前端质量消融，不再用增加课程数代替实验。完整Goal active。


### 观察轨迹编译与发音练习重启续跑

第二/第三套从既有原版反馈及实际配对记录编译进Swift，保留第一套定义；第三套原版成绩单关闭后已继续到建档、稍后、返回characters。35原版音频资源校验入库，第二套缺失配对声音不猜测。完成session独立持久化，原生第一套53状态/第二套57状态均完成并终止重启：依次实际显示sip/zip、tell/tall；主六课/生命3不变。保留检查器错误要求无编号文本的首次失败，修正后新目录重跑。构建/23核心通过；第一套旧v22仍171pass/24fail/6unavailable/1501not_run，六图仍不同。当前是观察顺序回放，原版自适应选题及音标进度公式未知，第四套缺资源的加载失败是已知缺口，不是产品范围限制。第三套完整原生UI、正常口语、视觉/声学差异及真实质量消融继续推进；下一批优先处理真实质量消融/正常口语，不用增加样本数代替效果验证。完整Goal active。[证据及复跑](../projects/duolingo-web/evidence/english-pronunciation-progression-v1/README.md)。


### 前端反馈质量消融01预注册

以真实历史4a9df58配对缺陷为起点，两组共享初始模型/原版证据/预算，唯一移除实际前端反馈，固定40要求与两幅同状态图像评价。协议、CLI哈希、输入和脚本在正式调用前提交推送。N=1历史任务不声称探索或RSI收益，不替代全App验收；实际结果待运行。[协议](../projects/frontend-quality-ablation/PROTOCOL.md)。


### 真实前端质量消融01完成

先推送bbad913协议，历史基线真实构建/22核心/52原生后wrapper绝对路径错误；模型零调用，失败保留，4256cc7先推送修正后续同一观察。三次实际gpt-6.1-sol/medium调用与四阶段原生测量完成：基线28/40，初始/无反馈/有反馈均40/40；两幅图有反馈RGB差异均大于无反馈。保留主指标初始即上限及负面结果，不声称RSI/泛化收益。共97345 reported tokens，实际消耗不同、费用unknown；输入/封存/源码/日志/截图/成本入库。实验含固定p11进度/文案，未替换产品或当成通用规则。下一步回到真实前端缺口与正常口语/进度规则，继续探索；完整Goal active。[实测报告](../projects/frontend-quality-ablation/REPORT.md)。


### 口语权限分支、前端几何与探索反例

第四/第五套真实源轨迹都没有口语，第五套元音反例推翻“元音必有口语”；出现条件未知，不加猜测冷却限制。候选接入显式录音/识别基础与拒绝/关闭，正常评分/推进、录音状态反馈未接，不能称正常口语完成。构建/23核心通过，55原生状态及终止重启到sip/zip、主六课/生命3不变。v23保留1702旧项增3，共182pass/24fail/1499not_run/0unavailable；录音/播放矩形和权限文本通过，暂缓宽度仍差0.1015625点保留失败。七对图像全部different。注入拒绝在权限/捕获前执行，没有环境录音，也不证明macOS授权或识别。保留四轮失败与AX覆盖诊断，检查器trap改throw清理；正常口语、角色/原音、音标进度及真实探索效果继续，完整Goal active。[证据、反例和复跑](../projects/duolingo-web/evidence/english-speech-permission-v1/README.md)。


### 发音练习退出：反例驱动补漏与媒体模具

第六套无口语；第八主课匿名建档提示重复，设置无口语开关。退出原版对照：未答/选中未提交/一错或两错直接返回；两错一对、首题正确、先对后错会确认。撤回按尝试次数的泛化，Swift从已答前缀及错题队列推导正确进度。采集模具新增按钮外可见媒体，发现确认框Duo原图；保存前预检避免覆盖，碰撞与菜单消失失败保留。当前构建/23核心通过，61原生状态退出0，取消完整AX不变、放弃不写进度、重进首题及完成后真正重启到sip/zip验证，主六课/生命3不变。v24保留1705旧项追加13，共192pass/27fail/1499not_run/0unavailable；新10pass/3几何fail。首次大幅位置错误修复，0.25点补偿实测反向且像素更差已撤回；最终三项误差仍失败。七对整图及弹窗区域都different，不拿区域比较代替全状态。正常口语及其它前端/音频/进度、真实自主探索效果继续；完整Goal active。[源对照、失败和复跑](../projects/duolingo-web/evidence/english-practice-exit-v1/README.md)。


### 发音卡片实际样式与共同图像验收

原版39卡DOM/CSS确认19px音标、15px单词、5px间隔及68px按钮；Swift修正字号/行高/点击区域，实际AX64→68。旧参考与当前æ cat区域逐像素相同，当前在线非零增长不冒充零进度全页一致。模具新增image_pixels实际读取PNG及测量元数据，ICC转换由通用provider拥有，缺图/依赖不可算pass。v25具体化1个旧pending并追加7图，旧可执行要求不变。完整55 Python、Swift构建/23核心及61原生状态通过执行；共同契约192pass/35fail/1498not_run/0unavailable，8图全fail，卡片区域和整页差异下降但未1:1。新增失败是扩大实际验收，不宣称产品回归或RSI收益。可移植回执重绑定PNG路径且逐字节核验，完整Goal active。[证据、图片与复跑](../projects/duolingo-web/evidence/english-pronunciation-cards-v1/README.md)。


### 实际字体解析及按住卡片补漏

前批残留字形偏粗促使改用实际platform font/CoreText探针：CSS500实际Latin轴400，但中文副标题实际Medium，故只修卡片音标/英文为400与0.8px字距，保留中文。源按住移动2px且2px阴影消失，候选修66点卡面/2点阴影并加实际按下反馈；源CSS圆角与SDK默认continuous不同，本页显式circular。v26保留全部1725旧项增4，源几何4/4，56框架/构建/23核心通过，最终64原生状态194pass/37fail/1498not_run/0unavailable；新增位移两项pass、绝对几何两项fail，8图仍fail。卡片区域差异约1.846→0.734、整页下降，不能代替1:1。首轮CGFloat类型错误及中间构建完整保留，原论文/负面消融不变。下一步继续未访问导航/主课、音标增长及前端/音频缺口；Goal active。[源发现与复跑](../projects/duolingo-web/evidence/english-pronunciation-typography-v1/README.md)。


### 特别任务导航页与独立练习新分支

从实际源/quests采集横幅/每日30经验/锁定/月挑战/媒体/几何，替换候选英文通用页。实际“去学个单元”去/practice四组听音配对，未答退出回/learn；不能用主课程代替，候选仍未实现入口。v11由源DOM编译，仅增加六课14小时快照，重编译字节一致；不是重置规则。v27保留1729旧项增18，源可执行17通过/1pending；候选新15pass/2fail/1not_run，整图和练习标题fail。首轮月挑战按钮偏10点、高48，经布局提议/contentShape修复后5几何全pass。完整34pass/6fail/1707not_run，不能与发音五状态回归80/22/1645累计；56框架/构建/23核心通过。整图均值23–26降到1.35–1.54仍不同，源素材及原始失败入库。默认v11，真实/practice完整轨迹及日界线/月挑战/其它导航继续，完整Goal active。[对照、frontier与复跑](../projects/duolingo-web/evidence/english-quests-v1/README.md)。

### 独立练习完整源轨迹与模具补漏

真实GLOBAL_PRACTICE走完16评分题、口语暂缓、实际插入/三次挑战替换、一次故意错误后的复习更正、结算/红心奖励/稍后建档返回。实际5XP/94%为截图读数，图片命名未出现保持unknown，返回红心4；奖励规则及自然恢复未独立拆分。驱动新增配对/听音填空/听写/缺词输入，完整集合和实际媒体匹配；键盘态及变题中止回执保留。两处截图前缀覆盖已标为较早帧时间对应unavailable，作答工具加动作前检查并有真实文件反例。v28原样保留1747旧项增88，40源状态投影自校验88pass；旧Swift归档重评34pass/6fail/1795not_run，新增全未访问，不冒充新原生运行。4 Node/56 Python通过。下一实施批次从实际trace编译独立Swift练习、共同夹具和前端驱动，补任务入口及奖励/恢复，并继续未访分支和真实探索效果实验；完整Goal active。[轨迹、限制与复跑](../projects/duolingo-web/evidence/english-general-practice-v1/README.md)。

### 独立练习Swift轨迹与前端负结果

从实际16评分题编译独立Course，接任务入口、口语暂缓插题/挑战替换/一次错误重练、实际结算与红心，47原生状态走通并真正重启，主六课不变。48原版资源和实际播放SVG帧入库，自有输出采集仅证明动作期有声音，不证明声学一致。API参考答案误生成键盘入口被核心/原生共同抓住，按源可见控件修复；AXPress未切换、资源重渲染漂移、private构建和间距漏计失败均保留。56 Python/4 Node/24核心/构建通过，发音52状态回归退出0但共同契约179/32/1624仍失败。最终通用轨迹全量81pass/47fail/1707not_run，新增46pass/42fail、40整图全fail；输入框修到原版精确矩形不能代替1:1。源另发现新实例、听力暂缓后插入assist及答对后退出确认；候选暂缓标题/实例选择、角色图形、正常口语和真实自主探索效果仍待补齐。完整Goal active，原论文及负消融保留。[源、实现、失败、frontier和复跑](../projects/duolingo-web/evidence/english-general-practice-native-v1/README.md)。


### 通用奖励图形与普通听写展示

核对既有源固定参考及11秒后快照，补五心图形和奖励页保留底栏，v29原样保留1835旧项增16。通用夹具v2/50原版资源，旧v1及主课v11保留。错误地共享listenTap蓝控件使普通listen整图误差上升，保留native-01负结果后按源PNG拆成Bea Rive/白色分段播放/多行输入，native-02完整47状态与真实重启走通。红心整图RGB约3.76→0.70，听写约4.51→2.00仍fail；五心0.25点及回顾静态角色等新失败原样保留。89pass/55fail/1707not_run/0unavailable，新16为7pass9fail；40练习整图全fail。构建/24核心/56 Python通过。听力暂缓入口仍缺、回顾/重练实际语义、字体/动画/进度与声学等继续，完整Goal active，未宣称RSI收益。[证据与复跑](../projects/duolingo-web/evidence/english-general-practice-presentation-v1/README.md)。


### 听力暂缓的实际插入与自适应反例

由缺暂缓入口的失败反馈选择实际listenTap分支，驱动前六题后明确停住，继续真实探索完成16评分题/两次暂缓/全对结算/稍后建档返回。听力暂缓插入water and coffee翻译，口语暂缓后的water and tea并非原口语句翻译，否定固定题单/直接跳过模型。采集器补文字Range/CSS及inlineSVG；v30保留1851旧项增34/28状态，源自检34pass，旧native重评89pass/55fail/1741not_run，新34全未运行。新状态机及原生验证尚待实施，不以探索回执冒充复刻完成；15分钟恢复/奖励上限/自适应选择仍未知。原论文与负消融保留，完整Goal active。[实际轨迹、模具与下一实施批次](../projects/duolingo-web/evidence/english-general-listening-decline-v1/README.md)。


### 听力替换实施及前端反例修复

可选实例替换接入Lesson，暂缓不评分，翻译位置与错误复习保持；显式原版观察实例45原生状态和真实重启，默认实例47状态回归均无驱动失败。修复286点播放宽条、524点黄色继续及词库纵向偏移；原版MP3/黄色勾绑定，类型检查超时负日志保留。v31保留1885旧项增18，共1903；最终56pass/35fail/1812not_run，新52为22pass30fail且28整图全fail。25核心/56框架通过，字体/图形/进度/替换音频、正常口语、通用实例选择及真实探索效果继续，完整Goal active。[详细验证及复跑](../projects/duolingo-web/evidence/english-general-listening-decline-native-v1/README.md)。

### 当前题续接与原版Eddy运动

新实例前五题实际接受，听力暂缓后插入Good morning翻译。新增当前可见renderer公共字段采集和单步回放，真实答对后遇到未支持speak留0作答未覆盖回执；显式停止亦0作答，无录音。共享投影覆盖旧两实例，9 Node通过；历史观察计划中的原创素材/缩小范围限制已撤回。原版Eddy公开Rive与实际缓冲236733字节SHA一致后导入；默认47原生状态及真实重启完成，角色区域待机/反馈各12种实际帧，q12角色仍缺。56 Python/构建/25核心通过；共同v31仍89pass/55fail/1759not_run，q5整图差异略增保留，气泡/下划线/分隔线/暂缓入口与几何继续。新插入实例还未进入候选共享契约；下一批接当前题分支与正常口语、修实际前端及声音，真实探索效果未证明。完整Goal active。[回执、负结果、frontier与复跑](../projects/duolingo-web/evidence/english-current-challenge-v1/README.md)。

### 听音填空前端与未发现目标题的探索

先从已有原版DOM/PNG冻结v32，保留1903旧项追加9，旧候选新增2pass4fail3unavailable。实际token编译通用夹具v3，补独立29×22播放、角色包装位置、气泡尖角/虚线/缺词正确绿色及分隔线；不改评分数据。默认47状态及真实重启执行完成，新增5pass1fail3unavailable，共94pass56fail1759not_run3unavailable。角色仍差0.0138794点，暂缓入口仍缺，整图均fail但两张差异下降。构建02限定无token实例仍旧间距，最终同一二进制45状态暂缓回归56pass35fail1821not_run、默认47状态再次重启计数仍94/56/1759/3；前轮回执保留。25核心/56 Python通过。源另一实例当前题实际答对13题仍没遇到听音填空，口语Hot please暂缓后插tea with sugar；引导页当前模式动作前失败需人工接续，现停挑战“茶加糖”未答。下一步补该闭环、听音填空暂缓规则与剩余前端/声学，不当RSI收益或完成，完整Goal active。[源反例、前端与复跑](../projects/duolingo-web/evidence/english-isolation-presentation-v1/README.md)。

### 当前题连续驱动与成绩单前端盲区

前批余下3题实际接受并到结算；回顾发现17卡含暂缓口语，展开仍显示原句为双方答案，仅为展示证据。采集器补实际DIV角色，v33原样保留1912旧项追加111，总2023，源新增全pass、旧候选新增全not_run。真实重练新实例先接受6题，口语未覆盖后人工暂缓，再接受10题并自动接一次挑战引导页，结算保存未覆盖不自动继续。两实例仍没找到listenIsolation，波形/该题暂缓规则未采到。12Node/56Python通过，冻结字节复现；无Swift修改或新原生运行，旧native-final重评94pass56fail1870not_run3unavailable。下一批实现实际历史/回顾、触发和滚动、重练及继续其它未访分支，不把此批当完整无监督或RSI收益。完整Goal active，原论文/负消融保留。[真实动作、模具、frontier与复跑](../projects/duolingo-web/evidence/english-current-walk-v1/README.md)。

### 真实成绩历史与原生滚动验证

原版证明hover不展开、点击移走保留、二次点击收起，稳定滚动387点。实际17卡轨迹编译显式夹具及45原资源，核心保存答案和nil评分的暂缓展示；Swift回顾接真实卡片/播放/展开/关闭/滚动。初轮驱动ID失败、裸勾/关闭差异及postToPid滚轮无移动的假成功保留。最终44原生状态无驱动失败并测到387点往返；v34保留2023旧项追加4，共147pass7fail1873not_run，新115为113pass2整图fail。两图修正后误差下降仍不1:1。同一二进制默认47状态/真正重启94pass56fail1874not_run3unavailable，不累计。26核心/56Python/12Node通过，编译/冻结字节复现及45资源哈希验证。默认回顾仍无元数据，错误卡/去重、听音填空及自适应重练规则优先探索，继续整图/声音与其它未访分支；完整Goal active，原论文/负消融保留。[证据与复跑](../projects/duolingo-web/evidence/english-result-review-native-v1/README.md)。

### 首错与课末改答的18卡探索

原版实际热→coffee错误后课末hot更正，18卡分别保留红错/绿对且不去重，短浮层99×136与上下位置采到；本实例仍无listenIsolation，frontier改换入口而非把重复重练当探索充分。共用编译器旧输出字节不变，49原资源哈希验证，v35保留2027旧项追加181，共2208。Swift修红卡/原叉及短浮层；基线与最终各48真实状态完成，三整图差异下降仍fail，红底ICC转换差1级仍fail；新增176pass5fail，全210pass10fail1988not_run。旧17卡同二进制44状态回归147pass7fail2054not_run。构建/27核心/56Python/12Node通过；默认真正重启结果见证据。原版解析cwd、冻结text-run和首驱动ID失败保留，未扩大产品限制或增加审批。默认回顾/听音填空、正常口语、声学/整图及其它未访分支继续，完整Goal active，原论文/负消融保留。[证据、frontier及复跑](../projects/duolingo-web/evidence/english-error-review-v1/README.md)。

### 改换等级复习入口与Escape取消

上一轮为实际进展。本轮按多次通用练习缺listenIsolation的历史改换路径：Practice锁定，4/4开始重复建档提示，直接读取实际提供的/lesson显示等级复习入口。当前题驱动接入口，先speak未覆盖、实际暂缓，再遇completeReverseTranslation停下；按真实空文本框和截图修完整句模式，4该类型真实接受，共12接受1暂缓13卡，仍无目标题。采到长浮层274.07×136且距卡顶103点，短样本78点规则不通用。v36新增Escape2项，基线及onExitCommand各49状态false，按钮系统取消快捷键最终49状态true；v36全212pass10fail1988not_run，旧17卡同二进制44状态147pass7fail2056not_run。v37继续冻结13卡/长浮层88项共2298，候选88全not_run；源485pass0fail1799not_run14unavailable。构建/27核心/56Python/14Node及双冻结复现完成，无新消融/RSI收益或声学结论。下一批优先接新等级复习与默认成绩元数据，修长锚点，再继续其它入口/未知题型、正常口语和整图声音；完整Goal active。[证据、frontier及复跑](../projects/duolingo-web/evidence/english-home-frontier-v1/README.md)。


### 默认第八单元和未完成的前端

原版13卡后实际走分数进度→经验宝→传奇邀请→建档→主页，两个Lesson完成且宝箱可打开，证明应接默认第八课，不能再作为独立演示。v12保留前七课，实际共115评分题（纠正旧102计数）；主课回顾接真实历史，8/8重启仍不标整课程完成。v38保留2298旧项追加23，共2321；41状态修改前/后均133pass/17fail/2171not_run，长浮层整图差异下降但仍失败，箭头AX边界、结算图形/按钮及解锁宝箱未齐。同一二进制17/18卡44/49状态回归，28核心/56Python/14Node及26原资源SHA通过。逐题前端、正常口语、自适应、声音与未访分支继续；不算RSI收益或完成，完整Goal active。[证据与frontier](../projects/duolingo-web/evidence/english-eighth-integration-v1/README.md)。


### 实际开箱与下一练习建档分支

按未访宝箱选择探索，首次真实click被排行榜已解锁遮罩拦截，Escape无效、正常遮罩click才关闭。开箱510→525，禁用已打开图及真实reload保留；下一Practice第1/2单元的Start又弹建档，稍后返回。v13保持八课115题并加入course隔离的一次性开箱保存及原SVG；导入器补实际80×90渲染，第一次方形素材/80×80 AX失败保留。最终6原生状态真实click/重启走通，边界仍差0.2265625点、整图仍fail。v39/v40/v41保留旧要求，共2373；本轨迹34pass/17fail/2322not_run，建档12新项全not_run。相同最终二进制八课41状态回归133pass/17fail/2223not_run，29核心/56Python/14Node通过。下一Start当前不可用，遮罩/建档/后续题、原结算/音频继续；无新RSI收益、完整Goal active。[证据与frontier](../projects/duolingo-web/evidence/english-chest-v1/README.md)。


### 下一Practice建档提示与CSS背景盲点

接实际Start→提示→稍后返回，源CSS背景Duo未被旧img/svg/canvas采集覆盖；采集器补可见background媒体，原144×250 SVG按源尺寸导入。v42保留2373旧项增1，原生8状态/真重启/Start/Later走通，几何0.25点及整图仍fail；AXLink映射遗漏修正并新增button不得冒充link测试。继续点实际创建档案发现空年龄页而非账号表单，v43再增8，当前2382项。候选年龄页未实施、创建按钮仍不可用且失败；本轨迹43pass/21fail/2318not_run。同一最终二进制八课41状态133pass/17fail/2232not_run；29核心/57Python/14Node通过。下一批补实际年龄入口/输入/后续分支，保留排行榜遮罩、结算/音频差异；无RSI收益或完成结论，完整Goal active。[证据与frontier](../projects/duolingo-web/evidence/english-path-profile-v1/README.md)。


### 年龄输入、注册方式与邮箱错误态

真实原版填28/清空/再填并Next，发现注册方式页；电子邮件入口空提交出现两条错误和上下布局位移，返回两次保留28再关闭。v44原样保留2382旧项新增51，共2433，先冻结再实现。原5个公开SVG按实际尺寸导入。Swift真实16状态完成开箱/重启/Start/年龄/邮箱错误/返回关闭；写死输入标识失败和编辑器竞争截断28为2的失败均保留，分别修根因。最终96pass/27fail/2310not_run，新增45pass6fail；全部新增控件几何与清空反馈通过，四整图/OAuth enabled失败。Google/Facebook禁用是实现缺口，不能升级为产品限制；登录/法律链接/清除/密码显示及非空注册继续。29核心/58Python/14Node通过，最终同二进制八课41状态回归133pass/17fail/2283not_run，驱动无失败。无新RSI消融或声学收益，完整Goal active。[源、失败、frontier和复跑](../projects/duolingo-web/evidence/english-registration-v1/README.md)。


### 注册输入控件、独立登录发现与焦点反例

由v44整图/缺失输入控件选择原版新探索：实际年龄清除禁Next，密码abc显示/隐藏保值，登录另含Apple/忘记密码，未提交帐号。v45保留2433旧项增43共2476，实施前冻结；3原inline SVG按原色/尺寸导入。候选清除/reveal与真实安全文本框已接，补源输入padding/字体及背景独立投影；自定义cell不可编辑、截图trap、两次年龄只到2和回顾失去活动目标等失败均保留。驱动输入/滚动激活并确认自有进程，最终同二进制两次20状态各116pass/31fail/2329not_run；新增20pass4整图fail19登录not_run。八课41状态回归无驱动失败，133pass/17fail/2326not_run。29核心/58Python/14Node/构建通过；邮箱整图差异下降，年龄图略增，负结果保留。不能宣称1:1或RSI收益，完整Goal active。[源、逐构建证据、frontier与复跑](../projects/duolingo-web/evidence/english-registration-controls-v1/README.md)。
