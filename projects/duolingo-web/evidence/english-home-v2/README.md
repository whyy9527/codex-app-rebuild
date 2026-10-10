# 英语主页与节点弹层（2026-10-10）

原版保持首课完成后的匿名状态：首节点Lesson 2 of 4，英语分数5、连胜1、宝石505、红心4，1200×732浅色。`english-home-v2.json`记录稳定主页、源资源及节点实际几何；两个PNG记录原版主页和节点弹层。`english-next-node-open.json`记录真正点击节点后出现标题、“第 2/4 单元”和“开始 +10 经验”链接。读节点时通用role/name匹配到包装器和内层button两个元素；随后按实际data-test明确选中，未重置状态。

Swift主页现在使用中文导航/卡片、英语旗帜、发音源图、五节点顺序（lesson、lesson、chest、practice、review）、首节点四课环和开始弹层。课程`home`与`pathNodes.lessonCount`保存参考元数据，不为未知后续课编造题目。候选第2课尚未编译，弹层开始按钮仍不可用；源可用，该差异明确失败。

## 首次失败与修正

`first-*`保留首轮原生AX、PNG及比较：15通过、8失败、75未执行（v2契约）。源两个新SVG返回gzip编码，下载器此前直接按SVG文本验证而失败，导致问号；已解码后渲染并登记原件/PNG哈希。源浏览器实际prefers-color-scheme dark=false且白底；原生首次继承宿主深色。现在测试显式传`--reference-color-scheme light`匹配环境，没有修改普通用户System Default设置。中文导航此前可见但AX标签是英语，且透明行只让内容可点击；已改成同样的中文标签和完整行hit shape。

`fixed-*`：v2文案21、导航几何2，共23通过，75未执行（含本次未走的15题）；源文案与几何断言没有放宽。`popover-*`：v2.1增加弹层3条文字和start_enabled断言，26通过、1失败、75未执行，失败为第2课开始不可用。`popover-draft-contract.json`保留中途比较使用的草稿，正式v2与v2.1分别版本化；`popover-frontend-result-v2.1.json`对应正式最终契约。

`popover-pixel-differences.json`按实际内容矩形去标题栏/2x缩至1x，主页与原版仍different；不遮罩、未设宽松阈值。字体、头像动画/静态帧、细节几何与完整行为仍未等价。`course-*`是新主页入口经弹层开始首课的实际原生错误/重练回归，15题标题通过，59未覆盖；7项核心业务检查通过。

## 复跑

```sh
swift build --package-path projects/education-swift
swift projects/duolingo-web/observe-frontend.swift artifacts/my-home-run projects/duolingo-web/fixture-reference-en-zh-v1.json --seed-progress projects/duolingo-web/evidence/english-home-v2/progress-after-first.json --reference-color-scheme light --observe-home-popover
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v2.1.json --observed artifacts/my-home-run/observed.json --out artifacts/my-home-run/result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/my-home-run --out artifacts/my-home-run/pixels.json --home-reference projects/duolingo-web/evidence/english-home-v2/reference-english-home-v2.png
```

比较器当前预期失败。原生后续页/Guidebook仍有历史实现，不能将主页局部改善称为全App一致。原版下一课已实际探索，发现静态API列表与实际挑战题尾部发生分歧，见`../english-second-v1/README.md`；下一步从真实题目轨迹编译第2课，修复本次明确失败，继续补页面、音频和动态探索。
