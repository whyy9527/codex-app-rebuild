# 英语原生首课执行（2026-10-10）

从英语首课真实公开内容、控件顺序、反馈及原始截图编译15题，Swift默认现在读取`fixture-reference-en-zh-v1.json`。默认普通进度按夹具名隔离，历史西语进度不再混入英语初态。`default-startup.json`是未提供--fixture的实际启动检查，确认课程标题“提供或接受饮料”；这只是默认入口检查。

## 证据和结果

- `observed.json`：真实原生AX回放，首题选sugar，扣心5→4；其余14题答对；最后咖啡题重练接受，红心仍4。`all-correct-observed.json`单独记录全对轨迹，不能混作首题错误状态的视觉基准。观察器收集了历史设置/Guidebook页面，它们不是英语等价实现。
- `en-zh-q*-before.png`、`*-feedback.png`：逐题真实原生截图；包含1200×732内容区域及原生标题栏，原始PNG2400×1528。`window.json`记录32点标题栏、2x backing scale。源PNG是1200×732，不直接拿整窗PNG计算差异。
- `frontend-result.json`与全对回执：同一`frontend-english-v1.json`比较器，15文字通过，59not_run，整体fail。59项不是已完成；源红心教学、题间鼓励、完整完成链、主页等还未移植。
- `pixel-differences.json`：原版与首题错误的原生轨迹逐题配对，28对全部different。只按实测窗口矩形裁掉标题栏并Lanczos缩到1x，无内容遮罩、无任意放宽阈值。像素诊断记录差异，不替代可执行前端验收；动画/声学未对齐，不宣称像素误差是纯实现误差。
- Swift构建通过，7项核心业务检查通过，包含英语15题错误/重练、资源/语言元数据及Codable保留。核心检查不能证明真实音效或视觉。
- `receipt.json`汇总本批范围。全UI回放之后只改了启动默认夹具/进度命名空间并重建，未改题面实现；默认入口随后单独实际验证。资源及所有源题目仍版本化保存，未删除旧回归断言。

## 资源和数据

`compile-english-course.py`交叉确认源API/实际UI，生成Swift夹具。原API白名单遗漏dialogue正文；`english-v1/dialogue-public-ui.json`明确标注原始PNG直接转录问句及实际播放URL，没有假装接口已保存。每个选项直接引用源图片，避免词语全局映射误配。`reference-assets-en-zh-v1.json`列出34个公共源资源：21音频、13SVG；`english-v1/resources.json`登记原件和透明3x PNG哈希。`fetch-english-resources.py --cli PATH --session OWNED_SESSION`在隔离browser context渲染原SVG，不改参考会话。

## 复跑

在仓库根使用新的输出目录（不会覆盖旧回执）：

```sh
python3 projects/duolingo-web/compile-english-course.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/my-english-run projects/duolingo-web/fixture-reference-en-zh-v1.json --walk-course --english-first-wrong
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v1.json --observed artifacts/my-english-run/observed.json --out artifacts/my-english-run/frontend-result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/my-english-run --out artifacts/my-english-run/pixel-differences.json
```

前端比较当前预期返回失败，不能把后续诊断命令的零退出码冒充验收通过。原生截图需已有本机AX/屏幕权限；这里只控制自有子进程，结束自动关闭。

## 下一步

英语主页/首节点四课与后续课程、发音入口、红心教学、鼓励、完成链、真正匹配原版的字体/布局/气泡/反馈以及声音输出仍未完成。Guidebook目前仍是历史西语页面，不能冒充英语指南。新听力按钮/对话气泡已能交互，但播放、慢速和所有分支还没有前端/声学验收。源观察不止于15题，后续持续探索，原RSI研究与真实消融目标不缩减。
