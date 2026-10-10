# 追查实际角色渲染器，修正静态素材假设

2026-10-11，实际原版英语第六课与当前默认五课 Swift。1:1 未完成；本批不是探索机制消融。原始 Dream-RSI/Cordis 与历史负面结果继续由[研究来源](../../../../docs/RESEARCH.md)维护。

## 探索与反思

原先把接口的 character.image.svg / character.url 当作页面全身角色，已经被裁切 SVG/PDF 与实际 canvas 画面否定。重复修现有文字 E2E 不会发现资源来源错误。本次根据这一反例改变探索对象，检查当前 challenge canvas 的渲染属性，发现独立的 Rive buffer、公开 CDN URL、artboard、state machine、反馈 trigger、darkmode/rtl 输入与缩放/偏移配置。

`hypothesis-update.json`记录旧假设、反例、修订和实际探针。`capture-source-canvas.mjs`导出真实透明绘图 buffer 的12帧；整页及 composited-region 单独保存，不把截图裁切伪装成透明动画资产。只检查当前 canvas 上关联的 renderer，不把整棵 React 状态或账号数据归档。

Bea/Lucy 的实际 RIVE buffer 均与公开 CDN **解压后**字节一致。直接比较网络 gzip 字节的第一次断言失败保留在`asset-verification.json`；不能据此误判素材不同。Bea idle/correct、Lucy idle 各12帧，透明像素与帧哈希可复算。这个由代理调整的探索步骤发现了先前遗漏的渲染需求，但还没有实现自主策略改进，也没有比较相同预算下的发现效果。

原版第六课仅第0题“牛奶”→milk实际提交并收到“不错哦！”。第1题 Hello./Lucy 已观察、未提交。`sixth-session.json`中的其余 API 题目不是已执行 UI 轨迹；初始 loading 采样保留。第六课未冒充已完成或编入默认题库。

## 实现与同状态验收

`ReferenceCharacter`按既有角色资源身份绑定实际 Bea/Lucy Rive 文件，官方 Apple RiveRuntime 精确锁定6.24.0；使用源 artboard/state machine/输入名及 transform。两人已进入默认五课对应题目，其他角色仍有裁切静态图，结算英雄区仍缺失。反馈触发已接入；mouth/audio同步、偏好对动画的实际影响、相位/时长一致性仍未验证。

独立 renderer fixture 只冻结真实第0题同状态，不代表完整第六课。源 canvas为`[301.8055419921875,161,118,175]`。原生01为`[300,181.5,120,150]`；02修正尺寸，03接入源 transform 后为`[302,181.5,118,175]`。原版实际 CSS 显示标题32px、40px行高，旧Swift标题28点且多留一段间距；修正后04为`[302,161,118,175]`。

当前9项契约为 **3pass / 1fail / 5not_run**。0.1944580078125点横向差仍失败，零容差未改变。04的12张 idle /12张 feedback 实际原生截图，角色ROI分别有8/12种RGB像素；证明应用实际播放了变化的角色画面，不能证明与源动画相位或声学输出一致。`pixel-and-motion-result.json`保存测量，两张整页同视口比较均different，不遮罩或设通过阈值。AX值为空不能用来声称动画状态正确。

01—04观察保留失败迭代。`full-initial-*`为标题修正前的五课回归，`full-final-*`为当前源码从空进度连续走完五课：214状态、walk_error=null，最终2红心、五课completedLessons、completedCourses为空。共享v10共752项：**434pass / 11fail / 307not_run，整体fail**。`full-final-en-zh-q3-*`与q6截图分别保存Bea/Lucy实际显示。

标题调整后独立听音配对回归 **14pass / 0fail / 4not_run**，原有按钮几何仍通过；15项核心业务检查通过。这些独立组件结果不与全程回执相加。仍失败的产品动作、几何和未覆盖视觉/音频需求全部保留。

## 复跑

仓库根，macOS 14+ / Swift6；像素分析另需 Pillow。首次 SwiftPM 构建下载官方SDK二进制约108MB，Package.resolved锁定版本；SDK及缓存不入Git。SwiftPM把RiveRuntime.framework放到可执行文件旁，直接运行时保留整个构建目录及资源bundle。

```sh
python3 projects/duolingo-web/compile-english-character-probe.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
artifacts/observe-frontend artifacts/character-recheck projects/duolingo-web/fixture-english-character-probe.json --walk-course --capture-character-frames --seed-progress projects/duolingo-web/evidence/english-character-render-v1/initial-progress.json --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-character-v1.json --observed artifacts/character-recheck/observed.json --out artifacts/character-recheck/frontend-result.json
python3 projects/duolingo-web/compare-character-render.py --native artifacts/character-recheck --out artifacts/character-recheck/pixel-and-motion-result.json
artifacts/observe-frontend artifacts/rive-five-recheck projects/duolingo-web/fixture-reference-en-zh-v6.json --walk-course --english-first-wrong --english-fifth-mixed-errors --exercise-duplicate-words --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v10.json --observed artifacts/rive-five-recheck/observed.json --out artifacts/rive-five-recheck/frontend-result.json
```

前端命令预期非零失败；输出目录需不存在。源码捕获可在自己的已打开CLI session上执行`node projects/duolingo-web/capture-source-canvas.mjs --cli <playwright-cli-wrapper> --session <session-name> --out artifacts/<fresh-name>`。原始stdout留在忽略目录，公开证据不保存base64或本机路径。Swift SDK接入时两次表达式类型检查超时，通过拆出状态、AnyView与直接RiveViewRepresentable构建解决；未改变源动画或契约。

## 接续

源浏览器停在第六课第1题 Hello.，未作答。继续实际探索该课及录音/剩余页面，追查其他角色和结算渲染器，把发现转成同状态前端与业务需求。完善实际音频、动画时序、主页/次要操作和持续探索机制；随后固定起点、预算和评价做真实探索消融。Goal保持active，五课和两名角色都不是范围上限。
