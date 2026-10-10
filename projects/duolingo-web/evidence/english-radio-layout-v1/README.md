# 听力选项：原版选中状态与几何补漏

本批在实现前依据已冻结原版 q3 的 DOM/ARIA 与 PNG，新增 `frontend-english-v15.json`：保留 v14 全部1489项，再加四项 checked 与四项零容差几何，共1497项。原版答题前两个 radio 未选中；反馈第二项 checked，两项 disabled；两个 DOM rect 分别为 `[300,406.5,600,62]` 与 `[300,476.5,600,62]`。原版事实回放358通过、0失败、1139未覆盖；不是重新操作原版全课程。

## 实际原生验证

`before` 保存新增观察器但未修布局的真实运行：checked 四项已通过，四项几何失败；旧 AX rect 为602×64。`insets-no-effect` 保存尝试改变 NSButton alignmentRectInsets 无效的反例，该尝试已撤回。

`bounds-fixed` 来自重新构建后实际点击 radio2 并接受的回放。NSButton 默认 AX frame 包含绘制边界外的焦点边距；现在将 AX frame 绑定实际视图 bounds，并按原版62高、8间距及角色区后的实际位置修复布局。两个控件在答题前/反馈后的四项几何均零差异，四项 checked 均通过；观察器保留实际 NSNumber 0/1，再序列化 checked，未知值不算 false。

聚焦夹具只有实际第七课 q3，用来隔离控件修复，并未替代默认七课。全契约在此局部回放为50通过、4失败、1443未覆盖；四个失败涉及缩短课程带来的主页任务/排行榜/连对状态，以及仍缺失的“现在不做听力题”。不能将上一构建的430状态全课程结果归给本次新构建。

两对同视口截图仍全部 different，未经遮罩或容差。原版反馈会补出 ice、选中项变绿，候选仍为空缺/蓝色，角色动画及题头、进度、反馈视觉仍有差异。几何和 checked 通过不证明整页通过。正常口语、radio1 声音、实际应用声学与 RSI 探索消融仍待完成。

## 复跑

```sh
projects/duolingo-web/run-native-course.sh artifacts/radio-new \
  projects/duolingo-web/evidence/english-radio-layout-v1/fixture-radio-probe.json \
  --walk-course --stop-after-question-id en-zh-l7-q3 --reference-color-scheme light
python3 -m capabilities.rebuild.frontend \
  --contract projects/duolingo-web/frontend-english-v15.json \
  --observed artifacts/radio-new/observed.json --out artifacts/radio-new/frontend-result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/radio-new \
  --pairs projects/duolingo-web/evidence/english-radio-layout-v1/pairs.json \
  --out artifacts/radio-new/visual-result.json
```

Swift产品构建通过；21业务检查与49框架测试通过，均不代替前端验证。所有原生观测绑定实际二进制/夹具哈希。

## 字体假设检查

`swift projects/duolingo-web/inspect-native-font.swift` 用与候选相同的已注册字体、字重与字号，通过 CoreText 对挑战入口文字排版。结果同样回退为 PingFangSC-Semibold，18字形，字号28；原版入口 CDP 为同字体、字号24。此处证明字体配置的实际回退与字号差异，不是检查 SwiftUI 已渲染字形，也不能推广到其它题面。因此本批没有盲目替换中文字体；应先按具体状态核对字号及布局。
